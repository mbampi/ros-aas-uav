//go:build opcua

package proxy

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/gopcua/opcua"
	"github.com/gopcua/opcua/monitor"
	"github.com/gopcua/opcua/ua"
)

const (
	opcuaServerURL = "opc.tcp://127.0.0.1:4840" // OPC UA port of the system under test
	outLogFileName = "out_log.csv"
)

// Example node IDs. Replace them with the ones your server exposes.
var nodesToMonitor = []string{
	"ns=3;s=AAS/Submodels/0/OperationalData/GlobalPosition/Latitude",
	"ns=3;s=AAS/Submodels/0/OperationalData/GlobalPosition/Longitude",
	"ns=3;s=AAS/Submodels/0/OperationalData/GlobalPosition/AltitudeMSL",
	"ns=3;s=AAS/Submodels/0/OperationalData/PowerSystem/Voltage",
	"ns=3;s=AAS/Submodels/0/OperationalData/PowerSystem/Current",
	"ns=3;s=AAS/Submodels/0/OperationalData/PowerSystem/PercentageRemaining",
}

// OutLogEntry is one line of the output log
type OutLogEntry struct {
	Timestamp int64       `json:"t_out_ns"`
	NodeID    string      `json:"node_id"`
	Value     interface{} `json:"value"`
}

var logger *log.Logger

// RunOutProxy starts the OPC UA monitor that logs data change notifications.
// Returns an error for fatal setup failures; runtime errors are logged.
func RunOutProxy() error {
	logFile, err := os.OpenFile(outLogFileName, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}
	defer logFile.Close()
	logger = log.New(logFile, "", 0)
	logger.Println(`{"level":"info", "message":"OPC UA Output Logger Started"}`)

	fmt.Printf("Connecting to %s. Logging to %s\n", opcuaServerURL, outLogFileName)

	ctx := context.Background()
	c, err := opcua.NewClient(opcuaServerURL, opcua.SecurityMode(ua.MessageSecurityModeNone))
	if err != nil {
		return fmt.Errorf("failed to create OPC UA client: %w", err)
	}
	if err := c.Connect(ctx); err != nil {
		return fmt.Errorf("failed to connect: %w", err)
	}
	defer c.Close(ctx)

	// 10ms interval to catch data as fast as possible
	m, err := monitor.New(c, opcua.TimeInterval(10*time.Millisecond))
	if err != nil {
		return fmt.Errorf("failed to create monitor: %w", err)
	}
	m.SetErrorHandler(func(_ *opcua.Client, s *monitor.Subscription, err error) {
		log.Printf("subscription error: sub=%d err=%v", s.SubscriptionID(), err)
	})

	if err := m.Start(ctx); err != "context canceled" && err != nil {
		return fmt.Errorf("failed to start monitor: %w", err)
	}
	defer m.Close(ctx)

	fmt.Println("Subscribing to nodes...")
	for _, nodeID := range nodesToMonitor {
		err := monitorNode(ctx, m, nodeID)
		if err != nil {
			log.Printf("Failed to monitor node %s: %v", nodeID, err)
		} else {
			fmt.Printf("  -> Subscribed to: %s\n", nodeID)
		}
	}

	fmt.Println("Listening for data changes... Press Ctrl+C to stop.")
	// Keep the program alive until context canceled
	<-ctx.Done()
	return nil
}

// monitorNode sets up the subscription for a single node
func monitorNode(ctx context.Context, m *monitor.Monitor, nodeID string) error {
	handler := func(s *monitor.Subscription, item *monitor.MonitoredItem, data *ua.DataValue) {
		t_out := time.Now().UnixNano()

		nodeID := item.NodeID().String()
		value := data.Value.Value()

		entry := OutLogEntry{
			Timestamp: t_out,
			NodeID:    nodeID,
			Value:     value,
		}

		line, err := json.Marshal(entry)
		if err != nil {
			log.Printf("Error marshaling log entry: %v", err)
			return
		}
		logger.Println(string(line))
	}

	// 0ms sampling interval to get data as fast as the server provides it
	_, err := m.Subscribe(ctx, opcua.TimeInterval(0), handler, nodeID)
	return err
}

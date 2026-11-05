package proxy

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"time"
)

const (
	listenAddr    = "127.0.0.1:14550" // Port for SITL to send to
	forwardAddr   = "127.0.0.1:14551" // Port the system under test listens on
	inLogFileName = "in_log.csv"
)

// Names of common MAVLink message IDs
var mavlinkMessageNames = map[uint32]string{
	0:   "HEARTBEAT",
	1:   "SYS_STATUS",
	11:  "SET_MODE",
	20:  "PARAM_REQUEST_READ",
	21:  "PARAM_REQUEST_LIST",
	22:  "PARAM_VALUE",
	23:  "PARAM_SET",
	24:  "GPS_RAW_INT",
	25:  "GPS_STATUS",
	26:  "SCALED_IMU",
	27:  "RAW_IMU",
	28:  "RAW_PRESSURE",
	29:  "SCALED_PRESSURE",
	30:  "ATTITUDE",
	31:  "ATTITUDE_QUATERNION",
	32:  "LOCAL_POSITION_NED",
	33:  "GLOBAL_POSITION_INT",
	34:  "RC_CHANNELS_SCALED",
	35:  "RC_CHANNELS_RAW",
	36:  "SERVO_OUTPUT_RAW",
	39:  "MISSION_ITEM",
	42:  "MISSION_CURRENT",
	44:  "MISSION_COUNT",
	47:  "MISSION_ACK",
	65:  "RC_CHANNELS",
	66:  "REQUEST_DATA_STREAM",
	67:  "DATA_STREAM",
	70:  "HIL_STATE",
	74:  "VFR_HUD",
	76:  "COMMAND_LONG",
	77:  "COMMAND_ACK",
	83:  "ATTITUDE_TARGET",
	105: "HIGHRES_IMU",
	147: "BATTERY_STATUS",
	241: "VIBRATION",
	242: "HOME_POSITION",
	253: "STATUSTEXT",
}

// InLogEntry is one line of the input log
type InLogEntry struct {
	Timestamp int64  `json:"t_in_ns"`
	MsgID     uint32 `json:"msg_id"`
	MsgName   string `json:"msg_name"`
	PacketHex string `json:"packet_hex"`
}

// logWriter runs in its own goroutine to write to the file
func logWriter(logChan <-chan *InLogEntry, logger *log.Logger) {
	for entry := range logChan {
		// One JSON object per line
		line, err := json.Marshal(entry)
		if err != nil {
			log.Printf("Error marshaling log entry: %v", err)
			continue
		}
		logger.Println(string(line))
	}
}

// RunInProxy starts the input UDP proxy which forwards packets and logs MAVLink metadata.
// It returns an error only on fatal setup failures; runtime errors are logged.
func RunInProxy() error {
	logFile, err := os.OpenFile(inLogFileName, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}
	logger := log.New(logFile, "", 0)
	logger.Println(`{"level":"info", "message":"MAVLink Input Logger Started (Raw Parser)"}`)

	logChan := make(chan *InLogEntry, 2048)
	go func() {
		logWriter(logChan, logger)
		logFile.Close()
	}()

	fwdAddr, err := net.ResolveUDPAddr("udp", forwardAddr)
	if err != nil {
		return fmt.Errorf("failed to resolve forward address: %w", err)
	}
	conn, err := net.ListenPacket("udp", listenAddr)
	if err != nil {
		return fmt.Errorf("failed to listen: %w", err)
	}
	defer conn.Close()

	fmt.Printf("Listening on %s. Forwarding to %s. Logging to %s\n", listenAddr, forwardAddr, inLogFileName)

	buffer := make([]byte, 4096)

	for {
		n, _, err := conn.ReadFrom(buffer)
		if err != nil {
			log.Printf("Error reading from UDP: %v", err)
			continue
		}

		t_in := time.Now().UnixNano()

		// Forward first, so logging doesn't add latency
		_, err = conn.WriteTo(buffer[:n], fwdAddr)
		if err != nil {
			log.Printf("Error forwarding packet: %v", err)
		}

		packet := buffer[:n]
		var msgID uint32
		var msgName string

		if n < 8 { // Too small for any MAVLink packet
			continue
		}

		if packet[0] == 0xFE { // MAVLink v1
			payloadLen := int(packet[1])
			if n != 8+payloadLen { // Header 6 + CRC 2 + payload
				continue // Invalid length
			}
			msgID = uint32(packet[5])
		} else if packet[0] == 0xFD { // MAVLink v2
			payloadLen := int(packet[1])
			if n < 12+payloadLen { // Header 10 + CRC 2 + payload (ignore signature)
				continue // Invalid length
			}
			// Extract 24-bit MAVLink v2 message ID
			msgID = uint32(packet[7]) | (uint32(packet[8]) << 8) | (uint32(packet[9]) << 16)
		} else {
			continue // Not a MAVLink packet
		}

		name, ok := mavlinkMessageNames[msgID]
		if !ok {
			name = "Unknown"
		}
		msgName = name

		entry := &InLogEntry{
			Timestamp: t_in,
			MsgID:     msgID,
			MsgName:   msgName,
			PacketHex: hex.EncodeToString(packet), // Log the raw packet as hex
		}

		// Non-blocking, so a full channel can't delay forwarding
		select {
		case logChan <- entry:
		default:
			log.Println("Log channel full. Dropping MAVLink log entry.")
		}
	}
}

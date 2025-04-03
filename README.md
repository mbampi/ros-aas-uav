# AAS Gateway

## Description

This repository contains the implementation of an OPC UA server and a ROS2 AAS Gateway. The OPC UA server is used to simulate an AAS provider, while the ROS2 AAS Gateway is used to connect the OPC UA server to a ROS2 network.

### AAS Gateway

The AAS Gateway is a ROS2 node that subscribes to multiple ROS Topics that contain data from the UAV. The AAS Gateway then sends this data to the OPC UA server, which is the AAS provider.

### UAV Publisher

The UAV Publisher is a ROS2 node that publishes data from the UAV to multiple ROS Topics.
In this example, the UAV Publisher simulates an UAV System publishing randomized synthetic data to the following ROS Topics:
- speed
- altitude
- battery

### OPC UA Server

The OPC UA server is a Python script that simulates an AAS provider. It waits for the AAS Gateway to connect and send the data from the UAV. The OPC UA server then prints the received data.

### Configuration

The main fields needed for the service are:
- Topic: The ROS Topic used by the UAV System to communicate the data. It is used by the AAS Gateway to subscribe to the data.
- NodeSet Identifier: The NodeSet Identifier used by the OPC UA server to identify the data. It is used by the AAS Gateway to send the data to the OPC UA server.
   - Example: "ns=2;s=Speed"
- Property: The AAS Property used to map the data. It is used by the AAS Gateway to send the data to the OPC UA server.
-  

To map the data throghout the system, the AAS Gateway uses the mapping "topic <-> property"
Where the topic is the ROS Topic and the property is the AAS property. 

## How to Run

### Run OPC UA Server

```bash
python3 opcua/server.py
```

### Run ROS2 AAS Gateway

```bash
cd ros2
pixi run aas_gateway
```

### Run ROS2 UAV Publisher

```bash
cd ros2
pixi run pub
```

### Collect metrics

interactive CLI
```bash
glances
```

export to csv metrics of the python processes
```bash
glances --export csv --export-csv-file ./glances.csv --quiet --export-process-filter "python.*"
```

## Performance

Published from UAV: 1739652619.386628
Received in AAS Gateway: 1739652619.399873 
Sent from AAS Gateway to Server: 1739652619.402693
Received in AAS Server: 1739652619.711016

The total latency is 324.39 milliseconds (ms) => 0.32439 s

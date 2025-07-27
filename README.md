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

## Configuration

The configuration for the AAS Gateway and the OPC UA server is done through YAML files. These files define the mapping between the ROS Topics and the AAS Properties.

### Asset Administration Shell Specification

The AAS Specification is defined by the NodeSet XML file. This file contains the structure of the AAS, including the Asset Information, Submodels, and Properties.

### Topics to AAS Properties Mapping

The mapping between the ROS Topics and the AAS Properties is defined in the `map.yaml` file. This file specifies which ROS Topic corresponds to which AAS Property.

## How to Run

### Run OPC UA Server

```bash
python3 opcua/server_from_file.py
```

### Run with Docker Compose

Run the following command to build and start the Docker containers for the ROS2 AAS Gateway and the mock publisher:
```bash
cd ros2
docker-compose up --build
```
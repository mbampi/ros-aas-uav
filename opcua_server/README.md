
# OPC UA Server

## Overview

This is a simple OPC UA server that can be used to test the ROS2 AAS Gateway. It is built using the `opcua` library and provides a basic structure for creating an OPC UA server with nodes and variables.
It is designed to load a XML file that defines the structure of the server and its nodes. It also loads a YAML file that defines the variables that will be used in the server.

## How to run the server

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Make sure you have the required dependencies installed. You can install them using pip:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server using the following command:
   ```bash
   python opcua_server.py
   ```
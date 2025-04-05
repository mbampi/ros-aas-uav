
# OPC UA Server

## Overview

This is a simple OPC UA server that can be used to test the ROS2 AAS Gateway. It is built using the `opcua` library and provides a basic structure for creating an OPC UA server with nodes and variables.
It is designed to load a XML file that defines the structure of the server and its nodes. It also loads a YAML file that defines the variables that will be used in the server.

## Setup

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Make sure you have the required dependencies installed. You can install them using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the server, use the following command:
```bash
python opcua_server.py
```
This will start the OPC UA server and load the XML and YAML files specified in the code. The server will listen on the specified endpoint and provide access to the nodes and variables defined in the XML and YAML files.

`$ python3 server_from_file.py --help`

```bash
usage: server_from_file.py [-h] [--endpoint ENDPOINT]
                           [--namespace NAMESPACE] [--xml XML]
                           [--yaml YAML]

Run OPC UA Server with YAML + XML configuration

options:
  -h, --help            show this help message and exit
  --endpoint ENDPOINT   Server endpoint URL
  --namespace NAMESPACE
                        Namespace URI
  --xml XML             Path to XML NodeSet file
  --yaml YAML           Path to YAML variable map file
```
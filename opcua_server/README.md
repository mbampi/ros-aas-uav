
# OPC UA Server

## Overview

This is a simple OPC UA server that can be used to test the ROS2 AAS Gateway. It is built using the `opcua` library and provides a basic structure for creating an OPC UA server with nodes and variables.
It is designed to load a XML file that defines the structure of the server and its nodes. It also loads a YAML file that defines the variables that will be used in the server.

## Setup

1. Set your virtual environment:
   ```bash
   python3 -m venv venv
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the server:
   ```bash
   python3 opcua_server.py
   ```

## Usage

`$ python3 opcua_server.py --help`

```bash
usage: opcua_server.py [-h] [--endpoint ENDPOINT]
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
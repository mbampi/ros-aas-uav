# OPC UA Server for UAV AAS

OPC UA server implementation for UAV Asset Administration Shell (AAS) with optional web dashboard for real-time monitoring.

## Features

- **Standards Compliant**: OPC UA server implementation with AAS support
- **Dynamic Configuration**: XML NodeSet + YAML mapping for flexible setup
- **Web Dashboard**: Optional real-time visualization and monitoring
- **Data Logging**: JSONL format logs with timestamps and latency measurements
- **Dual Mode**: CLI-only or web-enabled operation

## Quick Start

### Setup

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

**CLI-only mode:**
```bash
python opcua_server.py
```

**With web dashboard:**
```bash
python opcua_server.py --ui
```
Then open http://127.0.0.1:5000 in your browser.

## Command Line Options

```bash
usage: opcua_server.py [-h] [--endpoint ENDPOINT] [--namespace NAMESPACE] 
                       [--xml XML] [--yaml YAML] [--ui] [--ui-host UI_HOST] 
                       [--ui-port UI_PORT]

Options:
  --endpoint TEXT     Server endpoint URL (default: opc.tcp://0.0.0.0:4840/freeopcua/server/)
  --namespace TEXT    Namespace URI (default: http://aas-example.org)
  --xml TEXT          Path to XML NodeSet file (default: uav_submodel.xml)
  --yaml TEXT         Path to YAML variable map file (default: map.yaml)
  --ui                Enable web UI dashboard
  --ui-host TEXT      Web UI host (default: 127.0.0.1)
  --ui-port INTEGER   Web UI port (default: 5000)
```

## Web Dashboard

The optional web dashboard provides real-time visualization of UAV data:

### Features
- **Live Data Display**: Real-time updates of all OPC UA variables
- **Interactive Charts**: Time-series visualization for battery, altitude, speed, attitude
- **Statistics Dashboard**: Event counts, timestamps, and current values
- **Event Log**: Real-time streaming log of variable changes

### Dashboard Sections
- **Summary Cards**: Total events, active properties, server uptime
- **Properties Grid**: Current values and statistics per UAV parameter
- **Real-time Charts**: Dynamic plots for key UAV metrics
- **Event Log**: Live stream of all variable changes

### Access
When running with `--ui`, access the dashboard at:
- **Local**: http://127.0.0.1:5000
- **Remote**: http://YOUR_HOST:YOUR_PORT

## Configuration

**YAML Mapping (map.yaml)**: Maps ROS topics to OPC UA properties.

**XML NodeSet (uav_submodel.xml)**: Defines OPC UA nodes and variables according to AAS standards.

## Examples

### Basic UAV Monitoring
```bash
# Start server with web dashboard
python opcua_server.py --ui

# Connect ROS2 AAS Gateway to: opc.tcp://0.0.0.0:4840/freeopcua/server/
# View dashboard at: http://127.0.0.1:5000
```

### Production Deployment
```bash
# Run with UI accessible from network
python opcua_server.py --ui --ui-host 0.0.0.0 --ui-port 8080
```

### Development/Testing
```bash
# CLI-only mode for testing
python opcua_server.py --endpoint opc.tcp://localhost:4840/test/
```

## File Structure

```
opcua_server/
├── opcua_server.py          # Main server with UI integration
├── web_ui.py                # Web UI components  
├── static/                  # Web dashboard files
├── requirements.txt         # Core dependencies
├── map.yaml                # Variable mapping config
├── uav_submodel.xml        # OPC UA NodeSet
└── metrics/                # Generated logs
```

## Troubleshooting

**Port already in use:**
```bash
python opcua_server.py --ui --ui-port 8080
```

**Dashboard not loading:**
1. Check server startup logs
2. Verify correct URL (host:port)
3. Check browser console for errors

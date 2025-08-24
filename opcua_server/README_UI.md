# UAV OPC UA Server with Web Dashboard

This OPC UA server for UAV data monitoring now includes an optional web-based dashboard that provides real-time visualization and monitoring of OPC UA variables.

## Features

### Core OPC UA Server
- **Standards Compliant**: Full OPC UA server implementation
- **Dynamic Configuration**: XML NodeSet + YAML mapping for flexible variable setup
- **Data Logging**: JSONL format logs with timestamps and latency measurements
- **CLI Operation**: Traditional command-line interface preserved

### Web Dashboard (Optional)
- **Real-time Data Display**: Live updates of all OPC UA variables
- **Interactive Charts**: Time-series visualization for numeric data (battery, altitude, speed, attitude)
- **Statistics Dashboard**: Event counts, last values, update timestamps per property
- **Event Log**: Real-time streaming log of all variable changes
- **Modern UI**: Responsive design with dark/light themes
- **Socket.IO Integration**: Low-latency real-time updates

## Installation

### Core Dependencies
```bash
pip install -r requirements.txt
```

### Web UI Dependencies (Optional)
To enable the web dashboard, install additional packages:
```bash
pip install flask flask-socketio eventlet
```

## Usage

### CLI-Only Mode (Default)
```bash
# Basic usage - CLI only
python opcua_server.py

# With custom configuration
python opcua_server.py --xml custom_nodes.xml --yaml custom_mapping.yaml --endpoint opc.tcp://0.0.0.0:4840/server/
```

### Web Dashboard Mode
```bash
# Enable web UI on localhost:5000
python opcua_server.py --ui

# Custom UI host/port
python opcua_server.py --ui --ui-host 0.0.0.0 --ui-port 8080

# Full example with all options
python opcua_server.py --ui --ui-host 0.0.0.0 --ui-port 8080 --endpoint opc.tcp://0.0.0.0:4840/uav/server/
```

### Command Line Options
```
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

### Accessing the Dashboard
When running with `--ui`, the web dashboard will be available at:
- **Local**: http://127.0.0.1:5000 (default)
- **Custom**: http://YOUR_HOST:YOUR_PORT

### Dashboard Sections

#### 1. Summary Cards
- **Total Events**: Count of all variable updates received
- **Active Properties**: Number of OPC UA variables currently active
- **Server Uptime**: Time since server started

#### 2. Properties Grid
Each OPC UA variable is displayed in a card showing:
- **Current Value**: Latest received value
- **Event Count**: Number of updates for this property
- **Last Update**: Timestamp of most recent change
- **Node ID**: OPC UA NodeId for debugging

#### 3. Real-time Charts
Dynamic time-series charts for key UAV metrics:
- **Battery Level**: Shows battery percentage over time
- **Altitude**: Displays altitude changes
- **Speed**: Horizontal and vertical speed components
- **Attitude**: Pitch and heading angles

#### 4. Event Log
- **Live Stream**: Real-time log of all variable changes
- **Filtering**: Pause/resume log updates
- **Configurable**: Adjustable maximum entries (50-500)
- **Detailed**: Shows timestamp, variable name, and value

### Data Format
The dashboard expects data in the following JSON format:
```json
{
  "id": "unique-message-id",
  "recv_ts": 1640995200.123,
  "processed_ts": 1640995200.124,
  "value": 85.5
}
```

## Architecture

### Components
1. **OPCUAServer**: Core server with optional UI integration
2. **DataManager**: Thread-safe data storage and statistics
3. **WebUIServer**: Flask-SocketIO web server
4. **UIVariableChangeHandler**: Enhanced handler with UI broadcasting
5. **Dashboard Frontend**: HTML/CSS/JS with Chart.js and Socket.IO

### Data Flow
```
OPC UA Client → OPC UA Server → Variable Handler → Data Manager → Web UI → Browser
                                      ↓
                                 JSONL Log File
```

## File Structure

```
opcua_server/
├── opcua_server.py          # Main server with UI integration
├── web_ui.py                # Web UI components
├── static/                  # Web dashboard files
│   ├── index.html          # Dashboard HTML
│   ├── styles.css          # Styling
│   └── dashboard.js        # Frontend JavaScript
├── requirements.txt         # Dependencies
├── map.yaml                # Variable mapping config
├── uav_submodel.xml        # OPC UA NodeSet
├── metrics/                # Generated logs
│   └── events-*.jsonl      # Event logs
└── opcua_server.log        # Server logs
```

## Configuration

### YAML Mapping (map.yaml)
Maps ROS topics to OPC UA properties:
```yaml
topics_to_properties:
  - property: CurrentBatteryLevel
    topic: /px4_1/fmu/out/battery_status
    # ... other mappings
```

### XML NodeSet (uav_submodel.xml)
Defines OPC UA nodes, variables, and their NodeIds according to OPC UA standards.

## Monitoring & Logging

### Event Logs
- **Location**: `metrics/events-TIMESTAMP.jsonl`
- **Format**: One JSON object per line
- **Contents**: Variable name, value, timestamps, NodeId

### Server Logs
- **Location**: `opcua_server.log`
- **Contents**: Server lifecycle, errors, debug information

### Web UI Logs
- **Browser Console**: Client-side debug information
- **Server Logs**: Flask/SocketIO messages (if debug enabled)

## Troubleshooting

### Common Issues

#### Web UI Dependencies Missing
```
ERROR: Web UI requested but required dependencies not available.
Please install with: pip install flask flask-socketio eventlet
```
**Solution**: Install the optional dependencies as shown above.

#### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution**: Use a different port with `--ui-port PORT` or stop the process using the port.

#### Dashboard Not Loading
1. Check if the server started successfully
2. Verify the URL (check host:port in server logs)
3. Check browser console for JavaScript errors
4. Ensure static files are in the correct location

### Performance Considerations
- **High Frequency Updates**: Dashboard handles up to 100 updates/second per variable
- **Memory Usage**: History limited to last 50-100 points per variable
- **Network Traffic**: WebSocket compression enabled for efficiency

## Examples

### Basic UAV Monitoring
```bash
# Start server with UI for local monitoring
python opcua_server.py --ui

# Connect OPC UA client to: opc.tcp://0.0.0.0:4840/freeopcua/server/
# View dashboard at: http://127.0.0.1:5000
```

### Production Deployment
```bash
# Run with UI accessible from other machines
python opcua_server.py --ui --ui-host 0.0.0.0 --ui-port 80 --endpoint opc.tcp://0.0.0.0:4840/production/uav/
```

### Development/Testing
```bash
# Run simple server for testing
python simple_server.py

# Connect dashboard to simple server
python opcua_server.py --ui --xml uav_submodel.xml
```

## License & Credits

Built on:
- **python-opcua**: OPC UA server implementation
- **Flask + SocketIO**: Web framework and real-time communication  
- **Chart.js**: Interactive charting library
- **Modern CSS**: Responsive design principles

Compatible with UAV systems running PX4, ROS2, and similar frameworks.

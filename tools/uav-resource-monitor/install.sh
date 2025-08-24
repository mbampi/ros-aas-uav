#!/bin/bash
"""
UAV Resource Monitor Installation Script
Sets up the monitoring system on Raspberry Pi
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/uav-resource-monitor"
SERVICE_USER="uav-monitor"
PYTHON_BIN="/usr/bin/python3"

echo -e "${BLUE}UAV Resource Monitor Installation Script${NC}"
echo "========================================"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
   exit 1
fi

echo -e "${YELLOW}Installing system dependencies...${NC}"

# Update package list
apt-get update

# Install Python and pip if not present
apt-get install -y python3 python3-pip python3-venv

# Install system packages needed for Python dependencies
apt-get install -y python3-dev build-essential

# Install system monitoring tools
apt-get install -y htop iotop

echo -e "${YELLOW}Creating installation directory...${NC}"

# Create installation directory
mkdir -p "$INSTALL_DIR"
cp -r . "$INSTALL_DIR/"

# Create virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${YELLOW}Creating service user...${NC}"

# Create service user (if doesn't exist)
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
fi

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Make scripts executable
chmod +x "$INSTALL_DIR"/scripts/*.py

echo -e "${YELLOW}Installing systemd service...${NC}"

# Create systemd service file
cat > /etc/systemd/system/uav-resource-monitor.service << EOF
[Unit]
Description=UAV Resource Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/scripts
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/scripts/resource_monitor.py --config $INSTALL_DIR/config/monitor_config.json --session-id auto
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable uav-resource-monitor.service

echo -e "${YELLOW}Creating command-line aliases...${NC}"

# Create convenient command-line tools
cat > /usr/local/bin/uav-monitor << 'EOF'
#!/bin/bash
# UAV Resource Monitor CLI tool

INSTALL_DIR="/opt/uav-resource-monitor"
PYTHON_BIN="$INSTALL_DIR/venv/bin/python"
MONITOR_SCRIPT="$INSTALL_DIR/scripts/resource_monitor.py"
STATS_SCRIPT="$INSTALL_DIR/scripts/stats_generator.py"
CONFIG_FILE="$INSTALL_DIR/config/monitor_config.json"

case "$1" in
    start)
        echo "Starting UAV Resource Monitor..."
        sudo systemctl start uav-resource-monitor.service
        echo "Monitor started. Use 'uav-monitor status' to check status."
        ;;
    stop)
        echo "Stopping UAV Resource Monitor..."
        sudo systemctl stop uav-resource-monitor.service
        echo "Monitor stopped."
        ;;
    restart)
        echo "Restarting UAV Resource Monitor..."
        sudo systemctl restart uav-resource-monitor.service
        echo "Monitor restarted."
        ;;
    status)
        sudo systemctl status uav-resource-monitor.service
        ;;
    run)
        shift
        sudo -u uav-monitor $PYTHON_BIN $MONITOR_SCRIPT --config $CONFIG_FILE "$@"
        ;;
    analyze)
        shift
        sudo -u uav-monitor $PYTHON_BIN $STATS_SCRIPT --data-dir $INSTALL_DIR/data --output-dir $INSTALL_DIR/reports "$@"
        ;;
    logs)
        journalctl -u uav-resource-monitor.service -f
        ;;
    data)
        ls -la $INSTALL_DIR/data/
        ;;
    reports)
        ls -la $INSTALL_DIR/reports/
        ;;
    *)
        echo "UAV Resource Monitor CLI"
        echo "Usage: uav-monitor {start|stop|restart|status|run|analyze|logs|data|reports}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the monitoring service"
        echo "  stop      - Stop the monitoring service"
        echo "  restart   - Restart the monitoring service"
        echo "  status    - Show service status"
        echo "  run       - Run monitor manually with custom options"
        echo "  analyze   - Analyze collected data and generate reports"
        echo "  logs      - Show real-time service logs"
        echo "  data      - List available data files"
        echo "  reports   - List generated reports"
        echo ""
        echo "Examples:"
        echo "  uav-monitor run --duration 300 --session-id flight-test-1"
        echo "  uav-monitor analyze data/resource_metrics_flight-test-1.csv"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/uav-monitor

echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo "Usage:"
echo "  uav-monitor start          # Start monitoring service"
echo "  uav-monitor run --help     # Run monitor manually"
echo "  uav-monitor analyze        # Analyze collected data"
echo "  uav-monitor status         # Check service status"
echo ""
echo "Configuration file: $INSTALL_DIR/config/monitor_config.json"
echo "Data directory: $INSTALL_DIR/data/"
echo "Reports directory: $INSTALL_DIR/reports/"
echo ""
echo -e "${YELLOW}Note: You can start monitoring now with:${NC} uav-monitor start"

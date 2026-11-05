#!/bin/bash
# Sets up the UAV Resource Monitor for local development and testing

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed"
    exit 1
fi

echo "Installing Python dependencies..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p data logs reports

chmod +x scripts/*.py

echo ""
echo "Local setup completed."
echo ""
echo "Quick Start:"
echo "  python3 scripts/quick_monitor.py       # Show current status"
echo "  python3 scripts/quick_monitor.py --live # Live monitoring"
echo ""
echo "Full Monitoring:"
echo "  python3 scripts/resource_monitor.py --session-id test --duration 60"
echo "  python3 scripts/stats_generator.py data/resource_metrics_test_*.csv"

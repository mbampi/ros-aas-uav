#!/bin/bash
"""
Local Setup Script for UAV Resource Monitor
Sets up the monitoring system for local development/testing
"""

echo "🚁 UAV Resource Monitor - Local Setup"
echo "====================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "📦 Installing Python dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created virtual environment"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Create data and logs directories
mkdir -p data logs reports

echo "✅ Directory structure created"

# Make scripts executable
chmod +x scripts/*.py

echo "✅ Scripts made executable"

echo ""
echo "🎉 Local setup completed!"
echo ""
echo "Quick Start:"
echo "  python3 scripts/quick_monitor.py       # Show current status"
echo "  python3 scripts/quick_monitor.py --live # Live monitoring"
echo ""
echo "Full Monitoring:"
echo "  python3 scripts/resource_monitor.py --session-id test --duration 60"
echo "  python3 scripts/stats_generator.py data/resource_metrics_test_*.csv"

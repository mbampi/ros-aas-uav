# UAV Resource Monitor

A comprehensive system resource monitoring solution designed specifically for Raspberry Pi UAV companion computers. This tool provides real-time monitoring, data collection, and statistical analysis of system performance metrics.

## Features

### 🔍 **Comprehensive Monitoring**
- CPU usage, frequency, and temperature
- Memory and swap utilization
- Disk usage and I/O
- Network throughput and packets
- System load averages
- Process count and uptime
- Raspberry Pi specific metrics (GPU temperature, voltage)

### 📊 **Data Collection**
- Multiple output formats (CSV, JSON)
- Configurable sampling intervals
- Session-based data organization
- Automatic timestamping
- Robust error handling

### 📈 **Statistical Analysis**
- Comprehensive performance statistics
- Time series visualizations
- Distribution analysis
- Correlation heatmaps
- Performance scoring
- Thermal analysis with warnings

### 🚀 **Easy Deployment**
- One-command installation
- Systemd service integration
- Command-line interface
- Live monitoring display
- Quick test functionality

## Installation

### Quick Install (Raspberry Pi)
```bash
# Clone or copy the uav-resource-monitor directory to your Pi
sudo ./install.sh
```

### Manual Installation
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.py
chmod +x install.sh
```

## Usage

### Basic Monitoring

#### Start Background Monitoring Service
```bash
# Start the service
uav-monitor start

# Check status
uav-monitor status

# View logs
uav-monitor logs

# Stop the service
uav-monitor stop
```

#### Manual Monitoring Sessions
```bash
# Run for 5 minutes with custom session ID
uav-monitor run --duration 300 --session-id flight-test-1

# Run with high frequency sampling
python3 scripts/resource_monitor.py --interval 0.5 --session-id stress-test

# Run with custom configuration
python3 scripts/resource_monitor.py --config config/monitor_config.json
```

#### Quick Status Check
```bash
# Show current system status
python3 scripts/quick_monitor.py

# Live monitoring display
python3 scripts/quick_monitor.py --live

# Quick 60-second test
python3 scripts/quick_monitor.py --test 60
```

### Data Analysis

#### Generate Reports
```bash
# Analyze latest data (interactive selection)
uav-monitor analyze

# Analyze specific file
uav-monitor analyze data/resource_metrics_flight-test-1_20250824_123045.csv

# Custom analysis with different output directory
python3 scripts/stats_generator.py data/my_data.csv --output-dir custom_reports/
```

#### List Available Data
```bash
# List all collected data files
uav-monitor data

# List generated reports
uav-monitor reports
```

## Configuration

Edit `config/monitor_config.json` to customize monitoring behavior:

```json
{
  "sample_interval": 1.0,
  "output_format": "both",
  "alert_thresholds": {
    "cpu_percent": 90,
    "memory_percent": 95,
    "cpu_temp": 75
  },
  "monitoring_presets": {
    "high_frequency": {"sample_interval": 0.5},
    "standard": {"sample_interval": 1.0},
    "battery_saver": {"sample_interval": 10.0}
  }
}
```

## Output Files

### Data Files
- **CSV Format**: `data/resource_metrics_[session]_[timestamp].csv`
- **JSON Format**: `data/resource_metrics_[session]_[timestamp].jsonl`

### Analysis Reports
- **Text Report**: `reports/[session]_report.txt`
- **Statistics JSON**: `reports/[session]_stats.json`
- **Time Series Plot**: `reports/[session]_timeseries.png`
- **Distribution Plot**: `reports/[session]_distributions.png`
- **Correlation Heatmap**: `reports/[session]_correlation.png`

## Example Workflows

### Flight Testing Workflow
```bash
# 1. Start monitoring before flight
uav-monitor run --session-id pre-flight-check --duration 120

# 2. Monitor during flight
uav-monitor run --session-id flight-mission-1 --duration 1800

# 3. Analyze performance after flight
uav-monitor analyze data/resource_metrics_flight-mission-1_*.csv
```

### Development Workflow
```bash
# 1. Start background monitoring
uav-monitor start

# 2. Run your development/testing
# ... your code runs ...

# 3. Stop and analyze
uav-monitor stop
uav-monitor analyze
```

### Stress Testing
```bash
# High frequency monitoring for stress testing
python3 scripts/resource_monitor.py --interval 0.1 --session-id stress-test --duration 600
```

## System Requirements

### Raspberry Pi Models
- Raspberry Pi 3B+ or newer recommended
- Raspberry Pi OS (Raspbian) or Ubuntu
- At least 1GB RAM (2GB+ recommended)
- 500MB free disk space

### Python Dependencies
- Python 3.7+
- psutil (system metrics)
- pandas (data analysis)
- matplotlib, seaborn (visualizations)
- numpy (numerical computing)

## Monitoring Metrics

| Metric          | Description                    | Units         |
| --------------- | ------------------------------ | ------------- |
| CPU Usage       | Current CPU utilization        | %             |
| CPU Frequency   | Current/Max CPU frequency      | MHz           |
| CPU Temperature | Processor temperature          | °C            |
| Memory Usage    | RAM utilization                | % / Bytes     |
| Swap Usage      | Swap space utilization         | % / Bytes     |
| Disk Usage      | Storage utilization            | % / Bytes     |
| Network I/O     | Bytes/packets sent/received    | Bytes/Packets |
| Load Average    | System load (1m, 5m, 15m)      | Load units    |
| Process Count   | Number of running processes    | Count         |
| Uptime          | System uptime                  | Seconds       |
| GPU Temperature | GPU temperature (if available) | °C            |
| System Voltage  | Core voltage (Pi-specific)     | V             |

## Performance Analysis Features

### Statistics Generated
- **Basic Stats**: Mean, median, min, max, standard deviation, quartiles
- **Performance Scores**: Stability score, efficiency score
- **Thermal Analysis**: Thermal throttling risk assessment
- **Network Analysis**: Throughput calculations and total data transfer
- **Time Analysis**: High usage periods, duration analysis

### Visualizations
- **Time Series**: Resource usage over time with thresholds
- **Distributions**: Histograms with density curves for key metrics
- **Correlation**: Heatmap showing relationships between metrics

## Troubleshooting

### Common Issues

**Permission denied errors:**
```bash
# Ensure proper permissions
sudo chown -R uav-monitor:uav-monitor /opt/uav-resource-monitor
```

**Missing temperature data:**
- Some Pi models may not have all thermal zones
- Check available thermal zones: `ls /sys/class/thermal/`

**High resource usage from monitoring:**
- Increase sampling interval: `--interval 5.0`
- Use battery saver preset in config

**Service won't start:**
```bash
# Check service logs
journalctl -u uav-resource-monitor.service -n 50

# Check configuration
python3 scripts/resource_monitor.py --config config/monitor_config.json --help
```

## File Structure

```
uav-resource-monitor/
├── scripts/
│   ├── resource_monitor.py    # Main monitoring script
│   ├── stats_generator.py     # Analysis and reporting
│   └── quick_monitor.py       # Quick status and live monitoring
├── config/
│   └── monitor_config.json    # Configuration file
├── data/                      # Collected monitoring data
├── logs/                      # Application logs
├── reports/                   # Generated analysis reports
├── requirements.txt           # Python dependencies
├── install.sh                 # Installation script
└── README.md                  # This file
```
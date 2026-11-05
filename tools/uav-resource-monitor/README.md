# UAV Resource Monitor

Records system metrics on a Raspberry Pi companion computer and generates reports from them.

It collects CPU usage, frequency and temperature, memory and swap, disk usage, network counters, load averages, process count and uptime. On a Raspberry Pi it also reads GPU temperature and core voltage.

## Setup

For local use:

```bash
./setup_local.sh
source venv/bin/activate
```

To install it as a service on a Raspberry Pi:

```bash
sudo ./install.sh
```

This installs to `/opt/uav-resource-monitor`, enables a systemd service, and adds the `uav-monitor` command.

## Usage

Paths in `config/monitor_config.json` are relative to the directory you run from, so run the scripts from `scripts/`.

```bash
cd scripts

# Record for 5 minutes
python3 resource_monitor.py --config ../config/monitor_config.json --session-id flight-1 --duration 300

# Sample every 0.5 seconds
python3 resource_monitor.py --config ../config/monitor_config.json --interval 0.5

# Show the current status, a live display, or a 60 second test
python3 quick_monitor.py
python3 quick_monitor.py --live
python3 quick_monitor.py --test 60

# Generate a report
python3 stats_generator.py ../data/resource_metrics_flight-1_20250824_123045.csv
```

When installed as a service:

```bash
uav-monitor start
uav-monitor status
uav-monitor logs
uav-monitor stop
uav-monitor run --duration 300 --session-id flight-1
uav-monitor analyze
```

## Output

Data files, in `data/`:

- `resource_metrics_[session]_[timestamp].csv`
- `resource_metrics_[session]_[timestamp].jsonl`

Reports, in `reports/`:

- `[session]_report.txt`
- `[session]_stats.json`
- `[session]_timeseries.png`
- `[session]_distributions.png`
- `[session]_correlation.png`

## Configuration

`config/monitor_config.json` sets the sample interval, output directories, output format (`csv`, `json` or `both`), temperature sensor paths and the disk path to measure.

Some Raspberry Pi models don't have every thermal zone. Check which ones exist with `ls /sys/class/thermal/`.

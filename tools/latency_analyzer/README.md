# UAV Telemetry Latency Analyzer

A Python CLI tool for analyzing latency metrics from UAV telemetry JSONL files.

## Features

- **Terminal Statistics**: Latency analysis with mean, median, standard deviation, percentiles
- **Per-Variable Analysis**: Breakdown of latency by telemetry variable
- **Processing Steps**: Analysis of different processing stages (recv → processed → server)
- **Chart Generation**: Optional visualization with histograms, time-series, and comparison charts

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Analysis (Terminal Output Only)

```bash
python analyze_latency.py ../metrics/events-08-23T20-06-07.jsonl
```

### With Chart Generation

```bash
python analyze_latency.py ../metrics/events-08-23T20-06-07.jsonl --charts
```

### Custom Output Directory for Charts

```bash
python analyze_latency.py ../metrics/events-08-23T20-06-07.jsonl --charts --output-dir ./my_charts
```

## Output

### Terminal Statistics

The script provides four types of analysis:

1. **Overall Latency Statistics**: Mean, median, std dev, min, max, P95, P99 for each processing step
2. **Per-Variable Statistics**: Latency breakdown by telemetry variable (Altitude, Pitch, etc.)
3. **Processing Steps Breakdown**: Percentage contribution of each processing stage
4. **Event Frequency Analysis**: Data collection period, event rates, and per-variable frequencies

### Charts (Optional)

When `--charts` is specified, generates four PNG files:

- `latency_distributions.png`: Histograms and box plots for all latency types
- `latency_time_series.png`: Latency over time scatter plot  
- `latency_rolling_average.png`: Rolling average latency over time
- `latency_by_variable.png`: Mean latency comparison by variable

## Data Format

The analyzer expects JSONL files with events containing:

- `recv_ts`: Message receive timestamp
- `processed_ts`: Message processing completion timestamp  
- `server_recv_ts`: Server receive timestamp
- `variable`: Telemetry variable name
- `event`: Event type
- `message_id`: Unique message identifier

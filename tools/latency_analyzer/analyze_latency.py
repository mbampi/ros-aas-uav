#!/usr/bin/env python3
"""
UAV Telemetry Latency Analyzer

Analyzes latency metrics from JSONL files containing UAV telemetry events.
Provides terminal output with statistics and optional chart generation.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from statistics import mean, median, stdev
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from tabulate import tabulate


class LatencyAnalyzer:
    """Analyzes latency metrics from UAV telemetry data."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.events = []
        self.latency_data = {
            'processing_latency': [],  # processed_ts - recv_ts
            'server_latency': [],      # server_recv_ts - processed_ts
            'total_latency': []        # server_recv_ts - recv_ts
        }
        self.per_variable_latency = defaultdict(lambda: {
            'processing_latency': [],
            'server_latency': [],
            'total_latency': []
        })
        self.offset = 0.004  # Clock offset in seconds between client and server (if any)

    def load_and_parse_data(self) -> None:
        """Load JSONL file and parse events with latency calculations."""
        print(f"Loading data from {self.file_path}...")
        
        if not self.file_path.exists():
            print(f"Error: File {self.file_path} not found!")
            sys.exit(1)
            
        with open(self.file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Skip line numbers at the beginning if present
                if '|' in line and line.split('|', 1)[0].strip().isdigit():
                    line = line.split('|', 1)[1].strip()
                
                try:
                    event = json.loads(line)
                    self.events.append(event)
                    
                    # Calculate latencies for events with all required timestamps
                    if (event.get('recv_ts') and 
                        event.get('processed_ts') and 
                        event.get('server_recv_ts')):
                        
                        recv_ts = event['recv_ts']
                        processed_ts = event['processed_ts']
                        server_recv_ts = event['server_recv_ts']
                        server_recv_ts += self.offset

                        variable = event.get('variable', 'unknown')

                        processing_latency = processed_ts - recv_ts
                        processing_latency = processing_latency if processing_latency >= 0 else 0

                        server_latency = server_recv_ts - processed_ts
                        server_latency = server_latency if server_latency >= 0 else 0

                        total_latency = server_recv_ts - recv_ts
                        total_latency = total_latency if total_latency >= 0 else 0

                        # Store in overall latency data
                        self.latency_data['processing_latency'].append(processing_latency)
                        self.latency_data['server_latency'].append(server_latency)
                        self.latency_data['total_latency'].append(total_latency)
                        
                        # Store in per-variable data
                        self.per_variable_latency[variable]['processing_latency'].append(processing_latency)
                        self.per_variable_latency[variable]['server_latency'].append(server_latency)
                        self.per_variable_latency[variable]['total_latency'].append(total_latency)
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line {line_num}: {e}")
                    continue
                    
        print(f"Loaded {len(self.events)} events")
        print(f"Found {len(self.latency_data['total_latency'])} events with complete latency data")
        
    def calculate_statistics(self, data: List[float]) -> Dict:
        """Calculate statistical metrics for a dataset."""
        if not data:
            return {
                'count': 0,
                'mean': 0,
                'median': 0,
                'std': 0,
                'min': 0,
                'max': 0,
                'p95': 0,
                'p99': 0
            }
            
        return {
            'count': len(data),
            'mean': mean(data),
            'median': median(data),
            'std': stdev(data) if len(data) > 1 else 0,
            'min': min(data),
            'max': max(data),
            'p95': np.percentile(data, 95),
            'p99': np.percentile(data, 99)
        }
        
    def display_overall_statistics(self) -> None:
        """Display overall latency statistics in terminal."""
        print("\n" + "="*80)
        print("OVERALL LATENCY STATISTICS")
        print("="*80)
        
        # Calculate statistics for each latency type
        stats = {}
        for latency_type, data in self.latency_data.items():
            stats[latency_type] = self.calculate_statistics(data)
        
        # Convert to milliseconds for better readability
        table_data = []
        for latency_type, stat in stats.items():
            table_data.append([
                latency_type.replace('_', ' ').title(),
                f"{stat['count']}",
                f"{stat['mean']*1000:.2f}",
                f"{stat['median']*1000:.2f}",
                f"{stat['std']*1000:.2f}",
                f"{stat['min']*1000:.2f}",
                f"{stat['max']*1000:.2f}",
                f"{stat['p95']*1000:.2f}",
                f"{stat['p99']*1000:.2f}"
            ])
        
        headers = ["Latency Type", "Count", "Mean (ms)", "Median (ms)", 
                  "Std Dev (ms)", "Min (ms)", "Max (ms)", "P95 (ms)", "P99 (ms)"]
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
    def display_per_variable_statistics(self) -> None:
        """Display per-variable latency statistics."""
        print("\n" + "="*80)
        print("PER-VARIABLE LATENCY STATISTICS (Total Latency)")
        print("="*80)
        
        table_data = []
        for variable, data in self.per_variable_latency.items():
            total_latency = data['total_latency']
            if total_latency:
                stats = self.calculate_statistics(total_latency)
                table_data.append([
                    variable,
                    f"{stats['count']}",
                    f"{stats['mean']*1000:.2f}",
                    f"{stats['median']*1000:.2f}",
                    f"{stats['std']*1000:.2f}",
                    f"{stats['min']*1000:.2f}",
                    f"{stats['max']*1000:.2f}"
                ])
        
        # Sort by mean latency descending
        table_data.sort(key=lambda x: float(x[2]), reverse=True)
        
        headers = ["Variable", "Count", "Mean (ms)", "Median (ms)", 
                  "Std Dev (ms)", "Min (ms)", "Max (ms)"]
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
    def display_processing_steps_breakdown(self) -> None:
        """Display breakdown of processing steps."""
        print("\n" + "="*80)
        print("PROCESSING STEPS BREAKDOWN")
        print("="*80)
        
        processing_stats = self.calculate_statistics(self.latency_data['processing_latency'])
        server_stats = self.calculate_statistics(self.latency_data['server_latency'])
        total_stats = self.calculate_statistics(self.latency_data['total_latency'])
        
        print(f"Step 1 - Processing Latency (recv_ts → processed_ts):")
        print(f"  • Mean: {processing_stats['mean']*1000:.2f} ms")
        print(f"  • Percentage of total: {(processing_stats['mean']/total_stats['mean']*100):.1f}%")
        
        print(f"\nStep 2 - Server Latency (processed_ts → server_recv_ts):")
        print(f"  • Mean: {server_stats['mean']*1000:.2f} ms")
        print(f"  • Percentage of total: {(server_stats['mean']/total_stats['mean']*100):.1f}%")
        
        print(f"\nTotal End-to-End Latency (recv_ts → server_recv_ts):")
        print(f"  • Mean: {total_stats['mean']*1000:.2f} ms")
        
    def display_frequency_analysis(self) -> None:
        """Display event frequency and timing analysis."""
        print("\n" + "="*80)
        print("EVENT FREQUENCY ANALYSIS")
        print("="*80)
        
        # Get events with recv_ts for frequency analysis
        events_with_timestamps = []
        for event in self.events:
            if event.get('recv_ts'):
                events_with_timestamps.append(event['recv_ts'])
        
        if len(events_with_timestamps) < 2:
            print("Not enough events with timestamps for frequency analysis.")
            return
            
        events_with_timestamps.sort()
        
        first_event_time = events_with_timestamps[0]
        last_event_time = events_with_timestamps[-1]
        total_duration = last_event_time - first_event_time
        total_events = len(events_with_timestamps)
        events_per_second = total_events / total_duration if total_duration > 0 else 0
        
        # Convert timestamps to readable format
        first_event_str = datetime.fromtimestamp(first_event_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        last_event_str = datetime.fromtimestamp(last_event_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Calculate inter-event intervals
        intervals = []
        for i in range(1, len(events_with_timestamps)):
            interval = events_with_timestamps[i] - events_with_timestamps[i-1]
            intervals.append(interval)
        
        # Frequency statistics
        print(f"Data Collection Period:")
        print(f"  • First Event: {first_event_str}")
        print(f"  • Last Event:  {last_event_str}")
        print(f"  • Duration:    {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
        
        print(f"\nEvent Statistics:")
        print(f"  • Total Events:       {total_events}")
        print(f"  • Events with Latency: {len(self.latency_data['total_latency'])}")
        print(f"  • Average Frequency:   {events_per_second:.2f} events/second")
        
        if intervals:
            avg_interval = mean(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            
            print(f"\nInter-Event Intervals:")
            print(f"  • Average Interval: {avg_interval:.3f} seconds")
            print(f"  • Min Interval:     {min_interval:.3f} seconds")
            print(f"  • Max Interval:     {max_interval:.3f} seconds")
            print(f"  • Expected Rate:    {1/avg_interval:.2f} events/second")
        
        # Per-variable frequency analysis
        print(f"\nPer-Variable Event Counts:")
        variable_counts = defaultdict(int)
        for event in self.events:
            if event.get('variable'):
                variable_counts[event['variable']] += 1
        
        for variable, count in sorted(variable_counts.items(), key=lambda x: x[1], reverse=True):
            rate = count / total_duration if total_duration > 0 else 0
            print(f"  • {variable:18s}: {count:3d} events ({rate:.2f}/sec)")
        
    def generate_charts(self, output_dir: str = "charts") -> None:
        """Generate latency analysis charts."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\nGenerating charts in {output_path}...")
        
        # Set style
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        
        # Chart 1: Latency Distribution Histogram
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Latency Distribution Analysis', fontsize=16, fontweight='bold')
        
        # Processing latency histogram
        axes[0,0].hist(np.array(self.latency_data['processing_latency'])*1000, 
                      bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0,0].set_title('Processing Latency Distribution')
        axes[0,0].set_xlabel('Latency (ms)')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].grid(True, alpha=0.3)
        
        # Server latency histogram
        axes[0,1].hist(np.array(self.latency_data['server_latency'])*1000, 
                      bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
        axes[0,1].set_title('Server Latency Distribution')
        axes[0,1].set_xlabel('Latency (ms)')
        axes[0,1].set_ylabel('Frequency')
        axes[0,1].grid(True, alpha=0.3)
        
        # Total latency histogram
        axes[1,0].hist(np.array(self.latency_data['total_latency'])*1000, 
                      bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[1,0].set_title('Total Latency Distribution')
        axes[1,0].set_xlabel('Latency (ms)')
        axes[1,0].set_ylabel('Frequency')
        axes[1,0].grid(True, alpha=0.3)
        
        # Box plot comparison
        box_data = [np.array(self.latency_data['processing_latency'])*1000,
                   np.array(self.latency_data['server_latency'])*1000,
                   np.array(self.latency_data['total_latency'])*1000]
        axes[1,1].boxplot(box_data, tick_labels=['Processing', 'Server', 'Total'])
        axes[1,1].set_title('Latency Comparison (Box Plot)')
        axes[1,1].set_ylabel('Latency (ms)')
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / 'latency_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Chart 2: Time Series Analysis
        if self.events:
            timestamps = []
            total_latencies = []
            
            for event in self.events:
                if (event.get('recv_ts') and 
                    event.get('processed_ts') and 
                    event.get('server_recv_ts')):
                    timestamps.append(datetime.fromtimestamp(event['recv_ts']))
                    total_latencies.append((event['server_recv_ts'] - event['recv_ts']) * 1000)
            
            if timestamps:
                fig, ax = plt.subplots(figsize=(15, 6))
                ax.scatter(timestamps, total_latencies, alpha=0.6, s=10)
                ax.set_title('Latency Over Time', fontsize=16, fontweight='bold')
                ax.set_xlabel('Time')
                ax.set_ylabel('Total Latency (ms)')
                ax.grid(True, alpha=0.3)
                
                # Format x-axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                plt.tight_layout()
                plt.savefig(output_path / 'latency_time_series.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        # Chart 3: Rolling Average Latency Over Time
        if self.events:
            # Extract timestamp and latency data for events with complete data
            time_latency_data = []
            for event in self.events:
                if (event.get('recv_ts') and 
                    event.get('processed_ts') and 
                    event.get('server_recv_ts')):
                    time_latency_data.append({
                        'timestamp': datetime.fromtimestamp(event['recv_ts']),
                        'latency': (event['server_recv_ts'] - event['recv_ts']) * 1000
                    })
            
            if len(time_latency_data) > 10:  # Need enough data points for rolling average
                # Sort by timestamp
                time_latency_data.sort(key=lambda x: x['timestamp'])
                
                timestamps = [item['timestamp'] for item in time_latency_data]
                latencies = [item['latency'] for item in time_latency_data]
                
                # Calculate rolling average (window size = 10% of data points, minimum 5)
                window_size = max(5, len(latencies) // 10)
                rolling_avg = []
                rolling_timestamps = []
                
                for i in range(len(latencies)):
                    start_idx = max(0, i - window_size + 1)
                    end_idx = i + 1
                    avg_latency = mean(latencies[start_idx:end_idx])
                    rolling_avg.append(avg_latency)
                    rolling_timestamps.append(timestamps[i])
                
                fig, ax = plt.subplots(figsize=(15, 6))
                
                # Plot raw data as light scatter points
                ax.scatter(timestamps, latencies, alpha=0.3, s=8, color='lightgray', label='Individual Events')
                
                # Plot rolling average as a line
                ax.plot(rolling_timestamps, rolling_avg, color='red', linewidth=2, label=f'Rolling Average (window={window_size})')
                
                ax.set_title('Total Latency Over Time with Rolling Average', fontsize=16, fontweight='bold')
                ax.set_xlabel('Time')
                ax.set_ylabel('Total Latency (ms)')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                # Format x-axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Add statistics text box
                overall_mean = mean(latencies)
                overall_std = stdev(latencies) if len(latencies) > 1 else 0
                stats_text = f'Overall Mean: {overall_mean:.2f} ms\nStd Dev: {overall_std:.2f} ms\nSample Size: {len(latencies)}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                
                plt.tight_layout()
                plt.savefig(output_path / 'latency_rolling_average.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        # Chart 4: Per-Variable Latency Comparison
        if self.per_variable_latency:
            variables = []
            means = []
            
            for variable, data in self.per_variable_latency.items():
                if data['total_latency']:
                    variables.append(variable)
                    means.append(mean(data['total_latency']) * 1000)
            
            if variables:
                # Sort by mean latency
                sorted_data = sorted(zip(variables, means), key=lambda x: x[1], reverse=True)
                variables, means = zip(*sorted_data)
                
                fig, ax = plt.subplots(figsize=(12, 8))
                bars = ax.barh(variables, means, color='steelblue', alpha=0.7)
                ax.set_title('Mean Latency by Variable', fontsize=16, fontweight='bold')
                ax.set_xlabel('Mean Total Latency (ms)')
                ax.grid(True, alpha=0.3, axis='x')
                
                # Add value labels on bars
                for i, (bar, mean_val) in enumerate(zip(bars, means)):
                    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                           f'{mean_val:.2f}', va='center', fontsize=9)
                
                plt.tight_layout()
                plt.savefig(output_path / 'latency_by_variable.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        print(f"Charts saved to {output_path}/")
        print(f"  • latency_distributions.png - Histogram and box plot analysis")
        print(f"  • latency_time_series.png - Latency over time (scatter plot)")
        print(f"  • latency_rolling_average.png - Rolling average latency over time")
        print(f"  • latency_by_variable.png - Per-variable comparison")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze latency metrics from UAV telemetry JSONL files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ../metrics/events-08-23T20-06-07.jsonl
  %(prog)s ../metrics/events-08-23T20-06-07.jsonl --charts
  %(prog)s ../metrics/events-08-23T20-06-07.jsonl --charts --output-dir ./my_charts
        """
    )
    
    parser.add_argument(
        'file',
        help='Path to JSONL file containing telemetry events'
    )
    
    parser.add_argument(
        '--charts', 
        action='store_true',
        help='Generate and save latency analysis charts as PNG images'
    )
    
    parser.add_argument(
        '--output-dir',
        default='charts',
        help='Directory to save charts (default: charts)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = LatencyAnalyzer(args.file)
        
        # Load and parse data
        analyzer.load_and_parse_data()
        
        if not analyzer.latency_data['total_latency']:
            print("No events with complete latency data found!")
            print("Events need recv_ts, processed_ts, and server_recv_ts fields.")
            sys.exit(1)
        
        # Display terminal statistics
        analyzer.display_overall_statistics()
        analyzer.display_per_variable_statistics()
        analyzer.display_processing_steps_breakdown()
        analyzer.display_frequency_analysis()
        
        # Generate charts if requested
        if args.charts:
            analyzer.generate_charts(args.output_dir)
        
        print(f"\nAnalysis complete! Processed {len(analyzer.events)} total events.")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

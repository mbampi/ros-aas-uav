#!/usr/bin/env python3
"""
UAV Resource Monitor Statistics Generator
Analyzes collected system resource data and generates statistics, reports,
and visualizations.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
import sys
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


class StatsGenerator:
    """Generate statistics and visualizations from resource monitoring data"""
    
    def __init__(self, data_dir: str = "../data", output_dir: str = "../reports"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set plotting style
        plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
        sns.set_palette("husl")
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from CSV or JSON file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix == '.jsonl':
            data = []
            with open(file_path, 'r') as f:
                for line in f:
                    data.append(json.loads(line.strip()))
            df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate time differences for rates
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
        
        return df
    
    def calculate_basic_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate basic statistical metrics"""
        stats = {
            'session_info': {
                'start_time': df['timestamp'].min().isoformat(),
                'end_time': df['timestamp'].max().isoformat(),
                'duration_minutes': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60,
                'total_samples': len(df),
                'sample_rate_hz': len(df) / ((df['timestamp'].max() - df['timestamp'].min()).total_seconds())
            },
            'system_stats': {}
        }
        
        # Key metrics to analyze
        key_metrics = {
            'cpu_percent': 'CPU Usage (%)',
            'memory_percent': 'Memory Usage (%)',
            'disk_percent': 'Disk Usage (%)',
            'cpu_temp': 'CPU Temperature (°C)',
            'gpu_temp': 'GPU Temperature (°C)',
            'voltage': 'System Voltage (V)',
            'load_avg_1m': '1-min Load Average',
            'uptime': 'Uptime (hours)'
        }
        
        for col, description in key_metrics.items():
            if col in df.columns and df[col].notna().sum() > 0:
                series = df[col].dropna()
                
                # Convert uptime to hours for readability
                if col == 'uptime':
                    series = series / 3600
                
                stats['system_stats'][col] = {
                    'description': description,
                    'mean': float(series.mean()),
                    'median': float(series.median()),
                    'std': float(series.std()),
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'q25': float(series.quantile(0.25)),
                    'q75': float(series.quantile(0.75))
                }
                
                if col == 'cpu_percent':
                    high_cpu_threshold = 80
                    high_cpu_time = (series > high_cpu_threshold).sum() * stats['session_info']['sample_rate_hz']
                    stats['system_stats'][col]['high_usage_seconds'] = high_cpu_time
                    stats['system_stats'][col]['high_usage_percent'] = (high_cpu_time / (stats['session_info']['duration_minutes'] * 60)) * 100
                
                elif col == 'cpu_temp':
                    thermal_threshold = 70  # °C
                    if series.max() > thermal_threshold:
                        stats['system_stats'][col]['thermal_throttling_risk'] = True
                        stats['system_stats'][col]['time_above_threshold'] = (series > thermal_threshold).sum() * stats['session_info']['sample_rate_hz']
                    else:
                        stats['system_stats'][col]['thermal_throttling_risk'] = False
        
        return stats
    
    def calculate_performance_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate performance-specific metrics"""
        metrics = {}
        
        # Network throughput (if network data is available)
        if 'network_bytes_sent' in df.columns and 'network_bytes_recv' in df.columns:
            df['net_sent_rate'] = df['network_bytes_sent'].diff() / df['time_diff']
            df['net_recv_rate'] = df['network_bytes_recv'].diff() / df['time_diff']
            
            # Convert to MB/s
            df['net_sent_mbps'] = df['net_sent_rate'] / (1024*1024)
            df['net_recv_mbps'] = df['net_recv_rate'] / (1024*1024)
            
            metrics['network'] = {
                'avg_upload_mbps': float(df['net_sent_mbps'].mean()),
                'avg_download_mbps': float(df['net_recv_mbps'].mean()),
                'max_upload_mbps': float(df['net_sent_mbps'].max()),
                'max_download_mbps': float(df['net_recv_mbps'].max()),
                'total_sent_gb': float(df['network_bytes_sent'].max() / (1024**3)),
                'total_recv_gb': float(df['network_bytes_recv'].max() / (1024**3))
            }
        
        return metrics
    
    def generate_time_series_plots(self, df: pd.DataFrame, session_name: str):
        """Generate time series plots for key metrics"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'System Resource Usage Over Time - {session_name}', fontsize=16)
        
        # CPU Usage
        if 'cpu_percent' in df.columns:
            axes[0, 0].plot(df['timestamp'], df['cpu_percent'], color='red', alpha=0.7)
            axes[0, 0].set_title('CPU Usage')
            axes[0, 0].set_ylabel('CPU %')
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].axhline(y=80, color='orange', linestyle='--', alpha=0.7, label='High Usage (80%)')
            axes[0, 0].legend()
        
        # Memory Usage
        if 'memory_percent' in df.columns:
            axes[0, 1].plot(df['timestamp'], df['memory_percent'], color='blue', alpha=0.7)
            axes[0, 1].set_title('Memory Usage')
            axes[0, 1].set_ylabel('Memory %')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].axhline(y=90, color='orange', linestyle='--', alpha=0.7, label='High Usage (90%)')
            axes[0, 1].legend()
        
        # Temperature
        if 'cpu_temp' in df.columns and df['cpu_temp'].notna().sum() > 0:
            axes[1, 0].plot(df['timestamp'], df['cpu_temp'], color='green', alpha=0.7, label='CPU')
            if 'gpu_temp' in df.columns and df['gpu_temp'].notna().sum() > 0:
                axes[1, 0].plot(df['timestamp'], df['gpu_temp'], color='purple', alpha=0.7, label='GPU')
            axes[1, 0].set_title('Temperature')
            axes[1, 0].set_ylabel('Temperature (°C)')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].axhline(y=70, color='orange', linestyle='--', alpha=0.7, label='Thermal Threshold')
            axes[1, 0].legend()
        
        # Load Average
        if 'load_avg_1m' in df.columns:
            axes[1, 1].plot(df['timestamp'], df['load_avg_1m'], color='orange', alpha=0.7, label='1 min')
            if 'load_avg_5m' in df.columns:
                axes[1, 1].plot(df['timestamp'], df['load_avg_5m'], color='red', alpha=0.7, label='5 min')
            if 'load_avg_15m' in df.columns:
                axes[1, 1].plot(df['timestamp'], df['load_avg_15m'], color='purple', alpha=0.7, label='15 min')
            axes[1, 1].set_title('Load Average')
            axes[1, 1].set_ylabel('Load')
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].legend()
        
        # Format x-axis for all subplots
        for ax in axes.flat:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.output_dir / f"{session_name}_timeseries.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(plot_path)
    
    def generate_distribution_plots(self, df: pd.DataFrame, session_name: str):
        """Generate distribution plots for key metrics"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(f'Resource Usage Distributions - {session_name}', fontsize=16)
        
        metrics = ['cpu_percent', 'memory_percent', 'cpu_temp', 'load_avg_1m']
        titles = ['CPU Usage (%)', 'Memory Usage (%)', 'CPU Temperature (°C)', 'Load Average (1m)']
        
        for i, (metric, title) in enumerate(zip(metrics, titles)):
            if metric in df.columns and df[metric].notna().sum() > 0:
                row, col = i // 2, i % 2
                data = df[metric].dropna()
                
                # Histogram with density curve
                axes[row, col].hist(data, bins=30, alpha=0.7, density=True, color=f'C{i}')
                
                # Add kernel density estimate
                try:
                    from scipy.stats import gaussian_kde
                    kde = gaussian_kde(data)
                    x_range = np.linspace(data.min(), data.max(), 100)
                    axes[row, col].plot(x_range, kde(x_range), color='red', linewidth=2)
                except ImportError:
                    pass  # Skip KDE if scipy is not available
                
                axes[row, col].set_title(title)
                axes[row, col].set_ylabel('Density')
                axes[row, col].grid(True, alpha=0.3)
                
                # Add mean line
                mean_val = data.mean()
                axes[row, col].axvline(x=mean_val, color='orange', linestyle='--', 
                                      label=f'Mean: {mean_val:.1f}')
                axes[row, col].legend()
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.output_dir / f"{session_name}_distributions.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(plot_path)
    
    def generate_correlation_heatmap(self, df: pd.DataFrame, session_name: str):
        """Generate correlation heatmap for numeric metrics"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Select relevant columns for correlation analysis
        relevant_cols = [col for col in numeric_cols if col not in 
                        ['timestamp', 'boot_time', 'uptime', 'network_bytes_sent', 
                         'network_bytes_recv', 'memory_total', 'disk_total', 'time_diff']]
        
        if len(relevant_cols) > 1:
            corr_df = df[relevant_cols].corr()
            
            plt.figure(figsize=(10, 8))
            mask = np.triu(np.ones_like(corr_df, dtype=bool))
            sns.heatmap(corr_df, mask=mask, annot=True, cmap='coolwarm', center=0,
                       square=True, fmt='.2f', cbar_kws={"shrink": .8})
            plt.title(f'Resource Metrics Correlation - {session_name}')
            plt.tight_layout()
            
            # Save plot
            plot_path = self.output_dir / f"{session_name}_correlation.png"
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(plot_path)
        
        return None
    
    def generate_summary_report(self, stats: Dict, performance: Dict, session_name: str) -> str:
        """Generate a text report"""
        report_lines = [
            f"UAV RESOURCE MONITORING REPORT - {session_name}",
            "=" * 60,
            "",
            "SESSION INFORMATION:",
            f"  Start Time:     {stats['session_info']['start_time']}",
            f"  End Time:       {stats['session_info']['end_time']}",
            f"  Duration:       {stats['session_info']['duration_minutes']:.1f} minutes",
            f"  Total Samples:  {stats['session_info']['total_samples']:,}",
            f"  Sample Rate:    {stats['session_info']['sample_rate_hz']:.2f} Hz",
            "",
            "SYSTEM PERFORMANCE SUMMARY:",
            "-" * 30,
        ]
        
        # Add system stats
        for metric, data in stats['system_stats'].items():
            report_lines.extend([
                f"{data['description']}:",
                f"  Average:    {data['mean']:.2f}",
                f"  Min/Max:    {data['min']:.2f} / {data['max']:.2f}",
                f"  Std Dev:    {data['std']:.2f}",
                ""
            ])
            
            if 'high_usage_seconds' in data:
                report_lines.extend([
                    f"  High CPU Usage (>80%): {data['high_usage_seconds']:.1f}s ({data['high_usage_percent']:.1f}%)",
                    ""
                ])
            
            if 'thermal_throttling_risk' in data:
                if data['thermal_throttling_risk']:
                    report_lines.extend([
                        f"  WARNING: Temperature exceeded 70°C",
                        f"  Time above threshold: {data['time_above_threshold']:.1f}s",
                        ""
                    ])
                else:
                    report_lines.extend([
                        f"  Temperature stayed below 70°C",
                        ""
                    ])
        
        # Add performance metrics
        if performance:
            report_lines.extend([
                "PERFORMANCE ANALYSIS:",
                "-" * 20,
            ])
            
            if 'network' in performance:
                net = performance['network']
                report_lines.extend([
                    "Network Activity:",
                    f"  Avg Upload:     {net['avg_upload_mbps']:.3f} MB/s",
                    f"  Avg Download:   {net['avg_download_mbps']:.3f} MB/s",
                    f"  Total Sent:     {net['total_sent_gb']:.3f} GB",
                    f"  Total Received: {net['total_recv_gb']:.3f} GB",
                    ""
                ])
        
        report_lines.extend([
            f"Report generated: {datetime.now().isoformat()}",
            ""
        ])
        
        return "\n".join(report_lines)
    
    def analyze_session(self, data_file: str, session_name: str = None) -> Dict:
        """Analyze one data file and write the report, statistics and plots"""
        if session_name is None:
            session_name = Path(data_file).stem
        
        print(f"Loading data from {data_file}...")
        df = self.load_data(data_file)
        
        print("Calculating statistics...")
        stats = self.calculate_basic_stats(df)
        performance = self.calculate_performance_metrics(df)
        
        print("Generating visualizations...")
        plots = {}
        plots['timeseries'] = self.generate_time_series_plots(df, session_name)
        plots['distributions'] = self.generate_distribution_plots(df, session_name)
        
        corr_plot = self.generate_correlation_heatmap(df, session_name)
        if corr_plot:
            plots['correlation'] = corr_plot
        
        print("Generating report...")
        report_text = self.generate_summary_report(stats, performance, session_name)
        
        # Save text report
        report_path = self.output_dir / f"{session_name}_report.txt"
        with open(report_path, 'w') as f:
            f.write(report_text)
        
        # Save JSON stats
        json_path = self.output_dir / f"{session_name}_stats.json"
        combined_stats = {
            'basic_stats': stats,
            'performance_metrics': performance,
            'plots': plots,
            'report_file': str(report_path)
        }
        
        with open(json_path, 'w') as f:
            json.dump(combined_stats, f, indent=2, default=str)
        
        print(f"\nReport saved to: {report_path}")
        print(f"Statistics saved to: {json_path}")
        print(f"Plots saved to: {self.output_dir}")
        
        return combined_stats
    
    def list_available_sessions(self) -> List[str]:
        """List available data files for analysis"""
        data_files = []
        for pattern in ['*.csv', '*.jsonl']:
            data_files.extend(self.data_dir.glob(pattern))
        
        return [str(f) for f in sorted(data_files)]


def main():
    parser = argparse.ArgumentParser(description='UAV Resource Monitor Statistics Generator')
    parser.add_argument('data_file', nargs='?', help='Path to data file (CSV or JSONL)')
    parser.add_argument('--data-dir', '-d', default='../data', help='Data directory path')
    parser.add_argument('--output-dir', '-o', default='../reports', help='Output directory path')
    parser.add_argument('--session-name', '-s', help='Session name for output files')
    parser.add_argument('--list', '-l', action='store_true', help='List available data files')
    
    args = parser.parse_args()
    
    try:
        generator = StatsGenerator(data_dir=args.data_dir, output_dir=args.output_dir)
        
        if args.list:
            sessions = generator.list_available_sessions()
            if sessions:
                print("Available data files:")
                for i, session in enumerate(sessions, 1):
                    print(f"  {i}. {session}")
            else:
                print("No data files found in", generator.data_dir)
            return
        
        if not args.data_file:
            sessions = generator.list_available_sessions()
            if not sessions:
                print("No data files found. Please run the resource monitor first.")
                sys.exit(1)
            
            print("Available data files:")
            for i, session in enumerate(sessions, 1):
                print(f"  {i}. {Path(session).name}")
            
            try:
                choice = int(input("\nSelect a file to analyze (number): ")) - 1
                if 0 <= choice < len(sessions):
                    args.data_file = sessions[choice]
                else:
                    print("Invalid selection")
                    sys.exit(1)
            except (ValueError, KeyboardInterrupt):
                print("\nCanceled")
                sys.exit(1)
        
        # Perform analysis
        results = generator.analyze_session(args.data_file, args.session_name)
        
        # Print summary
        basic_stats = results['basic_stats']
        print(f"\nSession Summary:")
        print(f"  Duration: {basic_stats['session_info']['duration_minutes']:.1f} minutes")
        print(f"  Samples: {basic_stats['session_info']['total_samples']:,}")
        
        if 'cpu_percent' in basic_stats['system_stats']:
            cpu_avg = basic_stats['system_stats']['cpu_percent']['mean']
            print(f"  Avg CPU: {cpu_avg:.1f}%")
        
        if 'memory_percent' in basic_stats['system_stats']:
            mem_avg = basic_stats['system_stats']['memory_percent']['mean']
            print(f"  Avg Memory: {mem_avg:.1f}%")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

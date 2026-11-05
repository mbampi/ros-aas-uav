#!/usr/bin/env python3
"""
UAV Resource Monitor
Collects CPU, memory, disk, network, temperature, and other system metrics
on Raspberry Pi companion computers.
"""

import os
import sys
import time
import json
import csv
import psutil
import logging
import argparse
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List
import threading
from dataclasses import dataclass, asdict


@dataclass
class SystemMetrics:
    """Data class for system metrics"""
    timestamp: str
    cpu_percent: float
    cpu_freq_current: float
    cpu_freq_max: float
    cpu_temp: Optional[float]
    memory_total: int
    memory_available: int
    memory_used: int
    memory_percent: float
    swap_total: int
    swap_used: int
    swap_percent: float
    disk_total: int
    disk_used: int
    disk_free: int
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int
    boot_time: float
    uptime: float
    load_avg_1m: float
    load_avg_5m: float
    load_avg_15m: float
    process_count: int
    gpu_temp: Optional[float] = None
    voltage: Optional[float] = None


class ResourceMonitor:
    """Main resource monitoring class"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.running = False
        self.data_file = None
        self.csv_writer = None
        
        # Setup logging
        self._setup_logging()
        
        # Setup data directory
        self.data_dir = Path(self.config['data_directory'])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize baseline network stats
        self.baseline_net_io = psutil.net_io_counters()
        
        self.logger.info("Resource Monitor initialized")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'sample_interval': 1.0,  # seconds
            'data_directory': '../data',
            'log_directory': '../logs',
            'output_format': 'both',  # 'csv', 'json', or 'both'
            'temperature_sensors': {
                'cpu': '/sys/class/thermal/thermal_zone0/temp',
                'gpu': '/sys/class/thermal/thermal_zone1/temp'  # May not exist on all Pi models
            },
            'disk_path': '/',
            'enable_detailed_logging': True
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                print(f"Loaded configuration from {config_path}")
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")
                print("Using default configuration")
        
        return default_config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.config['log_directory'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_level = logging.DEBUG if self.config['enable_detailed_logging'] else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'resource_monitor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature from thermal zone (Raspberry Pi specific)"""
        try:
            temp_path = self.config['temperature_sensors']['cpu']
            if Path(temp_path).exists():
                with open(temp_path, 'r') as f:
                    temp_millic = int(f.read().strip())
                    return temp_millic / 1000.0  # Convert from millicelsius
        except Exception as e:
            self.logger.debug(f"Could not read CPU temperature: {e}")
        return None
    
    def _get_gpu_temperature(self) -> Optional[float]:
        """Get GPU temperature (Raspberry Pi specific)"""
        try:
            # Try thermal zone first
            temp_path = self.config['temperature_sensors']['gpu']
            if Path(temp_path).exists():
                with open(temp_path, 'r') as f:
                    temp_millic = int(f.read().strip())
                    return temp_millic / 1000.0
            
            # Fallback to vcgencmd if available
            import subprocess
            result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                temp_str = result.stdout.strip()
                # Extract temperature from "temp=XX.X'C"
                temp = float(temp_str.split('=')[1].split("'")[0])
                return temp
        except Exception as e:
            self.logger.debug(f"Could not read GPU temperature: {e}")
        return None
    
    def _get_voltage(self) -> Optional[float]:
        """Get system voltage (Raspberry Pi specific)"""
        try:
            import subprocess
            result = subprocess.run(['vcgencmd', 'measure_volts', 'core'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                volt_str = result.stdout.strip()
                # Extract voltage from "volt=X.XXXV"
                voltage = float(volt_str.split('=')[1].replace('V', ''))
                return voltage
        except Exception as e:
            self.logger.debug(f"Could not read voltage: {e}")
        return None
    
    def _collect_metrics(self) -> SystemMetrics:
        """Collect all system metrics"""
        current_time = datetime.now(timezone.utc).isoformat()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_current = cpu_freq.current if cpu_freq else 0
        cpu_freq_max = cpu_freq.max if cpu_freq else 0
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk = psutil.disk_usage(self.config['disk_path'])
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # System metrics
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        load_avg = os.getloadavg()
        process_count = len(psutil.pids())
        
        # Temperature and voltage (Raspberry Pi specific)
        cpu_temp = self._get_cpu_temperature()
        gpu_temp = self._get_gpu_temperature()
        voltage = self._get_voltage()
        
        return SystemMetrics(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            cpu_freq_current=cpu_freq_current,
            cpu_freq_max=cpu_freq_max,
            cpu_temp=cpu_temp,
            memory_total=memory.total,
            memory_available=memory.available,
            memory_used=memory.used,
            memory_percent=memory.percent,
            swap_total=swap.total,
            swap_used=swap.used,
            swap_percent=swap.percent,
            disk_total=disk.total,
            disk_used=disk.used,
            disk_free=disk.free,
            disk_percent=(disk.used / disk.total) * 100 if disk.total > 0 else 0,
            network_bytes_sent=net_io.bytes_sent,
            network_bytes_recv=net_io.bytes_recv,
            network_packets_sent=net_io.packets_sent,
            network_packets_recv=net_io.packets_recv,
            boot_time=boot_time,
            uptime=uptime,
            load_avg_1m=load_avg[0],
            load_avg_5m=load_avg[1],
            load_avg_15m=load_avg[2],
            process_count=process_count,
            gpu_temp=gpu_temp,
            voltage=voltage
        )
    
    def _setup_output_files(self, session_id: str):
        """Setup output files for data logging"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"resource_metrics_{session_id}_{timestamp}"
        
        if self.config['output_format'] in ['csv', 'both']:
            csv_path = self.data_dir / f"{base_filename}.csv"
            self.csv_file = open(csv_path, 'w', newline='')
            
            # Get field names from SystemMetrics
            fieldnames = list(SystemMetrics.__annotations__.keys())
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)
            self.csv_writer.writeheader()
            
            self.logger.info(f"CSV output: {csv_path}")
        
        if self.config['output_format'] in ['json', 'both']:
            self.json_path = self.data_dir / f"{base_filename}.jsonl"
            self.json_file = open(self.json_path, 'w')
            self.logger.info(f"JSON output: {self.json_path}")
    
    def _write_metrics(self, metrics: SystemMetrics):
        """Write metrics to output files"""
        metrics_dict = asdict(metrics)
        
        if self.csv_writer:
            self.csv_writer.writerow(metrics_dict)
            self.csv_file.flush()
        
        if hasattr(self, 'json_file'):
            json.dump(metrics_dict, self.json_file)
            self.json_file.write('\n')
            self.json_file.flush()
    
    def _cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'csv_file') and self.csv_file:
            self.csv_file.close()
        if hasattr(self, 'json_file') and self.json_file:
            self.json_file.close()
        self.logger.info("Resource Monitor stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def start(self, session_id: str = None, duration: float = None):
        """Start monitoring"""
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        self.logger.info(f"Starting resource monitoring (Session: {session_id})")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Setup output files
        self._setup_output_files(session_id)
        
        self.running = True
        start_time = time.time()
        
        try:
            while self.running:
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    self.logger.info(f"Duration limit ({duration}s) reached")
                    break
                
                # Collect and write metrics
                metrics = self._collect_metrics()
                self._write_metrics(metrics)
                
                # Log periodic status
                if hasattr(self, '_last_log_time'):
                    if time.time() - self._last_log_time >= 60:  # Log every minute
                        self.logger.info(f"Monitoring active - CPU: {metrics.cpu_percent:.1f}%, "
                                       f"Memory: {metrics.memory_percent:.1f}%, "
                                       f"Temp: {metrics.cpu_temp:.1f}°C" if metrics.cpu_temp else "N/A")
                        self._last_log_time = time.time()
                else:
                    self._last_log_time = time.time()
                
                # Wait for next sample
                time.sleep(self.config['sample_interval'])
                
        except Exception as e:
            self.logger.error(f"Error during monitoring: {e}")
        finally:
            self._cleanup()
    
    def stop(self):
        """Stop monitoring"""
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='UAV Resource Monitor')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--session-id', '-s', help='Session identifier')
    parser.add_argument('--duration', '-d', type=float, help='Monitoring duration in seconds')
    parser.add_argument('--interval', '-i', type=float, help='Sample interval in seconds')
    
    args = parser.parse_args()
    
    try:
        monitor = ResourceMonitor(config_path=args.config)
        
        # Override interval if provided
        if args.interval:
            monitor.config['sample_interval'] = args.interval
        
        monitor.start(session_id=args.session_id, duration=args.duration)
        
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

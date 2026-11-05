#!/usr/bin/env python3
"""
Quick UAV Resource Monitor
Simple script for quick monitoring sessions and real-time display
"""

import os
import sys
import time
import psutil
import argparse
from datetime import datetime


def get_system_info():
    """Get basic system information"""
    try:
        # Try to get Raspberry Pi model info
        with open('/proc/device-tree/model', 'r') as f:
            pi_model = f.read().strip().replace('\x00', '')
    except:
        pi_model = "Unknown"
    
    return {
        'hostname': os.uname().nodename,
        'system': f"{os.uname().sysname} {os.uname().release}",
        'pi_model': pi_model,
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total // (1024**3)  # GB
    }


def get_temperature():
    """Get CPU temperature"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return int(f.read().strip()) / 1000.0
    except:
        return None


def format_bytes(bytes_val):
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"


def print_system_status():
    """Print current system status"""
    # Clear screen
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # System info
    info = get_system_info()
    
    print("╔" + "═" * 78 + "╗")
    print(f"║{'UAV RESOURCE MONITOR - LIVE STATUS':^78}║")
    print("╠" + "═" * 78 + "╣")
    print(f"║ Host: {info['hostname']:<25} │ Model: {info['pi_model']:<39} ║")
    print(f"║ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<25} │ CPUs: {info['cpu_count']} cores, {info['memory_total']} GB RAM{'':<20} ║")
    print("╠" + "═" * 78 + "╣")
    
    # CPU Information
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    temp = get_temperature()
    load_avg = os.getloadavg()
    
    print(f"║ CPU Usage: {cpu_percent:5.1f}% │ ", end="")
    print(f"Frequency: {cpu_freq.current:.0f}/{cpu_freq.max:.0f} MHz │ ", end="") if cpu_freq else print("Frequency: N/A │ ", end="")
    print(f"Temp: {temp:.1f}°C ║") if temp else print("Temp: N/A   ║")
    
    # Create CPU usage bar
    cpu_bar_width = 50
    cpu_filled = int(cpu_percent / 100 * cpu_bar_width)
    cpu_bar = "█" * cpu_filled + "░" * (cpu_bar_width - cpu_filled)
    print(f"║ [{cpu_bar}] {'':<20} ║")
    
    print(f"║ Load Avg: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f} (1m, 5m, 15m){'':<31} ║")
    
    # Memory Information
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    print("╠" + "═" * 78 + "╣")
    print(f"║ Memory: {memory.percent:5.1f}% │ ", end="")
    print(f"Used: {format_bytes(memory.used):<12} │ ", end="")
    print(f"Free: {format_bytes(memory.available):<12} ║")
    
    # Memory usage bar
    mem_filled = int(memory.percent / 100 * cpu_bar_width)
    mem_bar = "█" * mem_filled + "░" * (cpu_bar_width - mem_filled)
    print(f"║ [{mem_bar}] {'':<20} ║")
    
    if swap.total > 0:
        print(f"║ Swap: {swap.percent:7.1f}% │ Used: {format_bytes(swap.used):<12} │ Total: {format_bytes(swap.total):<11} ║")
    
    # Disk Information
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    
    print("╠" + "═" * 78 + "╣")
    print(f"║ Disk: {disk_percent:7.1f}% │ Used: {format_bytes(disk.used):<12} │ Free: {format_bytes(disk.free):<12} ║")
    
    # Network Information
    net_io = psutil.net_io_counters()
    
    print("╠" + "═" * 78 + "╣")
    print(f"║ Network Sent: {format_bytes(net_io.bytes_sent):<15} │ Received: {format_bytes(net_io.bytes_recv):<15} ║")
    print(f"║ Packets Sent: {net_io.packets_sent:<15,} │ Received: {net_io.packets_recv:<15,} ║")
    
    # Process Information
    processes = len(psutil.pids())
    uptime = time.time() - psutil.boot_time()
    uptime_str = f"{int(uptime//3600)}h {int((uptime%3600)//60)}m"
    
    print("╠" + "═" * 78 + "╣")
    print(f"║ Processes: {processes:<8} │ Uptime: {uptime_str:<15} │ Boot: {datetime.fromtimestamp(psutil.boot_time()).strftime('%m/%d %H:%M'):<15} ║")
    print("╚" + "═" * 78 + "╝")


def live_monitor(interval: float = 2.0):
    """Run live monitoring display"""
    print("Starting live monitor... (Press Ctrl+C to stop)")
    
    try:
        while True:
            print_system_status()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nLive monitor stopped.")


def quick_test(duration: int = 30):
    """Run a quick monitoring test"""
    print(f"Running {duration} second resource test...")
    
    start_time = time.time()
    samples = []
    
    try:
        while time.time() - start_time < duration:
            # Collect metrics
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            temp = get_temperature()
            
            sample = {
                'time': time.time() - start_time,
                'cpu': cpu,
                'memory': memory.percent,
                'temp': temp
            }
            samples.append(sample)
            
            # Print progress
            elapsed = time.time() - start_time
            progress = int(elapsed / duration * 50)
            bar = "█" * progress + "░" * (50 - progress)
            print(f"\r[{bar}] {elapsed:.1f}s - CPU: {cpu:.1f}% Mem: {memory.percent:.1f}% Temp: {temp:.1f}°C" if temp else f"\r[{bar}] {elapsed:.1f}s - CPU: {cpu:.1f}% Mem: {memory.percent:.1f}%", end="")
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nTest interrupted.")
        return
    
    print(f"\n\nTest completed! {len(samples)} samples collected.")
    
    # Calculate simple statistics
    if samples:
        cpu_vals = [s['cpu'] for s in samples]
        mem_vals = [s['memory'] for s in samples]
        temp_vals = [s['temp'] for s in samples if s['temp'] is not None]
        
        print(f"\nResults:")
        print(f"  CPU:    avg={sum(cpu_vals)/len(cpu_vals):.1f}% max={max(cpu_vals):.1f}%")
        print(f"  Memory: avg={sum(mem_vals)/len(mem_vals):.1f}% max={max(mem_vals):.1f}%")
        if temp_vals:
            print(f"  Temp:   avg={sum(temp_vals)/len(temp_vals):.1f}°C max={max(temp_vals):.1f}°C")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Quick UAV Resource Monitor')
    parser.add_argument('--live', '-l', action='store_true', 
                       help='Run live monitoring display')
    parser.add_argument('--test', '-t', type=int, metavar='SECONDS', 
                       help='Run quick test for specified duration')
    parser.add_argument('--interval', '-i', type=float, default=2.0,
                       help='Update interval for live mode (default: 2.0s)')
    
    args = parser.parse_args()
    
    try:
        if args.live:
            live_monitor(args.interval)
        elif args.test:
            quick_test(args.test)
        else:
            # Default: show current status once
            print_system_status()
            print("\nUse --live for continuous monitoring or --test SECONDS for a quick test")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

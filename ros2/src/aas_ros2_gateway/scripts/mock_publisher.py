#!/usr/bin/env python3
"""
PX4 Mock Publisher for Academic Experiments

Focuses on two key variables:
1. Number of topics (which topics to enable)
2. Message frequency

Publishes PX4-format messages with basic data patterns.
Configuration is done via a YAML file.
"""

import math
import time
import random
import yaml
import rclpy
from rclpy.node import Node
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

# PX4 message imports
from px4_msgs.msg import (
    BatteryStatus, VehicleLocalPosition, VehicleAttitude, 
    VehicleStatus, SensorGps, VehicleGlobalPosition
)

class Px4MockPublisher(Node):
    """Mock publisher for PX4 messages with configurable topics and frequencies."""
    
    def __init__(self):
        super().__init__('px4_mock_publisher')
        
        # Load configuration from installed share directory so it works after install
        try:
            share_dir = Path(get_package_share_directory('aas_ros2_gateway'))
            config_path = share_dir / 'config' / 'mock_config.yaml'
        except Exception:
            # Fallback: try source layout
            config_path = Path(__file__).parent.parent / 'config' / 'mock_config.yaml'
        self.config = self._load_config(config_path)
        
        # Setup publishers and timers (avoid name clash with Node internals)
        self.topic_publishers = {}
        self.topic_timers = {}
        self.start_time = time.time()
        
        self._setup_publishers()
        
        # Log configuration
        enabled_topics = [topic for topic, cfg in self.config['topics'].items() if cfg.get('enabled', False)]
        total_frequency = sum(self.config['topics'][topic]['frequency'] for topic in enabled_topics)
        
        self.get_logger().info(f"PX4 Mock Publisher started")
        self.get_logger().info(f"Enabled topics: {len(enabled_topics)} - {enabled_topics}")
        self.get_logger().info(f"Total frequency: {total_frequency} Hz")
        
    def _load_config(self, config_path):
        """Load YAML configuration file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.get_logger().info(f"Loaded configuration from: {config_path}")
            return config
        except Exception as e:
            self.get_logger().error(f"Failed to load config: {e}")
            # Fallback to default config
            return self._default_config()
    
    def _default_config(self):
        """Default configuration if file loading fails."""
        return {
            'namespace': '/px4_1/fmu/out',
            'topics': {
                'battery_status': {'enabled': True, 'frequency': 2.0},
                'vehicle_local_position': {'enabled': True, 'frequency': 30.0},
                'vehicle_attitude': {'enabled': True, 'frequency': 50.0},
                'vehicle_status': {'enabled': True, 'frequency': 5.0},
                'vehicle_gps_position': {'enabled': True, 'frequency': 10.0},
                'vehicle_global_position': {'enabled': False, 'frequency': 10.0}
            }
        }
    
    def _setup_publishers(self):
        """Setup ROS2 publishers for enabled topics."""
        namespace = self.config.get('namespace', '/px4_1/fmu/out')
        
        topic_configs = {
            'battery_status': (BatteryStatus, self._publish_battery_status),
            'vehicle_local_position': (VehicleLocalPosition, self._publish_local_position),
            'vehicle_attitude': (VehicleAttitude, self._publish_attitude),
            'vehicle_status': (VehicleStatus, self._publish_vehicle_status),
            'vehicle_gps_position': (SensorGps, self._publish_gps_position),
            'vehicle_global_position': (VehicleGlobalPosition, self._publish_global_position)
        }
        
        for topic_name, topic_config in self.config['topics'].items():
            if not topic_config.get('enabled', False):
                continue
                
            if topic_name not in topic_configs:
                self.get_logger().warning(f"Unknown topic: {topic_name}")
                continue
                
            msg_type, publish_func = topic_configs[topic_name]
            topic_path = f"{namespace.rstrip('/')}/{topic_name}"
            
            # Create publisher
            publisher = self.create_publisher(msg_type, topic_path, 10)
            self.topic_publishers[topic_name] = publisher
            
            # Create timer
            frequency = float(topic_config['frequency'])
            if frequency <= 0:
                self.get_logger().warning(f"Frequency for {topic_name} must be > 0, skipping")
                continue
            period = 1.0 / frequency
            timer = self.create_timer(period, lambda tn=topic_name, pf=publish_func: pf(tn))
            self.topic_timers[topic_name] = timer
            
            self.get_logger().info(f"Setup {topic_name} at {frequency} Hz -> {topic_path}")
    
    def _get_timestamp(self):
        """Get current timestamp in PX4 format (microseconds)."""
        return int(time.time() * 1e6)
    
    def _get_time_since_start(self):
        """Get time elapsed since start."""
        return time.time() - self.start_time
    
    def _publish_battery_status(self, topic_name):
        """Publish battery status message."""
        msg = BatteryStatus()
        msg.timestamp = self._get_timestamp()
        
        # battery drain pattern
        t = self._get_time_since_start()
        msg.remaining = max(0.1, 1.0 - (t / 600.0))  # Drain over 10 minutes
        msg.voltage_v = 12.6 * msg.remaining
        msg.current_a = 2.0 + random.uniform(-0.5, 0.5)
        msg.temperature = 25.0 + 5.0 * math.sin(t / 60.0)
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_local_position(self, topic_name):
        """Publish local position message."""
        msg = VehicleLocalPosition()
        msg.timestamp = self._get_timestamp()
        
        # circular pattern
        t = self._get_time_since_start()
        radius = 20.0
        msg.x = radius * math.cos(t / 30.0)
        msg.y = radius * math.sin(t / 30.0)
        msg.z = -10.0 + 3.0 * math.sin(t / 20.0)
        
        # velocities (derivatives)
        msg.vx = -radius / 30.0 * math.sin(t / 30.0)
        msg.vy = radius / 30.0 * math.cos(t / 30.0)
        msg.vz = 3.0 / 20.0 * math.cos(t / 20.0)
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_attitude(self, topic_name):
        """Publish attitude message."""
        msg = VehicleAttitude()
        msg.timestamp = self._get_timestamp()
        
        # attitude changes
        t = self._get_time_since_start()
        roll = 0.1 * math.sin(t / 5.0)
        pitch = 0.1 * math.cos(t / 7.0)
        yaw = t / 20.0  # Slow rotation
        
        # Convert to quaternion
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        
        w = cy * cr * cp + sy * sr * sp
        x = cy * sr * cp - sy * cr * sp
        y = cy * cr * sp + sy * sr * cp
        z = sy * cr * cp - cy * sr * sp
        
        msg.q = [float(w), float(x), float(y), float(z)]
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_vehicle_status(self, topic_name):
        """Publish vehicle status message."""
        msg = VehicleStatus()
        msg.timestamp = self._get_timestamp()
        
        # Cycle through nav states every 60 seconds
        t = self._get_time_since_start()
        nav_states = [0, 2, 3, 4, 5]  # MANUAL, POSCTL, MISSION, LOITER, RTL
        state_index = int(t / 60.0) % len(nav_states)
        msg.nav_state = nav_states[state_index]
        
        # arming state (armed after 5 seconds)
        msg.arming_state = 3 if t > 5.0 else 2  # ARMED or STANDBY
        msg.failsafe = False
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_gps_position(self, topic_name):
        """Publish GPS position message."""
        msg = SensorGps()
        msg.timestamp = self._get_timestamp()
        
        # Fixed location with small variations
        t = self._get_time_since_start()
        msg.latitude_deg = 47.397742 + 0.00001 * math.sin(t / 100.0)
        msg.longitude_deg = 8.545594 + 0.00001 * math.cos(t / 100.0)
        msg.altitude_msl_m = 488.0 + 2.0 * math.sin(t / 50.0)
        msg.altitude_ellipsoid_m = msg.altitude_msl_m - 8.0
        
        # GPS accuracy
        msg.eph = 1.0 + 0.5 * random.random()
        msg.epv = 1.5 + 0.5 * random.random()
        msg.satellites_used = random.randint(10, 16)
        msg.fix_type = 3  # 3D fix
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_global_position(self, topic_name):
        """Publish global position message."""
        msg = VehicleGlobalPosition()
        msg.timestamp = self._get_timestamp()
        
        # global position data
        t = self._get_time_since_start()
        msg.lat = 47.397742 + 0.00001 * math.sin(t / 100.0)
        msg.lon = 8.545594 + 0.00001 * math.cos(t / 100.0)
        msg.alt = 488.0 + 2.0 * math.sin(t / 50.0)
        msg.yaw = (t / 20.0) % (2 * math.pi)
        
        self.topic_publishers[topic_name].publish(msg)


def main():
    """Main function."""
    rclpy.init()
    
    try:
        publisher = Px4MockPublisher()
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

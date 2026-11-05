#!/usr/bin/env python3
"""
MAVROS/MAVLink Mock Publisher for Experiments

Simulates MAVROS topics by publishing standard ROS2 messages that MAVROS would publish.
This allows testing without actual MAVLink hardware or simulation.

Focuses on two key variables:
1. Number of topics (which topics to enable)
2. Message frequency

Publishes MAVROS-format messages with simple synthetic patterns.
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

# Standard ROS2 message imports (what MAVROS publishes)
from sensor_msgs.msg import BatteryState, NavSatFix
from geometry_msgs.msg import PoseStamped, TwistStamped
from std_msgs.msg import Float64, Header
from mavros_msgs.msg import State, GPSRAW


class MavlinkMockPublisher(Node):
    """Mock publisher for MAVROS messages with configurable topics and frequencies."""
    
    def __init__(self):
        super().__init__('mavlink_mock_publisher')
        
        # Load configuration from installed share directory so it works after install
        try:
            share_dir = Path(get_package_share_directory('aas_ros2_gateway'))
            config_path = share_dir / 'config' / 'mavlink_mock_config.yaml'
        except Exception:
            # Fallback: try source layout
            config_path = Path(__file__).parent.parent / 'config' / 'mavlink_mock_config.yaml'
        self.config = self._load_config(config_path)
        
        # Setup publishers and timers (avoid name clash with Node internals)
        self.topic_publishers = {}
        self.topic_timers = {}
        self.start_time = time.time()
        self.seq_counters = {}  # Sequence counters for headers
        
        self._setup_publishers()
        
        # Log configuration
        enabled_topics = [topic for topic, cfg in self.config['topics'].items() if cfg.get('enabled', False)]
        total_frequency = sum(self.config['topics'][topic]['frequency'] for topic in enabled_topics)
        
        self.get_logger().info(f"MAVROS Mock Publisher started")
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
            'namespace': '/mavros',
            'topics': {
                'battery': {'enabled': True, 'frequency': 2.0},
                'local_position_pose': {'enabled': True, 'frequency': 30.0},
                'local_position_velocity': {'enabled': True, 'frequency': 30.0},
                'state': {'enabled': True, 'frequency': 5.0},
                'gps_raw': {'enabled': True, 'frequency': 10.0},
                'global_position': {'enabled': True, 'frequency': 10.0},
                'compass_hdg': {'enabled': True, 'frequency': 10.0}
            }
        }
    
    def _setup_publishers(self):
        """Setup ROS2 publishers for enabled topics."""
        namespace = self.config.get('namespace', '/mavros')
        
        topic_configs = {
            'battery': ('battery', BatteryState, self._publish_battery),
            'local_position_pose': ('local_position/pose', PoseStamped, self._publish_local_pose),
            'local_position_velocity': ('local_position/velocity_local', TwistStamped, self._publish_local_velocity),
            'state': ('state', State, self._publish_state),
            'gps_raw': ('gpsstatus/gps1/raw', GPSRAW, self._publish_gps_raw),
            'global_position': ('global_position/global', NavSatFix, self._publish_global_position),
            'compass_hdg': ('global_position/compass_hdg', Float64, self._publish_compass_heading)
        }
        
        for topic_name, topic_config in self.config['topics'].items():
            if not topic_config.get('enabled', False):
                continue
                
            if topic_name not in topic_configs:
                self.get_logger().warning(f"Unknown topic: {topic_name}")
                continue
                
            topic_suffix, msg_type, publish_func = topic_configs[topic_name]
            topic_path = f"{namespace.rstrip('/')}/{topic_suffix}"
            
            # Create publisher
            publisher = self.create_publisher(msg_type, topic_path, 10)
            self.topic_publishers[topic_name] = publisher
            self.seq_counters[topic_name] = 0
            
            # Create timer
            frequency = float(topic_config['frequency'])
            if frequency <= 0:
                self.get_logger().warning(f"Frequency for {topic_name} must be > 0, skipping")
                continue
            period = 1.0 / frequency
            timer = self.create_timer(period, lambda tn=topic_name, pf=publish_func: pf(tn))
            self.topic_timers[topic_name] = timer
            
            self.get_logger().info(f"Setup {topic_name} at {frequency} Hz -> {topic_path}")
    
    def _get_header(self, topic_name, frame_id='map'):
        """Create a standard ROS2 header with timestamp and frame_id."""
        header = Header()
        now = self.get_clock().now().to_msg()
        header.stamp = now
        header.frame_id = frame_id
        self.seq_counters[topic_name] += 1
        return header
    
    def _get_time_since_start(self):
        """Get time elapsed since start."""
        return time.time() - self.start_time
    
    def _euler_to_quaternion(self, roll, pitch, yaw):
        """Convert Euler angles to quaternion."""
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
        
        return (w, x, y, z)
    
    def _publish_battery(self, topic_name):
        """Publish battery status message (sensor_msgs/BatteryState)."""
        msg = BatteryState()
        msg.header = self._get_header(topic_name, 'base_link')
        
        # Battery drain pattern
        t = self._get_time_since_start()
        percentage = max(0.1, 1.0 - (t / 600.0))  # Drain over 10 minutes
        
        msg.voltage = 12.6 * percentage
        msg.temperature = 25.0 + 5.0 * math.sin(t / 60.0)
        msg.current = -(2.0 + random.uniform(-0.5, 0.5))  # Negative means discharging
        msg.charge = float('nan')  # Not available
        msg.capacity = float('nan')  # Not available
        msg.design_capacity = 5.0  # 5 Ah
        msg.percentage = percentage
        msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LIPO
        msg.present = True
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_local_pose(self, topic_name):
        """Publish local position pose message (geometry_msgs/PoseStamped)."""
        msg = PoseStamped()
        msg.header = self._get_header(topic_name, 'map')
        
        # Circular flight pattern
        t = self._get_time_since_start()
        radius = 20.0
        msg.pose.position.x = radius * math.cos(t / 30.0)
        msg.pose.position.y = radius * math.sin(t / 30.0)
        msg.pose.position.z = 10.0 + 3.0 * math.sin(t / 20.0)  # Altitude variation
        
        # Attitude changes
        roll = 0.1 * math.sin(t / 5.0)
        pitch = 0.1 * math.cos(t / 7.0)
        yaw = t / 20.0  # Slow rotation
        
        q = self._euler_to_quaternion(roll, pitch, yaw)
        msg.pose.orientation.w = q[0]
        msg.pose.orientation.x = q[1]
        msg.pose.orientation.y = q[2]
        msg.pose.orientation.z = q[3]
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_local_velocity(self, topic_name):
        """Publish local velocity message (geometry_msgs/TwistStamped)."""
        msg = TwistStamped()
        msg.header = self._get_header(topic_name, 'map')
        
        # Velocities derived from circular pattern
        t = self._get_time_since_start()
        radius = 20.0
        msg.twist.linear.x = -radius / 30.0 * math.sin(t / 30.0)
        msg.twist.linear.y = radius / 30.0 * math.cos(t / 30.0)
        msg.twist.linear.z = 3.0 / 20.0 * math.cos(t / 20.0)
        
        # Angular velocities
        msg.twist.angular.x = 0.1 / 5.0 * math.cos(t / 5.0)  # Roll rate
        msg.twist.angular.y = -0.1 / 7.0 * math.sin(t / 7.0)  # Pitch rate
        msg.twist.angular.z = 1.0 / 20.0  # Yaw rate
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_state(self, topic_name):
        """Publish vehicle state message (mavros_msgs/State)."""
        msg = State()
        msg.header = self._get_header(topic_name)
        
        # Cycle through flight modes
        t = self._get_time_since_start()
        modes = ["MANUAL", "STABILIZED", "ALTCTL", "POSCTL", "AUTO.LOITER", "AUTO.MISSION"]
        mode_index = int(t / 60.0) % len(modes)
        msg.mode = modes[mode_index]
        
        # Armed after 5 seconds
        msg.armed = t > 5.0
        msg.connected = True
        msg.guided = mode_index >= 4  # AUTO modes are guided
        msg.manual_input = mode_index < 2  # MANUAL and STABILIZED have manual input
        msg.system_status = 4  # MAV_STATE_ACTIVE
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_gps_raw(self, topic_name):
        """Publish raw GPS data message (mavros_msgs/GPSRAW)."""
        msg = GPSRAW()
        msg.header = self._get_header(topic_name, 'base_link')
        
        # Fixed location with small variations (Zurich, Switzerland)
        t = self._get_time_since_start()
        msg.lat = int((47.397742 + 0.00001 * math.sin(t / 100.0)) * 1e7)
        msg.lon = int((8.545594 + 0.00001 * math.cos(t / 100.0)) * 1e7)
        msg.alt = int((488.0 + 2.0 * math.sin(t / 50.0)) * 1000)  # mm
        
        # GPS accuracy
        msg.eph = int((1.0 + 0.5 * random.random()) * 100)  # cm
        msg.epv = int((1.5 + 0.5 * random.random()) * 100)  # cm
        msg.vel = int(math.sqrt(
            (20.0 / 30.0) ** 2 + (20.0 / 30.0) ** 2
        ) * 100)  # cm/s
        
        msg.cog = int((math.atan2(
            20.0 / 30.0 * math.cos(t / 30.0),
            -20.0 / 30.0 * math.sin(t / 30.0)
        ) * 180.0 / math.pi) * 100) % 36000  # centidegrees
        
        msg.fix_type = 3  # 3D fix
        msg.satellites_visible = random.randint(10, 16)
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_global_position(self, topic_name):
        """Publish global position message (sensor_msgs/NavSatFix)."""
        msg = NavSatFix()
        msg.header = self._get_header(topic_name, 'base_link')
        
        # Global position data (Zurich, Switzerland)
        t = self._get_time_since_start()
        msg.latitude = 47.397742 + 0.00001 * math.sin(t / 100.0)
        msg.longitude = 8.545594 + 0.00001 * math.cos(t / 100.0)
        msg.altitude = 488.0 + 2.0 * math.sin(t / 50.0)
        
        # GPS status
        msg.status.status = 0  # STATUS_FIX (0 = no fix, 1 = fix, 2 = SBAS fix)
        msg.status.service = 1  # SERVICE_GPS
        
        # Use fix_type from time to simulate GPS acquisition
        if t > 10.0:
            msg.status.status = 1  # GPS fix acquired after 10 seconds
        
        # Covariance (position uncertainty)
        # Format: [x, y, z] in ENU frame
        accuracy = 1.0 + 0.5 * random.random()
        msg.position_covariance = [
            accuracy**2, 0.0, 0.0,
            0.0, accuracy**2, 0.0,
            0.0, 0.0, (accuracy*1.5)**2
        ]
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_APPROXIMATED
        
        self.topic_publishers[topic_name].publish(msg)
    
    def _publish_compass_heading(self, topic_name):
        """Publish compass heading message (std_msgs/Float64)."""
        msg = Float64()
        
        # Heading from circular flight pattern
        t = self._get_time_since_start()
        heading_rad = (t / 20.0) % (2 * math.pi)
        msg.data = math.degrees(heading_rad)  # Convert to degrees
        
        self.topic_publishers[topic_name].publish(msg)


def main():
    rclpy.init()
    
    try:
        publisher = MavlinkMockPublisher()
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Flexible mock publisher for testing the AAS ROS2 Gateway.

Supports two modes:
- px4: publishes common typed topics similar to PX4/MAVROS (BatteryState, Imu, NavSatFix, Odometry, String status)
- simple: loads a YAML configuration describing string topics to publish (sequential, random_int, random_choice)

This lets you test both legacy string-based mappings and the message-type mappings.
"""
import argparse
import math
import time
import random
import json

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import Quaternion
from px4_msgs.msg import BatteryStatus, VehicleLocalPosition, VehicleAttitude, VehicleStatus, SensorGps

import yaml


def quaternion_from_euler(roll, pitch, yaw):
    # Convert Euler angles (radians) to quaternion
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)

    q = Quaternion()
    q.w = cy * cr * cp + sy * sr * sp
    q.x = cy * sr * cp - sy * cr * sp
    q.y = cy * cr * sp + sy * sr * cp
    q.z = sy * cr * cp - cy * sr * sp
    return q


class Px4MockPublisher(Node):
    """Publish PX4-style messages matching map.yaml fields.

    Publishes:
    - px4_msgs/BatteryStatus on <ns>/battery_status (field: remaining)
    - px4_msgs/VehicleLocalPosition on <ns>/vehicle_local_position (field: z)
    - px4_msgs/VehicleAttitude on <ns>/vehicle_attitude (field: q)
    - px4_msgs/VehicleStatus on <ns>/vehicle_status (field: nav_state)
    - px4_msgs/SensorGps on <ns>/vehicle_gps_position (fields: eph, satellites_used)
    """
    def __init__(self, hz: float, ns: str = '/px4_1/fmu/out'):
        super().__init__('px4_mock_publisher')
        self.hz = hz
        self.period = 1.0 / hz
        base = ns.rstrip('/')

        self.bat_pub = self.create_publisher(BatteryStatus, f'{base}/battery_status', 10)
        self.att_pub = self.create_publisher(VehicleAttitude, f'{base}/vehicle_attitude', 10)
        self.status_pub = self.create_publisher(VehicleStatus, f'{base}/vehicle_status', 10)
        self.vlp_pub = self.create_publisher(VehicleLocalPosition, f'{base}/vehicle_local_position', 10)
        self.gps_pub = self.create_publisher(SensorGps, f'{base}/vehicle_gps_position', 10)

        self.start_time = time.time()
        self.timer = self.create_timer(self.period, self.timer_callback)
        self.get_logger().info(f'PX4 mock publisher started at {hz} Hz (ns={base})')

    def timer_callback(self):
        t = self.get_clock().now().nanoseconds / 1e9

        # --- SensorGps ---
        sg = SensorGps()
        sg.timestamp = self.get_clock().now().nanoseconds // 1000
        sg.latitude_deg = 47.397742 + 0.00001 * math.sin(t / 30.0)
        sg.longitude_deg = 8.545594 + 0.00001 * math.cos(t / 30.0)
        sg.altitude_msl_m = 488.0
        sg.altitude_ellipsoid_m = 480.0
        sg.eph = 0.5
        sg.epv = 0.8
        sg.satellites_used = 12
        sg.cog_rad = math.pi
        self.gps_pub.publish(sg)

        # --- VehicleLocalPosition ---
        vlp = VehicleLocalPosition()
        vlp.timestamp = self.get_clock().now().nanoseconds // 1000
        vlp.x = 10.0 * math.sin(t / 10.0)
        vlp.y = 10.0 * math.cos(t / 10.0)
        vlp.z = -1.0 * (5.0 + 2.0 * math.sin(t / 5.0))
        self.vlp_pub.publish(vlp)

        # --- VehicleAttitude ---
        va = VehicleAttitude()
        va.timestamp = self.get_clock().now().nanoseconds // 1000
        roll = 0.1 * math.sin(t)
        pitch = 0.1 * math.cos(t)
        yaw = 0.0
        q = quaternion_from_euler(roll, pitch, yaw)
        # px4_msgs.VehicleAttitude.q expects a sequence of 4 floats (w,x,y,z)
        va.q = [float(q.w), float(q.x), float(q.y), float(q.z)]
        self.att_pub.publish(va)

        # --- VehicleStatus ---
        vs = VehicleStatus()
        vs.timestamp = self.get_clock().now().nanoseconds // 1000
        vs.nav_state = VehicleStatus.NAVIGATION_STATE_MANUAL
        self.status_pub.publish(vs)


class ConfigMockPublisher(Node):
    """YAML-driven simple publisher that emits String messages per topic."""
    def __init__(self, config_path: str):
        super().__init__('config_mock_publisher')
        self.publishers = {}
        self.timers = []
        self.topic_configs = {}
        self.sequence_counters = {}

        try:
            with open(config_path, 'r') as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            self.get_logger().error(f'Failed to open config: {e}')
            raise

        for item in cfg.get('publishers', []):
            topic = item.get('topic')
            if not topic:
                self.get_logger().warning('Skipping entry without topic')
                continue
            self.topic_configs[topic] = item
            self.publishers[topic] = self.create_publisher(String, topic, 10)
            if item.get('data_type') == 'sequential':
                self.sequence_counters[topic] = 0

            freq = float(item.get('frequency', 1.0))
            if freq <= 0:
                self.get_logger().error(f'Invalid frequency for {topic}')
                continue
            period = 1.0 / freq
            # create_timer closure
            timer = self.create_timer(period, lambda t=topic: self._pub_cb(t))
            self.timers.append(timer)
            self.get_logger().info(f'Configured simple publisher for {topic} @ {freq}Hz')

    def _generate(self, topic: str) -> str:
        cfg = self.topic_configs.get(topic, {})
        dt = cfg.get('data_type', 'random_choice')
        if dt == 'sequential':
            v = self.sequence_counters.get(topic, 0)
            self.sequence_counters[topic] = v + 1
            return str(v)
        if dt == 'random_int':
            low = int(cfg.get('min', 0))
            high = int(cfg.get('max', 100))
            return str(random.randint(low, high))
        # default: random_choice
        choices = cfg.get('mock_data', [])
        if not choices:
            return ''
        return str(random.choice(choices))

    def _pub_cb(self, topic: str):
        pub = self.publishers.get(topic)
        if not pub:
            return
        msg = String()
        msg.data = self._generate(topic)
        pub.publish(msg)
        self.get_logger().debug(json.dumps({'topic': topic, 'data': msg.data}))


def main():
    parser = argparse.ArgumentParser(description='Flexible mock ROS2 publisher')
    parser.add_argument('--mode', choices=['px4', 'simple'], default='px4', help='Publishing mode')
    parser.add_argument('--hz', type=float, default=1.0, help='Base publish rate for px4 mode')
    parser.add_argument('--ns', type=str, default='/px4_1/fmu/out', help='Namespace/prefix for px4 topics')
    parser.add_argument('--config', type=str, default='', help='Path to YAML config for simple mode')
    args = parser.parse_args()

    rclpy.init()
    node = None
    try:
        if args.mode == 'px4':
            node = Px4MockPublisher(args.hz, ns=args.ns)
        else:
            if not args.config:
                raise SystemExit('simple mode requires --config <path_to_yaml>')
            node = ConfigMockPublisher(args.config)

        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if 'node' in locals() and node is not None and rclpy.ok():
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import yaml
import random
import argparse

class MockPublisherNode(Node):
    """
    A flexible mock data publisher that generates data based on a YAML config.
    Supports sequential, random integer, and random choice data generation.
    """
    def __init__(self, config_path):
        super().__init__('mock_publisher')
        self.publishers_ = {}
        self.timers_ = []
        self.topic_configs_ = {}
        self.sequence_counters_ = {} # For sequential data generation

        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                self.load_publishers(config.get('publishers', []))
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.get_logger().error(f"Failed to load or parse config file '{config_path}': {e}")
            # Raise an exception to prevent the node from running with an invalid config
            raise

    def load_publishers(self, publishers_config):
        """Loads and sets up publishers and timers from the config list."""
        for item_config in publishers_config:
            topic = item_config.get('topic')
            if not topic:
                self.get_logger().warn("Skipping publisher item with no topic.")
                continue

            self.topic_configs_[topic] = item_config
            self.publishers_[topic] = self.create_publisher(String, topic, 10)
            
            if item_config.get('data_type') == 'sequential':
                self.sequence_counters_[topic] = 0

            # Create a timer that calls the publisher callback
            frequency = item_config.get('frequency', 1.0) # Default: 1 Hz
            if frequency <= 0:
                self.get_logger().error(f"Frequency for topic '{topic}' must be positive. Skipping.")
                continue
            
            timer_period = 1.0 / frequency
            timer = self.create_timer(timer_period, lambda t=topic: self.publish_message(t))
            self.timers_.append(timer)
            self.get_logger().info(f"Configured publisher for '{topic}' at {frequency} Hz.")

    def generate_data(self, topic):
        """Generates data for a given topic based on its configuration."""
        config = self.topic_configs_[topic]
        data_type = config.get('data_type', 'random_choice') # Default: random_choice

        if data_type == 'sequential':
            value = self.sequence_counters_[topic]
            self.sequence_counters_[topic] += 1
            return str(value)
        
        elif data_type == 'random_int':
            min_val = config.get('min', 0)
            max_val = config.get('max', 100)
            return str(random.randint(min_val, max_val))
            
        elif data_type == 'random_choice':
            choices = config.get('mock_data', [])
            if not choices:
                self.get_logger().warn(f"Data type for topic '{topic}' is 'random_choice' but no 'mock_data' list was provided.")
                return ""
            return str(random.choice(choices))
            
        else:
            self.get_logger().warn(f"Unknown data_type '{data_type}' for topic '{topic}'. Defaulting to empty string.")
            return ""

    def publish_message(self, topic):
        """Callback that generates and publishes a message for a specific topic."""
        publisher = self.publishers_[topic]
        msg = String()
        msg.data = self.generate_data(topic)
        publisher.publish(msg)

        log_payload = {
            'event': 'publish_message',
            'topic': topic,
            'data': msg.data
        }
        self.get_logger().info(json.dumps(log_payload))

def main(args=None):
    rclpy.init(args=args)
    
    parser = argparse.ArgumentParser(description='Mock ROS2 Publisher')
    parser.add_argument('config', type=str, help='Path to the publisher configuration YAML file.')
    
    try:
        known_args, ros_args = parser.parse_known_args()
        node = MockPublisherNode(known_args.config)
        rclpy.spin(node)
    except (SystemExit, FileNotFoundError, yaml.YAMLError):
        # This will catch argparse errors or file loading errors gracefully
        pass
    except KeyboardInterrupt:
        pass
    finally:
        if 'node' in locals() and rclpy.ok():
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()

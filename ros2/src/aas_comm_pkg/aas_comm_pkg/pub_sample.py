import rclpy
from rclpy.node import Node
import random
from std_msgs.msg import String


class MultiTopicPublisher(Node):

    # topic and seqnum
    topic_seqnum = {}

    def __init__(self, topics_with_periods_and_values: dict):
        super().__init__('multi_topic_publisher')

        self.topics_publishers = {}  # Store publishers for each topic
        self.topics_timers = {}  # Store timers for each topic

        # Initialize publishers and timers for each topic
        for topic, config in topics_with_periods_and_values.items():
            min_value = config['min']
            max_value = config['max']
            period = config['period']

            # Create publisher for the topic
            self.topics_publishers[topic] = self.create_publisher(String, topic, 10)

            # Create a timer that calls the `timer_callback` function periodically
            self.topics_timers[topic] = self.create_timer(period, lambda topic=topic, min_value=min_value, max_value=max_value: self.timer_callback(topic, min_value, max_value))

    def timer_callback(self, topic, min_value, max_value):
        # topic_value = random.randint(min_value, max_value)
        topic_value = self.topic_seqnum[topic] if topic in self.topic_seqnum else 0
        self.topic_seqnum[topic] = topic_value + 1
        msg = String()
        msg.data = str(topic_value)

        # Publish the random number to the appropriate topic
        self.topics_publishers[topic].publish(msg)
        self.get_logger().info(f'Publishing: "{msg.data}" to topic: "{topic}"')


def main(args=None):
    rclpy.init(args=args)

    # Define topics with their min/max values and publication periods
    topics_with_periods_and_values = {
        'horizontal_speed': {'min': 30, 'max': 60, 'period': 0.2},  # Horizontal Speed
        'vertical_speed': {'min': 0, 'max': 10, 'period': 0.2},  # Vertical Speed 
        'battery': {'min': 80, 'max': 80, 'period': 1},  # Battery
        'altitude': {'min': 20, 'max': 25, 'period': 0.2},  # Altitude 
        'temperature': {'min': 16, 'max': 18, 'period': 0.5},  # Temperature 
        'signal_strength': {'min': 90, 'max': 95, 'period': 0.5},  # Signal Strength
        'pitch': {'min': -15, 'max': 15, 'period': 0.2},  # Pitch Angle
        'roll': {'min': -20, 'max': 20, 'period': 0.2},  # Roll Angle   
        'imu_temperature': {'min': 20, 'max': 60, 'period': 1},  # IMU Sensor Temperature
        'motor_rpm': {'min': 1000, 'max': 8000, 'period': 0.2},  # Motor RPM        
    }
    # Calculate the total data frequency
    data_frequency = sum(1 / config['period'] for config in topics_with_periods_and_values.values())
    print(f"Total data frequency: {data_frequency} Hz")

    # Initialize the MultiTopicPublisher node with the topic configurations
    multi_topic_publisher = MultiTopicPublisher(topics_with_periods_and_values=topics_with_periods_and_values)

    # Spin the node to handle the timers and publisher callbacks
    rclpy.spin(multi_topic_publisher)

    # Clean up and shutdown
    multi_topic_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
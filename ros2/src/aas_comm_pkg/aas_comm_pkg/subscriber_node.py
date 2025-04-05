import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from .opcua_client import OPCUAClient

class MultiTopicSubscriber(Node):
    def __init__(self, topics_to_node_ids: dict, opcua_endpoint: str):
        super().__init__('multi_topic_subscriber')
        if not topics_to_node_ids:
            raise ValueError("topics_to_node_ids cannot be empty")

        self.opcua_client = OPCUAClient(opcua_endpoint)
        self._topic_subscriptions = []

        for topic, node_id in topics_to_node_ids.items():
            subscription = self.create_subscription(
                String,
                topic,
                lambda msg, topic=topic, node_id=node_id: self.listener_callback(msg, topic, node_id),
                10
            )
            self._topic_subscriptions.append(subscription)
            self.get_logger().info(f"Subscribed to topic: {topic} -> Node ID: {node_id}")

    def listener_callback(self, msg, topic, node_id):
        self.get_logger().info(f"Received on {topic}: '{msg.data}'")
        try:
            self.opcua_client.write_value(node_id, msg.data)
            self.get_logger().info(f"Wrote to OPC UA: {node_id} <- '{msg.data}'")
        except Exception as e:
            self.get_logger().error(f"OPC UA write error: {e}")
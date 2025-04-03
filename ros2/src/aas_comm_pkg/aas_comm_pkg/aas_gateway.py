import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from opcua import Client
import yaml
import xml.etree.ElementTree as ET

class MultiTopicSubscriber(Node):
    """
    ROS 2 Subscriber Node that listens to multiple topics and writes received data to an OPC UA server.
    """
    def __init__(self, topics_to_node_ids: dict):
        super().__init__('multi_topic_subscriber')

        if not topics_to_node_ids:
            raise ValueError("The topics_to_node_ids dictionary cannot be empty.")

        self.topic_subscriptions = []
        
        # Subscribe to each topic dynamically
        for topic, node_id in topics_to_node_ids.items():
            subscription = self.create_subscription(
                String,
                topic,
                lambda msg, topic=topic, node_id=node_id: self.listener_callback(msg, topic, node_id),
                10
            )
            self.topic_subscriptions.append(subscription)

        # Initialize OPC UA client
        self.opcua_client = Client("opc.tcp://127.0.0.1:4840/freeopcua/server/")
        try:
            self.opcua_client.connect()
            self.get_logger().info("Connected to OPC UA server.")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to OPC UA server: {e}")

    def listener_callback(self, msg, topic, node_id):
        """
        Callback function for ROS 2 topic subscribers.
        Writes received message data to the corresponding OPC UA node.
        """
        self.get_logger().info(f'Received message on topic: {topic}, data: "{msg.data}"')
        try:
            node = self.opcua_client.get_node(node_id)
            node.set_value(msg.data)
            self.get_logger().info(f"Data written to OPC UA server. Topic: {topic}, Data: {msg.data}, Node ID: {node_id}")
        except Exception as e:
            self.get_logger().error(f"Failed to write to OPC UA server. Topic: {topic}, Data: {msg.data}, Node ID: {node_id}, Error: {e}")


def define_topics_to_node_ids():
    """
    Parses YAML and XML files to map ROS 2 topics to OPC UA node IDs.
    """
    def load_yaml(file_path):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    def parse_xml(file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        node_id_map = {}
        for obj in root.findall(".//UAObject", namespaces={"": "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"}):
            node_id = obj.get("NodeId")
            browse_name = obj.get("BrowseName")
            if node_id and browse_name:
                simple_name = browse_name.split(":")[-1]
                node_id_map[simple_name] = node_id
        
        return node_id_map

    def map_topics_to_node_ids(yaml_path, xml_path):
        yaml_data = load_yaml(yaml_path)
        node_id_map = parse_xml(xml_path)
        
        topics_to_node_ids = {}
        for key, value in yaml_data.items():
            topic_name = value['topic']
            node_id = node_id_map.get(key)
            if node_id:
                topics_to_node_ids[topic_name] = node_id
        
        return topics_to_node_ids

    return map_topics_to_node_ids("map.yaml", "uav_submodel.xml")


def main(args=None):
    """
    Main entry point for the ROS 2 node.
    Initializes ROS, defines topics, and starts the MultiTopicSubscriber node.
    """
    rclpy.init(args=args)

    # topics_to_node_ids = define_topics_to_node_ids()  # Uncomment to load from YAML/XML
    topics_to_node_ids = {
        'horizontal_speed': "ns=2;i=2",
        'vertical_speed': "ns=2;i=3",
        'battery': "ns=2;i=4",
        'altitude': "ns=2;i=5",
        'temperature': "ns=2;i=6",
        'signal_strength': "ns=2;i=7",
        'pitch': "ns=2;i=8",
        'roll': "ns=2;i=9",
        'imu_temperature': "ns=2;i=10",
        'motor_rpm': "ns=2;i=11"
    }

    multi_topic_subscriber = MultiTopicSubscriber(topics_to_node_ids=topics_to_node_ids)

    try:
        rclpy.spin(multi_topic_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        multi_topic_subscriber.opcua_client.disconnect()
        multi_topic_subscriber.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
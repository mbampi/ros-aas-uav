# Copyright 2024 Matheus Dussin Bampi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from .opcua_client import OPCUAClient
from .topic_mapper import TopicNodeIdMapper

class MultiTopicSubscriber(Node):
    """
    A ROS2 node that subscribes to multiple topics and writes the received
    messages to an OPC UA server.
    """
    def __init__(self):
        """
        Initializes the MultiTopicSubscriber node.
        """
        super().__init__('multi_topic_subscriber')
        self.declare_parameter('mapping_path', 'default.yaml')
        self.declare_parameter('aas_path', 'default.xml')
        self.declare_parameter('opcua_endpoint', 'opc.tcp://127.0.0.1:4840/freeopcua/server/')

        mapping_path = self.get_parameter('mapping_path').get_parameter_value().string_value
        aas_path = self.get_parameter('aas_path').get_parameter_value().string_value
        opcua_endpoint = self.get_parameter('opcua_endpoint').get_parameter_value().string_value

        self.get_logger().info(f"Loading topic-node ID mappings from {mapping_path} and {aas_path}")
        mapper = TopicNodeIdMapper(self.get_logger())
        topics_to_node_ids = mapper.map_topics_to_node_ids(mapping_path, aas_path)

        if not topics_to_node_ids:
            self.get_logger().error("No topics to subscribe to. Exiting.")
            return

        self.opcua_client = OPCUAClient(opcua_endpoint, self.get_logger())
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
        """
        Callback function for the ROS topic subscriptions.

        Args:
            msg: The received message.
            topic (str): The topic the message was received on.
            node_id (str): The OPC UA node ID to write to.
        """
        log_payload = {
            'event': 'message_received',
            'topic': topic,
            'data': msg.data
        }
        self.get_logger().info(json.dumps(log_payload))
        
        log_payload['event'] = 'write_opcua'
        log_payload['node_id'] = node_id
        try:
            self.opcua_client.write_value(node_id, msg.data)
            log_payload['status'] = 'success'
            self.get_logger().info(json.dumps(log_payload))

        except Exception as e:
            log_payload['status'] = 'error'
            log_payload['error'] = str(e)
            self.get_logger().error(json.dumps(log_payload))

    def destroy_node(self):
        """
        Cleans up resources when the node is destroyed.
        """
        self.opcua_client.disconnect()
        super().destroy_node()
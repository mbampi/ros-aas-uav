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

from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from .opcua_client import OPCUAClient
from .topic_mapper import TopicNodeIdMapper
from .message_handler import MessageHandler


class MultiTopicSubscriber(Node):
    """
    ROS2 node that subscribes to multiple topics with different message types
    and writes processed data to an OPC UA server.
    """
    
    def __init__(self):
        """
        Initialize the MultiTopicSubscriber node.
        """
        super().__init__('aas_gateway')
        
        # Declare parameters
        self.declare_parameter('mapping_path', 'map.yaml')
        self.declare_parameter('aas_path', 'uav_submodel.xml')
        self.declare_parameter('opcua_endpoint', 'opc.tcp://127.0.0.1:4840/freeopcua/server/')
        self.declare_parameter('debug_enabled', False)
        self.declare_parameter('log_level', 'INFO')

        # Get parameter values
        mapping_path = self.get_parameter('mapping_path').get_parameter_value().string_value
        aas_path = self.get_parameter('aas_path').get_parameter_value().string_value
        opcua_endpoint = self.get_parameter('opcua_endpoint').get_parameter_value().string_value
        debug_enabled = self.get_parameter('debug_enabled').get_parameter_value().bool_value
        log_level = self.get_parameter('log_level').get_parameter_value().string_value
        
        # Configure logger level
        self._configure_logger_level(log_level)

        self.get_logger().info(f"Initializing AAS Gateway")
        self.get_logger().info(f"Config files: {mapping_path}, {aas_path}")
        self.get_logger().info(f"OPC UA endpoint: {opcua_endpoint}")
        self.get_logger().info(f"Debug mode: {debug_enabled}")
        
        try:
            # Initialize components
            self.get_logger().info("Setting up components...")
            self._setup_components(mapping_path, aas_path, opcua_endpoint)
            
            # Setup subscriptions
            self.get_logger().info("Setting up subscriptions...")
            self._setup_subscriptions(mapping_path, aas_path)
            
            self.get_logger().info("AAS Gateway initialization complete!")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize AAS Gateway: {e}")
            import traceback
            self.get_logger().error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _configure_logger_level(self, log_level: str):
        """
        Configure the logger level based on the parameter.
        
        Args:
            log_level: Log level string (DEBUG, INFO, WARN, ERROR, FATAL)
        """
        import rclpy.logging
        
        level_map = {
            'DEBUG': rclpy.logging.LoggingSeverity.DEBUG,
            'INFO': rclpy.logging.LoggingSeverity.INFO,
            'WARN': rclpy.logging.LoggingSeverity.WARN,
            'ERROR': rclpy.logging.LoggingSeverity.ERROR,
            'FATAL': rclpy.logging.LoggingSeverity.FATAL
        }
        
        severity = level_map.get(log_level.upper(), rclpy.logging.LoggingSeverity.INFO)
        self.get_logger().set_level(severity)
        self.get_logger().info(f"Logger level set to: {log_level.upper()}")

    def _setup_components(self, mapping_path: str, aas_path: str, opcua_endpoint: str):
        """Initialize mapper, message handler, and OPC UA client."""
        # Initialize mapper and validate configuration
        self.mapper = TopicNodeIdMapper(self.get_logger())
        
        if not self.mapper.validate_configuration(mapping_path, aas_path):
            raise RuntimeError("Configuration validation failed")
        
        # Initialize OPC UA client and topic subscriptions list
        self.opcua_client = OPCUAClient(opcua_endpoint, self.get_logger())
        self.topic_subscriptions = []
    
    def _setup_subscriptions(self, mapping_path: str, aas_path: str):
        """Set up topic subscriptions using configuration."""

        self.get_logger().info("Loading mappings and enums...")
        mappings = self.mapper.load_mapping(mapping_path, aas_path)
        enums = self.mapper.get_enums(mapping_path)
        
        self.get_logger().info(f"Found {len(mappings)} mappings and {len(enums)} enum groups")
        
        if not mappings:
            raise RuntimeError("No valid mappings found in configuration")
        
        # Initialize message handler
        self.get_logger().info("Initializing message handler...")
        self.message_handler = MessageHandler(self.get_logger(), enums)
        
        # Create subscriptions for each topic
        self.get_logger().info("Creating topic subscriptions...")
        for i, mapping in enumerate(mappings):
            self.get_logger().info(f"Creating subscription {i+1}/{len(mappings)}: {mapping}")
            self._create_subscription(mapping)
        
        self.get_logger().info(f"Created {len(self.topic_subscriptions)} topic subscriptions")
    
    def _create_subscription(self, mapping: dict):
        """
        Create a single topic subscription from mapping configuration.
        
        Args:
            mapping: Topic mapping configuration dictionary
        """
        topic = mapping['topic']
        message_type_str = mapping['message_type']
        property_name = mapping['property']
        node_id = mapping['node_id']
        field_path = mapping['field_path']
        transform_type = mapping['data_transform']
        
        # Import the message type
        message_class = self.message_handler.import_message_type(message_type_str)
        if message_class is None:
            self.get_logger().error(f"Failed to import {message_type_str} for {topic}")
            return
        
        # Create callback using message handler
        callback = self.message_handler.create_subscription_callback(
            topic, property_name, node_id, field_path, transform_type, self.opcua_client
        )

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            depth=10
        )
        
        # Create the subscription
        try:
            subscription = self.create_subscription(message_class, topic, callback, qos_profile)
            self.topic_subscriptions.append(subscription)
            self.get_logger().info(f"Subscribed: {topic} ({message_type_str}) -> {property_name}")
        except Exception as e:
            self.get_logger().error(f"Failed to subscribe to {topic}: {e}")

    def destroy_node(self):
        """
        Cleans up resources when the node is destroyed.
        """
        # Disconnect OPC UA client
        if hasattr(self, 'opcua_client'):
            self.opcua_client.disconnect()
            
        super().destroy_node()

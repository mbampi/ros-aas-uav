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

import yaml
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

class TopicNodeIdMapper:
    """
    Maps ROS topics to OPC UA node IDs based on YAML and XML configuration files.
    """
    
    def __init__(self, logger):
        """
        Initialize the TopicNodeIdMapper.

        Args:
            logger: ROS2 logger instance
        """
        self.logger = logger

    def load_yaml(self, file_path: str) -> Dict:
        """
        Loads a YAML file.

        Args:
            file_path (str): The path to the YAML file.

        Returns:
            dict: The loaded YAML data.
        """
        self.logger.info(f"Loading YAML file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"YAML file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file: {e}")
            return {}

    def parse_xml(self, file_path: str) -> Dict:
        """
        Parses an XML file to extract OPC UA node IDs.

        Args:
            file_path (str): The path to the XML file.

        Returns:
            dict: A dictionary mapping browse names to node IDs.
        """
        self.logger.info(f"Parsing XML file: {file_path}")
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            ns = {"": "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"}
            node_id_map = {}
            for obj in root.findall(".//UAObject", namespaces=ns):
                node_id = obj.get("NodeId")
                browse_name = obj.get("BrowseName")
                if node_id and browse_name:
                    simple_name = browse_name.split(":")[-1]
                    node_id_map[simple_name] = node_id
            self.logger.info(f"Extracted {len(node_id_map)} node IDs from XML")
            return node_id_map
        except FileNotFoundError:
            self.logger.error(f"XML file not found: {file_path}")
            return {}
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file: {e}")
            return {}

    def load_mapping(self, mapping_path: str, aas_path: str) -> List[Dict]:
        """
        Load topic mapping configuration with message types and field extraction.
        
        Args:
            mapping_path: Path to the YAML configuration file
            aas_path: Path to the XML file with OPC UA node IDs
            
        Returns:
            List of topic configuration dictionaries
        """
        yaml_data = self.load_yaml(mapping_path)
        node_id_map = self.parse_xml(aas_path)
        
        topics_config = yaml_data.get('topics_to_properties', [])
        if not isinstance(topics_config, list):
            self.logger.error(f"Invalid 'topics_to_properties' format in {mapping_path}")
            return []
        
        mappings = []
        
        for item in topics_config:
            mapping = self._process_mapping_item(item, node_id_map)
            if mapping:
                mappings.append(mapping)
        
        return mappings
    
    def _process_mapping_item(self, item: Dict, node_id_map: Dict) -> Optional[Dict]:
        """
        Process a single mapping item from the configuration.
        
        Args:
            item: Single mapping configuration item
            node_id_map: Map of property names to OPC UA node IDs
            
        Returns:
            Processed mapping dictionary or None if invalid
        """
        # Extract required fields
        property_name = item.get('property')
        topic_name = item.get('topic')
        
        if not property_name or not topic_name:
            self.logger.warning(f"Skipping invalid entry: {item}")
            return None
        
        # Get OPC UA node ID
        node_id = node_id_map.get(property_name)
        if not node_id:
            self.logger.warning(f"No node ID found for property '{property_name}'. Skipping.")
            return None
        
        # Extract optional fields with defaults
        message_type = item.get('message_type', 'std_msgs.msg.String')
        field_path = item.get('field_path', 'data')
        transform_type = item.get('data_transform', 'identity')
        
        mapping = {
            'property': property_name,
            'topic': topic_name,
            'message_type': message_type,
            'field_path': field_path,
            'data_transform': transform_type,
            'node_id': node_id
        }
        
        self.logger.info(f"Mapping: {topic_name} ({message_type}) -> {property_name}")
        return mapping
    
    def get_enums(self, mapping_path: str) -> Dict:
        """
        Extract enum mappings from the YAML configuration.
        
        Args:
            mapping_path: Path to the YAML configuration file
            
        Returns:
            Dictionary containing enum mappings
        """
        yaml_data = self.load_yaml(mapping_path)
        enums = yaml_data.get('px4_enums', {})
        
        if enums:
            self.logger.info(f"Loaded enum mappings: {list(enums.keys())}")
        
        return enums
    
    def validate_configuration(self, mapping_path: str, aas_path: str) -> bool:
        """
        Validate the configuration files for completeness and correctness.
        
        Args:
            mapping_path (str): Path to the YAML configuration file
            aas_path (str): Path to the XML file with OPC UA node IDs
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            mappings = self.load_mapping(mapping_path, aas_path)
            
            if not mappings:
                self.logger.error("No valid topic mappings found in configuration")
                return False
            
            # Check for required message type formats
            for mapping in mappings:
                message_type = mapping['message_type']
                if not self._is_valid_message_type_format(message_type):
                    self.logger.error(f"Invalid message type format: {message_type}")
                    return False
            
            self.logger.info(f"Configuration validation passed. Found {len(mappings)} valid mappings.")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def _is_valid_message_type_format(self, message_type: str) -> bool:
        """
        Check if a message type string follows the expected format.
        
        Args:
            message_type (str): Message type string to validate
            
        Returns:
            bool: True if format is valid
        """
        # Expected format: package_name.msg.MessageType
        parts = message_type.split('.')
        return len(parts) >= 3 and parts[-2] == 'msg'

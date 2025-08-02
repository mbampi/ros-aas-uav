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
from typing import Dict

class TopicNodeIdMapper:
    """
    Maps ROS topics to OPC UA node IDs based on YAML and XML configuration files.
    """
    def __init__(self, logger):
        """
        Initializes the TopicNodeIdMapper.

        Args:
            logger: The ROS2 logger instance.
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

    def map_topics_to_node_ids(self, mapping_path: str, aas_path: str) -> Dict:
        """
        Maps ROS topics to OPC UA node IDs using the new list-based YAML format.

        Args:
            mapping_path (str): The path to the YAML file with topic mappings.
            aas_path (str): The path to the XML file with node IDs.

        Returns:
            dict: A dictionary mapping topics to node IDs.
        """
        yaml_data = self.load_yaml(mapping_path)
        node_id_map = self.parse_xml(aas_path)
        mapping = {}

        # Check if the main key exists and is a list
        if 'topics_to_properties' not in yaml_data or not isinstance(yaml_data['topics_to_properties'], list):
            self.logger.error(f"YAML file {mapping_path} is missing 'topics_to_properties' list.")
            return mapping

        # Iterate through the list of mappings
        for item in yaml_data['topics_to_properties']:
            property_name = item.get('property')
            topic_name = item.get('topic')

            if not property_name or not topic_name:
                self.logger.warning(f"Skipping invalid entry in YAML: {item}")
                continue

            node_id = node_id_map.get(property_name)
            if node_id:
                mapping[topic_name] = node_id
                self.logger.info(f"Mapped topic '{topic_name}' to property '{property_name}' (Node ID: '{node_id}')")
            else:
                self.logger.warning(f"No node ID found for property '{property_name}' in XML file.")
        return mapping
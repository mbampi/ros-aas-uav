import yaml
import xml.etree.ElementTree as ET

class TopicNodeIdMapper:
    @staticmethod
    def load_yaml(file_path: str) -> dict:
        print(f"[Mapper] Loading YAML: {file_path}")
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def parse_xml(file_path: str) -> dict:
        print(f"[Mapper] Parsing XML: {file_path}")
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
        print(f"[Mapper] Extracted {len(node_id_map)} IDs")
        return node_id_map

    @staticmethod
    def map_topics_to_node_ids(yaml_path: str, xml_path: str) -> dict:
        yaml_data = TopicNodeIdMapper.load_yaml(yaml_path)
        node_id_map = TopicNodeIdMapper.parse_xml(xml_path)
        mapping = {}
        for key, value in yaml_data.items():
            topic = value['topic']
            node_id = node_id_map.get(key)
            if node_id:
                mapping[topic] = node_id
                print(f"[Mapper] {topic} -> {node_id}")
            else:
                print(f"[Mapper] Warning: No ID for '{key}'")
        return mapping
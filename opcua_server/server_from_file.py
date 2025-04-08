import argparse
import signal
import sys
import time
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime
from opcua import Server, ua
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class ConfigLoader:
    @staticmethod
    def load_yaml(file_path: str) -> Dict:
        """Load a YAML file and return its contents as a dictionary."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def variables_from_yaml(file_path: str) -> List[str]:
        """Extract variable names (keys) from a YAML configuration file."""
        data = ConfigLoader.load_yaml(file_path)
        return list(data.keys())

    @staticmethod
    def parse_xml(file_path: str) -> Dict[str, str]:
        """Parse an XML file and return a mapping from variable names to NodeId strings."""
        ns = {"ua": "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"}
        tree = ET.parse(file_path)
        root = tree.getroot()

        node_id_map = {}
        for tag in ["UAObject", "UAVariable", "UAObjectType"]:
            for node in root.findall(f".//ua:{tag}", ns):
                node_id = node.get("NodeId")
                browse_name = node.get("BrowseName")
                if not (node_id and browse_name):
                    continue
                
                name = browse_name.split(":", 1)[-1]
                node_id_map[name] = node_id

        return node_id_map

    @staticmethod
    def parse_nodeid(nodeid_str: str) -> ua.NodeId:
        """Convert a NodeId string (e.g., 'ns=2;i=1001') to a ua.NodeId object."""
        parts = nodeid_str.split(";")
        ns = int(parts[0].split("=")[-1])
        ident_part = parts[1]
        if ident_part.startswith("i="):
            identifier = int(ident_part.split("=")[-1])
            return ua.NodeId(identifier, ns)
        raise ValueError(f"Unsupported NodeId format: {nodeid_str}")

class VariableChangeHandler:
    def __init__(self, variable_map: Dict[ua.NodeId, str]):
        """Initialize with a mapping from NodeId to variable names."""
        self.variable_map = variable_map

    def datachange_notification(self, node, val, data):
        """Callback triggered when a subscribed variable changes its value."""
        label = self.variable_map.get(node.nodeid, "unknown")
        log.debug(f"Variable '{label}' changed value to: {val}. node: {node.nodeid}")

class OPCUAServer:
    def __init__(self, endpoint: str, namespace_uri: str, xml_path: str, yaml_path: str):
        """Initialize the OPC UA server and configuration parameters."""
        self.server = Server()
        self.server.set_endpoint(endpoint)
        self.namespace_uri = namespace_uri
        self.idx = self.server.register_namespace(namespace_uri)
        self.objects_node = self.server.get_objects_node()
        self.variable_map = {}
        self.xml_path = xml_path
        self.yaml_path = yaml_path
        self._running = False

    def setup_variables(self):
        """Create OPC UA variables using parsed XML and YAML configurations."""
        uav = self.objects_node.add_object(self.idx, "UAV")
        xml_node_map = ConfigLoader.parse_xml(self.xml_path)
        variables = ConfigLoader.variables_from_yaml(self.yaml_path)

        if not variables:
            log.error("No variables found in YAML file.")
            return

        for var in variables:
            nodeid_str = xml_node_map.get(var)
            if not nodeid_str:
                log.warning(f"NodeId for variable '{var}' not found in XML.")
                continue

            nodeid = ConfigLoader.parse_nodeid(nodeid_str)
            opcua_var = uav.add_variable(nodeid, var, 0)
            opcua_var.set_writable()
            self.variable_map[opcua_var.nodeid] = var
            log.debug(f"Created variable '{var}' with NodeId {opcua_var.nodeid}")

    def start(self):
        """Start the OPC UA server and handle variable subscriptions and runtime loop."""
        self.setup_variables()
        self.server.start()
        log.info(f"OPC UA Server running at {self.server.endpoint}")

        handler = VariableChangeHandler(self.variable_map)
        subscription = self.server.create_subscription(5, handler)

        for nodeid in self.variable_map:
            node = self.server.get_node(nodeid)
            subscription.subscribe_data_change(node)

        self._running = True
        while self._running:
            log.debug(f"Server time: {datetime.now()}")
            time.sleep(10)

    def stop(self):
        self._running = False
        self.server.stop()
        log.info("OPC UA Server stopped.")

def main():
    """Entry point to initialize and run the OPC UA server."""
    parser = argparse.ArgumentParser(description="Run OPC UA Server with YAML + XML configuration")
    parser.add_argument("--endpoint", default="opc.tcp://127.0.0.1:4840/freeopcua/server/", help="Server endpoint URL")
    parser.add_argument("--namespace", default="http://aas-example.org", help="Namespace URI")
    parser.add_argument("--xml", default="uav_submodel.xml", help="Path to XML NodeSet file")
    parser.add_argument("--yaml", default="map.yaml", help="Path to YAML variable map file")
    args = parser.parse_args()

    server = OPCUAServer(
        endpoint=args.endpoint,
        namespace_uri=args.namespace,
        xml_path=args.xml,
        yaml_path=args.yaml
    )

    def handle_exit(signum, frame):
        log.info("Interrupt received, stopping server...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        server.start()
    except Exception as e:
        log.error(f"Exception occurred: {e}")
        server.stop()

if __name__ == "__main__":
    main()
import argparse
import json
import signal
import sys
import time
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime
from opcua import Server, ua
from typing import Dict, List
import os
import logging

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# save logs to a file
file_handler = logging.FileHandler('opcua_server.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
log.addHandler(file_handler)


class ConfigLoader:
    @staticmethod
    def load_yaml(file_path: str) -> Dict:
        """Load a YAML file and return its contents as a dictionary."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def variables_from_yaml(file_path: str) -> List[str]:
        """Extract variable names (property names) from a YAML configuration file.
        
        Expects the format with 'topics_to_properties' list containing
        dictionaries with 'property' keys.
        """
        data = ConfigLoader.load_yaml(file_path)
        properties = []
        for item in data['topics_to_properties']:
            if 'property' in item:
                properties.append(item['property'])
        
        return properties

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
    def __init__(self, variable_map: Dict[ua.NodeId, str], latency_log_path: str = "latency.jsonl"):
        """Initialize with a mapping from NodeId to variable names and a path for latency logging.

        The handler writes one JSON object per line to `latency_log_path` so downstream tools
        can easily process latency measurements.
        """
        self.variable_map = variable_map
        self.latency_log_path = latency_log_path
        # Open file in append mode, create directories if needed
        try:
            os.makedirs(os.path.dirname(self.latency_log_path) or '.', exist_ok=True)
        except Exception:
            pass
        self._fp = open(self.latency_log_path, 'a', buffering=1)  # line-buffered

    def _safe_float(self, v):
        try:
            return float(v)
        except Exception:
            return None

    def datachange_notification(self, node, val, data):
        """Callback triggered when a subscribed variable changes its value.

        Expect payloads in the exact JSON format:
            { 'id': <uuid>, 'recv_ts': <float>, 'processed_ts': <float>, 'value': <any> }

        This method only records the server receive timestamp and echoes the
        payload fields into a JSONL file. No further calculations are performed
        here to avoid any impact on performance or alter the raw timestamps.
        """
        server_recv_ts = time.time()
        label = self.variable_map.get(node.nodeid, "unknown")

        parsed = None
        raw_payload = None

        # Normalize incoming value into a string containing JSON when possible
        try:
            # Common cases: bytes or str
            if isinstance(val, bytes):
                raw_payload = val.decode('utf-8', errors='replace')
            elif isinstance(val, str):
                raw_payload = val
            else:
                # Some OPC UA libraries wrap values; try to extract .Value
                if hasattr(val, 'Value'):
                    inner = val.Value
                    if isinstance(inner, bytes):
                        raw_payload = inner.decode('utf-8', errors='replace')
                    elif isinstance(inner, str):
                        raw_payload = inner
                    else:
                        # Best-effort serialization
                        try:
                            raw_payload = json.dumps(inner, default=str)
                        except Exception:
                            raw_payload = str(inner)
                else:
                    # Fallback: try to serialize the value
                    try:
                        raw_payload = json.dumps(val, default=str)
                    except Exception:
                        raw_payload = str(val)

            # First, try to parse the whole payload as JSON
            try:
                parsed = json.loads(raw_payload) if raw_payload is not None else None
            except Exception:
                # If that fails, try to find a JSON object inside the string
                try:
                    import re
                    if raw_payload:
                        m = re.search(r"\{.*\}", raw_payload)
                        if m:
                            parsed = json.loads(m.group(0))
                except Exception:
                    parsed = None

        except Exception:
            parsed = None

        if not isinstance(parsed, dict):
            parsed = {}

        record = {
            'event': 'variable_updated',
            'node_id': str(node.nodeid),
            'variable': label,
            'value': parsed.get('value', None),
            'message_id': parsed.get('id', None),
            'recv_ts': parsed.get('recv_ts', None),
            'processed_ts': parsed.get('processed_ts', None),
            'server_recv_ts': server_recv_ts,
        }

        # Write a single JSON object per line
        try:
            self._fp.write(json.dumps(record, default=str) + '\n')
        except Exception:
            log.exception('Failed to write latency record to file')

        # Keep a debug log copy
        log.debug(json.dumps(record))

    def close(self):
        try:
            if hasattr(self, '_fp') and not self._fp.closed:
                self._fp.flush()
                self._fp.close()
        except Exception:
            pass

class OPCUAServer:
    def __init__(self, endpoint: str, namespace_uri: str, aas_path: str, mapping_path: str):
        """Initialize the OPC UA server and configuration parameters."""
        self.server = Server()
        self.server.set_endpoint(endpoint)
        self.namespace_uri = namespace_uri
        self.idx = self.server.register_namespace(namespace_uri)
        self.objects_node = self.server.get_objects_node()
        self.variable_map = {}
        self.aas_path = aas_path
        self.mapping_path = mapping_path
        self._running = False

    def setup_variables(self):
        """Create OPC UA variables using parsed XML and YAML configurations."""
        uav = self.objects_node.add_object(self.idx, "UAV")
        xml_node_map = ConfigLoader.parse_xml(self.aas_path)
        variables = ConfigLoader.variables_from_yaml(self.mapping_path)

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

        ts = datetime.now().strftime("%m-%dT%H-%M-%S")
        metrics_dir = 'metrics'
        try:
            os.makedirs(metrics_dir, exist_ok=True)
        except Exception:
            pass

        latency_log = os.path.join(metrics_dir, f"events-{ts}.jsonl")
        handler = VariableChangeHandler(self.variable_map, latency_log_path=latency_log)
        
        self._latency_handler = handler # keep reference for closing later
        log.info(f"Writing latency records to {latency_log}")

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
        # Close latency handler file if present
        try:
            if hasattr(self, '_latency_handler'):
                self._latency_handler.close()
        except Exception:
            pass
        self.server.stop()
        log.info("OPC UA Server stopped.")

def main():
    """Entry point to initialize and run the OPC UA server."""
    parser = argparse.ArgumentParser(description="Run OPC UA Server with YAML + XML configuration")
    parser.add_argument("--endpoint", default="opc.tcp://0.0.0.0:4840/freeopcua/server/", help="Server endpoint URL")
    parser.add_argument("--namespace", default="http://aas-example.org", help="Namespace URI")
    parser.add_argument("--xml", default="uav_submodel.xml", help="Path to XML NodeSet file")
    parser.add_argument("--yaml", default="map.yaml", help="Path to YAML variable map file")
    args = parser.parse_args()

    server = OPCUAServer(
        endpoint=args.endpoint,
        namespace_uri=args.namespace,
        aas_path=args.xml,
        mapping_path=args.yaml
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
from opcua import Client

class OPCUAClient:
    def __init__(self, endpoint: str):
        self.client = Client(endpoint)
        try:
            self.client.connect()
            print(f"[OPCUAClient] Connected to OPC UA server at {endpoint}")
        except Exception as e:
            raise ConnectionError(f"[OPCUAClient] Failed to connect: {e}")

    def write_value(self, node_id: str, value: str):
        try:
            node = self.client.get_node(node_id)
            node.set_value(value)
            print(f"[OPCUAClient] Wrote value '{value}' to node {node_id}")
        except Exception as e:
            raise RuntimeError(f"[OPCUAClient] Failed to write: {e}")

    def disconnect(self):
        self.client.disconnect()
        print("[OPCUAClient] Disconnected")
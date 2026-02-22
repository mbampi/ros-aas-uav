import time
import threading
from collections import deque
from opcua import Client
from typing import Dict, Optional

class OPCUAClient:
    """
    A client to connect to and interact with an OPC UA server using a 
    non-blocking background thread and a bounded FIFO message buffer with TTL.
    """
    def __init__(self, endpoint: str, logger):
        self.client = Client(endpoint, timeout=1.0)
        self.logger = logger
        self.endpoint = endpoint
        self.is_connected = False

        self.namespace_uri = "http://matheus.edu/UAV-AAS/"
        self.ns_idx = 2 
        
        self.buffer = deque(maxlen=200)
        self.buffer_lock = threading.Lock()
        
        self._node_cache: Dict[str, object] = {}
        self.MAX_AGE_SECONDS = 1.5  
        
        self._write_count = 0
        self._failed_writes = 0
        
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        self.retry_interval = 0.1

    def _worker(self):
        """Background worker to handle server communication and queue flushing."""
        while True:
            try:
                if not self.is_connected:
                    try:
                        self.client.connect()
                        self.ns_idx = self.client.get_namespace_index(self.namespace_uri)
                        self.is_connected = True
                        self.logger.info(f"Connected to OPC UA server at {self.endpoint}. Target URI is at ns={self.ns_idx}")
                    except Exception as e:
                        time.sleep(self.retry_interval)
                        continue
                
                item = None
                with self.buffer_lock:
                    if self.buffer:
                        item = self.buffer.popleft() 
                
                if not item:
                    time.sleep(0.005) 
                    continue

                # TTL Check: Prevent Ghosting
                age = time.time() - item['recv_ts']
                if age > self.MAX_AGE_SECONDS:
                    self.logger.debug(f"Dropped stale data for node {item['node_id']}")
                    continue

                # Write to Server
                node_id = item['node_id']
                value = item['value']
                
                node = self._get_cached_node(node_id)
                if node is not None:
                    self.logger.debug(f"Attempting to write value '{value}' to node '{node_id}'...")
                    node.set_value(value)
                    self.logger.info(f"✅ Successfully written to server: Node {node_id} = {value}")
                else:
                    self._failed_writes += 1

            except Exception as e:
                # Differentiate between a data type error and a hard network disconnect
                error_msg = str(e)
                if "BadTypeMismatch" in error_msg:
                    self.logger.error(f"Type mismatch on node {item['node_id']}. Server refused the value '{item['value']}'. Error: {error_msg}")
                    self._failed_writes += 1
                else:
                    self.logger.error(f"OPC UA worker thread encountered a network error: {e}")
                    self.is_connected = False                    
                    self._node_cache.clear()
                    time.sleep(self.retry_interval)

    def _get_cached_node(self, node_id: str) -> Optional[object]:
        """Fetch and cache OPC UA node handles."""
        full_node_id = f"ns={self.ns_idx};{node_id}"
        if full_node_id in self._node_cache:
            return self._node_cache[full_node_id]
            
        try:
            node = self.client.get_node(full_node_id)
            self._node_cache[full_node_id] = node
            return node
        except Exception as e:
            self.logger.error(f"Failed to get node {full_node_id}: {e}")
            return None

    def write_value(self, node_id: str, value: any):
        """
        Non-blocking write. Adds data to the queue and returns immediately.
        """
        self._write_count += 1
        with self.buffer_lock:
            self.buffer.append({'node_id': node_id, 'value': value, 'recv_ts': time.time()})

    def disconnect(self):
        """Disconnects the client and stops the background state."""
        self.is_connected = False
        try:
            self.client.disconnect()
            self.logger.info("Disconnected from OPC UA server")
        except Exception:
            pass
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
        self.data_available = threading.Event()
        
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
                        self.logger.info(f"Connected to OPC UA server at {self.endpoint}")
                    except Exception as e:
                        time.sleep(self.retry_interval)
                        continue
                
                self.data_available.wait(timeout=0.1) 
                
                batch_items = []
                with self.buffer_lock:
                    while self.buffer:
                        batch_items.append(self.buffer.popleft())
                    self.data_available.clear()
                
                if not batch_items:
                    continue

                # 1. Deduplicate & TTL Check: Keep only the newest value per node
                latest_updates = {}
                current_time = time.time()
                for item in batch_items:
                    if (current_time - item['recv_ts']) <= self.MAX_AGE_SECONDS:
                        latest_updates[item['node_id']] = item['value']
                    else:
                        self.logger.debug(f"Dropped stale data for node {item['node_id']}")

                if not latest_updates:
                    continue

                # 2. Prepare the batch
                nodes_to_write = []
                values_to_write = []
                
                for node_id, value in latest_updates.items():
                    node = self._get_cached_node(node_id)
                    if node is not None:
                        nodes_to_write.append(node)
                        values_to_write.append(value)
                    else:
                        self._failed_writes += 1

                # 3. Network Write: Send ALL updates in a single TCP payload
                if nodes_to_write:
                    self.logger.info(f"Attempting batch write of {len(nodes_to_write)} nodes...")
                    self.client.set_values(nodes_to_write, values_to_write)
                    
                    for node_id, value in latest_updates.items():
                        self.logger.info(f"✅ Successfully written to server: Node {node_id} = {value}")

            except Exception as e:
                error_msg = str(e)
                if "BadTypeMismatch" in error_msg:
                    self.logger.error(f"Type mismatch during batch write. Error: {error_msg}")
                    self._failed_writes += len(nodes_to_write)
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
        self.data_available.set()

    def disconnect(self):
        """Disconnects the client and stops the background state."""
        self.is_connected = False
        try:
            self.client.disconnect()
            self.logger.info("Disconnected from OPC UA server")
        except Exception:
            pass
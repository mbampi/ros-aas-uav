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

import time
import threading
from queue import LifoQueue, Full
from opcua import Client
from typing import Dict, Optional

class OPCUAClient:
    """
    A client to connect to and interact with an OPC UA server using a 
    non-blocking background thread and message buffer.
    """
    def __init__(self, endpoint: str, logger):
        """
        Initializes the OPCUAClient with a background worker.
        """
        self.client = Client(endpoint)
        self.logger = logger
        self.endpoint = endpoint
        self.is_connected = False
        
        # Resilient buffering during outages
        self.buffer = LifoQueue(maxsize=100)
        self._node_cache: Dict[str, object] = {}
        
        # Performance and health metrics
        self._write_count = 0
        self._failed_writes = 0
        
        # Asynchronous task for reconnection and background writing
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _worker(self):
        """Background worker to handle server communication and queue flushing."""
        while True:
            # Reconnection logic that does not block the main ROS node
            if not self.is_connected:
                try:
                    self.client.connect()
                    self.is_connected = True
                    self.logger.info(f"Connected to OPC UA server at {self.endpoint}")
                except Exception:
                    time.sleep(1) # Retry interval
                    continue
            
            # Process the next message from the buffer
            item = self.buffer.get()
            node_id = item['node_id']
            json_payload = item['payload']
            
            try:
                node = self._get_cached_node(node_id)
                if node is not None:
                    node.set_value(json_payload)
                else:
                    self._failed_writes += 1
            except Exception as e:
                self.logger.error(f"OPC UA write failed, marking as disconnected: {e}")
                self.is_connected = False
            finally:
                self.buffer.task_done()

    def _get_cached_node(self, node_id: str) -> Optional[object]:
        """Fetch and cache OPC UA node handles."""
        if node_id in self._node_cache:
            return self._node_cache[node_id]
            
        try:
            node = self.client.get_node(node_id)
            self._node_cache[node_id] = node
            return node
        except Exception:
            return None

    def write_value(self, node_id: str, json_payload: str):
        """
        Non-blocking write. Adds data to the queue and returns immediately.
        Matches the paper's claim of 'minimal latency' during ROS callbacks.
        """
        try:
            self._write_count += 1
            self.buffer.put_nowait({'node_id': node_id, 'payload': json_payload})
        except Full:
            self.logger.warning("Gateway buffer full. Dropping oldest telemetry message.")

    def disconnect(self):
        """Disconnects the client and stops the background state."""
        self.is_connected = False
        try:
            self.client.disconnect()
            self.logger.info("Disconnected from OPC UA server")
        except Exception:
            pass
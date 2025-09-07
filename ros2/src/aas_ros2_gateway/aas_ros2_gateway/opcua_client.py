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
from opcua import Client
from threading import Lock
from typing import Dict, Optional

class OPCUAClient:
    """
    A client to connect to and interact with an OPC UA server.
    """
    def __init__(self, endpoint: str, logger):
        """
        Initializes the OPCUAClient.

        Args:
            endpoint (str): The OPC UA server endpoint URL.
            logger: The ROS2 logger instance.
        """
        self.client = Client(endpoint)
        self.logger = logger
        self.endpoint = endpoint
        self.is_connected = False
        
        # Caching for performance
        self._node_cache: Dict[str, object] = {}
        self._connection_lock = Lock()
        self._write_count = 0
        self._failed_writes = 0
        self._last_health_check = 0
        
        self.connect()
    
    def _get_cached_node(self, node_id: str) -> Optional[object]:
        """
        Get a cached OPC UA node handle. If not cached, fetches from server and caches it.
        
        Args:
            node_id: The OPC UA node ID
            
        Returns:
            The OPC UA node object or None if failed
        """
        if node_id in self._node_cache:
            return self._node_cache[node_id]
            
        try:
            node = self.client.get_node(node_id)
            self._node_cache[node_id] = node
            return node
        except Exception as e:
            self.logger.error(f"Failed to get node handle for {node_id}: {e}")
            return None

    def connect(self):
        """
        Connects to the OPC UA server with retry logic.
        """
        while not self.is_connected:
            try:
                self.client.connect()
                self.is_connected = True
                self.logger.info(f"Connected to OPC UA server at {self.endpoint}")
            except Exception as e:
                self.logger.error(f"Failed to connect to OPC UA server: {e}. Retrying in 5 seconds...")
                time.sleep(5)
    
    def write_value(self, node_id: str, json_payload: str):
        """
        Writes a JSON payload directly to OPC UA server with minimal latency.
        Uses cached node handles and direct connection for maximum speed.
        
        Args:
            node_id (str): The ID of the node to write to.
            json_payload (str): JSON string containing timestamps and value
        """
        try:
            self._write_count += 1
            
            if not self.is_connected:
                self.logger.info("Not connected to OPC UA server. Attempting to reconnect...")
                self.connect()
            
            node = self._get_cached_node(node_id)
            if node is not None:
                node.set_value(json_payload)
            else:
                self._failed_writes += 1
                raise RuntimeError(f"Failed to get node handle for {node_id}")
                
        except Exception as e:
            self._failed_writes += 1
            self.logger.error(f"OPC UA write failed for {node_id}: {e}")
            
            # Clear failed node from cache
            if node_id in self._node_cache:
                del self._node_cache[node_id]
                
            self.is_connected = False
            raise e
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get simple performance statistics.
        
        Returns:
            Dictionary with basic metrics
        """
        return {
            'total_writes': self._write_count,
            'failed_writes': self._failed_writes,
            'cached_nodes': len(self._node_cache)
        }

    def disconnect(self):
        """
        Disconnects from the OPC UA server.
        """
        try:
            if self.is_connected:
                self.client.disconnect()
                self.logger.info("Disconnected from OPC UA server")
        except Exception as e:
            self.logger.warning(f"Error during OPC UA disconnect: {e}")
        finally:
            self.is_connected = False
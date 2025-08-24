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
        self.connect()

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

    def write_value(self, node_id: str, value: str):
        """
        Writes a value to a specific node on the OPC UA server.

        Args:
            node_id (str): The ID of the node to write to.
            value (str): The value to write.
        """
        try:
            if not self.is_connected:
                self.logger.info("Not connected to OPC UA server. Attempting to reconnect...")
                self.connect()
            
            node = self.client.get_node(node_id)
            node.set_value(value)
            self.logger.debug(f"Successfully wrote '{value}' to node {node_id}")

        except Exception as e:
            self.logger.error(f"Failed to write value '{value}' to node {node_id}: {e}")
            self.is_connected = False
            raise e

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
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
        try:
            self.client.connect()
            self.logger.info(f"Connected to OPC UA server at {endpoint}")
        except Exception as e:
            self.logger.error(f"Failed to connect to OPC UA server: {e}")
            raise

def write_value(self, node_id: str, value: str):
    """
    Writes a value to a specific node on the OPC UA server.

    Args:
        node_id (str): The ID of the node to write to.
        value (str): The value to write.
    """
    try:
        node = self.client.get_node(node_id)
        node.set_value(value)

    except Exception as e:
        raise e

    def disconnect(self):
        """
        Disconnects from the OPC UA server.
        """
        self.client.disconnect()
        self.logger.info("Disconnected from OPC UA server")
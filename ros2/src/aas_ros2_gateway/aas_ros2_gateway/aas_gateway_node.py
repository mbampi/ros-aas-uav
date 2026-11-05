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

import rclpy
from .subscriber_node import MultiTopicSubscriber

def main(args=None):
    """
    Main function to initialize and run the aas_gateway node.
    """
    rclpy.init(args=args)
    node = None
    try:
        node = MultiTopicSubscriber()
        node.get_logger().info("aas_gateway node has been started.")
        rclpy.spin(node)
    except Exception as e:
        if node:
            node.get_logger().error(f"An error occurred: {e}")
    finally:
        if node:
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
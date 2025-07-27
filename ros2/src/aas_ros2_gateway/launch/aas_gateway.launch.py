from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    """
    Generates the launch description for the aas_gateway node.
    """
    config = os.path.join(
        get_package_share_directory('aas_ros2_gateway'),
        'config',
        'params.yaml'
        )

    return LaunchDescription([
        Node(
            package='aas_ros2_gateway',
            executable='aas_gateway',
            name='aas_gateway',
            parameters=[config]
        )
    ])
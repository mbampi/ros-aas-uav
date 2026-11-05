#!/usr/bin/env python3
"""
Launch file for MAVROS Mock Publisher

This simulates MAVROS topics without requiring actual hardware or simulation.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    """Generate launch description for MAVROS mock publisher."""
    
    pkg_share = get_package_share_directory('aas_ros2_gateway')
    
    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=os.path.join(pkg_share, 'config', 'mavlink_mock_config.yaml'),
        description='Path to the MAVROS mock configuration file'
    )
    
    mavlink_mock_node = Node(
        package='aas_ros2_gateway',
        executable='mavlink_mock_publisher',
        name='mavlink_mock_publisher',
        output='screen',
        parameters=[LaunchConfiguration('config_file')],
        emulate_tty=True
    )
    
    return LaunchDescription([
        config_file_arg,
        mavlink_mock_node
    ])

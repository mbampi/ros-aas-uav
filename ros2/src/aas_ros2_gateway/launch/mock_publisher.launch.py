#!/usr/bin/env python3
"""
Mock Publisher Launch File

Launches the PX4 mock publisher for academic experiments.
Configuration is read from config/mock_config.yaml

Usage:
    ros2 launch aas_ros2_gateway mock_publisher.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Generate launch description for mock publisher."""
    
    return LaunchDescription([
        Node(
            package='aas_ros2_gateway',
            executable='mock_publisher.py',
            name='px4_mock_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': False,
            }]
        )
    ])

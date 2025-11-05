import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'aas_ros2_gateway'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include all launch files
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
        # Include all config files
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*'))),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='Matheus D Bampi',
    maintainer_email='matheusbampi@gmail.com',
    description='A ROS2 package to facilitate communication between ROS and AAS OPC UA.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'aas_gateway = aas_ros2_gateway.aas_gateway_node:main',
            'mock_publisher = scripts.mock_publisher:main',
            'mavlink_mock_publisher = scripts.mavlink_mock_publisher:main',
        ],
    },
)

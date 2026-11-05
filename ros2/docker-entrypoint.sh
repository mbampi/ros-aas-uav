#!/bin/bash
set -e

# Source the base ROS 2
source /opt/ros/humble/setup.bash

# Then source the workspace
source /ros2_ws/install/setup.bash

# Execute the command passed to the docker run/command
exec "$@"

#!/bin/bash
set -e

# Source the ROS 2 workspace
source /ros2_ws/install/setup.bash

# Execute the command passed to the docker run/command
exec "$@"
# =====================================================================
# Stage 1: "builder" - Compiles the ROS2 workspace
# =====================================================================
FROM ros:humble-ros-base-jammy as builder

# Set shell to bash for all RUN commands
SHELL ["/bin/bash", "-c"]

# Install build tools and python dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    python3-rosdep \
    python3-colcon-common-extensions \
    git \
    python3-pip \
    libcurl4-openssl-dev \
    wget && \
    wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/llvm.gpg > /dev/null && \
    echo "deb http://apt.llvm.org/jammy/ llvm-toolchain-jammy main" | tee /etc/apt/sources.list.d/llvm.list > /dev/null && \
    apt-get update && \
    add-apt-repository universe -y && \
    apt-get update \
    && pip install opcua \
    && rosdep update \
    && rm -rf /var/lib/apt/lists/*

# Install micro-ROS agent
RUN mkdir -p /micro_ros_ws/src && \
    cd /micro_ros_ws/src && \
    git clone -b humble https://github.com/micro-ROS/micro_ros_setup.git && \
    cd /micro_ros_ws && \
    rosdep update && \
    apt-get update && \
    rosdep install --from-paths src --ignore-src -y && \
    source /opt/ros/humble/setup.bash && \
    colcon build && \
    source install/local_setup.bash && \
    ros2 run micro_ros_setup create_agent_ws.sh && \
    ros2 run micro_ros_setup build_agent.sh

# Create the workspace directory
WORKDIR /ros2_ws

# =====================================================================
# px4_msgs layer - This will be cached and only rebuilt when px4_msgs changes
# =====================================================================
# Clone and build px4_msgs first as a separate layer for better caching
RUN git clone --branch main https://github.com/PX4/px4_msgs.git src/px4_msgs && \
    source /opt/ros/humble/setup.bash && \
    rosdep install --from-paths src/px4_msgs --ignore-src -y --rosdistro humble && \
    colcon build --packages-select px4_msgs && \
    echo "px4_msgs build completed and cached"

# =====================================================================
# Application layer - This will rebuild when your code changes
# =====================================================================
# Copy package definition files first for dependency resolution
COPY src/aas_ros2_gateway/package.xml ./src/aas_ros2_gateway/

# Install dependencies for our package (excluding px4_msgs which is already built)
RUN source /opt/ros/humble/setup.bash && \
    rosdep install --from-paths src/aas_ros2_gateway --ignore-src -y --rosdistro humble --skip-keys "python3-opcua px4_msgs"

# Now copy the rest of the source code
COPY src/aas_ros2_gateway ./src/aas_ros2_gateway

# Build only our package (px4_msgs is already built)
RUN source /opt/ros/humble/setup.bash && \
    source install/setup.bash && \
    colcon build --packages-select aas_ros2_gateway

# =====================================================================
# Stage 2: "final" - The lean runtime image
# =====================================================================
FROM ros:humble-ros-base-jammy

# Copy compiled workspace from the builder stage
COPY --from=builder /ros2_ws/install /ros2_ws/install
COPY --from=builder /micro_ros_ws/install /micro_ros_ws/install

# Copy the pip-installed dependency from the builder stage
COPY --from=builder /usr/local/lib/python3.10/dist-packages/ /usr/local/lib/python3.10/dist-packages/

# Create and set up the entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# The default command to run when the container starts
CMD ["ros2", "run", "aas_ros2_gateway", "aas_gateway"]
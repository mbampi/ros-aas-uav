# =====================================================================
# Stage 1: "builder" - Compiles the ROS2 workspace
# =====================================================================
FROM ros:humble-ros-base-jammy as builder

# Set shell to bash for all RUN commands
SHELL ["/bin/bash", "-c"]

# Make the build-time architecture available as a variable
ARG TARGETARCH

# Install build tools and python dependencies
RUN apt-get update && apt-get install -y \
    python3-rosdep \
    python3-colcon-common-extensions \
    git \
    python3-pip \
    && pip install opcua \
    && rosdep update \
    && rm -rf /var/lib/apt/lists/*

# Create the workspace directory
WORKDIR /ros2_ws

# Check the TARGETARCH variable to decide how to get px4_msgs
RUN if [ "$TARGETARCH" = "amd64" ]; then \
    echo "AMD64 detected. Installing px4_msgs from apt." && \
    apt-get update && apt-get install -y ros-humble-px4-msgs && rm -rf /var/lib/apt/lists/*; \
    else \
    echo "Non-AMD64 architecture ($TARGETARCH) detected. Cloning px4_msgs from source." && \
    git clone --branch main https://github.com/PX4/px4_msgs.git src/px4_msgs; \
    fi

# Copy package definition files first
COPY src/aas_ros2_gateway/package.xml ./src/aas_ros2_gateway/

# Install all dependencies from source folders
RUN source /opt/ros/humble/setup.bash && \
    rosdep install --from-paths src --ignore-src -y --rosdistro humble --skip-keys "python3-opcua"

# Now copy the rest of the source code
COPY src/aas_ros2_gateway ./src/aas_ros2_gateway

# Build the entire workspace
RUN source /opt/ros/humble/setup.bash && \
    colcon build

# =====================================================================
# Stage 2: "final" - The lean runtime image
# =====================================================================
FROM ros:humble-ros-base-jammy

ARG TARGETARCH

# For amd64, we need the pre-compiled package for runtime dependencies.
# For arm64, this is not needed as the compiled files are in the copied install/ directory.
RUN if [ "$TARGETARCH" = "amd64" ]; then \
    echo "AMD64 detected. Installing runtime px4_msgs from apt." && \
    apt-get update && apt-get install -y ros-humble-px4-msgs && rm -rf /var/lib/apt/lists/*; \
    fi

# Copy compiled workspace from the builder stage
COPY --from=builder /ros2_ws/install /ros2_ws/install

# Copy the pip-installed dependency from the builder stage
COPY --from=builder /usr/local/lib/python3.10/dist-packages/ /usr/local/lib/python3.10/dist-packages/

# Create and set up the entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# The default command to run when the container starts
CMD ["ros2", "run", "aas_ros2_gateway", "aas_gateway"]
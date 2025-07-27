# =====================================================================
# Stage 1: "builder" - Compiles the ROS2 workspace
# =====================================================================
FROM ros:humble-ros-base-jammy as builder

# Set shell to bash for all RUN commands
SHELL ["/bin/bash", "-c"]

# Install build tools, python dependencies via pip, and update rosdep
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

# Copy your package source code
COPY src/aas_ros2_gateway ./src/aas_ros2_gateway

# Install dependencies, skipping the one we installed with pip
RUN source /opt/ros/humble/setup.bash && \
    rosdep install --from-paths src --ignore-src -y --rosdistro humble --skip-keys "python3-opcua"

# Build the workspace WITHOUT --symlink-install
RUN source /opt/ros/humble/setup.bash && \
    colcon build

# =====================================================================
# Stage 2: "final" - The lean runtime image
# =====================================================================
FROM ros:humble-ros-base-jammy

# Copy the compiled workspace from the builder stage
COPY --from=builder /ros2_ws/install /ros2_ws/install

# Copy the pip-installed dependency from the builder stage
COPY --from=builder /usr/local/lib/python3.10/dist-packages/ /usr/local/lib/python3.10/dist-packages/

# Create and set up the entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# The default command to run when the container starts
CMD ["ros2", "run", "aas_ros2_gateway", "aas_gateway"]
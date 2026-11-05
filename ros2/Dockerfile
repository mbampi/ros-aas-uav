FROM ros:humble-ros-base-jammy as builder

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    python3-rosdep \
    python3-colcon-common-extensions \
    git \
    python3-pip \
    ros-humble-mavros-msgs \
    && pip install asyncua \
    && rosdep update \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

# px4_msgs is slow to build, so it gets its own layer
RUN git clone --branch main https://github.com/PX4/px4_msgs.git src/px4_msgs && \
    source /opt/ros/humble/setup.bash && \
    rosdep install --from-paths src/px4_msgs --ignore-src -y --rosdistro humble && \
    colcon build --packages-select px4_msgs

COPY src/aas_ros2_gateway/package.xml ./src/aas_ros2_gateway/

RUN source /opt/ros/humble/setup.bash && \
    rosdep install --from-paths src/aas_ros2_gateway --ignore-src -y --rosdistro humble --skip-keys "python3-opcua px4_msgs"

COPY src/aas_ros2_gateway ./src/aas_ros2_gateway

RUN source /opt/ros/humble/setup.bash && \
    source install/setup.bash && \
    colcon build --packages-select aas_ros2_gateway

FROM ros:humble-ros-base-jammy

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ros-humble-mavros-msgs \
    ros-humble-sensor-msgs \
    ros-humble-geometry-msgs \
    ros-humble-std-msgs \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /ros2_ws/install /ros2_ws/install

# asyncua is installed with pip, so it isn't part of the workspace
COPY --from=builder /usr/local/lib/python3.10/dist-packages/ /usr/local/lib/python3.10/dist-packages/

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["ros2", "run", "aas_ros2_gateway", "aas_gateway"]

# AAS ROS2 Gateway

Documentation for the ROS2 AAS Gateway package. This package bridges ROS2 topics into an OPC UA Asset Administration Shell (AAS) model via a configurable mapping.

- Map ROS2 topics to AAS properties using YAML (`map.yaml`)
- Optionally support richer message types and transformations (PX4-friendly)
- Run inside ROS2 workspace or using Docker Compose

PX4 and message mappings:
- Use `message_type` to import ROS2 message classes (e.g. `sensor_msgs.msg.BatteryState` or `px4_msgs.msg.BatteryStatus`).
- Use `field_path` (e.g. `percentage` or `pose.position.x`) to extract nested fields.
- Apply `data_transform` to convert units or enums (percentage, quaternion_to_pitch, mm_to_m, px4_nav_state_to_string).

Mock publisher (PX4-like)
- A PX4-focused mock publisher is available at `scripts/mock_publisher.py`. It can publish typical PX4/MAVROS topics (battery, attitude, gps, odometry) for testing the gateway.

Troubleshooting & tips
- Use `ros2 topic list` and `ros2 topic info <topic>` to discover available topics and types.
- Use `ros2 interface show <msg>` to inspect message fields.
- Start with one mapping entry and verify before adding many.


## Quick start
1. Source your ROS2 workspace and build this package (colcon):

```bash
source ~/ros2_ws/install/setup.bash
colcon build --packages-select aas_ros2_gateway
```

1. Edit the mapping file (`config/map.yaml`) to match your AAS XML model (`config/uav_submodel.xml`).

2. Run the gateway with mapping (supports message types, field paths, transforms):

```bash
ros2 run aas_ros2_gateway aas_gateway_node --ros-args -p mapping_path:=config/map.yaml -p aas_path:=config/uav_submodel.xml
```

### Running with Docker Compose

You can also run the gateway using Docker Compose.

1.  **Build and run the container**:
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker image based on the `Dockerfile` and start the `aas_ros2_gateway` service defined in the `docker-compose.yml` file. The node will start automatically.

2.  **Stopping the container**:
    Press `Ctrl+C` in the terminal where `docker-compose` is running, and then run:
    ```bash
    docker-compose down
    ```

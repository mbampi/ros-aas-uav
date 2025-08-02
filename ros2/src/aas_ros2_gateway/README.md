# AAS ROS2 Gateway

A ROS2 package that acts as a gateway between ROS2 topics and an OPC UA server, using an Asset Administration Shell (AAS) submodel for mapping.

---

## Overview

This package provides a flexible way to bridge data from a ROS2 environment to an industrial control system that uses OPC UA. The mapping between ROS2 topics and OPC UA nodes is defined in a YAML file, making it easy to configure for different applications.

This node is implemented as a standard ROS 2 node for simplicity and ease of use.

---

## Features

* **Dynamic Topic Subscriptions:** Subscribes to a list of ROS2 topics defined in a configuration file.
* **OPC UA Integration:** Writes received ROS2 messages to corresponding nodes in an OPC UA server.
* **Configurable:** Easy to configure through a YAML file and ROS2 parameters.
* **Robust:** Includes error handling and logging.
* **Extensible:** The code is modular and easy to extend with new features.

---

## Getting Started

### Installation

Clone the repository into your ROS2 workspace:

```bash
cd ~/ros2_ws/src
git clone [https://github.com/mbampi/aas_ros2_gateway.git](https://github.com/mbampi/aas_ros2_gateway.git)
```

Install dependencies:

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

Build the package:

```bash
cd ~/ros2_ws
colcon build --packages-select aas_ros2_gateway
```

### Usage

1.  **Source your workspace**:
    ```bash
    source ~/ros2_ws/install/setup.bash
    ```

2.  **Configure your mappings** in `src/aas_ros2_gateway/config/map.yaml`:
    ```yaml
    topics_to_properties:
      - property: "HorizontalSpeed"
        topic: "horizontal_speed"
      - property: "VerticalSpeed"
        topic: "vertical_speed"
    ```

3.  **Launch the gateway**:
    ```bash
    ros2 launch aas_ros2_gateway aas_gateway.launch.py
    ```

You can also override the default parameters from the command line:

```bash
ros2 launch aas_ros2_gateway aas_gateway.launch.py opcua_server_url:='opc.tcp://your-server:4840'
```

---

## 🐳 Running with Docker Compose

You can also run the gateway using Docker Compose for a more isolated and reproducible environment.

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

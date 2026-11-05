# ROS2 AAS Gateway

A ROS2 node that listens, processes and maps the UAV telemetry data to Asset Administration Shell (AAS) via OPC UA.

## Quick Start

### Run with Real UAV Data
```bash
docker compose up
```

This starts the AAS Gateway that connects to a real UAV system running PX4 with ROS2.

### Run with Mock Data (for testing)
```bash
docker compose --profile mock up
```

This starts both the AAS Gateway and a mock publisher that generates synthetic UAV data for testing purposes.

## Services

- **aas_gateway**: The main ROS2 node that subscribes to UAV topics and forwards data to OPC UA server
- **mock_publisher**: (Optional) Generates fake UAV telemetry data for testing

## Configuration

- **Config files**: Located in `src/aas_ros2_gateway/config/`
- **Logs**: Output to `logs/aas_gateway/` directory
- **OPC UA endpoint**: Connect your OPC UA server to `opc.tcp://host.docker.internal:4840`

## Development

### Rebuild after code changes
```bash
docker compose up --build
```

### View logs
```bash
docker compose logs -f aas_gateway
```

### Stop services
```bash
docker compose down
```

## Requirements

- Docker and Docker Compose
- OPC UA server running (see `../opcua_server/` directory)

For more details, see the main project README.


## Build on MacOS &* Run on RaspberryPi

Build the Docker images for ARM64 architecture
```sh
docker buildx build --platform linux/arm64 -t aas-gateway-app:latest --load -f Dockerfile .
docker buildx build --platform linux/arm64 -t mavros-app:latest --load -f Dockerfile.mavros .
```

Save the images to tar files
```sh
docker save aas-gateway-app:latest -o aas-gateway-app.tar
docker save mavros-app:latest -o mavros-app.tar
```

Transfer the tar files to the Raspberry Pi using scp or another method
```sh
scp aas-gateway-app.tar pi@raspberrypi.local:/home/pi/ros-aas-uav/
scp mavros-app.tar pi@raspberrypi.local:/home/pi/ros-aas-uav/
```

ssh into the Raspberry Pi
```sh
ssh pi@raspberrypi.local
```

Load the images on the Raspberry Pi
```sh
docker load -i aas-gateway-app.tar
docker load -i mavros-app.tar
```

Run the Docker Compose setup on the Raspberry Pi
```sh
docker compose up --no-build
```

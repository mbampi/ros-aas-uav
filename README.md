# UAV AAS Middleware for ROS 2

> Enhancing UAV Interoperability with an Asset Administration Shell (AAS) Based Middleware for ROS 2

This repository implements a middleware solution that bridges UAV telemetry data from ROS 2 to Asset Administration Shell (AAS) via OPC UA, for integrating UAVs into Industry 4.0 systems.

## Quick Start

1. **Start the OPC UA Server:**
   ```bash
   cd opcua_server
   python opcua_server.py --ui  # With web dashboard
   ```

2. **Start the ROS2 Gateway:**
   ```bash
   cd ros2
   docker compose --profile mock up  # With mock data for testing
   ```

3. **View the Dashboard:** Open http://127.0.0.1:5000 to see real-time UAV data

## Project Structure

- **[`ros2/`](ros2/README.md)** - ROS2 AAS Gateway implementation with Docker support
- **[`opcua_server/`](opcua_server/README.md)** - OPC UA server with web dashboard for UAV AAS

## Key Features

### ROS2 AAS Gateway
- Bridges UAV telemetry from PX4/ROS2 to AAS via OPC UA
- Configuration-driven mapping (YAML)
- Runs in Docker
- Support for real UAV data and mock testing

### OPC UA Server
- Standards-compliant AAS implementation
- Optional web dashboard with real-time visualization
- Interactive charts for UAV metrics (battery, altitude, speed, attitude)
- Event logging and performance monitoring

### Academic Research
- Performance benchmarking and latency analysis
- Resource utilization studies for embedded deployment

## Technology Stack

- **UAV**: PX4 Autopilot
- **Middleware**: ROS 2 Humble + Python
- **Communication**: OPC UA + Asset Administration Shell
- **Deployment**: Docker + Docker Compose
- **Monitoring**: Web Dashboard with real-time charts

## Documentation

| Component     | Documentation                                    |
| ------------- | ------------------------------------------------ |
| ROS2 Gateway  | [ros2/README.md](ros2/README.md)                 |
| OPC UA Server | [opcua_server/README.md](opcua_server/README.md) |

## Development

### System Requirements
- Docker and Docker Compose
- Python 3.8+ (for OPC UA server)
- ROS 2 Humble (if running outside Docker)

### Configuration
- **YAML Mapping**: Maps ROS topics to AAS properties
- **XML NodeSet**: Defines AAS structure and OPC UA nodes
- **Docker Compose**: Profiles for real UAV data vs mock testing

## Testing

**With Mock Data (recommended for testing):**
```bash
cd ros2
docker compose --profile mock up
```

**With Real UAV (requires PX4 + ROS2 setup):**
```bash
cd ros2
docker compose up
```

## Performance

Benchmarked performance metrics:
- **Latency**: 12.17ms average end-to-end (120Hz)
- **Throughput**: 300Hz sustained with 100% delivery rate
- **Resources**: 27% CPU, 85MB memory (single core)
- **Reliability**: Zero data loss under stress testing

## Contributing

This project is part of ongoing research at Federal University of Rio Grande do Sul (UFRGS). Contributions, issues, and feature requests are welcome.

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE). Please cite appropriately if used in academic work.

---
 
**Contact**: matheus.bampi@inf.ufrgs.br

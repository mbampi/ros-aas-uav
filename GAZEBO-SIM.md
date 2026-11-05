# Gazebo Simulation

This section provides instructions on setting up and running the Gazebo simulation environment integrated with PX4 for UAV testing.

### Windows
```bash
cd UAV-Collision-Avoidance
source ./macros.bash
setros && buildall && remodel && loadmission && sim
```

### Checking ROS2 Topics
To verify that the ROS2 topics are being published correctly from the Gazebo simulation, you can use the following command:

`ros2 topic list`

It will show a list of active topics starting with `px4_1/` if everything is set up correctly.

### Checking Mavlink 

To check if Mavlink messages are being sent correctly, you can use the following command:

```bash
mavproxy.py --master=udpin:127.0.0.1:14550
```

### Routing MavLink to Other Computer

Run the following command, replacing `<TARGET_IP>` with the IP address of the target computer:

```bash
mavproxy.py --master=udpin:127.0.0.1:14560 --out=udp:<TARGET_IP>:14550
```
This command routes the MavLink messages to another computer over UDP.


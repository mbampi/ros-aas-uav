from opcua import Server, ua
from datetime import datetime
import time
import xml.etree.ElementTree as ET

# Dictionary to map variables to labels
# This is used to identify which variable changed when the handler is called
# e.g. variable_to_label['ns=2;i=2'] = 'speed'
variable_to_label = {}

class VariableChangeHandler:
    def datachange_notification(self, node, val, data):
        label = variable_to_label[node]
        # unix timestamp with format: 1739651002.091452451
        timestamp = datetime.now().timestamp()
        print(f"[{timestamp}] Variable '{label}' changed value to: {val}. node: {node.nodeid}")

def main():
    # Create OPC UA server
    server = Server()
    server.set_endpoint("opc.tcp://127.0.0.1:4840/freeopcua/server/")

    # Set server namespace
    uri = "http://aas-example.org"
    idx = server.register_namespace(uri)

    # Create a new object to hold variables
    objects = server.get_objects_node()
    uav = objects.add_object(idx, "UAV")

    # Define topics and corresponding OPC UA node names dynamically
    topics = [
        'horizontal_speed',
        'vertical_speed',
        'battery',
        'altitude',
        'temperature',
        'signal_strength',
        'pitch',
        'roll',
        'imu_temperature',
        'motor_rpm'
    ]

    # Create variables dynamically for each topic
    for topic in topics:
        var = uav.add_variable(idx, topic, 0)
        var.set_writable()
        print(f"Created variable '{topic}' = {var}")
        variable_to_label[var] = topic

    # Start the server
    server.start()
    print("OPC UA Server is running at opc.tcp://127.0.0.1:4840/freeopcua/server/")

    # Create the handler for data changes
    handler = VariableChangeHandler()

    # Create a subscription to monitor the variables
    subscription = server.create_subscription(10, handler)  # 10ms publishing interval

    # Subscribe to data changes for each variable dynamically
    for var in variable_to_label.keys():
        subscription.subscribe_data_change(var)

    try:
        while True:
            # Optionally update server time or other dynamic values
            server_time = datetime.now()
            print(f"Server time: {server_time}")
            time.sleep(10)
    finally:
        server.stop()
        print("OPC UA Server stopped.")


if __name__ == "__main__":
    main()

# clock_server.py
import time
from opcua import Server, ua

def get_server_time(parent):
    """
    This is the method that will be called by the client.
    It returns the server's current time as seconds since the Epoch.
    """
    print("-> Client requested server time. Replying...")
    # The OPC UA server expects method outputs as a sequence corresponding
    # to the declared output arguments. Return a one-element list with a
    # ua.Variant so the UA binary encoder can read the VariantType and
    # encode the value correctly.
    return [ua.Variant(time.time(), ua.VariantType.Double)]

if __name__ == "__main__":
    # 1. Setup the server
    server = Server()

    # Listen on all network interfaces to be reachable from other machines
    # Use 0.0.0.0, not localhost!
    endpoint_url = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
    server.set_endpoint(endpoint_url)

    # 2. Setup the namespace
    name = "ClockSyncServer"
    addspace = server.register_namespace(name)

    # 3. Get the Objects node and add our method
    objects_node = server.get_objects_node()
    
    method_node = objects_node.add_method(
        addspace,                       # Namespace index
        "GetServerTime",                # Method name for the client to call
        get_server_time,                # The Python function to execute
        [],                             # Input arguments (none)
        [ua.VariantType.Double]         # Output arguments (a float/double)
    )

    # 4. Start the server
    try:
        server.start()
        print(f"✅ Clock server started at {endpoint_url}")
        print("Waiting for client connections... Press Ctrl+C to stop.")
        # Keep the server running indefinitely
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server.")
    finally:
        server.stop()
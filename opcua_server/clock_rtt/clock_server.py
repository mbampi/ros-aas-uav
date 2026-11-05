import time
from opcua import Server, ua

def get_server_time(parent):
    """Return the server's current time as seconds since the epoch."""
    print("-> Client requested server time. Replying...")
    # The UA binary encoder needs a Variant to read the VariantType from
    return [ua.Variant(time.time(), ua.VariantType.Double)]

if __name__ == "__main__":
    server = Server()

    # Listen on all interfaces so the client can reach it from another machine
    endpoint_url = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
    server.set_endpoint(endpoint_url)

    name = "ClockSyncServer"
    addspace = server.register_namespace(name)

    objects_node = server.get_objects_node()

    method_node = objects_node.add_method(
        addspace,
        "GetServerTime",
        get_server_time,
        [],
        [ua.VariantType.Double]
    )

    try:
        server.start()
        print(f"Clock server started at {endpoint_url}")
        print("Waiting for client connections... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server.stop()

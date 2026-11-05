import time
from opcua import Client

# Local IP address of the machine running clock_server.py
SERVER_IP = "192.168.1.15"
SERVER_PORT = 4840
SAMPLES_TO_TAKE = 15 # Number of measurements to take for accuracy

def measure_offset(objects_node, method_nodeid):
    """
    Performs a single measurement of the clock offset using the provided
    Objects node and the resolved method NodeId string (e.g. 'ns=2;s=GetServerTime').
    Returns a tuple of (offset, rtt).
    """
    # Record start times
    monotonic_start = time.monotonic()

    # Call the server's method to get its timestamp
    # objects_node.call_method accepts a NodeId string like 'ns=2;s=GetServerTime'
    t_server = objects_node.call_method(method_nodeid)

    # Record end time
    monotonic_end = time.monotonic()
    t2 = time.time()

    # Calculate RTT and offset
    rtt = monotonic_end - monotonic_start
    offset = (t_server + (rtt / 2)) - t2

    return offset, rtt

if __name__ == "__main__":
    server_url = f"opc.tcp://{SERVER_IP}:{SERVER_PORT}/freeopcua/server/"
    client = Client(server_url)

    try:
        print(f"Connecting to server at {server_url}...")
        client.connect()
        print("Connection successful.")

        # Resolve the correct namespace index / NodeId for the GetServerTime method.
        # The server registered a namespace named 'ClockSyncServer', but its
        # namespace index can vary, so we probe the server to find the correct
        # NodeId. We'll try namespaces that contain 'ClockSyncServer' first,
        # then fall back to scanning all namespace indices.
        objects = client.get_objects_node()
        ns_array = client.get_namespace_array()

        # Print namespace array for debugging (index -> URI)
        print("Server namespaces:")
        for i, ns in enumerate(ns_array):
            print(f"  ns={i}: {ns}")

        # Candidate indices where the namespace URI contains the server name
        candidates = [i for i, ns in enumerate(ns_array) if 'ClockSyncServer' in (ns or '')]
        if not candidates:
            candidates = list(range(len(ns_array)))

        method_nodeid = None
        for idx in candidates:
            candidate = f"ns={idx};s=GetServerTime"
            try:
                # quick probe call to verify this NodeId exists and returns a float
                _ = objects.call_method(candidate)
                method_nodeid = candidate
                break
            except Exception:
                # not the right namespace index / node id, keep trying
                continue

        if method_nodeid is None:
            raise RuntimeError("Could not find method 'GetServerTime' in server namespaces."
                               " Ensure the server is running and the namespace name matches.")

        print(f"Resolved method NodeId: {method_nodeid}")

        measurements = []
        print(f"Taking {SAMPLES_TO_TAKE} measurements to find the best sample...")

        for i in range(SAMPLES_TO_TAKE):
            offset, rtt = measure_offset(objects, method_nodeid)
            measurements.append({'offset': offset, 'rtt': rtt})
            print(f"  Sample {i+1:2d}: RTT = {rtt*1000:6.2f} ms, Offset = {offset:+.6f} s")
            time.sleep(0.5) # Wait a moment between samples

        # Find the measurement with the minimum RTT
        # This is the most reliable sample because it had the least network jitter
        best_measurement = min(measurements, key=lambda m: m['rtt'])

        best_rtt_ms = best_measurement['rtt'] * 1000
        best_offset_s = best_measurement['offset']

        print("\n--- Results ---")
        print(f"Best measurement (based on lowest RTT of {best_rtt_ms:.2f} ms):")

        if best_offset_s > 0:
            print(f"The server clock is ahead of this client by: {abs(best_offset_s):.6f} seconds.")
        else:
            print(f"The server clock is behind this client by: {abs(best_offset_s):.6f} seconds.")

        print("\nUse this offset to normalize your timestamps:")
        print("Normalized_Server_Time = Original_Server_Time - ({:.6f})".format(best_offset_s))

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check:")
        print("1. The server script is running on the macOS machine.")
        print(f"2. The SERVER_IP ('{SERVER_IP}') is correct.")
        print("3. Firewalls on both machines are not blocking the connection.")
    finally:
        if client:
            client.disconnect()
            print("\nDisconnected from server.")
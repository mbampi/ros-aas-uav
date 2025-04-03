# Read the file "aas_gateway.txt", which has N entries of two-lines in format: (2 entries example)
# [INFO] [1739720151.216720025] [multi_topic_subscriber]: Listened. topic:horizontal_speed data:"30"
# [INFO] [1739720151.220127637] [multi_topic_subscriber]: Data written to OPC UA server. topic:horizontal_speed data:30 node_id:ns=2;i=2
# [INFO] [1739720151.234024963] [multi_topic_subscriber]: Listened. topic:pitch data:"0"
# [INFO] [1739720151.235176681] [multi_topic_subscriber]: Data written to OPC UA server. topic:pitch data:0 node_id:ns=2;i=8

# Read the file "opcua.txt" which has N lines in format: (2 entries example)
# [1739720151.472833] Variable 'horizontal_speed' changed value to: 30. node: NumericNodeId(ns=2;i=2)
# [1739720151.473062] Variable 'pitch' changed value to: 0. node: NumericNodeId(ns=2;i=8)

# Read the file "pub.txt" which has N lines in format: (2 entries example)
# [INFO] [1739720151.232275656] [multi_topic_publisher]: Publishing: "30" to topic: "horizontal_speed"
# [INFO] [1739720151.232813036] [multi_topic_publisher]: Publishing: "0" to topic: "pitch"

# For each entry (2 lines) in "aas_gateway.txt", find the corresponding entry in "opcua.txt" and "pub.txt" 
# and calculate the latency between the time of publishing and the time of receiving the data in the gateway.
# the latency between receiving that data and the time of writing it to the OPC UA server.
# the latency between time of writing it to the OPC UA server and the time of receiving the data in the OPC UA server.
# And the total latency between the time of publishing and the time of receiving the data in the OPC UA server.

# return it as CSV file containing each entry in "aas_gateway.txt" with the calculated latencies.
import re
import csv

# File names
AAS_GATEWAY_FILE = "aas_gateway.txt"
OPCUA_FILE = "opcua.txt"
PUB_FILE = "pub.txt"
OUTPUT_CSV = "latency_results.csv"

# Regex patterns for parsing log entries
AAS_GATEWAY_LISTENED_PATTERN = re.compile(r'\[INFO\] \[(\d+\.\d+)] .*?topic:(\S+) data:"(\d+)"')
AAS_GATEWAY_WRITTEN_PATTERN = re.compile(r'\[INFO\] \[(\d+\.\d+)] .*?topic:(\S+) data:(\d+) node_id:ns=\d+;i=\d+')
OPCUA_PATTERN = re.compile(r'\[(\d+\.\d+)] Variable \'(\S+)\' changed value to: (\d+)\.')
PUB_PATTERN = re.compile(r'\[INFO\] \[(\d+\.\d+)] .*?Publishing: "(\d+)" to topic: "(\S+)"')

# Read AAS Gateway log
def read_aas_gateway(file_path):
    aas_gateway_data = {}
    with open(file_path, "r") as file:
        lines = file.readlines()
        for i in range(0, len(lines), 2):
            listen_match = AAS_GATEWAY_LISTENED_PATTERN.search(lines[i])
            write_match = AAS_GATEWAY_WRITTEN_PATTERN.search(lines[i + 1])
            if listen_match and write_match:
                listen_time, topic, value = listen_match.groups()
                write_time, topic2, value2 = write_match.groups()
                if topic == topic2 and value == value2:
                    aas_gateway_data[(topic, value)] = {
                        "listen_time": float(listen_time),
                        "write_time": float(write_time),
                    }
    return aas_gateway_data

# Read OPC UA log
def read_opcua(file_path):
    opcua_data = {}
    with open(file_path, "r") as file:
        for line in file:
            match = OPCUA_PATTERN.search(line)
            if match:
                opcua_time, topic, value = match.groups()
                opcua_data[(topic, value)] = float(opcua_time)
    return opcua_data

# Read Publisher log
def read_pub(file_path):
    pub_data = {}
    with open(file_path, "r") as file:
        for line in file:
            match = PUB_PATTERN.search(line)
            if match:
                pub_time, value, topic = match.groups()
                pub_data[(topic, value)] = float(pub_time)
    return pub_data

# Calculate latencies and save results
def calculate_and_save_latencies():
    aas_gateway_data = read_aas_gateway(AAS_GATEWAY_FILE)
    opcua_data = read_opcua(OPCUA_FILE)
    pub_data = read_pub(PUB_FILE)

    results = []
    for (topic, value), aas_entry in aas_gateway_data.items():
        listen_time = aas_entry["listen_time"]
        write_time = aas_entry["write_time"]

        pub_time = pub_data.get((topic, value))
        opcua_time = opcua_data.get((topic, value))

        if pub_time is not None and opcua_time is not None:
            latency_pub_to_listen = listen_time - pub_time
            latency_listen_to_write = write_time - listen_time
            latency_write_to_opcua = opcua_time - write_time
            total_latency = opcua_time - pub_time

            results.append([topic, value, pub_time, listen_time, write_time, opcua_time,
                            latency_pub_to_listen, latency_listen_to_write, latency_write_to_opcua, total_latency])

    # Write results to CSV
    with open(OUTPUT_CSV, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Topic", "Value", "Pub Time", "Listen Time", "Write Time", "OPCUA Time",
                         "Latency Pub→Listen", "Latency Listen→Write", "Latency Write→OPCUA", "Total Latency"])
        writer.writerows(results)

    print(f"Latencies calculated and saved to {OUTPUT_CSV}")

# Run the script
calculate_and_save_latencies()
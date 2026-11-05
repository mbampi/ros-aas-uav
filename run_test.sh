#!/bin/bash

if [ -z "$1" ]; then
    echo "Error: No duration specified."
    echo "Usage: ./run_test.sh <duration_in_minutes>"
    exit 1
fi

DURATION_MINUTES=$1
DURATION_SECONDS=$((DURATION_MINUTES * 60))

OPCUA_DIR="./opcua_server"
ROS2_DIR="./ros2"

cleanup() {
    echo ""
    echo "--- Stopping experiment ---"

    echo "Stopping Docker services..."
    (cd "$ROS2_DIR" && docker compose --profile mock down)

    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "Stopping Python OPC-UA server (PID: $SERVER_PID)..."
        kill $SERVER_PID
    else
        echo "Python OPC-UA server (PID: $SERVER_PID) was not found. It may have already stopped."
    fi

    echo "Experiment cleanup complete."
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "--- Starting experiment for $DURATION_MINUTES minute(s) ---"

# exec so that $! is the python process and not a subshell
(cd "$OPCUA_DIR" && source venv/bin/activate && exec python3 opcua_server.py) &
SERVER_PID=$!
echo "Python OPC-UA server started from venv with PID: $SERVER_PID"

(cd "$ROS2_DIR" && docker compose --profile mock up -d)
echo "Docker services started."

echo ""
echo "Experiment is running. Waiting for $DURATION_MINUTES minute(s)..."
echo "Press Ctrl+C to stop the experiment early."

caffeinate sleep $DURATION_SECONDS

cleanup

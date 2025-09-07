#!/bin/bash

# --- Configuration & Argument Handling ---

# Check if a duration was provided as an argument
if [ -z "$1" ]; then
    echo "Error: No duration specified."
    echo "Usage: ./run_test.sh <duration_in_minutes>"
    exit 1
fi

DURATION_MINUTES=$1
DURATION_SECONDS=$((DURATION_MINUTES * 60)) # Convert minutes to seconds for sleep

# --- Directory Paths ---
OPCUA_DIR="./opcua_server"
ROS2_DIR="./ros2"

# --- Cleanup Function ---
# This function is called to gracefully stop all processes.
cleanup() {
    echo ""
    echo "--- Stopping experiment ---"
    
    # Change to the ros2 directory to run 'docker compose down'
    echo "Stopping Docker services..."
    (cd "$ROS2_DIR" && docker compose --profile mock down)
    
    # Stop the Python server using its stored Process ID (PID)
    # Check if the process exists before trying to kill it
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "Stopping Python OPC-UA server (PID: $SERVER_PID)..."
        kill $SERVER_PID
    else
        echo "Python OPC-UA server (PID: $SERVER_PID) was not found. It may have already stopped."
    fi
    
    echo "Experiment cleanup complete."
    exit 0
}

# --- Main Script ---

# Set a trap to run the cleanup function on script interruption (Ctrl+C) or termination
trap cleanup SIGINT SIGTERM

echo "--- Starting experiment for $DURATION_MINUTES minute(s) ---"

# Run the Python server, activating the venv first.
# Use 'exec' to replace the shell with the python process.
(cd "$OPCUA_DIR" && source venv/bin/activate && exec python3 opcua_server.py) &
SERVER_PID=$!
echo "Python OPC-UA server started from venv with PID: $SERVER_PID"

# Run Docker Compose in its directory, in detached mode (-d)
(cd "$ROS2_DIR" && docker compose --profile mock up -d)
echo "Docker services started."

echo ""
echo "Experiment is running. Waiting for $DURATION_MINUTES minute(s)..."
echo "Press Ctrl+C to stop the experiment early."

# Wait for the specified duration
caffeinate sleep $DURATION_SECONDS

# After the wait, call the cleanup function to stop everything
cleanup
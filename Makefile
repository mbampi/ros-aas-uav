# Makefile to manage ROS log files

# Default target that runs when you just type 'make'
all: clean logs

# Target to remove all files inside the log directory
clean:
	@echo "Removing all files in ~/my_ros_logs/..."
	@rm -rf ~/my_ros_logs/*

# Target to create the specified log files
logs:
	@echo "Creating new log files..."
	@mkdir -p ~/my_ros_logs
	@touch ~/my_ros_logs/aas_gateway_output.log
	@touch ~/my_ros_logs/pub_sample_output.log

# A phony target to avoid conflicts with a file named 'clean' or 'logs'
.PHONY: all clean logs

move_logs:
	@echo "Moving log files to ./latency_measure/..."
	@mv ~/my_ros_logs/*.log ./latency_measure/
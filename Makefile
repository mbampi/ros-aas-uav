# Makefile to manage log files

# Target to collect all logs into experiments directory with timestamp
collect-logs:
	$(eval TIMESTAMP := $(shell date +"%Y-%m-%dT%H-%M-%S"))
	@echo "Collecting logs into experiments/$(TIMESTAMP)/..."
	@mkdir -p experiments/$(TIMESTAMP)

	@echo "Copying aas_gateway.log..."
	@if [ -f "ros2/logs/aas_gateway/aas_gateway.log" ]; then \
		mv "ros2/logs/aas_gateway/aas_gateway.log" "experiments/$(TIMESTAMP)/aas_gateway.log"; \
	else \
		echo "Warning: aas_gateway.log not found"; \
	fi

	@echo "Copying resource_monitor.log..."
	@if [ -f "ros2/logs/resource_monitor/resource_usage.log" ]; then \
		mv "ros2/logs/resource_monitor/resource_usage.log" "experiments/$(TIMESTAMP)/resource_monitor.log"; \
	else \
		echo "Warning: resource_usage.log not found"; \
	fi

	@echo "Copying opcua_server events..."
	@if [ -d "opcua_server/events" ] && [ "$$(ls -A opcua_server/events/*.jsonl 2>/dev/null)" ]; then \
		mv opcua_server/events/*.jsonl "experiments/$(TIMESTAMP)/opcua_server.log"; \
		echo "Merged $$(ls opcua_server/events/*.jsonl | wc -l | tr -d ' ') OPCUA log files"; \
	else \
		echo "Warning: no opcua_server .jsonl files found"; \
	fi
	
	@echo "Log collection complete! Files saved to: experiments/$(TIMESTAMP)/"
	@echo "Contents:"
	@ls -la "experiments/$(TIMESTAMP)/"

# A phony target to avoid conflicts with a file named 'clean' or 'logs'
.PHONY: all clean logs collect-logs

move_logs:
	@echo "Moving log files to ./latency_measure/..."
	@mv ~/my_ros_logs/*.log ./latency_measure/

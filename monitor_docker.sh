#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="logs/monitor.log"

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
    echo -e "$1"
}

# Function to check if a container is running
check_container() {
    local container_name=$1
    local container_status=$(docker inspect --format='{{.State.Status}}' $container_name 2>/dev/null)
    
    if [ "$container_status" != "running" ]; then
        log_message "${RED}Container $container_name is not running (status: $container_status)${NC}"
        return 1
    else
        log_message "${GREEN}Container $container_name is running${NC}"
        return 0
    fi
}

# Function to restart the Docker environment
restart_docker() {
    log_message "${YELLOW}Restarting PerplexityTrader Docker environment...${NC}"
    
    # Run the start script
    ./start_docker.sh >> $LOG_FILE 2>&1
    
    log_message "${GREEN}PerplexityTrader Docker environment has been restarted.${NC}"
}

# Main monitoring loop
log_message "${YELLOW}Starting PerplexityTrader Docker monitor...${NC}"

# Check if containers are running
check_container "docker_nginx_1" || RESTART=true
check_container "docker_agent_1" || RESTART=true
check_container "docker_webhook_1" || RESTART=true
check_container "docker_websocket_1" || RESTART=true

# Restart if any container is not running
if [ "$RESTART" = true ]; then
    log_message "${RED}One or more containers are not running. Restarting...${NC}"
    restart_docker
else
    log_message "${GREEN}All containers are running.${NC}"
fi

log_message "${YELLOW}PerplexityTrader Docker monitor completed.${NC}" 
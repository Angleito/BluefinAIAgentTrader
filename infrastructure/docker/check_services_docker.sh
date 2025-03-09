#!/bin/bash

# Script to check and restart Docker services if needed
# This script is designed to be run as a cron job inside the Docker environment

# Log file
LOG_FILE="/app/logs/service_check.log"

# Function to log messages
log_message() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

log_message "Starting service check..."

# Check if webhook server is running by calling its health endpoint
if ! curl -s http://localhost:5001/health > /dev/null; then
  log_message "Webhook server is not running or health check failed. Restarting..."
  nohup python webhook_server.py > /app/logs/webhook.log 2>&1 &
  log_message "Webhook server restarted with PID: $!"
else
  log_message "Webhook server is running and healthy."
fi

# Check if trading agent is running by calling its health endpoint
if ! curl -s http://localhost:5002/health > /dev/null; then
  log_message "Trading agent is not running or health check failed. Restarting..."
  nohup python agent.py > /app/logs/agent.log 2>&1 &
  log_message "Trading agent restarted with PID: $!"
else
  log_message "Trading agent is running and healthy."
fi

log_message "Service check completed." 
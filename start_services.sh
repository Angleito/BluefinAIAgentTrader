#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing webhook server or agent processes
pkill -f "python webhook_server.py" || true
pkill -f "python agent.py" || true

# Wait for processes to terminate
sleep 2

# Start the webhook server in the background
echo "Starting webhook server..."
nohup python webhook_server.py > logs/webhook_nohup.log 2>&1 &
WEBHOOK_PID=$!
echo "Webhook server started with PID: $WEBHOOK_PID"

# Wait for webhook server to initialize
sleep 5

# Start the trading agent in the background
echo "Starting trading agent..."
nohup python agent.py > logs/agent_nohup.log 2>&1 &
AGENT_PID=$!
echo "Trading agent started with PID: $AGENT_PID"

# Save PIDs to a file for later reference
echo "$WEBHOOK_PID" > logs/webhook.pid
echo "$AGENT_PID" > logs/agent.pid

echo "Services started. To check logs:"
echo "tail -f logs/webhook_nohup.log"
echo "tail -f logs/agent_nohup.log" 
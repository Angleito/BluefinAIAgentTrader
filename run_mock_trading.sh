#!/bin/bash
# Script to run the agent in mock trading mode and watch logs

# Clean up alerts directory
rm -rf alerts
mkdir -p alerts logs

# Create a compatible buy alert
echo '{
    "indicator": "vmanchu_cipher_b",
    "symbol": "SUI/USD",
    "timeframe": "5m",
    "signal_type": "GREEN_CIRCLE",
    "action": "BUY",
    "price": 1.45
}' > alerts/mock_buy_alert.json

# Create a compatible sell alert
echo '{
    "indicator": "vmanchu_cipher_b",
    "symbol": "BTC/USD",
    "timeframe": "5m",
    "signal_type": "RED_CIRCLE",
    "action": "SELL",
    "price": 67890.12
}' > alerts/mock_sell_alert.json

echo "Created test alerts"

# Run the agent in mock trading mode
echo "Starting agent in mock trading mode..."
MOCK_TRADING=True python agent.py > logs/agent_stdout.log 2>&1 &
AGENT_PID=$!

echo "Agent started with PID: $AGENT_PID"
echo "Monitoring logs..."

# Give the agent time to process the alert
sleep 5

# Display running processes
ps aux | grep agent.py

# Check the logs directory
echo "Contents of logs directory:"
ls -la logs/

# Check if agent log was created
if [ -f "logs/agent.log" ]; then
    echo "Agent log found. Last 20 lines:"
    tail -n 20 logs/agent.log
elif [ -f "logs/agent_stdout.log" ]; then
    echo "Agent stdout log found. Last 20 lines:"
    tail -n 20 logs/agent_stdout.log
else
    echo "No log files found"
fi

# Check if alerts were processed
if [ "$(ls -A alerts/)" ]; then
    echo "Alerts still present in directory (not processed):"
    ls -la alerts/
else
    echo "All alerts were processed"
fi

# Cleanup on exit
echo "Press Ctrl+C to stop the agent"
trap "kill $AGENT_PID; echo 'Agent process terminated'" EXIT

# Keep script running to allow monitoring
tail -f logs/agent_stdout.log 
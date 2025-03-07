#!/bin/bash

# Check if webhook server is running
if pgrep -f "python webhook_server.py" > /dev/null; then
  WEBHOOK_PID=$(pgrep -f "python webhook_server.py")
  echo "Webhook server is running with PID: $WEBHOOK_PID"
  echo "Running for: $(ps -o etime= -p $WEBHOOK_PID)"
else
  echo "Webhook server is not running."
fi

# Check if trading agent is running
if pgrep -f "python agent.py" > /dev/null; then
  AGENT_PID=$(pgrep -f "python agent.py")
  echo "Trading agent is running with PID: $AGENT_PID"
  echo "Running for: $(ps -o etime= -p $AGENT_PID)"
else
  echo "Trading agent is not running."
fi

# Show recent logs
echo ""
echo "Recent webhook server logs:"
tail -n 10 logs/webhook.log
echo ""
echo "Recent trading agent logs:"
tail -n 10 logs/agent.log 
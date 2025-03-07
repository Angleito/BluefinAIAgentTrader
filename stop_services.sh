#!/bin/bash

# Kill any existing webhook server or agent processes
echo "Stopping webhook server and trading agent..."
pkill -f "python webhook_server.py" || true
pkill -f "python agent.py" || true

# Check if processes were killed
if pgrep -f "python webhook_server.py" > /dev/null; then
  echo "Warning: Webhook server is still running. Trying to kill it forcefully..."
  pkill -9 -f "python webhook_server.py" || true
else
  echo "Webhook server stopped successfully."
fi

if pgrep -f "python agent.py" > /dev/null; then
  echo "Warning: Trading agent is still running. Trying to kill it forcefully..."
  pkill -9 -f "python agent.py" || true
else
  echo "Trading agent stopped successfully."
fi

echo "Services stopped." 
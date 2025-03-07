#!/bin/bash

# Check if webhook server is running
if ! systemctl is-active --quiet perplexitytrader-webhook.service; then
  echo "Webhook server is not running. Restarting..."
  sudo systemctl restart perplexitytrader-webhook.service
else
  echo "Webhook server is running."
fi

# Check if trading agent is running
if ! systemctl is-active --quiet perplexitytrader.service; then
  echo "Trading agent is not running. Restarting..."
  sudo systemctl restart perplexitytrader.service
else
  echo "Trading agent is running."
fi

# Show recent logs
echo ""
echo "Recent webhook server logs:"
sudo journalctl -u perplexitytrader-webhook.service -n 10 --no-pager
echo ""
echo "Recent trading agent logs:"
sudo journalctl -u perplexitytrader.service -n 10 --no-pager 
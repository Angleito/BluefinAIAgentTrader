#!/bin/bash

# Make sure we're running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Copy service files to systemd directory
cp perplexitytrader.service /etc/systemd/system/
cp perplexitytrader-webhook.service /etc/systemd/system/

# Reload systemd to recognize new services
systemctl daemon-reload

# Enable services to start on boot
systemctl enable perplexitytrader.service
systemctl enable perplexitytrader-webhook.service

# Start services
systemctl start perplexitytrader-webhook.service
systemctl start perplexitytrader.service

# Check status
echo "Webhook server status:"
systemctl status perplexitytrader-webhook.service
echo ""
echo "Trading agent status:"
systemctl status perplexitytrader.service

echo ""
echo "Services installed and started. To check logs, use:"
echo "journalctl -u perplexitytrader.service -f"
echo "journalctl -u perplexitytrader-webhook.service -f" 
#!/bin/bash

# Create a temporary file with the current crontab
crontab -l > /tmp/current_crontab 2>/dev/null || echo "" > /tmp/current_crontab

# Check if the entry already exists
if grep -q "check_services.sh" /tmp/current_crontab; then
  echo "Cron job already exists."
else
  # Add the new cron job
  echo "*/5 * * * * $(pwd)/check_services.sh >> $(pwd)/logs/service_check.log 2>&1" >> /tmp/current_crontab
  
  # Install the new crontab
  crontab /tmp/current_crontab
  
  echo "Cron job added to check services every 5 minutes."
fi

# Clean up
rm /tmp/current_crontab

echo "To view the current crontab, run: crontab -l" 
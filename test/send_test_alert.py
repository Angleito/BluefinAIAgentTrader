#!/usr/bin/env python
"""
Script to send test TradingView alerts to the webhook server.

This script sends a sample VuManChu Cipher B alert to the webhook server
for testing purposes.

Usage:
    python test/send_test_alert.py [--url URL] [--symbol SYMBOL] [--signal SIGNAL]

Arguments:
    --url URL       The webhook URL (default: http://localhost:5001/webhook)
    --symbol SYMBOL The symbol to use (default: SUI/USD)
    --signal SIGNAL The signal type (default: GREEN_CIRCLE)
                    Options: GREEN_CIRCLE, RED_CIRCLE, GOLD_CIRCLE, PURPLE_TRIANGLE,
                            LITTLE_CIRCLE, BULL_FLAG, BEAR_FLAG, BULL_DIAMOND, BEAR_DIAMOND
    --timeframe TF  The timeframe (default: 5m)
    --action ACTION The action (BUY or SELL, default: BUY)
"""

import argparse
import json
import logging
import requests
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("send_test_alert")

# Valid signal types
VALID_SIGNALS = [
    "GREEN_CIRCLE",
    "RED_CIRCLE",
    "GOLD_CIRCLE",
    "PURPLE_TRIANGLE",
    "LITTLE_CIRCLE",
    "BULL_FLAG",
    "BEAR_FLAG",
    "BULL_DIAMOND",
    "BEAR_DIAMOND"
]

def create_test_alert(symbol, signal_type, timeframe, action):
    """Create a test alert with the provided parameters."""
    return {
        "indicator": "vmanchu_cipher_b",
        "symbol": symbol,
        "timeframe": timeframe,
        "signal_type": signal_type,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    }

def send_alert(url, alert_data):
    """Send the alert to the webhook server."""
    try:
        logger.info(f"Sending alert to {url}")
        logger.info(f"Alert data: {json.dumps(alert_data)}")
        
        response = requests.post(
            url,
            json=alert_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Alert sent successfully")
            logger.info(f"Response: {json.dumps(response.json())}")
        else:
            logger.error(f"Failed to send alert: {response.text}")
            
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to webhook server: {str(e)}")
        return None

def main():
    """Parse arguments and send the test alert."""
    parser = argparse.ArgumentParser(description="Send a test TradingView alert to the webhook server.")
    parser.add_argument("--url", default="http://localhost:5001/webhook", help="The webhook URL")
    parser.add_argument("--symbol", default="SUI/USD", help="The symbol to use")
    parser.add_argument("--signal", default="GREEN_CIRCLE", choices=VALID_SIGNALS, help="The signal type")
    parser.add_argument("--timeframe", default="5m", help="The timeframe")
    parser.add_argument("--action", default="BUY", choices=["BUY", "SELL"], help="The action (BUY or SELL)")
    
    args = parser.parse_args()
    
    # Create the test alert
    alert = create_test_alert(args.symbol, args.signal, args.timeframe, args.action)
    
    # Send the alert
    response = send_alert(args.url, alert)
    
    if response and response.status_code == 200:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 
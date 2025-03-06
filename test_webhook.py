#!/usr/bin/env python3
import requests
import argparse
import json
import os
from datetime import datetime

def test_webhook(url, alert_type="BUY", symbol="SUI/USD", timeframe="5m"):
    """
    Send a test webhook to the specified URL
    """
    # Create a test payload that resembles a VuManChu Cipher B alert
    payload = {
        "indicator": "vmanchu_cipher_b",
        "symbol": symbol,
        "timeframe": timeframe,
        "action": alert_type,
        "signal_type": "WAVE1",
        "timestamp": datetime.utcnow().isoformat(),
        "passphrase": os.getenv("TV_WEBHOOK_SECRET", "cipher_b_secret_key")
    }
    
    print(f"\n{'-'*50}")
    print(f"Testing webhook: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'-'*50}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print("\n✅ Webhook test successful!")
        else:
            print("\n❌ Webhook test failed!")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error sending webhook: {str(e)}")
        
    print(f"{'-'*50}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the TradingView webhook server")
    parser.add_argument("--url", type=str, required=True, help="The webhook URL to test")
    parser.add_argument("--action", type=str, default="BUY", choices=["BUY", "SELL"], help="The action to send (BUY or SELL)")
    parser.add_argument("--symbol", type=str, default="SUI/USD", help="The trading symbol")
    parser.add_argument("--timeframe", type=str, default="5m", help="The timeframe")
    
    args = parser.parse_args()
    
    test_webhook(args.url, args.action, args.symbol, args.timeframe) 
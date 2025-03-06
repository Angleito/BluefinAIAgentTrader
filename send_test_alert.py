import requests
import json
import argparse

def send_alert(url, signal_type="GREEN_CIRCLE", action="BUY", symbol="SUI/USD", timeframe="5m"):
    """Send a test alert to the webhook server"""
    
    payload = {
        "indicator": "vmanchu_cipher_b",
        "symbol": symbol,
        "timeframe": timeframe,
        "action": action,
        "signal_type": signal_type
    }
    
    print(f"Sending alert to {url}:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload)
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
    except Exception as e:
        print(f"Error sending alert: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send a test alert to the webhook server')
    parser.add_argument('--url', type=str, default='http://localhost:5001/webhook', help='Webhook URL')
    parser.add_argument('--signal-type', type=str, default='GREEN_CIRCLE', help='Signal type')
    parser.add_argument('--action', type=str, default='BUY', help='Action (BUY or SELL)')
    parser.add_argument('--symbol', type=str, default='SUI/USD', help='Symbol')
    parser.add_argument('--timeframe', type=str, default='5m', help='Timeframe')
    
    args = parser.parse_args()
    
    send_alert(args.url, args.signal_type, args.action, args.symbol, args.timeframe) 
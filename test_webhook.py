#!/usr/bin/env python3
import requests
import argparse
import json
import os
from datetime import datetime

# Define signal type classifications
BULLISH_SIGNALS = ["GREEN_CIRCLE", "GOLD_CIRCLE", "BULL_FLAG", "BULL_DIAMOND"]
BEARISH_SIGNALS = ["RED_CIRCLE", "BEAR_FLAG", "BEAR_DIAMOND"]
AMBIGUOUS_SIGNALS = ["PURPLE_TRIANGLE", "LITTLE_CIRCLE"]

def get_trade_direction(signal_type, action=None):
    """
    Determine if a signal is Bullish (long) or Bearish (short)
    
    Args:
        signal_type (str): The VuManChu Cipher B signal type
        action (str, optional): BUY or SELL action, needed for ambiguous signals
        
    Returns:
        str: "Bullish" for long trades, "Bearish" for short trades
    """
    if signal_type in BULLISH_SIGNALS:
        return "Bullish"
    elif signal_type in BEARISH_SIGNALS:
        return "Bearish"
    else:
        # For ambiguous signals like PURPLE_TRIANGLE or LITTLE_CIRCLE
        # use the specified action to determine direction
        if action and action.upper() == "BUY":
            return "Bullish"
        elif action and action.upper() == "SELL":
            return "Bearish"
        else:
            # Default to Bullish if can't determine
            return "Bullish"

def test_webhook(url, alert_type="BUY", symbol="SUI/USD", timeframe="5m", signal_type="GREEN_CIRCLE"):
    """
    Send a test webhook to the specified URL
    """
    # Determine trade direction based on signal type and action
    trade_direction = get_trade_direction(signal_type, alert_type)
    
    # Create a test payload that resembles a VuManChu Cipher B alert
    payload = {
        "indicator": "vmanchu_cipher_b",
        "symbol": symbol,
        "timeframe": timeframe,
        "action": alert_type,
        "signal_type": signal_type,
        "trade_direction": trade_direction,  # Add explicit trade direction
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"\n{'-'*50}")
    print(f"Testing webhook: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Trade Direction: {trade_direction} ({alert_type})")
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

def get_default_action_for_signal(signal_type):
    """Return the appropriate default action for a signal type"""
    if signal_type in BULLISH_SIGNALS:
        return "BUY"
    elif signal_type in BEARISH_SIGNALS:
        return "SELL"
    return "BUY"  # Default for ambiguous signals

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the TradingView webhook server")
    parser.add_argument("--url", type=str, required=True, help="The webhook URL to test")
    
    # Create signal type help text with direction information
    signal_help = """The VuManChu Cipher B signal type to test:
    Bullish signals (long trades): GREEN_CIRCLE, GOLD_CIRCLE, BULL_FLAG, BULL_DIAMOND
    Bearish signals (short trades): RED_CIRCLE, BEAR_FLAG, BEAR_DIAMOND
    Ambiguous signals (specify action): PURPLE_TRIANGLE, LITTLE_CIRCLE
    """
    
    parser.add_argument("--signal-type", type=str, default="GREEN_CIRCLE", 
                        choices=BULLISH_SIGNALS + BEARISH_SIGNALS + AMBIGUOUS_SIGNALS,
                        help=signal_help)
    
    parser.add_argument("--timeframe", type=str, default="5m", help="The timeframe")
    parser.add_argument("--symbol", type=str, default="SUI/USD", help="The trading symbol")
    
    # Dynamically set default action based on the chosen signal type
    args, unknown = parser.parse_known_args()
    default_action = get_default_action_for_signal(args.signal_type)
    
    parser.add_argument("--action", type=str, default=None, choices=["BUY", "SELL"], 
                      help="The action to send (BUY for Bullish/long, SELL for Bearish/short)")
    
    args = parser.parse_args()
    
    # If action not specified, use the default for the signal type
    if args.action is None:
        args.action = default_action
    
    test_webhook(args.url, args.action, args.symbol, args.timeframe, args.signal_type) 
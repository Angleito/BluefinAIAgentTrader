#!/usr/bin/env python3
"""
Tool to send test alerts to the trading agent.
This script writes alerts to the alerts directory that will be processed by the agent.
"""
import json
import os
import sys
import datetime
import argparse
import uuid
from pathlib import Path

def create_buy_alert(symbol="SUI/USD", price=1.45, timeframe="5m"):
    """Create a buy alert for the specified symbol"""
    alert_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    alert_data = {
        "symbol": symbol,
        "type": "buy",
        "timeframe": timeframe,
        "signal_type": "GREEN_CIRCLE",
        "entry_time": timestamp,
        "position_size": 1.0,
        "leverage": 5,
        "stop_loss": price * 0.95,  # 5% below current price
        "take_profit": price * 1.10,  # 10% above current price
        "confidence": 0.85,
        "price": price,
        "original_alert": {
            "indicator": "vumanchu_cipher_b",
            "value": "bullish_cross",
            "price": price
        }
    }
    
    # Save alert to file
    alert_file = f"alerts/buy_alert_{alert_id}.json"
    with open(alert_file, "w") as f:
        json.dump(alert_data, f, indent=4)
    
    print(f"Created buy alert: {alert_file}")
    return alert_file

def create_sell_alert(symbol="SUI/USD", price=1.52, timeframe="5m"):
    """Create a sell alert for the specified symbol"""
    alert_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    alert_data = {
        "symbol": symbol,
        "type": "sell",
        "timeframe": timeframe,
        "signal_type": "RED_CIRCLE",
        "entry_time": timestamp,
        "position_size": 1.0,
        "leverage": 5,
        "stop_loss": price * 1.05,  # 5% above current price
        "take_profit": price * 0.90,  # 10% below current price
        "confidence": 0.82,
        "price": price,
        "original_alert": {
            "indicator": "vumanchu_cipher_b",
            "value": "bearish_cross",
            "price": price
        }
    }
    
    # Save alert to file
    alert_file = f"alerts/sell_alert_{alert_id}.json"
    with open(alert_file, "w") as f:
        json.dump(alert_data, f, indent=4)
    
    print(f"Created sell alert: {alert_file}")
    return alert_file

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Create test trade alerts")
    parser.add_argument("--type", "-t", choices=["buy", "sell", "both"], default="both", 
                        help="Type of alert to create (buy, sell, or both)")
    parser.add_argument("--symbol", "-s", default="SUI/USD", 
                        help="Symbol to trade (default: SUI/USD)")
    parser.add_argument("--price", "-p", type=float, default=1.45,
                        help="Current price of the symbol (default: 1.45)")
    parser.add_argument("--timeframe", "-tf", default="5m",
                        help="Timeframe for the trade (default: 5m)")
    
    return parser.parse_args()

def main():
    """Main function"""
    # Parse arguments
    args = parse_arguments()
    
    # Create alerts directory if it doesn't exist
    os.makedirs("alerts", exist_ok=True)
    
    # Create alerts based on arguments
    if args.type == "buy" or args.type == "both":
        create_buy_alert(args.symbol, args.price, args.timeframe)
    
    if args.type == "sell" or args.type == "both":
        create_sell_alert(args.symbol, args.price * 1.05, args.timeframe)  # Slightly higher price for sell
    
    print(f"Created test alerts for {args.symbol} at ${args.price}")
    print("Run 'python agent.py' to process these alerts and simulate trades")

if __name__ == "__main__":
    main() 
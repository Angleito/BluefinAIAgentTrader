#!/usr/bin/env python3
"""
Generate sample TradingView webhook alerts for testing the agent in mock mode.
"""
import json
import os
import time
import random
from datetime import datetime, timedelta

def create_alert(ticker, alert_type, price, timeframe="5m"):
    """Create a TradingView-style webhook alert"""
    alert_data = {
        "ticker": ticker,
        "price": str(price),
        "alert_type": alert_type,
        "timeframe": timeframe,
        "strategy": "vumanchu_cipher_b",
        "confidence": random.uniform(0.75, 0.95)
    }
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    alert_id = f"{timestamp}_{alert_type}_{ticker.replace('/', '_')}"
    
    # Create alerts directory if it doesn't exist
    os.makedirs("alerts", exist_ok=True)
    
    # Write alert to file
    filename = f"alerts/{alert_id}.json"
    with open(filename, "w") as f:
        json.dump(alert_data, f, indent=4)
    
    print(f"Created alert: {filename}")
    return filename

def main():
    """Generate a sequence of buy and sell alerts for testing"""
    # List of tickers to create alerts for
    tickers = ["SUI-PERP", "ETH-PERP", "BTC-PERP"]
    
    # Sample prices
    prices = {
        "SUI-PERP": 1.48,
        "ETH-PERP": 3890.75,
        "BTC-PERP": 68754.32
    }
    
    # Generate alerts
    alert_types = ["buy_signal", "sell_signal"]
    
    print("Generating sample TradingView webhook alerts...")
    
    # Create one of each alert type for each ticker
    for ticker in tickers:
        price = prices[ticker]
        
        # Buy signal
        create_alert(ticker, "buy_signal", price)
        
        # Small price increase for sell signal
        adjusted_price = price * (1 + random.uniform(0.01, 0.03))
        create_alert(ticker, "sell_signal", adjusted_price)
    
    print("\nAll alerts created successfully!")
    print("\nTo process these alerts, run:")
    print("  MOCK_TRADING=True python agent.py")
    print("\nThe agent will read these alert files and simulate trades.")

if __name__ == "__main__":
    main() 
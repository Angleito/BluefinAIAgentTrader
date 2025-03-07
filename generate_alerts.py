#!/usr/bin/env python3
"""
Generate alerts compatible with the agent's process_alerts function.
"""
import json
import os
import time
import random
from datetime import datetime

def create_alert(symbol, action, signal_type="GREEN_CIRCLE"):
    """Create a VuManChu Cipher B alert compatible with the agent"""
    alert_data = {
        "indicator": "vmanchu_cipher_b",
        "symbol": symbol,
        "timeframe": "5m",
        "signal_type": signal_type,
        "action": action,
        "price": random.uniform(1.40, 1.60) if "SUI" in symbol else random.uniform(3500, 4200)
    }
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    alert_id = f"{timestamp}_{action}_{symbol.replace('/', '_')}"
    
    # Create alerts directory if it doesn't exist
    os.makedirs("alerts", exist_ok=True)
    
    # Write alert to file
    filename = f"alerts/{alert_id}.json"
    with open(filename, "w") as f:
        json.dump(alert_data, f, indent=4)
    
    print(f"Created alert: {filename}")
    return filename

def main():
    """Generate compatible alerts for testing"""
    # Clear existing alerts
    if os.path.exists("alerts"):
        for file in os.listdir("alerts"):
            if file.endswith(".json"):
                os.remove(os.path.join("alerts", file))
    
    # Symbols to create alerts for
    symbols = ["SUI/USD", "ETH/USD"]
    
    # Valid signals
    signal_types = ["GREEN_CIRCLE", "RED_CIRCLE", "GOLD_CIRCLE", "PURPLE_TRIANGLE"]
    
    # Actions (trade direction)
    actions = ["BUY", "SELL"]
    
    print("Generating VuManChu Cipher B alerts...")
    
    # Create various combinations
    for symbol in symbols:
        for action in actions:
            # Select appropriate signal type based on action
            if action == "BUY":
                signal = "GREEN_CIRCLE"
            else:
                signal = "RED_CIRCLE"
                
            create_alert(symbol, action, signal)
    
    print("\nAll alerts created successfully!")
    print("\nTo process these alerts, run:")
    print("  MOCK_TRADING=True python agent.py")
    print("\nThe agent will read these alert files and simulate trades.")

if __name__ == "__main__":
    main() 
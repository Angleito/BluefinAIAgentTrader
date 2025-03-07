#!/usr/bin/env python3
"""
Debug script to verify alert processing and formatting
"""
import os
import json
import time
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("debug_alerts")

def create_test_alerts():
    """Create test alerts with the correct format"""
    # Create alerts directory if it doesn't exist
    os.makedirs("alerts", exist_ok=True)
    
    # Clear existing alerts
    for file in os.listdir("alerts"):
        if file.endswith(".json"):
            os.remove(os.path.join("alerts", file))
    
    # Create first test alert (buy SUI)
    buy_alert = {
        "indicator": "vmanchu_cipher_b",
        "symbol": "SUI/USD",
        "timeframe": "5m",
        "signal_type": "GREEN_CIRCLE",
        "action": "BUY",
        "price": 1.45
    }
    
    with open("alerts/buy_alert.json", "w") as f:
        json.dump(buy_alert, f, indent=4)
    
    logger.info(f"Created buy alert: alerts/buy_alert.json")
    
    # Create second test alert (sell BTC)
    sell_alert = {
        "indicator": "vmanchu_cipher_b",
        "symbol": "BTC/USD",
        "timeframe": "5m",
        "signal_type": "RED_CIRCLE",
        "action": "SELL",
        "price": 67890.12
    }
    
    with open("alerts/sell_alert.json", "w") as f:
        json.dump(sell_alert, f, indent=4)
    
    logger.info(f"Created sell alert: alerts/sell_alert.json")

def simulate_alert_processing():
    """Simulate the agent's alert processing logic"""
    logger.info("Simulating alert processing logic...")
    
    # Check for alert files
    alert_files = [f for f in os.listdir("alerts") if f.endswith(".json")]
    
    if not alert_files:
        logger.error("No alert files found!")
        return
    
    logger.info(f"Found {len(alert_files)} alert files")
    
    # Process each alert
    for file in alert_files:
        alert_path = os.path.join("alerts", file)
        
        try:
            # Read the alert data
            with open(alert_path, "r") as f:
                alert = json.load(f)
            
            logger.info(f"Processing alert: {alert}")
            
            # Check if it's a VuManChu Cipher B alert
            if "indicator" in alert and alert["indicator"] == "vmanchu_cipher_b":
                symbol = alert.get("symbol", "Unknown")
                timeframe = alert.get("timeframe", "Unknown")
                signal_type = alert.get("signal_type", "Unknown")
                action = alert.get("action", "Unknown")
                
                logger.info(f"VuManChu Cipher B alert detected:")
                logger.info(f"Symbol: {symbol}, Timeframe: {timeframe}")
                logger.info(f"Signal Type: {signal_type}, Action: {action}")
                
                # Check if action is valid
                if action in ["BUY", "SELL"]:
                    logger.info(f"Valid action: {action}")
                    
                    # Check if signal type is valid
                    valid_signals = ["GREEN_CIRCLE", "RED_CIRCLE", "GOLD_CIRCLE", "PURPLE_TRIANGLE"]
                    if signal_type in valid_signals:
                        logger.info(f"Valid signal type: {signal_type}")
                        
                        # Simulate mock trade
                        logger.info(f"MOCK TRADE: Would execute a {action} trade for {symbol}")
                        logger.info(f"Trade direction: {'Bullish' if action == 'BUY' else 'Bearish'}")
                    else:
                        logger.warning(f"Invalid signal type: {signal_type}")
                else:
                    logger.warning(f"Invalid action: {action}")
            else:
                logger.warning(f"Not a VuManChu Cipher B alert or missing indicator field")
            
            # Clean up processed alert
            os.remove(alert_path)
            logger.info(f"Removed processed alert: {file}")
            
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from file: {alert_path}")
        except Exception as e:
            logger.error(f"Error processing alert file {alert_path}: {e}")

def main():
    """Main function"""
    logger.info("Starting alert debugging")
    
    # Create test alerts
    create_test_alerts()
    
    # Simulate processing
    simulate_alert_processing()
    
    # Check if all alerts were processed
    remaining_alerts = [f for f in os.listdir("alerts") if f.endswith(".json")]
    if remaining_alerts:
        logger.warning(f"Unprocessed alerts remain: {remaining_alerts}")
    else:
        logger.info("All alerts were successfully processed")

if __name__ == "__main__":
    main() 
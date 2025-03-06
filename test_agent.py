import os
import json
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_test.log')
    ]
)

logger = logging.getLogger('agent_test')

def process_alerts():
    """Process incoming alerts from the webhook server"""
    
    if not os.path.exists("alerts"):
        os.makedirs("alerts", exist_ok=True)
        return
        
    # Check for new alert files
    for file in os.listdir("alerts"):
        if file.endswith(".json"):
            alert_path = os.path.join("alerts", file)
            
            try:
                # Read the alert data
                with open(alert_path, "r") as f:
                    alert = json.load(f)
                
                logger.info(f"New alert received: {alert}")
                
                # Extract key data from the alert
                if "indicator" in alert and alert["indicator"] == "vmanchu_cipher_b":
                    symbol = alert.get("symbol", "SUI/USD")
                    timeframe = alert.get("timeframe", "5m")
                    signal_type = alert.get("signal_type", "")
                    action = alert.get("action", "")
                    
                    logger.info(f"Processing VuManChu Cipher B signal: {signal_type}")
                    logger.info(f"Symbol: {symbol}, Timeframe: {timeframe}, Action: {action}")
                    
                    # Determine trade direction based on signal type and action
                    if action == "BUY":
                        trade_direction = "Bullish"
                        side = "BUY"
                    elif action == "SELL":
                        trade_direction = "Bearish"
                        side = "SELL"
                    else:
                        logger.warning(f"Invalid action in alert: {action}")
                        os.remove(alert_path)
                        continue
                    
                    # Check if this is a valid signal type
                    valid_signals = ["GREEN_CIRCLE", "RED_CIRCLE", "GOLD_CIRCLE", "PURPLE_TRIANGLE"]
                    if signal_type not in valid_signals:
                        logger.warning(f"Invalid signal type: {signal_type}")
                        os.remove(alert_path)
                        continue
                    
                    # Mock trade execution
                    logger.info(f"MOCK TRADE: Would execute a {side} trade for {symbol} based on {signal_type} signal")
                    logger.info(f"Trade direction: {trade_direction}")
                else:
                    logger.warning(f"Unsupported alert type: {alert}")
                
                # Clean up the processed alert file
                os.remove(alert_path)
                
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from file: {alert_path}")
                os.remove(alert_path)
            except Exception as e:
                logger.error(f"Error processing alert file {alert_path}: {e}")

def main():
    logger.info("Starting test agent...")
    
    # Create necessary directories
    os.makedirs("alerts", exist_ok=True)
    
    # Main loop
    try:
        while True:
            process_alerts()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Test agent stopped by user")

if __name__ == "__main__":
    main() 
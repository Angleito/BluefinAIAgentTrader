import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import hmac
import hashlib
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook_server")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

app = Flask(__name__)

# Optional security key for TradingView
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "")

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "OK", "timestamp": datetime.utcnow().isoformat()})

@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    Endpoint for TradingView alerts.
    
    Expected format:
    {
        "passphrase": "your_secret_key",  # Optional security
        "indicator": "vmanchu_cipher_b",
        "symbol": "SUI/USD",
        "timeframe": "5m",
        "action": "BUY" or "SELL",
        "signal_type": "WAVE1", "WAVE2", "RSI_BULL", etc.
        "timestamp": "2023-01-01T12:00:00Z"
    }
    """
    try:
        # Get the request data
        data = request.json
        
        # Log the received webhook
        logger.info(f"Received webhook: {json.dumps(data)}")
        
        # Verify passphrase if set
        if TV_WEBHOOK_SECRET:
            if "passphrase" not in data or data["passphrase"] != TV_WEBHOOK_SECRET:
                logger.warning("Invalid passphrase in webhook")
                return jsonify({"status": "error", "message": "Invalid passphrase"}), 401
        
        # Validate required fields
        required_fields = ["indicator", "symbol", "timeframe", "action"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
        
        # Add timestamp if not provided
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
        
        # Process the VuManChu Cipher B alert
        if data["indicator"].lower() == "vmanchu_cipher_b":
            # Here, you would implement logic to process the alert
            # For now, we'll just log it and pass it to the agent
            
            # Save the alert to a file for the agent to pick up
            save_alert_for_agent(data)
            
            # Return success response
            return jsonify({
                "status": "success",
                "message": "Alert received and processed",
                "data": data
            })
        else:
            logger.warning(f"Unknown indicator: {data['indicator']}")
            return jsonify({"status": "error", "message": "Unsupported indicator"}), 400
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

def save_alert_for_agent(alert_data):
    """Save the alert to a file that the agent can process."""
    try:
        # Create alerts directory if it doesn't exist
        os.makedirs("alerts", exist_ok=True)
        
        # Generate a filename based on timestamp and symbol
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"alerts/alert_{timestamp}_{alert_data['symbol'].replace('/', '_')}.json"
        
        # Write the alert data to the file
        with open(filename, "w") as f:
            json.dump(alert_data, f, indent=2)
            
        logger.info(f"Alert saved to file: {filename}")
        
        # Optionally, notify the agent directly
        try:
            agent_notify_url = "http://localhost:5000/api/process_alert"
            requests.post(agent_notify_url, json=alert_data, timeout=1)
            logger.info("Alert forwarded to agent")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not forward alert to agent: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error saving alert: {str(e)}", exc_info=True)

if __name__ == "__main__":
    port = int(os.getenv("WEBHOOK_PORT", 5001))
    
    # Print instructions for TradingView alerts
    print(f"\n{'='*50}")
    print("TradingView Webhook Server")
    print(f"{'='*50}")
    print(f"Listening on port: {port}")
    print("To use with TradingView alerts, setup ngrok and use the webhook URL in TradingView.")
    print(f"{'='*50}\n")
    
    app.run(host="0.0.0.0", port=port, debug=False) 
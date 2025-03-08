import os
import json
import logging
import asyncio
from datetime import datetime
import hmac
import hashlib
import requests
import sys

try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Error: Flask package not installed. Run: pip install flask")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed. Run: pip install python-dotenv")
    sys.exit(1)

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

# Valid VuManChu Cipher B signal types with explicit Bullish/Bearish tags
VALID_SIGNAL_TYPES = [
    "GREEN_CIRCLE",   # Bullish: Wavetrend waves at oversold level and crossed up
    "RED_CIRCLE",     # Bearish: Wavetrend waves at overbought level and crossed down
    "GOLD_CIRCLE",    # Bullish: Strong Buy - RSI below 20, WaveTrend <= -80, crossed up after bullish divergence
    "PURPLE_TRIANGLE", # Can be Bullish or Bearish: Divergence with WT crosses at overbought/oversold
    "LITTLE_CIRCLE",  # Can be Bullish or Bearish: All WaveTrend wave crossings
    "BULL_FLAG",      # Bullish: MFI+RSI>0, WT<0 and crossed up, VWAP>0 on higher timeframe
    "BEAR_FLAG",      # Bearish: MFI+RSI<0, WT>0 and crossed down, VWAP<0 on higher timeframe
    "BULL_DIAMOND",   # Bullish: Pattern with HT green candle
    "BEAR_DIAMOND"    # Bearish: Pattern with HT red candle
]

# Import core modules
try:
    from core.signal_processor import process_tradingview_alert
except ImportError:
    logger.warning("Cannot import signal_processor module. Continuing without trading functionality.")

    # Fallback implementation
    def process_tradingview_alert(alert_data):
        logger.info(f"Using fallback signal processor: {alert_data}")
        return alert_data

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "OK", 
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    Endpoint for TradingView alerts.
    
    Expected format:
    {
        "indicator": "vmanchu_cipher_b",
        "symbol": "SUI/USD",
        "timeframe": "5m",
        "action": "BUY" or "SELL",
        "signal_type": "GREEN_CIRCLE", "RED_CIRCLE", "GOLD_CIRCLE", "PURPLE_TRIANGLE", "LITTLE_CIRCLE", etc.
        "timestamp": "2023-01-01T12:00:00Z"
    }
    """
    try:
        # Get the request data
        if not request.is_json:
            logger.warning("Received non-JSON request")
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
            
        data = request.json
        if not data:
            logger.warning("Received empty JSON request")
            return jsonify({"status": "error", "message": "Empty JSON request"}), 400
        
        # Log the received webhook
        logger.info(f"Received webhook: {json.dumps(data)}")
        
        # Validate required fields
        required_fields = ["indicator", "symbol", "timeframe", "signal_type"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
        
        # Validate signal type for VuManChu Cipher B
        if data["indicator"].lower() == "vmanchu_cipher_b":
            if data["signal_type"] not in VALID_SIGNAL_TYPES:
                logger.warning(f"Invalid signal type: {data['signal_type']}")
                return jsonify({
                    "status": "error", 
                    "message": f"Invalid signal type. Must be one of: {', '.join(VALID_SIGNAL_TYPES)}"
                }), 400
            
        # Add timestamp if not provided
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
        
        # Process the VuManChu Cipher B alert
        if data["indicator"].lower() == "vmanchu_cipher_b":
            # Process the alert using the signal processor
            processed_signal = process_tradingview_alert(data)
            
            if not processed_signal:
                return jsonify({
                    "status": "warning",
                    "message": "Alert was received but not processed due to filtering rules"
                }), 200
            
            # Save the processed alert to a file for the agent to pick up
            save_alert_for_agent(processed_signal)
            
            # Return success response
            return jsonify({
                "status": "success",
                "message": "Alert received and processed",
                "data": processed_signal
            })
        else:
            logger.warning(f"Unsupported indicator: {data['indicator']}")
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
        symbol = alert_data["symbol"].replace("/", "_").replace("-", "_")
        filename = f"alerts/alert_{timestamp}_{symbol}.json"
        
        # Write the alert data to the file
        with open(filename, "w") as f:
            json.dump(alert_data, f, indent=2)
            
        logger.info(f"Alert saved to file: {filename}")
        
        # Notify the agent directly
        notify_agent(alert_data)
    
    except Exception as e:
        logger.error(f"Error saving alert: {str(e)}", exc_info=True)

def notify_agent(alert_data):
    """Notify the agent of a new alert via API."""
    try:
        agent_api_url = os.getenv("AGENT_API_URL", "http://localhost:5000/api/process_alert")
        
        # Send asynchronously to avoid blocking
        def send_notification():
            try:
                response = requests.post(
                    agent_api_url, 
                    json=alert_data, 
                    timeout=2,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    logger.info("Alert successfully forwarded to agent")
                else:
                    logger.warning(f"Agent returned non-200 status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Could not forward alert to agent: {str(e)}")
        
        # Run in a separate thread to avoid blocking
        from threading import Thread
        thread = Thread(target=send_notification)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        logger.error(f"Error notifying agent: {str(e)}", exc_info=True)

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify the webhook server is working."""
    return jsonify({
        "status": "OK",
        "message": "Webhook server is running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "webhook": "/webhook (POST)",
            "health": "/health (GET)"
        }
    })

@app.route('/simulate', methods=['POST'])
def simulate_webhook():
    """
    Endpoint to simulate a TradingView webhook for testing.
    
    Example:
    {
        "indicator": "vmanchu_cipher_b",
        "symbol": "SUI/USD",
        "timeframe": "5m",
        "signal_type": "GREEN_CIRCLE",
        "action": "BUY"
    }
    """
    try:
        # This endpoint only works in development mode
        if os.getenv("FLASK_ENV") != "development":
            return jsonify({"status": "error", "message": "This endpoint is only available in development mode"}), 403
            
        # Get the request data
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
            
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Empty JSON request"}), 400
        
        # Log that we're simulating a webhook
        logger.info(f"Simulating webhook with data: {json.dumps(data)}")
        
        # Add timestamp if not provided
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
            
        # Forward to the webhook endpoint
        response = tradingview_webhook()
        
        return response
            
    except Exception as e:
        logger.error(f"Error simulating webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Set up Flask app
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t", "yes")
    port = int(os.getenv("WEBHOOK_PORT", 5001))
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("alerts", exist_ok=True)
    
    # Print startup message
    print("\n==================================================")
    print("TradingView Webhook Server")
    print("==================================================")
    print(f"Listening on port: {port}")
    print(f"Debug mode: {'Enabled' if debug_mode else 'Disabled'}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    
    # Check if ngrok is enabled
    use_ngrok = os.getenv("USE_NGROK", "False").lower() in ("true", "1", "t", "yes")
    if use_ngrok:
        try:
            import subprocess
            import time
            import json
            
            # Check if ngrok is installed
            try:
                # Try to start ngrok
                ngrok_cmd = ["ngrok", "http", str(port)]
                
                # Add domain if specified
                ngrok_domain = os.getenv("NGROK_DOMAIN", "")
                if ngrok_domain:
                    ngrok_cmd.extend(["--domain", ngrok_domain])
                
                # Start ngrok in the background
                subprocess.Popen(ngrok_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for ngrok to start
                time.sleep(3)
                
                # Get the public URL from the ngrok API
                try:
                    ngrok_api = requests.get("http://localhost:4040/api/tunnels").json()
                    public_url = ngrok_api["tunnels"][0]["public_url"]
                    print(f"Ngrok tunnel established: {public_url}")
                    print(f"Use this URL in your TradingView alerts: {public_url}/webhook")
                except Exception as e:
                    print(f"Ngrok started, but couldn't get public URL: {e}")
                    print("Check http://localhost:4040 for the ngrok dashboard")
            except Exception as e:
                print(f"Error starting ngrok: {e}")
                print("Continuing without ngrok...")
        except ImportError:
            print("Ngrok Python package not installed. Continuing without ngrok...")
    
    print("==================================================\n")
    
    # Start the Flask app
    app.run(host=host, port=port, debug=debug_mode) 
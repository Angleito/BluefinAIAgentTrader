#!/usr/bin/env python3
"""
Simple webhook server for PerplexityTrader.
This is a simplified version that avoids the Flask/Werkzeug compatibility issues.
"""

import os
import json
import logging
import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'webhook.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('webhook')

# Create Flask app
app = Flask(__name__)

# Get environment variables
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 5004))
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '0.0.0.0')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the webhook service."""
    return jsonify({"status": "healthy", "service": "webhook"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive webhook alerts from TradingView."""
    try:
        # Get the request data
        data = request.json
        
        # Log the alert data
        logger.info(f"Received webhook alert: {json.dumps(data)}")
        
        # Save the alert to a file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        alert_file = os.path.join('logs', f'alert_{timestamp}.json')
        
        with open(alert_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return jsonify({"status": "success", "message": "Alert received and processed"}), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get the status of the webhook service."""
    return jsonify({
        "service": "webhook",
        "status": "running",
        "uptime": "since startup",
        "version": "1.0.0"
    }), 200

if __name__ == '__main__':
    # Create the logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logger.info(f"Starting webhook service on {WEBHOOK_HOST}:{WEBHOOK_PORT}")
    app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT) 
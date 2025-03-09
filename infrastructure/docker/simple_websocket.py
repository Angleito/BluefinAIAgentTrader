#!/usr/bin/env python3
"""
Simple websocket server for PerplexityTrader.
This is a simplified version that avoids the Flask/Werkzeug compatibility issues.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'websocket.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('websocket')

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'perplexity-trader-secret'

# Get environment variables
WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', 5008))
WEBSOCKET_HOST = os.getenv('WEBSOCKET_HOST', '0.0.0.0')

# Store active clients
clients = []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the websocket service."""
    return jsonify({"status": "healthy", "service": "websocket"}), 200

@app.route('/status', methods=['GET'])
def status():
    """Get the status of the websocket service."""
    return jsonify({
        "service": "websocket",
        "status": "running",
        "uptime": "since startup",
        "version": "1.0.0",
        "active_clients": len(clients)
    }), 200

@app.route('/ws/connect', methods=['POST'])
def handle_connect():
    """Simulate client connection."""
    client_id = request.json.get('client_id', f'client_{len(clients) + 1}')
    clients.append(client_id)
    logger.info(f"Client connected: {client_id}. Total clients: {len(clients)}")
    return jsonify({
        "status": "connected",
        "client_id": client_id,
        "message": "Connected to PerplexityTrader WebSocket Service"
    }), 200

@app.route('/ws/disconnect', methods=['POST'])
def handle_disconnect():
    """Simulate client disconnection."""
    client_id = request.json.get('client_id')
    if client_id in clients:
        clients.remove(client_id)
        logger.info(f"Client disconnected: {client_id}. Total clients: {len(clients)}")
        return jsonify({
            "status": "disconnected",
            "client_id": client_id
        }), 200
    return jsonify({
        "status": "error",
        "message": "Client not found"
    }), 404

@app.route('/ws/subscribe', methods=['POST'])
def handle_subscribe():
    """Simulate subscription to a topic."""
    client_id = request.json.get('client_id')
    topic = request.json.get('topic', 'unknown')
    
    if client_id not in clients:
        return jsonify({
            "status": "error",
            "message": "Client not connected"
        }), 404
    
    logger.info(f"Client {client_id} subscribed to {topic}")
    return jsonify({
        "status": "subscribed",
        "client_id": client_id,
        "topic": topic
    }), 200

@app.route('/ws/send', methods=['POST'])
def handle_message():
    """Simulate sending a message."""
    client_id = request.json.get('client_id')
    message = request.json.get('message', {})
    
    if client_id not in clients:
        return jsonify({
            "status": "error",
            "message": "Client not connected"
        }), 404
    
    logger.info(f"Received message from {client_id}: {message}")
    return jsonify({
        "status": "sent",
        "client_id": client_id,
        "message": message
    }), 200

@app.route('/ws/broadcast', methods=['POST'])
def broadcast_update():
    """Simulate broadcasting an update to all connected clients."""
    topic = request.json.get('topic')
    data = request.json.get('data', {})
    
    message = {
        'topic': topic,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    logger.info(f"Broadcasting {topic} update to {len(clients)} clients")
    return jsonify({
        "status": "broadcasted",
        "topic": topic,
        "clients": len(clients),
        "message": message
    }), 200

if __name__ == '__main__':
    # Create the logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logger.info(f"Starting websocket service on {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    app.run(host=WEBSOCKET_HOST, port=WEBSOCKET_PORT) 
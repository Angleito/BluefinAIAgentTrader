#!/usr/bin/env python
"""
WebSocket Server for PerplexityTrader

This server handles real-time updates between the backend and frontend.
"""

import os
import json
import logging
import time
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit, request
from flask_cors import CORS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/websocket_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("websocket_server")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Get port from environment variable
port = int(os.environ.get('SOCKET_PORT', 5001))

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Store connected clients
connected_clients = set()

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        status = {
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "environment": os.environ.get("FLASK_ENV", "development"),
            "connected_clients": len(connected_clients)
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected")
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle client subscription to a channel"""
    channel = data.get('channel')
    if channel:
        logger.info(f"Client subscribed to channel: {channel}")
        emit('subscription_status', {'status': 'subscribed', 'channel': channel})

def broadcast_update(event_type, data):
    """Broadcast an update to all connected clients"""
    socketio.emit(event_type, data)
    logger.info(f"Broadcasted {event_type} event to {len(connected_clients)} clients")

if __name__ == '__main__':
    logger.info(f"Starting WebSocket server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False) 
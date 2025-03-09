#!/usr/bin/env python3
"""
Simple agent server for PerplexityTrader.
This is a simplified version that avoids the Flask/Werkzeug compatibility issues.
"""

import os
import json
import logging
import random
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'agent.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('agent')

# Create Flask app
app = Flask(__name__)

# Get environment variables
AGENT_PORT = int(os.getenv('AGENT_PORT', 5003))
AGENT_HOST = os.getenv('AGENT_HOST', '0.0.0.0')
MOCK_TRADING = os.getenv('MOCK_TRADING', 'true').lower() == 'true'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the agent service."""
    return jsonify({"status": "healthy", "service": "agent"}), 200

@app.route('/api/status', methods=['GET'])
def status():
    """Get the status of the agent service."""
    return jsonify({
        "service": "agent",
        "status": "running",
        "uptime": "since startup",
        "version": "1.0.0",
        "mock_trading": MOCK_TRADING
    }), 200

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze market data and provide trading recommendations."""
    try:
        # Get the request data
        data = request.json
        
        # Log the request data
        logger.info(f"Received analysis request: {json.dumps(data)}")
        
        # Create a directory for analysis results
        os.makedirs('analysis', exist_ok=True)
        
        # Mock analysis result
        result = {
            "timestamp": datetime.now().isoformat(),
            "symbol": data.get("symbol", "BTC-USDT"),
            "timeframe": data.get("timeframe", "1h"),
            "analysis": {
                "trend": random.choice(["bullish", "bearish", "neutral"]),
                "strength": random.randint(1, 10),
                "support": random.randint(25000, 30000),
                "resistance": random.randint(30000, 35000),
                "rsi": random.randint(0, 100),
                "macd": {
                    "signal": random.choice(["buy", "sell", "hold"]),
                    "histogram": random.uniform(-2, 2)
                }
            },
            "recommendation": {
                "action": random.choice(["buy", "sell", "hold"]),
                "confidence": random.uniform(0.1, 1.0),
                "target_price": random.randint(25000, 35000),
                "stop_loss": random.randint(25000, 35000)
            }
        }
        
        # Save the analysis result to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = os.path.join('analysis', f'analysis_{timestamp}.json')
        
        with open(analysis_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error processing analysis request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/trade', methods=['POST'])
def trade():
    """Execute a trade based on the provided parameters."""
    try:
        # Get the request data
        data = request.json
        
        # Log the trade request
        logger.info(f"Received trade request: {json.dumps(data)}")
        
        # Import Bluefin client only when needed
        from bluefin_client_python_sui import BluefinClient
        
        if MOCK_TRADING:
            # Mock trade execution
            trade_result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "order_id": f"mock-{random.randint(10000, 99999)}",
                "symbol": data.get("symbol", "SUI-PERP"),
                "side": data.get("side", "SHORT"),
                "type": data.get("type", "MARKET"),
                "quantity": data.get("quantity", 1),
                "price": data.get("price", 3.0),
                "executed_price": data.get("price", 3.0) * random.uniform(0.995, 1.005),
                "message": "Mock trade executed successfully"
            }
        else:
            # Real trading using Bluefin client
            client = BluefinClient(
                network=os.getenv('BLUEFIN_NETWORK', 'SUI_PROD'),
                private_key=os.getenv('BLUEFIN_PRIVATE_KEY'),
                api_key=os.getenv('BLUEFIN_API_KEY'),
                api_secret=os.getenv('BLUEFIN_API_SECRET')
            )
            
            # Prepare trade parameters
            symbol = data.get("symbol", "SUI-PERP")
            side = data.get("side", "SHORT")
            order_type = data.get("type", "MARKET")
            quantity = data.get("quantity", 1)
            price = data.get("price", None)
            
            # Execute the trade
            try:
                if order_type == "MARKET":
                    trade_result = client.place_market_order(
                        symbol=symbol,
                        side=side,
                        quantity=quantity
                    )
                elif order_type == "LIMIT":
                    trade_result = client.place_limit_order(
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=price
                    )
                else:
                    raise ValueError(f"Unsupported order type: {order_type}")
                
                # Format the trade result
                trade_result = {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "order_id": trade_result.get('order_id', 'N/A'),
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "price": price,
                    "message": "Trade executed successfully"
                }
            except Exception as e:
                logger.error(f"Trade execution error: {str(e)}")
                return jsonify({
                    "status": "error", 
                    "message": f"Trade execution failed: {str(e)}"
                }), 500
        
        return jsonify(trade_result), 200
    
    except Exception as e:
        logger.error(f"Error processing trade request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Create the logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logger.info(f"Starting agent service on {AGENT_HOST}:{AGENT_PORT}")
    logger.info(f"Mock trading mode: {MOCK_TRADING}")
    app.run(host=AGENT_HOST, port=AGENT_PORT) 
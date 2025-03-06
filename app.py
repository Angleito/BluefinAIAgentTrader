from flask import Flask, jsonify, request, render_template
import os
import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('perplexitytrader-web')

# Initialize Flask app
app = Flask(__name__)

# Default trading parameters (same as in agent.py)
DEFAULT_PARAMS = {
    "symbol": "SUI/USD",
    "timeframe": "5m", 
    "leverage": 7,
    "stop_loss_pct": 0.15,
    "position_size_pct": 0.05,
    "max_positions": 3
}

# Global state to store current trading parameters and status
trading_state = {
    "active": False,
    "current_parameters": DEFAULT_PARAMS.copy(),
    "open_positions": [],
    "last_analysis": None
}

@app.route('/')
def index():
    """Render the main dashboard page"""
    # In a full implementation, you'd render an HTML template
    return jsonify({
        "status": "PerplexityTrader API running",
        "endpoints": [
            "/status - Get current trading status",
            "/start - Start the trading bot",
            "/stop - Stop the trading bot",
            "/configure - Configure trading parameters",
            "/positions - Get open positions",
            "/analysis - Get latest analysis result"
        ]
    })

@app.route('/status', methods=['GET'])
def get_status():
    """Get the current status of the trading bot"""
    return jsonify({
        "active": trading_state["active"],
        "current_parameters": trading_state["current_parameters"],
        "open_positions_count": len(trading_state["open_positions"]),
        "last_analysis_time": trading_state["last_analysis"]["timestamp"] if trading_state["last_analysis"] else None
    })

@app.route('/start', methods=['POST'])
def start_trading():
    """Start the trading bot with current parameters"""
    if trading_state["active"]:
        return jsonify({"status": "error", "message": "Trading bot is already running"}), 400
    
    # In a full implementation, you would start the trading agent in a separate process
    # For now, we'll just update the state
    trading_state["active"] = True
    logger.info(f"Started trading with parameters: {trading_state['current_parameters']}")
    
    return jsonify({"status": "success", "message": "Trading bot started", "parameters": trading_state["current_parameters"]})

@app.route('/stop', methods=['POST'])
def stop_trading():
    """Stop the trading bot"""
    if not trading_state["active"]:
        return jsonify({"status": "error", "message": "Trading bot is not running"}), 400
    
    # In a full implementation, you would stop the trading agent process
    trading_state["active"] = False
    logger.info("Stopped trading")
    
    return jsonify({"status": "success", "message": "Trading bot stopped"})

@app.route('/configure', methods=['POST'])
def configure():
    """Configure trading parameters"""
    try:
        new_params = request.json
        
        # Validate required parameters
        required_params = ["symbol", "timeframe", "leverage", "stop_loss_pct", "position_size_pct", "max_positions"]
        for param in required_params:
            if param not in new_params:
                return jsonify({"status": "error", "message": f"Missing required parameter: {param}"}), 400
        
        # Update trading parameters
        trading_state["current_parameters"] = new_params
        logger.info(f"Updated trading parameters: {new_params}")
        
        return jsonify({"status": "success", "message": "Trading parameters updated", "parameters": new_params})
    except Exception as e:
        logger.error(f"Error configuring trading parameters: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/positions', methods=['GET'])
def get_positions():
    """Get open positions"""
    return jsonify({"positions": trading_state["open_positions"]})

@app.route('/analysis', methods=['GET'])
def get_analysis():
    """Get the latest analysis result"""
    if not trading_state["last_analysis"]:
        return jsonify({"status": "error", "message": "No analysis available"}), 404
    
    return jsonify({"analysis": trading_state["last_analysis"]})

# Mock endpoint to simulate receiving an analysis result
@app.route('/mock_analysis', methods=['POST'])
def mock_analysis():
    """Mock endpoint to simulate receiving an analysis result (for testing)"""
    try:
        analysis = request.json
        trading_state["last_analysis"] = {
            "timestamp": datetime.now().isoformat(),
            "result": analysis
        }
        logger.info(f"Received mock analysis: {analysis}")
        
        return jsonify({"status": "success", "message": "Analysis received"})
    except Exception as e:
        logger.error(f"Error processing mock analysis: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # In production, use Gunicorn instead of the Flask development server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 
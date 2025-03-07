from flask import Flask, jsonify, request, render_template
import os
import logging
from datetime import datetime, timedelta
import json
from anthropic import Client
import subprocess
import threading
from core.config import TRADING_PARAMS, RISK_PARAMS, AI_PARAMS
import jwt
from functools import wraps
from flask_socketio import SocketIO

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/webhook_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook_server")

# Initialize Flask app
app = Flask(__name__)

# Initialize Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Claude client
claude_client = None
try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key and api_key != "your_api_key_here":
        claude_client = Client(api_key=api_key)
        logger.info("Claude client initialized")
    else:
        logger.warning("Claude API key not found or not set")
except Exception as e:
    logger.error(f"Failed to initialize Claude client: {e}")

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

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(days=1)

def generate_token(user_id):
    """Generate a new JWT token for the given user_id"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
        if not token:
            return jsonify({'status': 'error', 'message': 'Authentication token is missing'}), 401
            
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            # Store user_id in g instead of request
            from flask import g
            g.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Authentication token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Invalid authentication token'}), 401
            
        return f(*args, **kwargs)
    return decorated

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
            "/analysis - Get latest analysis result",
            "/api/process_alert - Process TradingView alerts"
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
@token_required
def configure():
    """Configure trading parameters"""
    try:
        new_params = request.json
        
        # Validate required parameters
        required_params = ["symbol", "timeframe", "leverage", "stop_loss_pct", "position_size_pct", "max_positions"]
        for param in required_params:
            if param not in new_params:
                return jsonify({"status": "error", "message": f"Missing required parameter: {param}"}), 400
        
        # Update in-memory trading parameters
        trading_state["current_parameters"] = new_params
        logger.info(f"Updated trading parameters: {new_params}")
        
        # Save updated parameters to config file
        config_dir = "config"
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "config.json"), "w") as f:
            json.dump({
                "TRADING_PARAMS": new_params,
                "RISK_PARAMS": RISK_PARAMS,
                "AI_PARAMS": AI_PARAMS
            }, f, indent=2)
        
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

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle webhooks from TradingView or other sources
    Expected payload format:
    {
        "ticker": "SUI/USD",
        "price": "3.22",
        "alert_type": "buy_signal",
        "timeframe": "5m"
    }
    """
    try:
        data = request.json
        logger.info(f"Received webhook: {json.dumps(data)}")
        
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        # Validate required fields
        required_fields = ["ticker"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
        # Process the webhook data and trigger the trading agent
        ticker = data.get("ticker")
        timeframe = data.get("timeframe", "5m")
        
        # Save webhook data to file for the agent to process
        os.makedirs("analysis", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis/webhook_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(data, f)
            
        logger.info(f"Saved webhook data to {filename}")
        
        # Start the analysis in a background thread so we can return immediately
        threading.Thread(target=run_analysis, args=(ticker, timeframe)).start()
        
        return jsonify({
            "status": "success",
            "message": f"Processing trade signal for {ticker} on {timeframe} timeframe",
            "timestamp": timestamp
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/process_alert', methods=['POST'])
def process_vmanchu_alert():
    """
    Process alerts from the VuManChu Cipher B indicator
    
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
        data = request.json
        logger.info(f"Received VuManChu Cipher B alert: {json.dumps(data)}")
        
        # Validate required fields
        required_fields = ["symbol", "timeframe", "action", "indicator"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        # Verify indicator is VuManChu Cipher B
        if data.get("indicator").lower() != "vmanchu_cipher_b":
            return jsonify({"status": "error", "message": "Only VuManChu Cipher B alerts are supported by this endpoint"}), 400
            
        # Map to our existing parameters format
        symbol = data.get("symbol")
        timeframe = data.get("timeframe")
        action = data.get("action").upper()
        signal_type = data.get("signal_type", "UNKNOWN")
        
        # Save the alert to a file for reference
        os.makedirs("alerts", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"alerts/vmanchu_alert_{timestamp}_{symbol.replace('/', '_')}.json"
        
        with open(filename, "w") as f:
            json.dump(data, f)
        
        logger.info(f"Saved VuManChu alert to {filename}")
        
        # Start the analysis and trading decision process
        threading.Thread(target=process_cipher_b_signal, 
                         args=(symbol, timeframe, action, signal_type, data)).start()
        
        return jsonify({
            "status": "success",
            "message": f"Processing VuManChu Cipher B {action} signal for {symbol} on {timeframe}",
            "signal_type": signal_type,
            "timestamp": timestamp
        })
        
    except Exception as e:
        logger.error(f"Error processing VuManChu alert: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

def process_cipher_b_signal(symbol, timeframe, action, signal_type, alert_data):
    """Process a VuManChu Cipher B signal and make a trading decision"""
    try:
        # Get the trade direction (Bullish/Bearish) from the alert data or calculate it
        trade_direction = alert_data.get("trade_direction")
        if not trade_direction:
            # If trade_direction wasn't provided, determine it based on signal type and action
            if signal_type in ["GREEN_CIRCLE", "GOLD_CIRCLE", "BULL_FLAG", "BULL_DIAMOND"]:
                trade_direction = "Bullish"
            elif signal_type in ["RED_CIRCLE", "BEAR_FLAG", "BEAR_DIAMOND"]:
                trade_direction = "Bearish"
            else:
                # For ambiguous signals like PURPLE_TRIANGLE or LITTLE_CIRCLE
                # use the specified action to determine direction
                trade_direction = "Bullish" if action.upper() == "BUY" else "Bearish"
        
        logger.info(f"Processing {signal_type} signal for {symbol} on {timeframe}")
        logger.info(f"Trade direction: {trade_direction}, Action: {action}")
        
        # In a full implementation, you would call your agent with specific parameters
        # for the VuManChu Cipher B indicator
        cmd = [
            "python", "agent.py",
            "--symbol", symbol,
            "--timeframe", timeframe,
            "--action", action,
            "--signal_type", signal_type,
            "--trade_direction", trade_direction,
            "--vmanchu_mode"
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error running agent for VuManChu signal: {stderr.decode()}")
        else:
            logger.info(f"Successfully processed VuManChu {action} signal for {symbol}")
            
            # Update the last analysis information
            trading_state["last_analysis"] = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "timeframe": timeframe,
                "action": action,
                "signal_type": signal_type,
                "trade_direction": trade_direction,
                "result": "Signal processed successfully"
            }
            
    except Exception as e:
        logger.error(f"Failed to process VuManChu signal: {str(e)}", exc_info=True)

def run_analysis(ticker, timeframe):
    """Run the trading agent analysis for a specific ticker and timeframe"""
    try:
        logger.info(f"Starting analysis for {ticker} on {timeframe} timeframe")
        cmd = ["python", "agent.py", "--ticker", ticker, "--timeframe", timeframe]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error running agent: {stderr.decode()}")
        else:
            logger.info(f"Agent analysis completed successfully for {ticker}")
            
    except Exception as e:
        logger.error(f"Failed to run analysis: {str(e)}", exc_info=True)

@app.route('/test-claude', methods=['GET'])
def test_claude():
    """Test the Claude AI integration"""
    if not claude_client:
        return jsonify({
            "status": "error",
            "message": "Claude client not initialized. Check your ANTHROPIC_API_KEY."
        }), 500
    
    try:
        # Get Claude model information
        model = os.environ.get("CLAUDE_MODEL", "claude-3.7-sonnet")
        
        # Simple test message
        response = claude_client.messages.create(
            model=model,
            max_tokens=100,
            temperature=0.2,
            system="You are a helpful trading assistant.",
            messages=[
                {"role": "user", "content": "What are the key technical indicators that traders use?"}
            ]
        )
        
        # Extract response
        response_text = ""
        for content_block in response.content:
            if content_block.type == "text":
                response_text = content_block.text
                break
        
        return jsonify({
            "status": "success",
            "model": model,
            "response": response_text
        })
    except Exception as e:
        logger.error(f"Error testing Claude: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.json
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400
            
        # For demo purposes, hardcoded credentials
        # In production, you would validate against a database
        if data.get('username') == 'admin' and data.get('password') == 'password':
            token = generate_token('admin')
            return jsonify({
                'status': 'success',
                'token': token,
                'user': {
                    'id': 'admin',
                    'username': 'admin'
                }
            })
        else:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/configuration', methods=['GET'])
def get_configuration():
    """Get current configuration"""
    try:
        # Load configuration from file if it exists
        config_dir = "config"
        config_file = os.path.join(config_dir, "config.json")
        
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
        else:
            # Return default configuration from core.config
            config = {
                "TRADING_PARAMS": TRADING_PARAMS,
                "RISK_PARAMS": RISK_PARAMS,
                "AI_PARAMS": AI_PARAMS
            }
            
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

# Function to emit updates to connected clients
def emit_update(event_type, data):
    """Emit an update to all connected clients"""
    socketio.emit(event_type, data)

# Update the run code to use socketio instead of app.run
if __name__ == '__main__':
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Start the Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 
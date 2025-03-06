"""
Trading agent for Bluefin Exchange that analyzes TradingView charts and executes trades.

This script provides automated trading functionality by analyzing TradingView charts 
for the SUI/USD pair, confirming signals with Perplexity AI, and executing trades
on the Bluefin Exchange.

Requirements:
- Python 3.8+
- Required Python libraries:
  pip install python-dotenv playwright asyncio backoff
  python -m playwright install

- Either of the Bluefin client libraries:
  # For SUI integration
  pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git
  
  # OR for general v2 integration
  pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git

Environment variables:
- Set in .env file:
  # For SUI client
  BLUEFIN_PRIVATE_KEY=your_private_key_here
  BLUEFIN_NETWORK=MAINNET  # or TESTNET
  
  # For v2 client
  BLUEFIN_API_KEY=your_api_key_here
  BLUEFIN_API_SECRET=your_api_secret_here
  BLUEFIN_API_URL=optional_custom_url_here

Usage:
- Run: python agent.py
- Check config.py for configurable trading parameters

Reference:
- Bluefin API Documentation: https://bluefin-exchange.readme.io/reference/introduction
"""

import os
import sys
import time
import json
import asyncio
import random
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import backoff
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from typing import Dict, List, Optional, Union, Any, TypeVar, Type, cast
import requests
import base64
import aiohttp
from anthropic import Client
import re
import tempfile

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/agent.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bluefin_agent")

# Try to import configuration, with fallbacks if not available
try:
    from config import TRADING_PARAMS, RISK_PARAMS, AI_PARAMS, CLAUDE_CONFIG
except ImportError:
    logger.warning("Could not import configuration from config.py, using defaults")
    
    # Default trading parameters
    TRADING_PARAMS = {
        "chart_symbol": "BTCUSDT",
        "timeframe": "1h",
        "candle_type": "Heikin Ashi",
        "indicators": ["MACD", "RSI", "Bollinger Bands"],
        "min_confidence": 0.7,
        "analysis_interval_seconds": 300,
        "max_position_size_usd": 1000,
        "leverage": 5,
        "trading_symbol": "BTC-PERP",
        "stop_loss_percentage": 0.02,
        "take_profit_multiplier": 2
    }
    
    # Default risk parameters
    RISK_PARAMS = {
        "max_risk_per_trade": 0.02,  # 2% of account balance
        "max_open_positions": 3,
        "max_daily_loss": 0.05,  # 5% of account balance
        "min_risk_reward_ratio": 2.0
    }
    
    # Default AI parameters
    AI_PARAMS = {
        "use_perplexity": True,
        "use_claude": True,
        "perplexity_confidence_threshold": 0.7,
        "claude_confidence_threshold": 0.7,
        "confidence_concordance_required": True
    }

# Define default enums for order types and sides
class ORDER_SIDE_ENUM:
    BUY = "BUY"
    SELL = "SELL"

class ORDER_TYPE_ENUM:
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_MARKET = "STOP_MARKET"

# Initialize with default enums
ORDER_SIDE = ORDER_SIDE_ENUM
ORDER_TYPE = ORDER_TYPE_ENUM

# Type definitions to help with linting
# Use Any instead of TypeVar for better compatibility with linter
BluefinClientType = Any
NetworksType = Any
OrderSignatureRequestType = Any

# Create a class that can be used as a type hint for BluefinClient
class BaseBluefinClient:
    async def close_position(self, position_id): pass
    async def get_account_equity(self): pass
    async def create_order(self, **kwargs): pass

# Now set BluefinClient to this base class for type checking
BLUEFIN_CLIENT_SUI_AVAILABLE = False
BLUEFIN_V2_CLIENT_AVAILABLE = False
BluefinClient = BaseBluefinClient

# Set up variables for Bluefin clients
Networks = None
OrderSignatureRequest = None
NETWORKS = {
    "testnet": "testnet",
    "mainnet": "mainnet"
}

# Create Networks mock class for the mock BluefinClient
class MockNetworks:
    """Mock networks for the MockBluefinClient"""
    MAINNET = "mainnet"
    TESTNET = "testnet"

# Set up Networks
Networks = MockNetworks()

# Update BluefinClient variable definition
BluefinClient = None  # Will be set to either the real client or MockBluefinClient

# Update the mock BluefinClient to handle missing methods
class MockBluefinClient:
    """Mock implementation of BluefinClient for simulation mode"""
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        logger.info("Using MockBluefinClient for simulation")
    
    async def close_position(self, position_id):
        logger.info(f"[SIMULATION] Closing position {position_id}")
        return {"status": "success", "position_id": position_id}
    
    async def get_account_equity(self):
        logger.info("[SIMULATION] Getting account equity")
        return 10000.0  # Return a mock equity value
    
    async def create_order(self, symbol, side, size, **kwargs):
        logger.info(f"[SIMULATION] Creating {side} order for {size} {symbol}")
        return {
            "id": f"sim_{get_timestamp()}",
            "symbol": symbol,
            "side": side,
            "size": size,
            "status": "filled"
        }

# Try to import SUI client first
try:
    # Disable linter warnings for imports that might not be available
    # pylint: disable=import-error
    # type: ignore
    # These imports may fail if the library is not installed, but the code handles this gracefully
    # fmt: off
    from bluefin_client_sui import (  # type: ignore # noqa
        BluefinClient as SUIBluefinClient,
        Networks as SUINetworks,
        ORDER_SIDE as SUI_ORDER_SIDE,
        ORDER_TYPE as SUI_ORDER_TYPE,
        OrderSignatureRequest as SuiOrderSignatureRequest
    )
    # fmt: on
    
    BluefinClient = SUIBluefinClient
    Networks = SUINetworks
    ORDER_SIDE = SUI_ORDER_SIDE
    ORDER_TYPE = SUI_ORDER_TYPE
    OrderSignatureRequest = SuiOrderSignatureRequest
    BLUEFIN_CLIENT_SUI_AVAILABLE = True
    logger.info("Successfully imported Bluefin SUI client")
except ImportError:
    logger.warning("Bluefin SUI client not available, will try v2 client")
    # Try to import v2 client as fallback
    try:
        from bluefin.v2.client import BluefinClient as V2BluefinClient
        from bluefin.v2.types import OrderSignatureRequest as V2OrderSignatureRequest
        # Assign the imported classes to our variables
        BluefinClient = V2BluefinClient
        OrderSignatureRequest = V2OrderSignatureRequest
        BLUEFIN_V2_CLIENT_AVAILABLE = True
        logger.info("Successfully imported Bluefin v2 client")
    except ImportError:
        logger.warning("Bluefin v2 client not available")
        logger.warning("Running in simulation mode without actual trading capabilities")

# Warn if no Bluefin client libraries are available
if not BLUEFIN_CLIENT_SUI_AVAILABLE and not BLUEFIN_V2_CLIENT_AVAILABLE:
    print("WARNING: No Bluefin client libraries found. Using mock implementation.")
    print("Please install one of the following:")
    print("   pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
    print("   pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git")

# Define mock client for testing if no libraries are available
if BluefinClient is None:
    class BluefinClient:
        def __init__(self, *args, **kwargs):
            self.address = "0xmock_address"
            self.network = kwargs.get('network', 'testnet')
            self.api_key = kwargs.get('api_key', 'mock_api_key')
            self.api = self.MockAPI()
        
        class MockAPI:
            async def close_session(self):
                print("Mock: Closing session")
                
        async def init(self, *args, **kwargs):
            print("Mock: Initializing client")
            return self
            
        def get_public_address(self):
            return self.address
            
        async def connect(self):
            print("Mock: Connecting to Bluefin")
            return True
            
        async def disconnect(self):
            print("Mock: Disconnecting from Bluefin")
            return True
            
        async def get_user_account_data(self):
            print("Mock: Getting user account data")
            return {"balance": 1000.0}
            
        async def get_user_margin(self):
            print("Mock: Getting user margin")
            return {"available": 800.0}
            
        async def get_user_positions(self):
            print("Mock: Getting user positions")
            return []
            
        async def get_user_leverage(self, symbol):
            print(f"Mock: Getting user leverage for {symbol}")
            return 5
            
        def create_signed_order(self, signature_request):
            print("Mock: Creating signed order")
            return {"signature": "0xmock_signature"}
            
        async def post_signed_order(self, signed_order):
            print("Mock: Posting signed order")
            return {"orderId": "mock_order_id"}
            
        async def get_account_info(self):
            print("Mock: Getting account info")
            return {
                "address": self.address,
                "network": self.network,
                "balance": 1000.0,
                "available_margin": 800.0,
                "positions": []
            }
            
        async def place_order(self, **kwargs):
            print(f"Mock: Placing {kwargs.get('side')} order")
            return {"orderId": "mock_order_id"}

# Define mock OrderSignatureRequest class that will be used as a fallback
class MockOrderSignatureRequest:
    def __init__(self, *args, **kwargs):
        self.symbol = kwargs.get('symbol', 'SUI-PERP')
        self.price = kwargs.get('price', 1.0)
        self.quantity = kwargs.get('quantity', 1.0)
        self.side = kwargs.get('side', ORDER_SIDE.BUY)
        self.type = kwargs.get('type', ORDER_TYPE.MARKET)
        self.leverage = kwargs.get('leverage', 5)
        self.post_only = kwargs.get('post_only', False)
        self.reduce_only = kwargs.get('reduce_only', False)
        self.time_in_force = kwargs.get('time_in_force', 'GoodTillTime')
        self.expiration = kwargs.get('expiration', int(time.time()) + 604800)  # 1 week

# Use the mock class if OrderSignatureRequest is None
if OrderSignatureRequest is None:
    OrderSignatureRequest = MockOrderSignatureRequest

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"trading_log_{int(datetime.now().timestamp())}.log"),
            logging.StreamHandler()
        ]
    )

def initialize_risk_manager():
    """Initialize the risk management system."""
    logger.info("Initializing risk manager")
    # Here we would normally import and initialize a proper risk manager
    # For now, we'll just return the risk parameters
    logger.info(f"Risk parameters: {RISK_PARAMS}")
    return RISK_PARAMS

# Add a simple RiskManager class to replace references to the risk_manager module
class RiskManager:
    def __init__(self, risk_params):
        self.account_balance = risk_params.get("initial_account_balance", 1000)
        self.max_risk_per_trade = risk_params.get("risk_per_trade", 0.01)
        self.max_open_trades = risk_params.get("max_positions", 3)
        self.max_daily_drawdown = risk_params.get("max_daily_drawdown", 0.05)
        self.daily_pnl = 0
        
    def update_account_balance(self, balance):
        self.account_balance = balance
        
    def calculate_position_size(self, entry_price, stop_loss):
        risk_amount = self.account_balance * self.max_risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            return 0
        return risk_amount / price_risk
        
    def can_open_new_trade(self):
        # Check if we have too many open positions
        if self.current_positions >= self.max_open_trades:
            return False
            
        # Check if we've hit our daily drawdown limit
        if self.daily_pnl <= -self.account_balance * self.max_daily_drawdown:
            return False
            
        return True
        
    @property
    def current_positions(self):
        # This would normally check the actual positions
        # For now, just return a placeholder value
        return 0

# Initialize the risk manager
risk_manager = RiskManager(RISK_PARAMS)

# Add retry decorator for API calls
@backoff.on_exception(backoff.expo, 
                     (asyncio.TimeoutError, ConnectionError, OSError),
                     max_tries=3,
                     max_time=30)
async def get_account_info(client):
    """
    Retrieve account information and balances from Bluefin API.
    
    Note: The specific method calls and response format will depend on whether
    you're using the bluefin_client_sui library or bluefin.v2.client.
    
    For bluefin_client_sui:
    - Use client.get_user_account_data() for account data
    - Use client.get_user_margin() for margin data
    - Use client.get_user_positions() for positions
    
    For bluefin.v2.client:
    - The API structure is slightly different; refer to its documentation
    """
    try:
        # Get account data based on API
        if hasattr(client, 'get_user_account_data'):
            # bluefin_client_sui approach
            account_data = await client.get_user_account_data()
            margin_data = await client.get_user_margin()
            positions = await client.get_user_positions() or []
            
            account_info = {
                "balance": float(account_data.get("totalCollateralValue", 0)),
                "availableMargin": float(margin_data.get("availableMargin", 0)),
                "positions": positions
            }
        else:
            # Fallback for other client implementations
            account_info = await client.get_account_info()
            
        logger.info(f"Account info retrieved: balance={account_info['balance']}, "
                   f"margin={account_info['availableMargin']}, "
                   f"positions={len(account_info['positions'])}")
        
        return account_info
    except Exception as e:
        logger.error(f"Failed to retrieve account info: {e}")
        # Re-raise the exception to trigger the retry mechanism
        raise

# Default trading parameters
DEFAULT_PARAMS = {
    "symbol": "SUI/USD",
    "timeframe": "5m", 
    "leverage": 7,
    "stop_loss_pct": 0.15,
    "position_size_pct": 0.05,
    "max_positions": 3
}

# Symbol-specific parameters (can be overridden by user)
SYMBOL_PARAMS = {
    "SUI/USD": DEFAULT_PARAMS,
    "BTC/USD": {
        "symbol": "BTC/USD",
        "timeframe": "15m",
        "leverage": 10,
        "stop_loss_pct": 0.1,
        "position_size_pct": 0.03,
        "max_positions": 2
    },
    "ETH/USD": {
        "symbol": "ETH/USD", 
        "timeframe": "15m",
        "leverage": 8,
        "stop_loss_pct": 0.12,
        "position_size_pct": 0.04,
        "max_positions": 2
    }
}

# Initialize Bluefin client
client = None
if BLUEFIN_CLIENT_SUI_AVAILABLE:
    client = BluefinClient(private_key=os.getenv("BLUEFIN_PRIVATE_KEY"), network=Networks.MAINNET)
elif BLUEFIN_V2_CLIENT_AVAILABLE:
    client = BluefinClient(api_key=os.getenv("BLUEFIN_API_KEY"), api_secret=os.getenv("BLUEFIN_API_SECRET"))
else:
    logger.warning("No Bluefin client available, running in simulation mode")
    client = MockBluefinClient()

def get_timestamp():
    """Get current timestamp in YYYYMMDD_HHMMSS format"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Update the mock PerplexityClient class to match the expected interface
class MockPerplexityClient:
    """Mock implementation of PerplexityClient"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        logger.info("Using MockPerplexityClient")
    
    def analyze_chart(self, image_path, prompt):
        logger.warning("[SIMULATION] Analyzing chart with mock client")
        return {
            "analysis": "Mock analysis - This is a simulated response",
            "action": "BUY",
            "confidence": 0.75,
            "rationale": "This is a mock rationale for simulation purposes"
        }
    
    def query(self, prompt):
        logger.warning("[SIMULATION] Querying with mock client")
        return {
            "response": "Mock response - This is a simulated response to your query"
        }

# Try to import real PerplexityClient, fall back to mock if not available
try:
    from core.perplexity_client import PerplexityClient
except ImportError:
    logger.error("Could not import PerplexityClient from core.perplexity_client")
    PerplexityClient = MockPerplexityClient  # Use mock implementation

def opposite_type(order_type: str) -> str:
    """Get the opposite order type (BUY -> SELL, SELL -> BUY)"""
    return "BUY" if order_type == "SELL" else "SELL"

async def analyze_tradingview_chart(symbol, timeframe="1D"):
    """Analyze a TradingView chart using AI"""
    logger.info(f"Analyzing TradingView chart for {symbol} on {timeframe} timeframe")
    
    # Create temporary directory for screenshot
    with tempfile.TemporaryDirectory() as tmpdir:
        screenshot_path = os.path.join(tmpdir, f"{symbol}_{timeframe}_chart.png")
        
        try:
            # Setup Playwright
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to TradingView
                tradingview_url = f"https://www.tradingview.com/chart/?symbol={symbol}&interval={timeframe}"
                logger.info(f"Navigating to {tradingview_url}")
                await page.goto(tradingview_url, timeout=60000)
                
                # Wait for chart to load
                logger.info("Waiting for chart to load")
                await page.wait_for_selector(".chart-markup-table", timeout=30000)
                
                # Additional wait for chart elements to render
                await asyncio.sleep(5)
                
                # Take screenshot of chart
                logger.info(f"Taking screenshot of {symbol} chart")
                chart_element = await page.query_selector(".chart-markup-table")
                if chart_element:
                    await chart_element.screenshot(path=screenshot_path)
                else:
                    logger.error("Could not find chart element for screenshot")
                    return None
                
                # Close browser
                await browser.close()
                
            # First, try to analyze chart with Claude 3.7 Sonnet
            logger.info(f"Attempting chart analysis with Claude 3.7 Sonnet for {symbol}")
            claude_analysis = await analyze_chart_with_claude(screenshot_path, symbol)
            
            if claude_analysis and "error" not in claude_analysis:
                logger.info(f"Chart analysis with Claude successful for {symbol}")
                return claude_analysis
            else:
                logger.warning(f"Chart analysis with Claude failed for {symbol}, falling back to Perplexity")
            
            # If Claude fails, fall back to Perplexity with sonar-pro model  
            logger.info(f"Using Perplexity sonar-pro to analyze {symbol} chart")
            perplexity_analysis = analyze_chart_with_perplexity(screenshot_path, symbol)
            
            if not perplexity_analysis:
                logger.error("Failed to get Perplexity analysis")
                return None
                
            # Extract trading decision from Perplexity analysis
            trading_recommendation = parse_perplexity_analysis(perplexity_analysis, symbol)
            
            # If we have a trading signal, get confirmation from Perplexity
            if trading_recommendation.get("recommendation", {}).get("action") != "NONE":
                # Get confirmation from Perplexity
                confirmation = await get_perplexity_confirmation(symbol, trading_recommendation["recommendation"]["action"])
                trading_recommendation["confirmation"] = confirmation
                
                if confirmation:
                    logger.info(f"Perplexity confirmed the {trading_recommendation['recommendation']['action']} signal for {symbol}")
                else:
                    logger.info(f"Perplexity rejected the {trading_recommendation['recommendation']['action']} signal for {symbol}")
                    # Reset action to NONE if not confirmed
                    trading_recommendation["recommendation"]["action"] = "NONE"
                    trading_recommendation["recommendation"]["confidence"] = 0
            
            return trading_recommendation
                
        except Exception as e:
            logger.error(f"Error analyzing TradingView chart: {e}", exc_info=True)
            return None

async def get_perplexity_confirmation(symbol: str, position_type: str) -> bool:
    """Get trade confirmation from Perplexity API."""
    # Get API key from environment
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("Perplexity API key not found in environment variables")
        return False
    
    prompt = f"Would you recommend a {position_type} trade on {symbol} based on current market conditions? Answer with YES or NO at the beginning of your response, followed by your reasoning."
    
    # Construct request payload
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500
    }
    
    # Setup headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Query Perplexity API
        response = requests.post("https://api.perplexity.ai/chat/completions", json=payload, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Error from Perplexity API: {response.status_code} - {response.text}")
            return False
            
        result = response.json()
        
        # Extract the response text
        response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "").lower()
        
        # Check if response is affirmative
        is_confirmed = response_text.startswith("yes")
        logger.info(f"Perplexity confirmation for {position_type} on {symbol}: {'YES' if is_confirmed else 'NO'}")
        
        return is_confirmed
        
    except Exception as e:
        logger.error(f"Error getting Perplexity confirmation: {e}")
        return False

async def manage_trade(position: Dict, chart_data: Dict):
    """Manage an open position based on chart data and Perplexity confirmation."""
    symbol = position["symbol"]
    position_type = position["side"]
    
    # Check VuManChu indicators
    # TODO: Implement actual indicator checks
    vumanchu_signal = "CLOSE"
    
    if vumanchu_signal == "CLOSE":
        # Get Perplexity confirmation
        close_confirmed = await get_perplexity_confirmation(symbol, position_type)
        
        if close_confirmed:
            # Close position
            await client.close_position(position["id"])
            
            # Open opposite position
            new_side = opposite_type(position_type)
            new_position = await open_position(symbol, new_side, position["size"])
            logger.info(f"Closed {position_type} and opened {new_side} on {symbol}")
            
            return new_position
        
    # Hold position until next check
    return position

async def open_position(symbol: str, side: str, size: float) -> Dict:
    """Open a new position with Bluefin client."""
    # Get parameters for symbol
    params = SYMBOL_PARAMS.get(symbol, DEFAULT_PARAMS)
    
    # Calculate position size
    equity = await client.get_account_equity()
    position_size = params["position_size_pct"] * equity
    
    # Open position
    order = await client.create_order(
        symbol=symbol,
        side=side,
        size=position_size,
        leverage=params["leverage"],
        stop_loss_pct=params["stop_loss_pct"]
    )
    
    logger.info(f"Opened {side} of {position_size} {symbol} at {order['price']}")
    
    return order

# Initialize Claude client
try:
    claude_client = Client(
        api_key=CLAUDE_CONFIG["api_key"],
        max_retries=3  # Increased from default 2 to handle rate limits better
    )
    logger.info("Initialized Claude client with config from config.py")
except ImportError:
    # Fallback to environment variables
    claude_client = Client(os.environ["ANTHROPIC_API_KEY"], max_retries=3)
    logger.info("Initialized Claude client from environment variables")
except Exception as e:
    logger.error(f"Failed to initialize Claude client: {e}")
    claude_client = None

def init_clients():
    """Initialize API clients for the trading agent"""
    global bluefin_client, claude_client
    
    try:
        # Initialize Bluefin client
        logger.info("Initializing Bluefin client")
        init_bluefin_client()
        
        # NOTE: Claude initialization is disabled temporarily, but kept for future use
        # Initialize Claude client
        logger.info("Initializing Claude client")
        if os.environ.get("ENABLE_CLAUDE", "false").lower() == "true":
            init_claude_client()
        else:
            logger.info("Claude API is disabled, skipping initialization")
            claude_client = None
    
    except Exception as e:
        logger.error(f"Error initializing clients: {e}", exc_info=True)
        if not bluefin_client:
            logger.warning("Failed to initialize Bluefin client")
        if not claude_client:
            logger.warning("Failed to initialize Claude client")

def init_bluefin_client():
    """Initialize the Bluefin client using environment variables"""
    global bluefin_client
    
    try:
        # Check for API key in environment variables
        if "BLUEFIN_API_KEY" in os.environ and "BLUEFIN_API_SECRET" in os.environ:
            api_key = os.environ["BLUEFIN_API_KEY"]
            api_secret = os.environ["BLUEFIN_API_SECRET"]
            bluefin_client = BluefinClient(api_key, api_secret)
        else:
            logger.warning("Bluefin API credentials not found in environment variables")
            bluefin_client = None
    except Exception as e:
        logger.error(f"Error initializing Bluefin client: {e}", exc_info=True)
        bluefin_client = None

def init_claude_client():
    """Initialize the Claude API client using environment variables"""
    global claude_client
    
    try:
        # Check for API key in environment variables
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key or api_key == "your_api_key_here":
            logger.warning("Claude API key not found or not set in environment variables")
            claude_client = None
            return
        
        # Initialize Claude client with API key
        logger.info("Initializing Claude client with Anthropic API key")
        claude_client = Client(api_key=api_key)
        
        # Log Claude rate limits from environment (for monitoring)
        requests_per_minute = os.environ.get("CLAUDE_REQUESTS_PER_MINUTE", 50)
        input_tokens_per_minute = os.environ.get("CLAUDE_INPUT_TOKENS_PER_MINUTE", 20000)
        output_tokens_per_minute = os.environ.get("CLAUDE_OUTPUT_TOKENS_PER_MINUTE", 8000)
        
        logger.info(f"Claude API rate limits: {requests_per_minute} requests/min, " 
                    f"{input_tokens_per_minute} input tokens/min, "
                    f"{output_tokens_per_minute} output tokens/min")
    except Exception as e:
        logger.error(f"Failed to initialize Claude client: {e}", exc_info=True)
        claude_client = None

def test_claude_api():
    """Test the Claude API with a simple prompt"""
    global claude_client
    
    if not claude_client:
        logger.error("Claude client not initialized")
        return False
        
    try:
        logger.info("Testing Claude API with a simple prompt")
        
        response = claude_client.messages.create(
            model=os.environ.get("CLAUDE_MODEL", "claude-3.5-haiku"),
            max_tokens=100,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": "Analyze the cryptocurrency market briefly. What are your thoughts on SUI/USD?"
                }
            ]
        )
        
        logger.info(f"Claude API test successful. Response: {response.content[0].text}")
        return True
    except Exception as e:
        logger.error(f"Error testing Claude API: {e}", exc_info=True)
        return False

async def main():
    """Main function to run the trading agent"""
    logger.info("Starting trading agent")
    
    # Initialize API clients
    init_clients()
    
    # Load trading configuration
    symbol = os.environ.get("DEFAULT_SYMBOL", "BTC/USD")
    timeframe = os.environ.get("DEFAULT_TIMEFRAME", "1h")
    
    logger.info(f"Beginning trading analysis for {symbol} on {timeframe} timeframe")
    
    try:
        # Analyze TradingView chart using Perplexity only
        chart_analysis = await analyze_tradingview_chart(symbol, timeframe)
        
        if not chart_analysis:
            logger.error("Failed to analyze chart, aborting")
            return
        
        # Log analysis results
        logger.info(f"Chart analysis results: {json.dumps(chart_analysis, indent=2)}")
        
        # Execute trade if appropriate based on analysis
        trade_result = await execute_trade_when_appropriate(chart_analysis)
        
        if trade_result:
            logger.info(f"Trade executed: {trade_result}")
        else:
            logger.info("No trade executed")
    
    except Exception as e:
        logger.error(f"Error in trading analysis: {e}", exc_info=True)
    
    logger.info("Trading agent run completed")

def capture_chart_screenshot(ticker, timeframe="1D"):
    """Capture a screenshot of the TradingView chart for the given ticker and timeframe"""
    try:
        with sync_playwright() as p:
            # Create screenshots directory if it doesn't exist
            os.makedirs("screenshots", exist_ok=True)
            
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to TradingView chart for the specified ticker
            page.goto(f"https://www.tradingview.com/chart/?symbol={ticker}")
            
            # Wait for chart to load completely
            page.wait_for_selector(".chart-container")
            
            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"screenshots/{ticker}_{timeframe}_{timestamp}.png"
            page.screenshot(path=screenshot_path)
            browser.close()
            
            return screenshot_path
    except Exception as e:
        logger.error(f"Error capturing chart screenshot: {e}")
        return None

def analyze_chart_with_perplexity(screenshot_path, ticker):
    """Analyze a chart screenshot using Perplexity AI"""
    # Get API key from environment
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        logger.error("Perplexity API key not found in environment variables")
        return None
    
    # Construct a simple text-only prompt for testing
    prompt = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": f"Analyze the current market conditions for {ticker}. Would you recommend a BUY, SELL, or HOLD position? Include your reasoning."
            }
        ],
        "max_tokens": 1000
    }
    
    # Setup headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Send to Perplexity API
    response = requests.post("https://api.perplexity.ai/chat/completions", json=prompt, headers=headers)
    
    # Process response
    if response.status_code == 200:
        analysis = response.json()
        # Debug: Print the raw response
        logger.info(f"Raw Perplexity response: {json.dumps(analysis, indent=2)}")
        return analysis
    else:
        logger.error(f"Error from Perplexity API: {response.status_code} - {response.text}")
        return None

async def analyze_chart_with_claude(screenshot_path, ticker):
    """
    Analyze a chart screenshot using Claude AI
    
    Args:
        screenshot_path: Path to the screenshot image
        ticker: Symbol being analyzed
        
    Returns:
        dict: Analysis results with trading recommendations
    """
    global claude_client
    
    if not claude_client:
        logger.error("Claude client not initialized, cannot analyze chart")
        return None
        
    try:
        # Load config settings
        try:
            from config import CLAUDE_CONFIG
            max_tokens = CLAUDE_CONFIG.get("max_tokens", 8000)
            model = CLAUDE_CONFIG.get("model", "claude-3.7-sonnet")
            temperature = CLAUDE_CONFIG.get("temperature", 0.2)
        except ImportError:
            logger.warning("Could not import CLAUDE_CONFIG, using defaults")
            max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", 8000))
            model = os.getenv("CLAUDE_MODEL", "claude-3.7-sonnet")
            temperature = float(os.getenv("CLAUDE_TEMPERATURE", 0.2))
        
        # Convert image to base64 for transmission
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Construct system prompt
        system_prompt = f"""You are an expert cryptocurrency trader and technical analyst. 
You are analyzing a trading chart for {ticker} to make trading decisions.
Analyze the chart thoroughly and provide:
1. Key technical indicators visible on the chart
2. Support and resistance levels
3. Current market trend (bullish, bearish, or neutral)
4. Trading recommendation (BUY, SELL, or HOLD) with specific entry, stop loss, and take profit levels
5. Confidence score (1-10) for your recommendation
6. Risk/reward ratio for the recommended trade

Format your analysis in a structured way with clear sections."""
        
        # Make API call to Claude
        logger.info(f"Sending chart analysis request to Claude for {ticker}")
        
        # Create message with anthropic.Client - using correct schema
        response = claude_client.messages.create(
            model="claude-3.7-sonnet",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": encoded_image
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Analyze this {ticker} chart and provide a detailed trading recommendation."
                        }
                    ]
                }
            ]
        )
        
        # Extract and return results - handling response structure correctly
        analysis_text = ""
        for content_block in response.content:
            if content_block.type == "text":
                analysis_text = content_block.text
                break
        
        # Parse the analysis to extract trading recommendation
        recommendation = parse_claude_analysis(analysis_text, ticker)
        
        logger.info(f"Claude analysis completed for {ticker}")
        return {
            "raw_analysis": analysis_text,
            "recommendation": recommendation
        }
        
    except Exception as e:
        logger.error(f"Error analyzing chart with Claude: {e}", exc_info=True)
        return None

def parse_claude_analysis(analysis_text, ticker):
    """
    Parse Claude's analysis to extract trading recommendations
    
    Args:
        analysis_text: Raw analysis text from Claude
        ticker: Symbol being analyzed
        
    Returns:
        dict: Structured trading recommendation
    """
    # Default values
    recommendation = {
        "symbol": ticker,
        "action": "NONE",  # Default to no action
        "entry_price": None,
        "stop_loss": None,
        "take_profit": None,
        "confidence": 0,  # 0-10 scale
        "risk_reward_ratio": 0,
        "trend": "NEUTRAL"
    }
    
    try:
        # Extract action (BUY/SELL/HOLD)
        if "BUY" in analysis_text.upper() or "LONG" in analysis_text.upper():
            recommendation["action"] = "BUY"
        elif "SELL" in analysis_text.upper() or "SHORT" in analysis_text.upper():
            recommendation["action"] = "SELL"
        elif "HOLD" in analysis_text.upper() or "NEUTRAL" in analysis_text.upper():
            recommendation["action"] = "NONE"
            
        # Extract trend
        if "BULLISH" in analysis_text.upper():
            recommendation["trend"] = "BULLISH"
        elif "BEARISH" in analysis_text.upper():
            recommendation["trend"] = "BEARISH"
            
        # Extract confidence score (1-10)
        confidence_match = re.search(r"confidence[:\s]+(\d+)(?:\s*\/\s*10)?", analysis_text.lower())
        if confidence_match:
            recommendation["confidence"] = int(confidence_match.group(1))
            
        # Extract price levels (using regex)
        # Entry price
        entry_match = re.search(r"entry[:\s]+[$]?(\d+(?:\.\d+)?)", analysis_text.lower())
        if entry_match:
            recommendation["entry_price"] = float(entry_match.group(1))
            
        # Stop loss
        sl_match = re.search(r"stop[:\s]*loss[:\s]+[$]?(\d+(?:\.\d+)?)", analysis_text.lower())
        if sl_match:
            recommendation["stop_loss"] = float(sl_match.group(1))
            
        # Take profit
        tp_match = re.search(r"take[:\s]*profit[:\s]+[$]?(\d+(?:\.\d+)?)", analysis_text.lower())
        if tp_match:
            recommendation["take_profit"] = float(tp_match.group(1))
            
        # Risk/reward ratio
        rr_match = re.search(r"risk[:/]reward[:\s]+(\d+(?:\.\d+)?)[:\s]*(?:to)[:\s]*(\d+(?:\.\d+)?)", analysis_text.lower())
        if rr_match:
            reward = float(rr_match.group(2))
            risk = float(rr_match.group(1))
            if risk > 0:
                recommendation["risk_reward_ratio"] = reward / risk
                
    except Exception as e:
        logger.error(f"Error parsing Claude analysis: {e}")
        
    return recommendation

async def execute_trade_when_appropriate(analysis):
    """Execute a trade if the analysis recommends it with sufficient confidence"""
    if not analysis or not isinstance(analysis, dict):
        logger.warning("Invalid analysis data, cannot execute trade")
        return
        
    trade_rec = analysis.get("recommendation", {})
    action = trade_rec.get("action", "NONE")
    confidence = trade_rec.get("confidence", 0)
    
    # Default min confidence
    min_confidence = 0.7
    
    # Get min_confidence from TRADING_PARAMS if available
    if 'TRADING_PARAMS' in globals() and isinstance(TRADING_PARAMS, dict):
        min_confidence = TRADING_PARAMS.get("min_confidence", min_confidence)
    
    if action != "NONE" and confidence >= min_confidence:
        logger.info(f"Executing {action} trade with confidence {confidence}")
        # Execute trade logic here
    else:
        logger.info(f"Not executing trade. Action: {action}, Confidence: {confidence}")

def parse_perplexity_analysis(analysis, ticker):
    """
    Parse Perplexity API response to extract trading recommendations
    
    Args:
        analysis: The raw Perplexity API response
        ticker: The symbol being analyzed
        
    Returns:
        dict: Trading recommendation with action, confidence, and other metrics
    """
    recommendation = {
        "symbol": ticker,
        "timestamp": datetime.now().isoformat(),
        "recommendation": {
            "action": "NONE",
            "confidence": 0,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "risk_reward_ratio": None,
            "timeframe": None
        }
    }
    
    try:
        if not analysis or not isinstance(analysis, dict):
            logger.warning("Invalid Perplexity analysis data")
            return recommendation
            
        # Extract the response text from Perplexity
        analysis_text = ""
        if "choices" in analysis and len(analysis["choices"]) > 0:
            message = analysis["choices"][0].get("message", {})
            if "content" in message:
                analysis_text = message["content"]
            
        if not analysis_text:
            logger.warning("No text content found in Perplexity analysis")
            return recommendation
            
        # Debug: Print the extracted text
        logger.info(f"Extracted analysis text: {analysis_text[:200]}...")
        
        # Detect recommendation type based on explicit statements
        recommendation_type = "NONE"
        confidence = 0.0
        
        # Look for explicit recommendations
        if re.search(r'recommendation.*?\b(buy|long)\b', analysis_text.lower()) or re.search(r'\b(buy|long)\b.*?recommended', analysis_text.lower()):
            recommendation_type = "BUY"
            confidence = 0.8
        elif re.search(r'recommendation.*?\b(sell|short)\b', analysis_text.lower()) or re.search(r'\b(sell|short)\b.*?recommended', analysis_text.lower()):
            recommendation_type = "SELL"
            confidence = 0.8
        elif re.search(r'recommendation.*?\b(hold|neutral|accumulate)\b', analysis_text.lower()) or re.search(r'\b(hold|neutral|accumulate)\b.*?recommended', analysis_text.lower()):
            recommendation_type = "HOLD"
            confidence = 0.7
            
        # If no explicit recommendation, use sentiment analysis
        if recommendation_type == "NONE":
            # Look for buy/sell signals
            buy_indicators = ["buy", "bullish", "uptrend", "long", "positive", "increase", "growth"]
            sell_indicators = ["sell", "bearish", "downtrend", "short", "negative", "decrease", "fall"]
            hold_indicators = ["hold", "neutral", "mixed", "cautious", "moderate", "balanced", "sideways", "accumulate"]
            
            # Count mentions of bullish/bearish terms
            buy_count = sum(1 for indicator in buy_indicators if indicator in analysis_text.lower())
            sell_count = sum(1 for indicator in sell_indicators if indicator in analysis_text.lower())
            hold_count = sum(1 for indicator in hold_indicators if indicator in analysis_text.lower())
            
            # Determine action based on sentiment
            if buy_count > sell_count + hold_count:
                recommendation_type = "BUY"
                confidence = min(0.5 + (buy_count - sell_count) * 0.05, 0.75)
            elif sell_count > buy_count + hold_count:
                recommendation_type = "SELL"
                confidence = min(0.5 + (sell_count - buy_count) * 0.05, 0.75)
            elif hold_count > 0:
                recommendation_type = "HOLD"
                confidence = min(0.5 + hold_count * 0.05, 0.7)
        
        recommendation["recommendation"]["action"] = recommendation_type
        recommendation["recommendation"]["confidence"] = confidence
            
        # Extract price targets if available
        price_match = re.search(r"(?:current|price|trading at)[:\s]+\$?(\d+(?:\.\d+)?)", analysis_text.lower())
        if price_match:
            recommendation["recommendation"]["entry_price"] = float(price_match.group(1))
            
        # Look for support levels as potential stop loss
        sl_match = re.search(r"(?:stop[- ]loss|support)[:\s]+\$?(\d+(?:\.\d+)?)", analysis_text.lower())
        if sl_match:
            recommendation["recommendation"]["stop_loss"] = float(sl_match.group(1))
            
        # Look for resistance as potential take profit
        tp_match = re.search(r"(?:take[- ]profit|target|resistance)[:\s]+\$?(\d+(?:\.\d+)?)", analysis_text.lower())
        if tp_match:
            recommendation["recommendation"]["take_profit"] = float(tp_match.group(1))
            
        # Try to extract timeframe
        if "short-term" in analysis_text.lower() or "day" in analysis_text.lower() or "hourly" in analysis_text.lower():
            recommendation["recommendation"]["timeframe"] = "short-term"
        elif "medium-term" in analysis_text.lower() or "week" in analysis_text.lower() or "monthly" in analysis_text.lower():
            recommendation["recommendation"]["timeframe"] = "medium-term"
        elif "long-term" in analysis_text.lower() or "year" in analysis_text.lower():
            recommendation["recommendation"]["timeframe"] = "long-term"
            
        # Calculate risk/reward if both stop-loss and take-profit are available
        if recommendation["recommendation"]["stop_loss"] and recommendation["recommendation"]["take_profit"] and recommendation["recommendation"]["entry_price"]:
            entry = recommendation["recommendation"]["entry_price"]
            sl = recommendation["recommendation"]["stop_loss"]
            tp = recommendation["recommendation"]["take_profit"]
            
            if recommendation["recommendation"]["action"] == "BUY":
                if entry > sl and tp > entry:  # Valid buy setup
                    risk = entry - sl
                    reward = tp - entry
                    if risk > 0:
                        recommendation["recommendation"]["risk_reward_ratio"] = reward / risk
            elif recommendation["recommendation"]["action"] == "SELL":
                if entry < sl and tp < entry:  # Valid sell setup
                    risk = sl - entry
                    reward = entry - tp
                    if risk > 0:
                        recommendation["recommendation"]["risk_reward_ratio"] = reward / risk
    
    except Exception as e:
        logger.error(f"Error parsing Perplexity analysis: {e}")
        
    return recommendation

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('bluefin_agent')
    
    # Initialize clients
    init_clients()
    
    # Run the main function (Perplexity only)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Trading agent stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
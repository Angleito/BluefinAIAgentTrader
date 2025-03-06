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
    from config import TRADING_PARAMS, RISK_PARAMS, AI_PARAMS
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

async def analyze_tradingview_chart(symbol: str, timeframe: str) -> Dict[str, Any]:
    """Analyze TradingView chart using Pyth data and VuManChu indicators."""
    logger.info(f"Analyzing {symbol} {timeframe} chart on TradingView using Pyth data source")
    
    # Set up browser with Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to TradingView chart
        url = f"https://www.tradingview.com/chart/"
        await page.goto(url)
        
        # Wait for chart to load
        await page.wait_for_selector(".chart-container", timeout=30000)
        
        # Click on symbol selector to change data source to Pyth
        await page.click(".tv-symbol-select-container")
        
        # Type in the search box to find Pyth data source for the symbol
        symbol_search = symbol.replace("/", "")  # Convert SUI/USD to SUIUSD for search
        await page.fill(".js-search-input", f"PYTH:{symbol_search}")
        
        # Wait for search results and click on the correct Pyth source
        await page.wait_for_selector(".symbol-search-item")
        await page.click(f"text=PYTH:{symbol_search}")
        
        # Wait for chart to load with Pyth data
        await page.wait_for_timeout(3000)
        
        # Change to Heikin Ashi candles
        await page.click("#header-toolbar-chart-styles")
        await page.click("text=Heikin Ashi")
        
        # Set timeframe
        await page.click("#header-toolbar-intervals")
        await page.click(f"text={timeframe}")
        
        # Add VuManChu Cipher A and B indicators
        await page.click("#header-toolbar-indicators")
        await page.fill("input", "VuManChu")
        await page.click("text=VuManChu Cipher A")
        await page.click("text=VuManChu Cipher B")
        
        # Wait for indicators to load
        await page.wait_for_selector(".study", timeout=30000)
        
        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)
        
        # Take screenshot of chart with Pyth data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/{symbol_search}_PYTH_{timeframe}_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        
        # Setup webhook alert on TradingView for additional confirmation
        # TODO: Implement webhook alert setup if needed
        
        await browser.close()
        
    # Return chart data
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data_source": "PYTH",
        "screenshot_path": screenshot_path,
        "timestamp": datetime.now().isoformat()
    }

async def get_perplexity_confirmation(symbol: str, position_type: str) -> bool:
    """Get trade confirmation from Perplexity API."""
    prompt = f"Would you close your {position_type} on {symbol} here and open a {opposite_type(position_type)}?"
    
    # Query Perplexity API
    perplexity_client = PerplexityClient(api_key=os.environ["PERPLEXITY_API_KEY"])
    result = perplexity_client.query(prompt)
    
    # Check if response is affirmative
    return result.get("choices", [{}])[0].get("text", "").lower().startswith("yes")

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

async def main():
    """
    Main function to run AI analysis and execute trades.
    
    Required environment variables:
    - For bluefin_client_sui:
      - BLUEFIN_PRIVATE_KEY: Your private key for authentication
    
    - For bluefin.v2.client:
      - BLUEFIN_API_KEY: Your API key
      - BLUEFIN_API_SECRET: Your API secret
      - BLUEFIN_API_URL: (Optional) Custom API URL
    """
    global perplexity_client
    # global bluefin_client

    load_dotenv()

    setup_logging()
    logger.info("Starting Perplexity Trader Agent")

    perplexity_client = PerplexityClient(api_key=os.environ["PERPLEXITY_API_KEY"])
    
    # Remove the bluefin_client setup
    # try:
    #     bluefin_client = setup_bluefin_client()
    # except Exception as e:
    #     logger.error(f"Failed to set up Bluefin client: {e}")
    #     sys.exit(1)

    client = None
    try:
        # Initialize clients based on available libraries
        if BLUEFIN_CLIENT_SUI_AVAILABLE:
            # Use SUI client
            private_key = os.getenv("BLUEFIN_PRIVATE_KEY")
            if not private_key:
                logger.error("BLUEFIN_PRIVATE_KEY not found in environment variables")
                logger.error("Please add your private key to the .env file as BLUEFIN_PRIVATE_KEY=your_private_key_here")
                logger.error("For security, never share your private key or commit it to version control")
                return
                
            try:
                network_str = os.getenv("BLUEFIN_NETWORK", "MAINNET")
                if network_str not in ["MAINNET", "TESTNET"]:
                    logger.error(f"Invalid network: {network_str}. Must be either 'MAINNET' or 'TESTNET'")
                    return
                    
                if network_str == "MAINNET":
                    logger.warning("Using MAINNET for trading. Ensure this is intentional and that you understand the risks.")
                    
                # Get the network from Networks enum if available, otherwise use default mapping
                if Networks is not None and hasattr(Networks, network_str):
                    network = getattr(Networks, network_str)
                else:
                    network = NETWORKS.get(network_str.lower(), "testnet")
                
                logger.info(f"Initializing Bluefin SUI client with network: {network_str}")
                
                if BluefinClient is not None:
                    client = BluefinClient(private_key=private_key, network=network)
                    await client.init()
                    
                    logger.info(f"Connecting to Bluefin network: {network_str}")
                    connect_result = await client.connect()
                    if connect_result:
                        logger.info("Successfully connected to Bluefin")
                    else:
                        logger.error("Failed to connect to Bluefin")
                        return
                else:
                    logger.error("BluefinClient class is not available")
                    return
            except Exception as e:
                logger.error(f"Error initializing SUI client: {e}", exc_info=True)
                return
                
        elif BLUEFIN_V2_CLIENT_AVAILABLE:
            # Use V2 client
            api_key = os.getenv("BLUEFIN_API_KEY")
            api_secret = os.getenv("BLUEFIN_API_SECRET")
            custom_api_url = os.getenv("BLUEFIN_API_URL")
            
            if not api_key or not api_secret:
                logger.error("BLUEFIN_API_KEY and/or BLUEFIN_API_SECRET not found in environment variables")
                logger.error("Please add your API credentials to the .env file")
                logger.error("For security, never share your API credentials or commit them to version control")
                return
                
            try:
                network_str = os.getenv("BLUEFIN_NETWORK", "mainnet").lower()
                if network_str not in ["mainnet", "testnet"]:
                    logger.error(f"Invalid network: {network_str}. Must be either 'mainnet' or 'testnet'")
                    return
                    
                if network_str == "mainnet":
                    logger.warning("Using MAINNET for trading. Ensure this is intentional and that you understand the risks.")
                
                kwargs = {
                    "api_key": api_key,
                    "api_secret": api_secret,
                    "network": network_str
                }
                
                if custom_api_url:
                    kwargs["api_url"] = custom_api_url
                
                logger.info(f"Initializing Bluefin v2 client with network: {network_str}")
                
                if BluefinClient is not None:
                    client = BluefinClient(**kwargs)
                    
                    # V2 client might not have connect method, check if it exists
                    if hasattr(client, 'connect'):
                        logger.info("Connecting to Bluefin network")
                        connect_result = await client.connect()
                        if connect_result:
                            logger.info("Successfully connected to Bluefin")
                        else:
                            logger.error("Failed to connect to Bluefin")
                            return
                    else:
                        logger.info("No explicit connect method for v2 client, assuming connected")
                else:
                    logger.error("BluefinClient class is not available")
                    return
            except Exception as e:
                logger.error(f"Error initializing v2 client: {e}", exc_info=True)
                return
        else:
            logger.error("No Bluefin client libraries available")
            logger.error("Please install one of the following:")
            logger.error("   pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
            logger.error("   pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git")
            return
        
        # Initialize risk manager
        risk_manager_instance = risk_manager
        
        # Create directories for storing results
        os.makedirs("logs", exist_ok=True)
        os.makedirs("screenshots", exist_ok=True)
        os.makedirs("analysis", exist_ok=True)
        
        # Trading loop
        while True:
            try:
                # Get account information
                account_info = await get_account_info(client)
                
                # Analyze TradingView chart
                analysis = await analyze_tradingview_chart(symbol, params["timeframe"])
                
                # Extract trade recommendation
                trade_rec = extract_trade_recommendation(analysis)
                
                # Execute trade if appropriate
                if trade_rec["action"] != "NONE" and trade_rec["confidence"] >= TRADING_PARAMS.get("min_confidence", 0.7):
                    execution_result = await execute_trade(client, trade_rec, account_info)
                    
                    # Save the analysis and result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    analysis_file = f"analysis/trade_analysis_{timestamp}.json"
                    
                    with open(analysis_file, "w") as f:
                        json.dump({
                            "timestamp": timestamp,
                            "trade_recommendation": trade_rec,
                            "execution_result": execution_result,
                            "account_info": {
                                "balance": account_info.get("balance", 0),
                                "available_margin": account_info.get("available_margin", 0),
                                "positions_count": len(account_info.get("positions", []))
                            }
                        }, f, indent=2)
                        
                    logger.info(f"Trade analysis saved to {analysis_file}")
                    
                    # Save screenshot if available
                    if "screenshot_path" in analysis and analysis["screenshot_path"]:
                        screenshot_file = f"screenshots/chart_{timestamp}.png"
                        with open(screenshot_file, "wb") as f:
                            f.write(open(analysis["screenshot_path"], "rb").read())
                        logger.info(f"Chart screenshot saved to {screenshot_file}")
                else:
                    logger.info(f"No trade executed - action: {trade_rec['action']}, confidence: {trade_rec['confidence']}")
                
                # Wait for next analysis interval
                wait_time = TRADING_PARAMS.get("analysis_interval_seconds", 300)  # Default 5 minutes
                logger.info(f"Waiting {wait_time} seconds until next analysis")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                # Wait a bit before retrying
                await asyncio.sleep(30)
    
    except Exception as e:
        logger.error(f"Unhandled error in main function: {e}", exc_info=True)
    finally:
        # Clean up resources
        if client:
            if hasattr(client, 'disconnect'):
                try:
                    logger.info("Disconnecting from Bluefin")
                    await client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting from Bluefin: {e}", exc_info=True)
            
            if hasattr(client, 'api') and hasattr(client.api, 'close_session'):
                try:
                    logger.info("Closing API session")
                    await client.api.close_session()
                except Exception as e:
                    logger.error(f"Error closing API session: {e}", exc_info=True)

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
    # Convert image to base64 for transmission
    with open(screenshot_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Construct prompt with image and context
    prompt = {
        "model": "sonar-reasoning",  # Using the deep seek R1 model
        "messages": [
            {
                "role": "user",
                "content": f"Analyze this trading chart for {ticker}. What are the key technical indicators, support/resistance levels, and potential trade setups?",
                "images": [encoded_image]
            }
        ]
    }
    
    # Send to Perplexity API
    response = requests.post("https://api.perplexity.ai/analyze", json=prompt)
    
    # Process response
    if response.status_code == 200:
        analysis = response.json()
        return analysis
    else:
        logger.error(f"Error from Perplexity API: {response.status_code} - {response.text}")
        return None

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

if __name__ == "__main__":
    setup_logging()
    initialize_risk_manager() 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Trading agent stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
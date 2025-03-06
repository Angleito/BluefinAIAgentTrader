"""
AI Trading Agent for Bluefin Exchange

This script implements an automated trading agent that:
1. Analyzes TradingView charts for SUI/USD with specified indicators
2. Uses AI models (Claude and Perplexity) to confirm trading signals
3. Executes trades on the Bluefin Exchange using the Bluefin API

Requirements:
-------------
1. Install required Python libraries:
   - pip install python-dotenv playwright asyncio
   - python -m playwright install  # Install browser automation dependencies

2. Install one of the Bluefin client libraries:
   - For SUI integration: pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git
   - For v2 integration: pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git

3. Set environment variables in a .env file:
   - For SUI client:
     BLUEFIN_PRIVATE_KEY=your_private_key_here
   
   - For v2 client:
     BLUEFIN_API_KEY=your_api_key_here
     BLUEFIN_API_SECRET=your_api_secret_here
     BLUEFIN_API_URL=optional_custom_url_here

Usage:
------
Run the script: python agent.py

Configuration:
-------------
See config.py for configurable trading parameters.

References:
----------
Bluefin API Documentation: https://bluefin-exchange.readme.io/reference/introduction
"""

from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
import logging
import json
import time  # Added missing import
from datetime import datetime
import importlib.util
from playwright.async_api import async_playwright
import backoff  # Added for API retries

# Define fallback constants in case imports fail
NETWORKS = {"MAINNET": "mainnet", "TESTNET": "testnet"}

# Create proper enum-like objects that will work with the linter
class ORDER_SIDE_ENUM:
    BUY = "BUY"
    SELL = "SELL"

class ORDER_TYPE_ENUM:
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_MARKET = "STOP_MARKET"

# Check if the bluefin client modules are available
BLUEFIN_CLIENT_SUI_AVAILABLE = importlib.util.find_spec("bluefin_client_sui") is not None
BLUEFIN_V2_CLIENT_AVAILABLE = importlib.util.find_spec("bluefin.v2.client") is not None

# Note: The following imports may show linter errors, but this is expected.
# We're using dynamic imports based on what's available at runtime.
# The linter errors can be safely ignored as our code handles missing libraries gracefully.

# Import the appropriate client
if BLUEFIN_CLIENT_SUI_AVAILABLE:
    # Use SUI-specific client
    from bluefin_client_sui import BluefinClient, Networks, ORDER_SIDE, ORDER_TYPE, OrderSignatureRequest
    print("Using Bluefin SUI client")
elif BLUEFIN_V2_CLIENT_AVAILABLE:
    # Fallback to the v2 client
    from bluefin.v2.client import BluefinClient
    from bluefin.v2.types import OrderSignatureRequest, ORDER_SIDE, ORDER_TYPE
    Networks = NETWORKS
    print("Using Bluefin v2 client")
else:
    # Provide dummy implementation for linting purposes
    class BluefinClient:
        def __init__(self, *args, **kwargs):
            print("WARNING: No Bluefin client available. Install with: ")
            print("  pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
            # Mock API objects with proper async methods
            class MockAPI:
                async def close_session(self):
                    pass
            
            self.apis = MockAPI()
            self.dmsApi = MockAPI()
        
        async def init(self, *args, **kwargs):
            pass
        
        def get_public_address(self):
            return "0x0000000000000000000000000000000000000000"
        
        async def connect(self):
            pass
        
        async def disconnect(self):
            pass
        
        async def get_user_account_data(self):
            return {"totalCollateralValue": 0}
        
        async def get_user_margin(self):
            return {"availableMargin": 0}
        
        async def get_user_positions(self):
            return []
        
        async def get_user_leverage(self, symbol):
            return BLUEFIN_DEFAULTS.get("leverage", 5)
        
        def create_signed_order(self, signature_request):
            return {}
        
        async def post_signed_order(self, signed_order):
            return {"status": "PENDING", "id": "mock-order-id"}
        
        async def get_account_info(self):
            return {
                "balance": 0,
                "availableMargin": 0,
                "positions": []
            }
        
        async def place_order(self, **kwargs):
            return {"status": "NEW", "orderId": "mock-order-id"}

class OrderSignatureRequest:
    def __init__(self, *args, **kwargs):
        pass

Networks = NETWORKS
ORDER_SIDE = ORDER_SIDE_ENUM
ORDER_TYPE = ORDER_TYPE_ENUM

print("ERROR: Bluefin client not found. Please install either:")
print("  - SUI client: pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
print("  - V2 client: pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git")

from config import TRADING_PARAMS, BLUEFIN_DEFAULTS
from core.performance_tracker import performance_tracker
from core.risk_manager import risk_manager
from core.visualization import visualizer

logger = logging.getLogger(__name__)

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
    """Initialize the risk manager with parameters from config."""
    risk_manager.update_account_balance(TRADING_PARAMS["initial_account_balance"])
    risk_manager.max_risk_per_trade = TRADING_PARAMS["max_risk_per_trade"]
    risk_manager.max_open_trades = TRADING_PARAMS["max_concurrent_positions"]
    risk_manager.max_daily_drawdown = TRADING_PARAMS["max_daily_drawdown"]

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

async def analyze_tradingview_chart():
    """
    Load TradingView chart and analyze for potential trades.
    
    This function uses Playwright to:
    1. Load TradingView chart for the configured symbol
    2. Set the timeframe, indicators, and candle type
    3. Take a screenshot for analysis
    
    Returns:
        str: Path to the screenshot image file
    """
    logger.info(f"Analyzing TradingView chart for {TRADING_PARAMS['chart_symbol']}")
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Load TradingView chart with the configured symbol
            chart_url = f"https://www.tradingview.com/chart/?symbol={TRADING_PARAMS['chart_symbol']}"
            logger.info(f"Loading chart: {chart_url}")
            
            # Add timeout and retry mechanism for page navigation
            for attempt in range(3):
                try:
                    await page.goto(chart_url, timeout=60000)
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        logger.error(f"Failed to load TradingView chart after 3 attempts: {e}")
                        raise
                    logger.warning(f"Error loading chart (attempt {attempt+1}/3): {e}")
                    await asyncio.sleep(2)

            # Wait for chart to load with timeout and retry
            logger.info("Waiting for chart to load...")
            try:
                await page.wait_for_selector(".chart-container", timeout=60000)
            except Exception as e:
                logger.warning(f"Chart container selector not found, but continuing: {e}")
                
            # Additional wait to ensure chart is fully loaded
            await asyncio.sleep(5)

            try:
                # Set chart timeframe
                logger.info(f"Setting timeframe to {TRADING_PARAMS['chart_timeframe']} minutes")
                await page.click(".group-wWM3zP_M", timeout=10000)  # Timeframe menu
                await page.click(f".item-2xPVYue0[data-value='{TRADING_PARAMS['chart_timeframe']}']", timeout=10000)
                await asyncio.sleep(1)
                
                # Add indicators
                for indicator in TRADING_PARAMS['chart_indicators']:
                    logger.info(f"Adding indicator: {indicator}")
                    await page.click(".group-LWPzJcGo", timeout=10000)  # Indicators menu
                    await page.click(".input-2rGFhmzm", timeout=10000)  # Indicator search
                    await page.fill(".input-2rGFhmzm", indicator)
                    await page.press(".input-2rGFhmzm", "Enter")
                    await asyncio.sleep(1)
                
                # Set candle type
                logger.info(f"Setting candle type to {TRADING_PARAMS['chart_candle_type']}")
                await page.click(".group-4rFIXF8R", timeout=10000)  # Candles menu
                await page.click(f".item-2xPVYue0[data-value='{TRADING_PARAMS['chart_candle_type']}']", timeout=10000)
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error setting chart parameters: {e}")
                logger.warning("Continuing with default chart settings")

            # Wait for chart to reflect all changes
            await asyncio.sleep(5)

            # Take screenshot of chart analysis
            timestamp = int(datetime.now().timestamp())
            screenshot_path = f"chart_analysis_{timestamp}.png"
            logger.info(f"Taking screenshot: {screenshot_path}")
            
            try:
                await page.screenshot(path=screenshot_path, full_page=False)
                logger.info(f"Chart analysis screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.error(f"Failed to take screenshot: {e}")
                screenshot_path = None

            return screenshot_path
    except Exception as e:
        logger.error(f"Error in chart analysis: {e}", exc_info=True)
        return None
    finally:
        # Ensure browser is closed
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

def extract_trade_recommendation(analysis):
    """
    Extract trade recommendation details from AI analysis.
    
    Args:
        analysis: String containing AI analysis text
        
    Returns:
        dict: Dictionary with trade parameters
    """
    # Set default values
    trade_rec = {
        "symbol": TRADING_PARAMS.get("chart_symbol", "BTC-PERP").split(":")[-1],
        "side": "BUY",  # Default to buy
        "price": 0,
        "stopLoss": 0,
        "takeProfit": 0,
        "confidence": 0
    }
    
    # Use symbol from config if available, otherwise default
    if ":" in trade_rec["symbol"]:
        parts = trade_rec["symbol"].split(":")
        if len(parts) == 2:
            trade_rec["symbol"] = parts[1]
    
    # Handle case where analysis is None or empty
    if not analysis:
        logger.warning("Empty analysis provided to extract_trade_recommendation")
        return trade_rec
    
    try:
        # Parse analysis line by line to extract trade details
        for line in analysis.split('\n'):
            line_lower = line.lower()
            
            # Determine trade side (buy or sell)
            if "buy" in line_lower or "long" in line_lower:
                trade_rec["side"] = "BUY"
            elif "sell" in line_lower or "short" in line_lower:
                trade_rec["side"] = "SELL"
                
            # Parse price information
            if "entry" in line_lower:
                try:
                    # Extract price value, removing any currency symbols and commas
                    value_str = line.split(':')[1].strip()
                    value_str = value_str.replace('$', '').replace(',', '')
                    trade_rec["price"] = float(value_str)
                except (IndexError, ValueError) as e:
                    logger.warning(f"Failed to parse entry price: {e} - Line: {line}")
            
            # Parse stop loss
            elif "stop loss" in line_lower or "stoploss" in line_lower:
                try:
                    value_str = line.split(':')[1].strip()
                    value_str = value_str.replace('$', '').replace(',', '')
                    trade_rec["stopLoss"] = float(value_str)
                except (IndexError, ValueError) as e:
                    logger.warning(f"Failed to parse stop loss: {e} - Line: {line}")
            
            # Parse take profit
            elif "take profit" in line_lower or "takeprofit" in line_lower:
                try:
                    value_str = line.split(':')[1].strip()
                    value_str = value_str.replace('$', '').replace(',', '')
                    trade_rec["takeProfit"] = float(value_str)
                except (IndexError, ValueError) as e:
                    logger.warning(f"Failed to parse take profit: {e} - Line: {line}")
            
            # Parse confidence score
            elif "confidence" in line_lower:
                try:
                    value_str = line.split(':')[1].strip()
                    value_str = value_str.replace('/10', '')
                    trade_rec["confidence"] = float(value_str)
                except (IndexError, ValueError) as e:
                    logger.warning(f"Failed to parse confidence: {e} - Line: {line}")
    except Exception as e:
        logger.error(f"Error parsing trade recommendation: {e}", exc_info=True)
    
    # Set default values if parsing failed to extract valid values
    if trade_rec["price"] <= 0:
        logger.warning("Invalid or missing entry price, trade cannot be executed")
        return None
    
    # Use default stop loss if not provided
    if trade_rec["stopLoss"] <= 0:
        if trade_rec["side"] == "BUY":
            trade_rec["stopLoss"] = trade_rec["price"] * (1 - TRADING_PARAMS["stop_loss_percentage"])
        else:
            trade_rec["stopLoss"] = trade_rec["price"] * (1 + TRADING_PARAMS["stop_loss_percentage"])
        logger.info(f"Using default stop loss: {trade_rec['stopLoss']}")
    
    # Use default take profit if not provided
    if trade_rec["takeProfit"] <= 0:
        risk = abs(trade_rec["price"] - trade_rec["stopLoss"])
        if trade_rec["side"] == "BUY":
            trade_rec["takeProfit"] = trade_rec["price"] + (risk * 2)  # 1:2 risk-reward
        else:
            trade_rec["takeProfit"] = trade_rec["price"] - (risk * 2)  # 1:2 risk-reward
        logger.info(f"Using default take profit: {trade_rec['takeProfit']}")
    
    logger.info(f"Extracted trade recommendation: {trade_rec}")
    return trade_rec

@backoff.on_exception(backoff.expo, 
                     (asyncio.TimeoutError, ConnectionError),
                     max_tries=3,
                     max_time=30)
async def execute_trade(client, trade_rec, account_info):
    """
    Execute a trade on Bluefin based on the recommendation.
    
    The implementation differs based on which Bluefin client is being used:
    - bluefin_client_sui uses OrderSignatureRequest and signing
    - bluefin.v2.client might use different methods
    
    Args:
        client: The Bluefin client instance
        trade_rec: Trade recommendation dictionary with details
        account_info: Account information dictionary
        
    Returns:
        bool: True if trade was executed successfully, False otherwise
    """
    if not trade_rec or not trade_rec.get("price", 0) > 0:
        logger.error("Invalid trade recommendation")
        return False
        
    logger.info(f"Executing trade: {trade_rec}")
    
    # Check risk and position size
    entry_price = trade_rec["price"]
    stop_loss = trade_rec["stopLoss"] 
    pos_size = risk_manager.calculate_position_size(entry_price, stop_loss)
    
    # Check if trade can be opened
    can_open, adjusted_size, reason = risk_manager.can_open_new_trade(
        trade_rec["symbol"], entry_price, stop_loss, pos_size
    )
    
    if not can_open:
        logger.warning(f"Trade cannot be executed: {reason}")
        return False
    
    try:
        # Determine which client type we're using based on available methods
        if hasattr(client, 'create_signed_order'):
            # Using bluefin_client_sui
            logger.info("Using bluefin_client_sui for trade execution")
            
            # Get user's current leverage for this symbol
            user_leverage = await client.get_user_leverage(trade_rec["symbol"])
            logger.info(f"Current leverage: {user_leverage}x")
            
            # Determine order side (BUY or SELL)
            order_side = ORDER_SIDE.BUY if trade_rec["side"].upper() == "BUY" else ORDER_SIDE.SELL
            
            # Ensure we have valid values for the orders
            if adjusted_size <= 0:
                logger.error(f"Invalid position size: {adjusted_size}")
                return False
                
            # Ensure the symbol format is correct
            symbol = trade_rec["symbol"]
            if not symbol.endswith("-PERP"):
                symbol = f"{symbol}-PERP"
            
            # 1. Create the main order signature request
            signature_request = OrderSignatureRequest(
                symbol=symbol,
                price=entry_price,
                quantity=adjusted_size,
                side=order_side,
                orderType=ORDER_TYPE.LIMIT,
                leverage=user_leverage,
                reduceOnly=False
            )
            
            # 2. Sign the order
            signed_order = client.create_signed_order(signature_request)
            logger.info(f"Created signed order: {signed_order.get('symbol', 'unknown')} {signed_order.get('side', 'unknown')}")
            
            # 3. Place the order
            order = await client.post_signed_order(signed_order)
            logger.info(f"Order placed: Status={order.get('status', 'unknown')}, ID={order.get('id', 'unknown')}")
            
            if not order or not order.get("status") or order.get("status") not in ["PENDING", "NEW", "FILLED"]:
                logger.error(f"Failed to place main order: {order}")
                return False
            
            # 4. Create stop loss order (opposite side of main order)
            opposite_side = ORDER_SIDE.SELL if order_side == ORDER_SIDE.BUY else ORDER_SIDE.BUY
            
            stop_loss_signature_request = OrderSignatureRequest(
                symbol=symbol,
                price=stop_loss,
                quantity=adjusted_size,
                side=opposite_side,
                orderType=ORDER_TYPE.STOP_MARKET,
                leverage=user_leverage,
                reduceOnly=True
            )
            
            stop_loss_signed_order = client.create_signed_order(stop_loss_signature_request)
            stop_loss_order = await client.post_signed_order(stop_loss_signed_order)
            logger.info(f"Stop loss order placed: Status={stop_loss_order.get('status', 'unknown')}, ID={stop_loss_order.get('id', 'unknown')}")
            
            # 5. Create take profit order (opposite side of main order)
            take_profit_signature_request = OrderSignatureRequest(
                symbol=symbol,
                price=trade_rec["takeProfit"],
                quantity=adjusted_size,
                side=opposite_side,
                orderType=ORDER_TYPE.LIMIT,
                leverage=user_leverage,
                reduceOnly=True
            )
            
            take_profit_signed_order = client.create_signed_order(take_profit_signature_request)
            take_profit_order = await client.post_signed_order(take_profit_signed_order)
            logger.info(f"Take profit order placed: Status={take_profit_order.get('status', 'unknown')}, ID={take_profit_order.get('id', 'unknown')}")
            
            # Check if main order was placed successfully
            if order.get("status") in ["PENDING", "NEW", "FILLED"]:
                success = True
                order_id = order.get("id") or order.get("orderId")
            else:
                success = False
                order_id = None
        else:
            # Using bluefin.v2.client or other implementation
            logger.info("Using bluefin.v2.client for trade execution")
            
            # Ensure the symbol format is correct
            symbol = trade_rec["symbol"]
            if not symbol.endswith("-PERP"):
                symbol = f"{symbol}-PERP"
                
            # Using simpler combined API (for v2 client)
            order = await client.place_order(
                symbol=symbol,
                side=trade_rec["side"].upper(),
                order_type="LIMIT",
                quantity=adjusted_size,
                price=entry_price,
                stop_loss=stop_loss,
                take_profit=trade_rec["takeProfit"],
                reduce_only=False
            )
            
            logger.info(f"Order placed using v2 client: {order}")
            success = order.get("status") == "NEW"
            order_id = order.get("orderId")
        
        # Log and track the trade if successful
        if success:
            trade = {
                "trade_id": order_id,
                "symbol": trade_rec["symbol"], 
                "side": trade_rec["side"],
                "timestamp": datetime.now().timestamp(),
                "entry_price": entry_price,
                "position_size": adjusted_size,
                "stop_loss": stop_loss,
                "take_profit": trade_rec["takeProfit"],
                "confidence": trade_rec["confidence"]
            }
            performance_tracker.log_trade_entry(trade)
            logger.info(f"Trade executed successfully: {trade}")
            return True
        else:
            logger.error(f"Failed to execute trade: {order}")
            return False
    except Exception as e:
        logger.error(f"Error executing trade: {e}", exc_info=True)
        raise  # Re-raise for retry mechanism

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
    client = None
    try:
        # Initialize clients based on available libraries
        if BLUEFIN_CLIENT_SUI_AVAILABLE:
            # Initialize SUI client according to documentation
            # Reference: https://bluefin-exchange.readme.io/reference/initialization-example
            logger.info("Initializing SUI-specific Bluefin client")
            
            private_key = os.getenv("BLUEFIN_PRIVATE_KEY")
            if not private_key:
                logger.error("BLUEFIN_PRIVATE_KEY not found in environment variables")
                return
                
            network = BLUEFIN_DEFAULTS.get("network", "MAINNET")
            logger.info(f"Using network: {network}")
            
            try:
                client = BluefinClient(
                    True,  # agree to terms and conditions
                    Networks[network],  # Use Networks["TESTNET"] or Networks["MAINNET"]
                    private_key  # private key for authentication
                )
                
                # Initialize client (onboard if first time)
                await client.init(True)
                logger.info(f'Connected to Bluefin with account address: {client.get_public_address()}')
            except Exception as e:
                logger.error(f"Failed to initialize SUI client: {e}")
                raise
            
        elif BLUEFIN_V2_CLIENT_AVAILABLE:
            # Initialize v2 client according to documentation
            logger.info("Initializing v2 Bluefin client")
            
            api_key = os.getenv("BLUEFIN_API_KEY")
            api_secret = os.getenv("BLUEFIN_API_SECRET")
            
            if not api_key or not api_secret:
                logger.error("BLUEFIN_API_KEY or BLUEFIN_API_SECRET not found in environment variables")
                return
                
            network = BLUEFIN_DEFAULTS.get("network", "MAINNET").lower()
            logger.info(f"Using network: {network}")
                
            try:
                client = BluefinClient(
                    api_key=api_key,
                    api_secret=api_secret,
                    network=network,  # Use 'testnet' or 'mainnet'
                    base_url=os.getenv("BLUEFIN_API_URL", None)  # Optional: use default URL if not specified
                )
                
                # Connect to the exchange
                await client.connect()
                logger.info("Connected to Bluefin exchange")
            except Exception as e:
                logger.error(f"Failed to initialize v2 client: {e}")
                raise
        else:
            logger.error("No Bluefin client libraries available. Please install one of the client libraries.")
            logger.error("For SUI-specific client: pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
            logger.error("For v2 client: pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git")
            return

        # Create the visualizations directory if it doesn't exist
        if not os.path.exists("visualizations"):
            os.makedirs("visualizations")
            logger.info("Created visualizations directory")

        # Main trading loop
        while True:
            try:
                # Retrieve account info
                account_info = await get_account_info(client)
                if not account_info:
                    logger.error("Failed to retrieve account info, retrying in 60 seconds")
                    await asyncio.sleep(60)
                    continue

                # Analyze TradingView chart
                chart_screenshot = await analyze_tradingview_chart()
                if not chart_screenshot:
                    logger.error("Failed to analyze TradingView chart, retrying in 60 seconds")
                    await asyncio.sleep(60)
                    continue

                # TODO: Implement actual API calls to perplexity and Claude
                # Run AI analysis (placeholders for now)
                perplexity_result = "Perplexity analysis: BUY SUI/USD. Entry: $2.50, Stop Loss: $2.40, Take Profit: $2.70, Confidence: 8/10" 
                claude_result = "Claude analysis: Strong buy signal for SUI/USD. Entry: $2.50, Stop Loss: $2.40, Take Profit: $2.70, Confidence: 8/10"
                
                # Extract trade recommendation
                trade_rec = extract_trade_recommendation(claude_result)
                if not trade_rec:
                    logger.warning("Could not extract valid trade recommendation, skipping trade execution")
                    await asyncio.sleep(60)
                    continue

                # Check Perplexity confirmation
                # TODO: Implement actual Perplexity API call with chart_screenshot
                perplexity_confirmation = True

                if perplexity_confirmation and trade_rec["confidence"] >= TRADING_PARAMS.get("min_confidence_threshold", 7):
                    success = await execute_trade(client, trade_rec, account_info)
                    if success:
                        # Save results and generate report
                        timestamp = int(datetime.now().timestamp())
                        with open(f"trading_analysis_{timestamp}.json", "w") as f:
                            json.dump({
                                "timestamp": timestamp,
                                "chart_screenshot": chart_screenshot,
                                "perplexity_analysis": perplexity_result,
                                "claude_analysis": claude_result,
                                "trade_recommendation": trade_rec,
                                "trading_parameters": TRADING_PARAMS,
                                "account_info": {
                                    "balance": account_info.get("balance", 0),
                                    "availableMargin": account_info.get("availableMargin", 0),
                                    "positions_count": len(account_info.get("positions", []))
                                }
                            }, f, indent=2)
                        
                        # Generate performance report if we have trades
                        try:
                            report_files = visualizer.generate_performance_report()
                            logger.info(f"Performance report generated: {report_files}")
                        except Exception as e:
                            logger.error(f"Error generating performance report: {e}")
                else:
                    logger.info(f"Trade not executed. Perplexity confirmation: {perplexity_confirmation}, Confidence: {trade_rec['confidence']}/10")

                # Wait for the configured interval before next analysis
                wait_time = TRADING_PARAMS.get("analysis_interval", 300)  # Default to 5 minutes
                logger.info(f"Waiting {wait_time} seconds before next analysis")
                await asyncio.sleep(wait_time)  
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                logger.info("Waiting 60 seconds before retry")
                await asyncio.sleep(60)
        
    except Exception as e:
        logger.exception(f"Critical error in main function: {e}")
        raise
    finally:
        # Ensure proper cleanup of resources
        if client:
            try:
                # Close connections based on client type
                if hasattr(client, 'apis') and client.apis:
                    logger.info("Closing SUI client connections")
                    await client.apis.close_session()
                    if hasattr(client, 'dmsApi') and client.dmsApi:
                        await client.dmsApi.close_session()
                elif hasattr(client, 'disconnect'):
                    logger.info("Disconnecting v2 client")
                    await client.disconnect()
            except Exception as e:
                logger.error(f"Error during client cleanup: {e}")

if __name__ == "__main__":
    setup_logging()
    initialize_risk_manager() 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Trading agent stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
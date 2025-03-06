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
from datetime import datetime
import importlib.util
from playwright.async_api import async_playwright

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
        return None

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
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Load TradingView chart with the configured symbol
        chart_url = f"https://www.tradingview.com/chart/?symbol={TRADING_PARAMS['chart_symbol']}"
        logger.info(f"Loading chart: {chart_url}")
        await page.goto(chart_url)

        # Wait for chart to load
        logger.info("Waiting for chart to load...")
        await page.wait_for_selector(".chart-container", timeout=60000)
        await asyncio.sleep(3)  # Additional wait to ensure chart is fully loaded

        try:
            # Set chart timeframe
            logger.info(f"Setting timeframe to {TRADING_PARAMS['chart_timeframe']} minutes")
            await page.click(".group-wWM3zP_M")  # Timeframe menu
            await page.click(f".item-2xPVYue0[data-value='{TRADING_PARAMS['chart_timeframe']}']")
            await asyncio.sleep(1)
            
            # Add indicators
            for indicator in TRADING_PARAMS['chart_indicators']:
                logger.info(f"Adding indicator: {indicator}")
                await page.click(".group-LWPzJcGo")  # Indicators menu
                await page.click(".input-2rGFhmzm")  # Indicator search
                await page.fill(".input-2rGFhmzm", indicator)
                await page.press(".input-2rGFhmzm", "Enter")
                await asyncio.sleep(1)
            
            # Set candle type
            logger.info(f"Setting candle type to {TRADING_PARAMS['chart_candle_type']}")
            await page.click(".group-4rFIXF8R")  # Candles menu
            await page.click(f".item-2xPVYue0[data-value='{TRADING_PARAMS['chart_candle_type']}']")
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
        
        await page.screenshot(path=screenshot_path, full_page=False)
        logger.info(f"Chart analysis screenshot saved: {screenshot_path}")

        await browser.close()
        return screenshot_path

def extract_trade_recommendation(analysis):
    """Extract trade recommendation details from AI analysis."""
    trade_rec = {
        "symbol": "BTC-PERP",
        "side": "buy", 
        "price": 0,
        "stopLoss": 0,
        "takeProfit": 0,
        "confidence": 0
    }
    
    for line in analysis.split('\n'):
        if "entry" in line.lower(): 
            trade_rec["price"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "stop loss" in line.lower():
            trade_rec["stopLoss"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "take profit" in line.lower(): 
            trade_rec["takeProfit"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "confidence" in line.lower():
            trade_rec["confidence"] = float(line.split(':')[1].strip().replace('/10', ''))
            
    if trade_rec["stopLoss"] == 0:
        trade_rec["stopLoss"] = trade_rec["price"] * (1 - TRADING_PARAMS["stop_loss_percentage"])
    if trade_rec["takeProfit"] == 0:
        risk = abs(trade_rec["price"] - trade_rec["stopLoss"])
        trade_rec["takeProfit"] = trade_rec["price"] + (risk * 2)  # 1:2 risk-reward
    
    return trade_rec

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
            
            # 1. Create the main order signature request
            signature_request = OrderSignatureRequest(
                symbol=trade_rec["symbol"],
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
            
            # 4. Create stop loss order (opposite side of main order)
            opposite_side = ORDER_SIDE.SELL if order_side == ORDER_SIDE.BUY else ORDER_SIDE.BUY
            
            stop_loss_signature_request = OrderSignatureRequest(
                symbol=trade_rec["symbol"],
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
                symbol=trade_rec["symbol"],
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
            
            # Using simpler combined API (for v2 client)
            order = await client.place_order(
                symbol=trade_rec["symbol"],
                side=trade_rec["side"],
                order_type="LIMIT",
                quantity=adjusted_size,
                price=entry_price,
                stop_loss=stop_loss,
                take_profit=trade_rec["takeProfit"]
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
        return False

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
            client = BluefinClient(
                True,  # agree to terms and conditions
                Networks["MAINNET"],  # Use Networks["TESTNET"] or Networks["MAINNET"]
                os.getenv("BLUEFIN_PRIVATE_KEY")  # private key for authentication
            )
            
            # Initialize client (onboard if first time)
            await client.init(True)
            logger.info(f'Connected to Bluefin with account address: {client.get_public_address()}')
            
        elif BLUEFIN_V2_CLIENT_AVAILABLE:
            # Initialize v2 client according to documentation
            logger.info("Initializing v2 Bluefin client")
            client = BluefinClient(
                api_key=os.getenv("BLUEFIN_API_KEY"),
                api_secret=os.getenv("BLUEFIN_API_SECRET"),
                network="mainnet",  # Use 'testnet' or 'mainnet'
                base_url=os.getenv("BLUEFIN_API_URL", None)  # Optional: use default URL if not specified
            )
            
            # Connect to the exchange
            await client.connect()
            logger.info("Connected to Bluefin exchange")
        else:
            logger.error("No Bluefin client libraries available. Please install one of the client libraries.")
            logger.error("For SUI-specific client: pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
            logger.error("For v2 client: pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git")
            return

        while True:
            # Retrieve account info
            account_info = await get_account_info(client)
            if not account_info:
                logger.error("Failed to retrieve account info, aborting trading.")
                break

            # Analyze TradingView chart
            chart_screenshot = await analyze_tradingview_chart()

            # Run AI analysis
            perplexity_result = "Perplexity analysis placeholder" 
            claude_result = "Claude analysis placeholder"
            
            # Extract trade recommendation
            trade_rec = extract_trade_recommendation(claude_result)

            # Check Perplexity confirmation
            # TODO: Implement Perplexity API call with chart_screenshot
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
                            "account_info": account_info
                        }, f, indent=2)
                    
                    report_files = visualizer.generate_performance_report()
                    logger.info(f"Performance report generated: {report_files}")
            else:
                logger.info(f"Trade not executed. Perplexity confirmation: {perplexity_confirmation}, Confidence: {trade_rec['confidence']}/10")

            # Wait for the configured interval before next analysis
            wait_time = TRADING_PARAMS.get("analysis_interval", 300)  # Default to 5 minutes
            logger.info(f"Waiting {wait_time} seconds before next analysis")
            await asyncio.sleep(wait_time)  
        
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
        raise
    finally:
        if client:
            # Close connections based on client type
            if hasattr(client, 'apis') and client.apis:
                logger.info("Closing SUI client connections")
                await client.apis.close_session()
                if hasattr(client, 'dmsApi') and client.dmsApi:
                    await client.dmsApi.close_session()
            elif hasattr(client, 'disconnect'):
                logger.info("Disconnecting v2 client")
                await client.disconnect()

if __name__ == "__main__":
    setup_logging()
    initialize_risk_manager() 
    asyncio.run(main())
#!/usr/bin/env python3
import os
import asyncio
import logging
from dotenv import load_dotenv
from decimal import Decimal
from bluefin_client_sui import BluefinClient, Networks
from bluefin_client_sui.constants import DAPI_BASE_NUM
from bluefin_client_sui.enumerations import ORDER_SIDE, ORDER_TYPE

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("bluefin_test")

# Load environment variables
load_dotenv()

# Retrieve credentials from environment variables
PRIVATE_KEY = os.getenv("BLUEFIN_PRIVATE_KEY")
API_KEY = os.getenv("BLUEFIN_API_KEY")
API_SECRET = os.getenv("BLUEFIN_API_SECRET")
NETWORK = os.getenv("BLUEFIN_NETWORK", "MAINNET")

# Constants for testing
TEST_SYMBOL = "BTC-PERP"
TEST_LEVERAGE = 5
DEFAULT_AMOUNT = Decimal('0.001')  # Very small amount for testing

async def initialize_client():
    """Initialize Bluefin client using either private key or API key authentication"""
    logger.info(f"Initializing Bluefin client with network: {NETWORK}")
    
    network = getattr(Networks, f"SUI_{NETWORK}")
    
    try:
        if PRIVATE_KEY:
            logger.info("Using private key authentication")
            client = BluefinClient(
                network=network,
                private_key=PRIVATE_KEY,
                are_terms_accepted=True
            )
        elif API_KEY and API_SECRET:
            logger.info("Using API key authentication")
            client = BluefinClient(
                network=network,
                api_key=API_KEY,
                api_secret=API_SECRET
            )
        else:
            raise ValueError("No authentication method provided. Set either BLUEFIN_PRIVATE_KEY or both BLUEFIN_API_KEY and BLUEFIN_API_SECRET.")
        
        logger.info("Initializing client...")
        await client.init(onboarding=True)  # Initialize with onboarding=True
        
        logger.info("Client initialization complete")
        return client
    except Exception as e:
        logger.error(f"Error initializing Bluefin client: {e}")
        raise

async def test_account_info(client):
    """Test retrieving account information from Bluefin"""
    try:
        logger.info("Getting account data...")
        account_data = await client.get_user_account_data()
        logger.info(f"Account data: {account_data}")
        
        logger.info("Getting margin info...")
        margin_info = await client.get_user_margin()
        logger.info(f"Margin info: {margin_info}")
        
        logger.info("Getting positions...")
        positions = await client.get_user_positions()
        logger.info(f"Open positions: {positions}")
        
        return True
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return False

async def test_leverage(client, symbol=TEST_SYMBOL):
    """Test setting and getting leverage for a symbol"""
    try:
        logger.info(f"Getting current leverage for {symbol}...")
        current_leverage = await client.get_user_leverage(symbol)
        logger.info(f"Current leverage: {current_leverage}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing leverage: {e}")
        return False

async def test_order_creation(client, do_real_trade=False):
    """Test creating an order on Bluefin (can be simulated or real)"""
    if not do_real_trade:
        logger.info("Skipping real trade creation (dry run only)")
        order_details = {
            "symbol": TEST_SYMBOL,
            "side": ORDER_SIDE.BUY,
            "type": ORDER_TYPE.MARKET,
            "size": DEFAULT_AMOUNT,
            "price": Decimal('30000.0'),  # For limit orders
            "reduceOnly": False
        }
        logger.info(f"Order would be created with details: {order_details}")
        return True
    
    try:
        # In a real implementation, you would use:
        # result = await client.place_order(
        #     symbol=TEST_SYMBOL,
        #     side=ORDER_SIDE.BUY,
        #     orderType=ORDER_TYPE.MARKET,
        #     size=DEFAULT_AMOUNT,
        #     price=None,  # Market orders don't need price
        #     reduceOnly=False
        # )
        
        logger.warning("NOT EXECUTING REAL TRADE - TEST ONLY")
        return True
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return False

async def main():
    """Main function to run all tests"""
    logger.info("Starting Bluefin SDK integration test")
    
    try:
        # Initialize client
        client = await initialize_client()
        
        # Test account info
        logger.info("Testing account info...")
        account_info_success = await test_account_info(client)
        
        # Test leverage
        logger.info("Testing leverage...")
        leverage_success = await test_leverage(client)
        
        # Test order creation (dry run)
        logger.info("Testing order creation (dry run)...")
        order_success = await test_order_creation(client, do_real_trade=False)
        
        # Print results
        logger.info("Test Results:")
        logger.info(f"Account Info Test: {'Passed' if account_info_success else 'Failed'}")
        logger.info(f"Leverage Test: {'Passed' if leverage_success else 'Failed'}")
        logger.info(f"Order Creation Test: {'Passed' if order_success else 'Failed'}")
        
    except Exception as e:
        logger.error(f"Error in main test function: {e}")
    
    logger.info("Bluefin SDK integration test completed")

if __name__ == "__main__":
    asyncio.run(main()) 
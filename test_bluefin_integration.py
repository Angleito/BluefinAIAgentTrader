#!/usr/bin/env python
"""
Test script to verify Bluefin SDK integration and show available methods.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("bluefin_test")

# Load environment variables
load_dotenv()

# Test SUI Client
def test_sui_client():
    try:
        from bluefin_client_sui import (
            BluefinClient,
            Networks,
            ORDER_SIDE,
            ORDER_TYPE
        )
        
        logger.info("Successfully imported Bluefin SUI client")
        logger.info(f"Available networks: {dir(Networks)}")
        logger.info(f"Order side options: {dir(ORDER_SIDE)}")
        logger.info(f"Order type options: {dir(ORDER_TYPE)}")
        
        # Initialize client
        private_key = os.getenv("BLUEFIN_PRIVATE_KEY")
        if not private_key:
            logger.error("BLUEFIN_PRIVATE_KEY not found in environment variables")
            return False, None, None, None
            
        logger.info(f"Initializing Bluefin SUI client with private key: {private_key[:10]}...")
        client = BluefinClient(private_key=private_key, network=Networks.MAINNET)
        logger.info("Bluefin SUI client initialized successfully")
        
        # Show available methods
        logger.info("Available client methods:")
        for method_name in dir(client):
            if not method_name.startswith('_'):  # Skip private methods
                logger.info(f"  - {method_name}")
                
        return True, client, ORDER_SIDE, ORDER_TYPE
    except ImportError as e:
        logger.error(f"Error importing Bluefin SUI client: {e}")
        return False, None, None, None
    except Exception as e:
        logger.error(f"Error initializing Bluefin SUI client: {e}")
        return False, None, None, None

# Test V2 Client
def test_v2_client():
    try:
        from bluefin.v2.client import BluefinClient
        from bluefin.v2.types import OrderSignatureRequest
        
        logger.info("Successfully imported Bluefin V2 client")
        
        # Initialize client
        api_key = os.getenv("BLUEFIN_API_KEY")
        api_secret = os.getenv("BLUEFIN_API_SECRET")
        if not api_key or not api_secret:
            logger.error("BLUEFIN_API_KEY or BLUEFIN_API_SECRET not found in environment variables")
            return False, None
            
        logger.info(f"Initializing Bluefin V2 client with API key: {api_key[:10]}...")
        client = BluefinClient(api_key=api_key, api_secret=api_secret)
        logger.info("Bluefin V2 client initialized successfully")
        
        # Show available methods
        logger.info("Available client methods:")
        for method_name in dir(client):
            if not method_name.startswith('_'):  # Skip private methods
                logger.info(f"  - {method_name}")
                
        return True, client
    except ImportError as e:
        logger.error(f"Error importing Bluefin V2 client: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Error initializing Bluefin V2 client: {e}")
        return False, None

# Test getting account information
async def test_account_info(client):
    try:
        logger.info("Testing get_account_info...")
        
        # Method depends on client type
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

async def main():
    logger.info("Testing Bluefin SDK integration")
    
    # Test SUI client
    sui_success, sui_client, ORDER_SIDE, ORDER_TYPE = test_sui_client()
    
    # If SUI client failed, try V2 client
    if not sui_success:
        logger.info("Trying Bluefin V2 client...")
        v2_success, v2_client = test_v2_client()
        if v2_success:
            client = v2_client
        else:
            logger.error("Both Bluefin clients failed to initialize")
            return
    else:
        client = sui_client
    
    # Test getting account info
    account_info = await test_account_info(client)
    if account_info:
        logger.info("Account info test passed")
    else:
        logger.error("Account info test failed")

if __name__ == "__main__":
    asyncio.run(main()) 
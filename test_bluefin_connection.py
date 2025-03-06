#!/usr/bin/env python
"""
Bluefin Connection Test Script

This script tests the connection to the Bluefin API and verifies that your
authentication credentials are working properly.

Usage:
    python test_bluefin_connection.py
"""

import os
import asyncio
import importlib.util
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define fallback constants
NETWORKS = {"MAINNET": "mainnet", "TESTNET": "testnet"}
network = os.getenv("BLUEFIN_NETWORK", "MAINNET")

# Check if the Bluefin client modules are available
BLUEFIN_CLIENT_SUI_AVAILABLE = importlib.util.find_spec("bluefin_client_sui") is not None
BLUEFIN_V2_CLIENT_AVAILABLE = importlib.util.find_spec("bluefin.v2.client") is not None

async def test_connection():
    """Test connection to Bluefin API."""
    client = None
    
    try:
        if BLUEFIN_CLIENT_SUI_AVAILABLE:
            from bluefin_client_sui import BluefinClient, Networks
            logger.info("Testing SUI client connection...")
            
            private_key = os.getenv("BLUEFIN_PRIVATE_KEY")
            if not private_key:
                logger.error("BLUEFIN_PRIVATE_KEY not found in environment variables")
                return False
                
            try:
                client = BluefinClient(
                    True,  # agree to terms and conditions
                    Networks[network],  # Use Networks["TESTNET"] or Networks["MAINNET"]
                    private_key  # private key for authentication
                )
                
                # Initialize client (onboard if first time)
                await client.init(True)
                address = client.get_public_address()
                logger.info(f'✅ Successfully connected to Bluefin with account address: {address}')
                
                # Get account data
                account_data = await client.get_user_account_data()
                logger.info(f"Account data retrieved: {account_data}")
                
                # Get margin info
                margin_data = await client.get_user_margin()
                logger.info(f"Margin data retrieved: {margin_data}")
                
                # Get positions
                positions = await client.get_user_positions()
                logger.info(f"Found {len(positions)} open positions")
                
                return True
            except Exception as e:
                logger.error(f"Failed to connect with SUI client: {e}")
                return False
                
        elif BLUEFIN_V2_CLIENT_AVAILABLE:
            from bluefin.v2.client import BluefinClient
            logger.info("Testing v2 client connection...")
            
            api_key = os.getenv("BLUEFIN_API_KEY")
            api_secret = os.getenv("BLUEFIN_API_SECRET")
            
            if not api_key or not api_secret:
                logger.error("BLUEFIN_API_KEY or BLUEFIN_API_SECRET not found in environment variables")
                return False
                
            try:
                client = BluefinClient(
                    api_key=api_key,
                    api_secret=api_secret,
                    network=network.lower(),  # Use 'testnet' or 'mainnet'
                    base_url=os.getenv("BLUEFIN_API_URL", None)  # Optional: use default URL if not specified
                )
                
                # Connect to the exchange
                await client.connect()
                logger.info("✅ Successfully connected to Bluefin exchange")
                
                # Test API calls
                account_info = await client.get_account_info()
                logger.info(f"Account info retrieved: {account_info}")
                
                return True
            except Exception as e:
                logger.error(f"Failed to connect with v2 client: {e}")
                return False
        else:
            logger.error("No Bluefin client libraries available. Please install one of the client libraries.")
            logger.error("For SUI-specific client: pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
            logger.error("For v2 client: pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git")
            return False
    finally:
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
    
    return False

async def main():
    """Run the test."""
    logger.info("Testing Bluefin API connection...")
    
    success = await test_connection()
    
    if success:
        logger.info("🎉 Connection test passed! Your Bluefin API configuration is working properly.")
    else:
        logger.error("❌ Connection test failed. Please check your API credentials and network settings.")

if __name__ == "__main__":
    asyncio.run(main()) 
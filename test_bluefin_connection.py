#!/usr/bin/env python
"""
Bluefin Connection Test Script

This script tests the connection to the Bluefin API and verifies that your
authentication credentials are working properly. It also performs basic security
checks on your API configuration.

Usage:
    python test_bluefin_connection.py
"""

import os
import asyncio
import importlib.util
import logging
import time
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

def check_env_file_permissions():
    """Check if .env file has appropriate permissions."""
    try:
        if os.path.exists(".env"):
            import stat
            st = os.stat(".env")
            permissions = st.st_mode & 0o777
            
            # Check if file is readable by others
            if permissions & 0o044:
                logger.warning("⚠️ Security risk: .env file is readable by others (permissions: %o)", permissions)
                logger.warning("Recommended: Run 'chmod 600 .env' to restrict access")
            else:
                logger.info("✅ .env file has appropriate permissions")
        else:
            logger.warning("⚠️ .env file not found. Environment variables may be set elsewhere.")
    except Exception as e:
        logger.error(f"Error checking .env file permissions: {e}")

def check_network_security():
    """Check network security settings."""
    if network.upper() == "MAINNET":
        logger.warning("⚠️ Using MAINNET for API connections")
        logger.warning("   Ensure this is intentional for production use")
    else:
        logger.info("✅ Using TESTNET for API connections (safer for testing)")

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

def print_security_recommendations():
    """Print security recommendations for API usage."""
    logger.info("\n===== SECURITY RECOMMENDATIONS =====")
    logger.info("1. API Key Management:")
    logger.info("   - Rotate your API keys regularly (every 30-90 days)")
    logger.info("   - Use different keys for development and production")
    
    logger.info("\n2. Permissions and Access:")
    logger.info("   - Use keys with the minimum necessary permissions")
    logger.info("   - Consider read-only keys for monitoring")
    
    logger.info("\n3. Environment Separation:")
    logger.info("   - Use separate keys for testnet and mainnet")
    logger.info("   - Implement additional safeguards for mainnet")
    
    logger.info("\n4. Monitoring:")
    logger.info("   - Set up alerts for unusual trading activity")
    logger.info("   - Regularly review trading logs")
    logger.info("=====================================")

async def main():
    """Run the test."""
    logger.info("Testing Bluefin API connection...")
    
    # Check .env file permissions
    check_env_file_permissions()
    
    # Check network security
    check_network_security()
    
    # Test API connection
    start_time = time.time()
    success = await test_connection()
    response_time = time.time() - start_time
    
    if success:
        logger.info(f"🎉 Connection test passed! Your Bluefin API configuration is working properly.")
        logger.info(f"API response time: {response_time:.2f} seconds")
    else:
        logger.error("❌ Connection test failed. Please check your API credentials and network settings.")
    
    # Print security recommendations
    print_security_recommendations()

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Test script to verify Bluefin client integration.
Based on the official documentation: https://bluefin-exchange.readme.io/reference/initialization
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

async def test_bluefin_v2_client():
    """Test the Bluefin v2 client integration"""
    try:
        from bluefin_v2_client import BluefinClient, Networks
        logger.info("✅ Successfully imported Bluefin v2 client")
        
        # Get environment variables
        private_key = os.getenv("BLUEFIN_PRIVATE_KEY")
        network_str = os.getenv("BLUEFIN_NETWORK", "testnet").lower()
        
        # Map network string to enum
        if network_str == "mainnet":
            network = Networks.MAINNET
        elif network_str == "sui_staging":
            network = Networks.SUI_STAGING
        elif network_str == "sui_prod":
            network = Networks.SUI_PROD
        else:
            network = Networks.TESTNET
        
        if not private_key:
            logger.error("❌ Missing BLUEFIN_PRIVATE_KEY environment variable")
            return False
        
        # Initialize client according to documentation
        client = BluefinClient(
            are_terms_accepted=True,
            network=network,
            private_key=private_key
        )
        logger.info(f"✅ Successfully created Bluefin client for network: {network_str}")
        
        # Initialize the client
        await client.init(onboard_user=True)
        logger.info("✅ Successfully initialized Bluefin client")
        
        # Get public address
        public_address = client.get_public_address()
        logger.info(f"✅ Connected with wallet address: {public_address}")
        
        # Get account details
        account_details = await client.get_account_details()
        logger.info(f"✅ Account details: {account_details}")
        
        # Test margin bank functions
        # Based on https://bluefin-exchange.readme.io/reference/get-deposit-withdraw-usdc-from-marginbank
        try:
            # Get margin bank balance
            margin_balance = await client.get_margin_bank_balance()
            logger.info(f"✅ Margin bank balance: {margin_balance} USDC")
            
            # Test deposit (with a small amount for testing)
            if margin_balance < 1:
                deposit_amount = 0.1  # Small amount for testing
                deposit_result = await client.deposit_margin_to_bank(deposit_amount)
                logger.info(f"✅ Deposited {deposit_amount} USDC to margin bank: {deposit_result}")
                
                # Check updated balance
                new_balance = await client.get_margin_bank_balance()
                logger.info(f"✅ Updated margin bank balance: {new_balance} USDC")
                
                # Test withdraw (the same small amount)
                withdraw_result = await client.withdraw_margin_from_bank(deposit_amount)
                logger.info(f"✅ Withdrew {deposit_amount} USDC from margin bank: {withdraw_result}")
            else:
                logger.info("✅ Skipping deposit/withdraw test as margin balance is sufficient")
        except Exception as e:
            logger.error(f"❌ Error testing margin bank functions: {e}")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import Bluefin v2 client: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing Bluefin v2 client: {e}")
        return False

async def test_bluefin_sui_client():
    """Test the Bluefin SUI client integration"""
    try:
        from bluefin_client_sui import BluefinClient, Networks
        logger.info("✅ Successfully imported Bluefin SUI client")
        
        # Get environment variables
        private_key = os.getenv("BLUEFIN_PRIVATE_KEY")
        network_str = os.getenv("BLUEFIN_NETWORK", "testnet").lower()
        
        # Map network string to enum
        network = Networks.MAINNET if network_str == "mainnet" else Networks.TESTNET
        
        if not private_key:
            logger.error("❌ Missing BLUEFIN_PRIVATE_KEY environment variable")
            return False
        
        # Initialize client according to documentation
        client = BluefinClient(private_key=private_key, network=network)
        logger.info(f"✅ Successfully created Bluefin SUI client for network: {network_str}")
        
        # Get public address
        public_address = client.get_public_address()
        logger.info(f"✅ Connected with wallet address: {public_address}")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import Bluefin SUI client: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing Bluefin SUI client: {e}")
        return False

async def main():
    """Main function to run the tests"""
    logger.info("Starting Bluefin integration tests...")
    
    # Test Bluefin v2 client
    v2_success = await test_bluefin_v2_client()
    
    # Test Bluefin SUI client
    sui_success = await test_bluefin_sui_client()
    
    if v2_success or sui_success:
        logger.info("✅ At least one Bluefin client is working correctly")
        return 0
    else:
        logger.error("❌ All Bluefin client tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 
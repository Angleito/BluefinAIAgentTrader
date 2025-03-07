#!/usr/bin/env python3
"""
Test script to verify Bluefin client libraries are properly installed and working in Docker.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("bluefin_docker_test")

# Load environment variables
load_dotenv()

def check_sui_client():
    """Test if the SUI Bluefin client is installed and importable"""
    try:
        from bluefin_client_sui import BluefinClient, Networks
        from bluefin_client_sui.constants import DAPI_BASE_NUM
        from bluefin_client_sui.enumerations import ORDER_SIDE, ORDER_TYPE
        
        logger.info("✅ SUI Bluefin client libraries successfully imported")
        logger.info(f"Available networks: {dir(Networks)}")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import SUI Bluefin client: {e}")
        return False

def check_v2_client():
    """Test if the v2 Bluefin client is installed and importable"""
    try:
        from bluefin.v2.client import BluefinClient
        from bluefin.v2.types import OrderSignatureRequest
        
        logger.info("✅ V2 Bluefin client libraries successfully imported")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import V2 Bluefin client: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Testing Bluefin client libraries in Docker environment")
    
    sui_client_available = check_sui_client()
    v2_client_available = check_v2_client()
    
    if sui_client_available or v2_client_available:
        logger.info("✅ At least one Bluefin client library is available")
        
        # Print environment variables for verification
        logger.info(f"BLUEFIN_NETWORK: {os.getenv('BLUEFIN_NETWORK', 'Not set')}")
        logger.info(f"BLUEFIN_PRIVATE_KEY: {'Set' if os.getenv('BLUEFIN_PRIVATE_KEY') else 'Not set'}")
        logger.info(f"BLUEFIN_API_KEY: {'Set' if os.getenv('BLUEFIN_API_KEY') else 'Not set'}")
        logger.info(f"BLUEFIN_API_SECRET: {'Set' if os.getenv('BLUEFIN_API_SECRET') else 'Not set'}")
        
        return 0
    else:
        logger.error("❌ No Bluefin client libraries are available")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
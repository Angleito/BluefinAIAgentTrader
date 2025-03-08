#!/usr/bin/env python
"""
Route Testing Script for PerplexityTrader

This script tests all the routes in the application to ensure they're working properly.
"""

import os
import sys
import json
import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/route_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("route_test")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Base URL for the API
BASE_URL = os.environ.get("API_URL", "http://localhost:5001")

# Test data for webhook
WEBHOOK_TEST_DATA = {
    "indicator": "vmanchu_cipher_b",
    "symbol": "SUI/USD",
    "timeframe": "5m",
    "signal_type": "GREEN_CIRCLE",
    "action": "BUY",
    "timestamp": datetime.utcnow().isoformat()
}

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")

def test_route(route, method="GET", data=None, auth=None, expected_status=200):
    """Test a route and return the result"""
    url = f"{BASE_URL}{route}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, auth=auth, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, auth=auth, timeout=10)
        else:
            logger.error(f"Unsupported method: {method}")
            return False, None
        
        if response.status_code == expected_status:
            logger.info(f"✅ {method} {route} - Status: {response.status_code}")
            return True, response.json() if response.headers.get("content-type") == "application/json" else response.text
        else:
            logger.error(f"❌ {method} {route} - Expected status {expected_status}, got {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False, None
    except Exception as e:
        logger.error(f"❌ {method} {route} - Error: {str(e)}")
        return False, None

def get_auth_token():
    """Get an authentication token"""
    success, data = test_route("/login", method="POST", data={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    
    if success and data and isinstance(data, dict) and "token" in data:
        return data["token"]
    return None

def main():
    """Main function to test all routes"""
    print("\n==================================================")
    print("PerplexityTrader Route Test")
    print("==================================================")
    print(f"Testing routes at: {BASE_URL}")
    print("==================================================\n")
    
    # Test health check
    test_route("/health")
    
    # Test root route
    test_route("/")
    
    # Test webhook route
    test_route("/webhook", method="POST", data=WEBHOOK_TEST_DATA)
    
    # Test test endpoint
    test_route("/test")
    
    # Get auth token
    token = get_auth_token()
    if token:
        logger.info("Authentication successful")
        
        # Test authenticated routes
        auth_header = {"Authorization": f"Bearer {token}"}
        
        # Test status endpoint
        test_route("/status", auth=auth_header)
        
        # Test configuration endpoint
        test_route("/configuration", auth=auth_header)
        
        # Test positions endpoint
        test_route("/positions", auth=auth_header)
        
        # Test analysis endpoint
        test_route("/analysis", auth=auth_header)
    else:
        logger.warning("Authentication failed, skipping authenticated routes")
    
    print("\n==================================================")
    print("Route testing complete")
    print("Check logs/route_test.log for details")
    print("==================================================\n")

if __name__ == "__main__":
    main() 
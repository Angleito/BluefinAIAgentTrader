#!/usr/bin/env python
"""
Integration test for the TradingView webhook server and signal processor.

This script tests the integration between the webhook server and the
signal processor by sending sample VuManChu Cipher B alerts and
verifying that they are properly processed.

Run with:
    FLASK_ENV=development python -m test.test_webhook_integration
"""

import os
import json
import logging
import requests
import asyncio
import unittest
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_webhook_integration")

# Import the modules to test
try:
    from core.signal_processor import (
        process_tradingview_alert, 
        map_tradingview_to_bluefin_symbol,
        get_trade_direction
    )
    from core.bluefin_client import create_bluefin_client, MockBluefinClient
except ImportError:
    logger.error("Failed to import required modules. Please run this test from the project root directory.")
    raise

# Sample VuManChu Cipher B alerts for testing
SAMPLE_ALERTS = [
    {
        "indicator": "vmanchu_cipher_b",
        "symbol": "SUI/USD",
        "timeframe": "5m",
        "signal_type": "GREEN_CIRCLE",
        "action": "BUY",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "indicator": "vmanchu_cipher_b",
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "signal_type": "RED_CIRCLE",
        "action": "SELL",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "indicator": "vmanchu_cipher_b",
        "symbol": "ETH/USD",
        "timeframe": "15m",
        "signal_type": "GOLD_CIRCLE",
        "action": "BUY",
        "timestamp": datetime.utcnow().isoformat()
    },
    {
        "indicator": "vmanchu_cipher_b",
        "symbol": "SOL/USD",
        "timeframe": "4h",
        "signal_type": "PURPLE_TRIANGLE",
        "action": "BUY",
        "timestamp": datetime.utcnow().isoformat()
    }
]

class TestWebhookIntegration(unittest.TestCase):
    """Test the integration between the webhook server and signal processor."""
    
    def setUp(self):
        """Set up the test environment."""
        # Determine if we're testing against a running webhook server
        self.webhook_url = os.getenv("WEBHOOK_URL", "http://localhost:5001/webhook")
        self.test_live = os.getenv("TEST_LIVE", "false").lower() == "true"
        logger.info(f"Testing {'against live server' if self.test_live else 'locally'}")
    
    def test_signal_processor(self):
        """Test that the signal processor correctly processes alerts."""
        for alert in SAMPLE_ALERTS:
            processed = process_tradingview_alert(alert)
            
            # Check that the alert was processed
            self.assertIsNotNone(processed, f"Alert was not processed: {alert}")
            
            if processed:  # Add null check to satisfy linter
                # Check that the required fields are present
                self.assertIn("symbol", processed)
                self.assertIn("type", processed)
                self.assertIn("leverage", processed)
                self.assertIn("stop_loss", processed)
                self.assertIn("take_profit", processed)
                
                # Check that the symbol was mapped correctly
                if "SUI" in alert["symbol"]:
                    self.assertEqual(processed["symbol"], "SUI-PERP")
                
                # Check that the trade direction was set correctly
                if alert["signal_type"] == "GREEN_CIRCLE":
                    self.assertEqual(processed["type"], "buy")
                elif alert["signal_type"] == "RED_CIRCLE":
                    self.assertEqual(processed["type"], "sell")
                
                logger.info(f"Processed alert: {json.dumps(processed)}")
    
    def test_symbol_mapping(self):
        """Test that symbols are mapped correctly from TradingView to Bluefin."""
        test_cases = [
            ("SUI/USD", "SUI-PERP"),
            ("BTC/USD", "BTC-PERP"),
            ("ETH/USDT", "ETH-PERP"),
            ("BINANCE:BTCUSDT", "BTC-PERP"),
            ("BINANCE:SOLUSDT", "SOL-PERP"),
            ("COINBASE:ETHBTC", "ETHBTC-PERP")
        ]
        
        for tv_symbol, expected in test_cases:
            result = map_tradingview_to_bluefin_symbol(tv_symbol)
            self.assertEqual(result, expected)
    
    async def test_mock_bluefin_client(self):
        """Test the mock Bluefin client."""
        # Create a mock client
        client = MockBluefinClient()
        
        # Check account info
        account_info = await client.get_account_info()
        self.assertIsNotNone(account_info)
        self.assertIn("balance", account_info)
        self.assertIn("availableMargin", account_info)
        
        # Place an order
        order = await client.place_order(
            symbol="SUI-PERP",
            side="BUY",
            quantity=1.0,
            leverage=10
        )
        
        self.assertIsNotNone(order)
        self.assertIn("id", order)
        self.assertEqual(order["symbol"], "SUI-PERP")
        self.assertEqual(order["side"], "BUY")
        
        # Check positions
        positions = await client.get_positions()
        self.assertIsNotNone(positions)
        self.assertEqual(len(positions), 1)
        
        # Close position
        close_result = await client.close_position("SUI-PERP")
        self.assertIsNotNone(close_result)
        self.assertIn("id", close_result)
        
        # Positions should be empty now
        positions = await client.get_positions()
        self.assertIsNotNone(positions)
        self.assertEqual(len(positions), 0)
        
        await client.close()
    
    def test_webhook_server_if_available(self):
        """Test sending alerts to the webhook server if it's available."""
        if not self.test_live:
            logger.info("Skipping live webhook test")
            return
        
        for alert in SAMPLE_ALERTS:
            try:
                # Send the alert to the webhook server
                response = requests.post(
                    self.webhook_url,
                    json=alert,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                # Check that the request was successful
                self.assertEqual(response.status_code, 200)
                
                # Check the response JSON
                response_json = response.json()
                self.assertEqual(response_json["status"], "success")
                
                logger.info(f"Webhook response: {json.dumps(response_json)}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to connect to webhook server: {str(e)}")
                self.skipTest("Webhook server not available")

def run_async_tests():
    """Run the async test methods."""
    loop = asyncio.get_event_loop()
    test = TestWebhookIntegration()
    test.setUp()
    loop.run_until_complete(test.test_mock_bluefin_client())

if __name__ == "__main__":
    # Run the async tests
    run_async_tests()
    
    # Run the other tests
    unittest.main() 
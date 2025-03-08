#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_position_doubling")

# API endpoint
API_URL = "http://localhost:5002"

async def main():
    """Test the position doubling feature when opening opposite positions."""
    logger.info("Starting position doubling test")
    
    # First, check if there are any existing positions
    try:
        positions_response = requests.get(f"{API_URL}/positions")
        positions = positions_response.json()
        logger.info(f"Current positions: {positions}")
        
        # Close any existing positions
        if positions:
            logger.info("Closing existing positions before test")
            for position in positions:
                position_id = position.get("id")
                if position_id:
                    close_response = requests.post(f"{API_URL}/close_trade?trade_id={position_id}")
                    logger.info(f"Closed position {position_id}: {close_response.status_code}")
    except Exception as e:
        logger.error(f"Error checking/closing positions: {e}")
    
    # Step 1: Directly add a mock position to the mock client
    logger.info("Step 1: Adding a mock LONG position directly to the mock client")
    
    # Create a mock position via a special endpoint
    mock_position = {
        "id": "mock_position_1",
        "symbol": "SUI-PERP",
        "side": "LONG",
        "entryPrice": 1.5,
        "markPrice": 1.5,
        "quantity": 1.0,
        "leverage": 12,
        "unrealizedPnl": 0.0,
        "marginType": "ISOLATED"
    }
    
    try:
        # Use a special endpoint to add a mock position (you'll need to implement this)
        # If this endpoint doesn't exist, we'll need to modify the agent code to add a test endpoint
        mock_response = requests.post(f"{API_URL}/add_mock_position", json=mock_position)
        logger.info(f"Added mock position response: {mock_response.status_code}")
        if mock_response.status_code != 200:
            logger.warning("Could not add mock position. The test may not work as expected.")
            logger.warning("Falling back to regular test flow.")
    except Exception as e:
        logger.error(f"Error adding mock position: {e}")
        logger.warning("Falling back to regular test flow.")
    
    # Check positions after adding mock position
    try:
        positions_response = requests.get(f"{API_URL}/positions")
        positions = positions_response.json()
        logger.info(f"Positions after adding mock: {positions}")
    except Exception as e:
        logger.error(f"Error checking positions after adding mock: {e}")
    
    # Step 2: Open a SELL position (opposite direction)
    logger.info("Step 2: Opening a SELL position (opposite direction)")
    sell_alert = {
        "symbol": "SUI-PERP",
        "type": "sell",
        "timeframe": "5m",
        "signal_type": "RED_CIRCLE",
        "entry_time": datetime.utcnow().isoformat(),
        "position_size": 1.0,  # Same size as before, should be doubled
        "leverage": 12,
        "stop_loss": 0.15,
        "take_profit": 0.3,
        "confidence": 0.8,
        "original_alert": {
            "indicator": "vmanchu_cipher_b",
            "symbol": "SUI/USD",
            "timeframe": "5m",
            "action": "SELL",
            "signal_type": "RED_CIRCLE",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    try:
        sell_response = requests.post(f"{API_URL}/open_trade", json=sell_alert)
        logger.info(f"SELL position response: {sell_response.status_code}")
        logger.info(f"SELL position details: {sell_response.json()}")
    except Exception as e:
        logger.error(f"Error opening SELL position: {e}")
    
    # Wait a moment for the position to be processed
    await asyncio.sleep(2)
    
    # Check positions after SELL
    try:
        positions_response = requests.get(f"{API_URL}/positions")
        positions = positions_response.json()
        logger.info(f"Positions after SELL: {positions}")
    except Exception as e:
        logger.error(f"Error checking positions after SELL: {e}")
    
    # Check trades to see if position size was doubled
    try:
        trades_response = requests.get(f"{API_URL}/trades")
        trades = trades_response.json()
        logger.info(f"Trades history: {trades}")
        
        # Look for the SELL trade to verify position size
        sell_trades = [t for t in trades if t.get("type") == "sell"]
        if sell_trades:
            latest_sell = sell_trades[-1]
            logger.info(f"Latest SELL trade: {latest_sell}")
            logger.info(f"Position size for SELL trade: {latest_sell.get('position_size')}")
            
            # Check if position size was doubled
            if latest_sell.get('position_size', 0) > 1.0:
                logger.info("SUCCESS: Position size was increased for the opposite trade!")
            else:
                logger.warning("Position size was not increased for the opposite trade.")
        else:
            logger.warning("No SELL trades found in history.")
    except Exception as e:
        logger.error(f"Error checking trades: {e}")
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Bluefin Market Utility Test

This script demonstrates how to use the BluefinMarket utility to fetch prices
for the main trading pairs from Bluefin Exchange.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the BluefinMarket utility
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.bluefin_market import (
        get_price, 
        get_main_prices, 
        get_all_prices,
        get_sui_price,
        get_btc_price, 
        get_eth_price, 
        get_sol_price,
        MAIN_TRADING_PAIRS,
        market  # Import the market singleton for cleanup
    )
    logger.info("Successfully imported BluefinMarket utility")
except ImportError as e:
    logger.error(f"Error importing BluefinMarket utility: {e}")
    logger.error("Please ensure you have created the core/bluefin_market.py file")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error importing BluefinMarket utility: {e}")
    sys.exit(1)

async def test_individual_prices():
    """Test getting prices for individual trading pairs"""
    logger.info("Testing individual price fetching...")
    
    # Get SUI price
    sui_price = await get_sui_price()
    logger.info(f"SUI-PERP price: {sui_price}")
    
    # Get BTC price
    btc_price = await get_btc_price()
    logger.info(f"BTC-PERP price: {btc_price}")
    
    # Get ETH price
    eth_price = await get_eth_price()
    logger.info(f"ETH-PERP price: {eth_price}")
    
    # Get SOL price
    sol_price = await get_sol_price()
    logger.info(f"SOL-PERP price: {sol_price}")
    
    return {
        "SUI-PERP": sui_price,
        "BTC-PERP": btc_price,
        "ETH-PERP": eth_price,
        "SOL-PERP": sol_price
    }

async def test_batch_prices():
    """Test getting prices for main trading pairs in batch"""
    logger.info("Testing batch price fetching...")
    
    # Get prices for main trading pairs
    prices = await get_main_prices()
    for symbol, price in prices.items():
        logger.info(f"{symbol} price: {price}")
    
    return prices

async def main():
    """Main test function"""
    logger.info("Starting Bluefin Market Utility Test...")
    
    try:
        # Test getting individual prices
        individual_prices = await test_individual_prices()
        
        # Test getting batch prices
        batch_prices = await test_batch_prices()
        
        # Print results in table format
        print("\n=== BLUEFIN MARKET PRICES ===")
        print("Symbol        | Individual    | Batch         | Match")
        print("-" * 58)
        
        for symbol in MAIN_TRADING_PAIRS:
            ind_price = individual_prices.get(symbol)
            bat_price = batch_prices.get(symbol)
            ind_str = f"{ind_price:.4f}" if ind_price is not None else "N/A"
            bat_str = f"{bat_price:.4f}" if bat_price is not None else "N/A"
            match = "✓" if ind_price == bat_price else "✗"
            print(f"{symbol:<13} | {ind_str:<13} | {bat_str:<13} | {match}")
        
        print("=" * 58)
        
        # Verify results
        all_successful = all(
            individual_prices.get(symbol) is not None and 
            batch_prices.get(symbol) is not None
            for symbol in MAIN_TRADING_PAIRS
        )
        
        if all_successful:
            print("\n✅ All price fetches successful!")
        else:
            print("\n❌ Some price fetches failed!")
    finally:
        # Ensure we close the session
        logger.info("Cleaning up client session...")
        if hasattr(market, 'close') and callable(market.close):
            await market.close()

if __name__ == "__main__":
    try:
        # Load environment variables
        load_dotenv()
        
        # Run the test
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True) 
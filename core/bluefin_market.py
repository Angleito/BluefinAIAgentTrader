"""
Bluefin Market Utility

This module provides utility functions for fetching market data from Bluefin Exchange API.
It handles the main trading pairs and provides a simple interface for fetching prices.
"""

import os
import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Union, Any
import atexit
import weakref
import contextlib

# Configure logging
logger = logging.getLogger(__name__)

# API endpoints
BLUEFIN_TESTNET_API = "https://dapi.api.sui-staging.bluefin.io"
BLUEFIN_MAINNET_API = "https://dapi.api.sui-prod.bluefin.io"

# Main trading pairs to monitor
MAIN_TRADING_PAIRS = [
    "SUI-PERP",   # Sui
    "BTC-PERP",   # Bitcoin
    "ETH-PERP",   # Ethereum
    "SOL-PERP",   # Solana
]

# Additional trading pairs that may be of interest
ADDITIONAL_TRADING_PAIRS = [
    "AVAX-PERP",  # Avalanche
    "TIA-PERP",   # Celestia
    "APT-PERP",   # Aptos
    "ARB-PERP",   # Arbitrum
]

# Track sessions for cleanup
_SESSIONS = weakref.WeakSet()

# Session cleanup
async def _cleanup_sessions():
    """Close all open sessions at exit"""
    for session in list(_SESSIONS):
        if not session.closed:
            await session.close()

# Register exit handler
def _exit_handler():
    """Run cleanup on process exit"""
    try:
        loop = asyncio.get_running_loop()
        if not loop.is_closed():
            loop.run_until_complete(_cleanup_sessions())
    except RuntimeError:
        # No event loop, nothing to do
        pass

atexit.register(_exit_handler)

@contextlib.asynccontextmanager
async def get_session():
    """Context manager for getting an aiohttp session."""
    session = aiohttp.ClientSession()
    _SESSIONS.add(session)
    try:
        yield session
    finally:
        if not session.closed:
            await session.close()
            _SESSIONS.discard(session)

class BluefinMarket:
    """Utility class for fetching market data from Bluefin Exchange"""
    
    def __init__(self, use_testnet: bool = False):
        """
        Initialize the BluefinMarket utility.
        
        Args:
            use_testnet: Whether to use testnet API (default: False)
        """
        self.base_url = BLUEFIN_TESTNET_API if use_testnet else BLUEFIN_MAINNET_API
        self.session = None
        self.network = "testnet" if use_testnet else "mainnet"
        
    async def ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            _SESSIONS.add(self.session)
        return self.session
        
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
            
    async def get_price(self, symbol: str) -> Optional[float]:
        """
        Get the current price for a symbol from Bluefin Exchange.
        
        This method handles the blockchain-specific 18-decimal format and
        converts it to a standard float.
        
        Args:
            symbol: The trading symbol (e.g., 'SUI-PERP')
            
        Returns:
            float: The current price or None if failed
        """
        url = f"{self.base_url}/marketData?symbol={symbol}"
        
        try:
            # Use the context manager for session management
            async with get_session() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Try to get the price from different possible fields
                        price_fields = ['marketPrice', 'oraclePrice', 'indexPrice', 'lastPrice']
                        
                        for field in price_fields:
                            if field in data and data[field]:
                                # Convert from blockchain native format (with 18 decimals)
                                raw_price = data[field]
                                price = float(raw_price) / 1e18
                                logger.debug(f"Got {symbol} price from {field}: {price}")
                                return price
                        
                        logger.warning(f"No price fields found for {symbol}")
                    else:
                        logger.warning(f"Failed to get price for {symbol}: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            
        return None
        
    async def get_main_prices(self) -> Dict[str, Optional[float]]:
        """
        Get prices for the main trading pairs.
        
        Returns:
            dict: A dictionary mapping symbols to their prices
        """
        tasks = [self.get_price(symbol) for symbol in MAIN_TRADING_PAIRS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for i, result in enumerate(results):
            symbol = MAIN_TRADING_PAIRS[i]
            if isinstance(result, Exception):
                logger.error(f"Error fetching {symbol} price: {result}")
                prices[symbol] = None
            else:
                prices[symbol] = result
                
        return prices
        
    async def get_all_prices(self) -> Dict[str, Optional[float]]:
        """
        Get prices for all trading pairs (main + additional).
        
        Returns:
            dict: A dictionary mapping symbols to their prices
        """
        all_pairs = MAIN_TRADING_PAIRS + ADDITIONAL_TRADING_PAIRS
        tasks = [self.get_price(symbol) for symbol in all_pairs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for i, result in enumerate(results):
            symbol = all_pairs[i]
            if isinstance(result, Exception):
                logger.error(f"Error fetching {symbol} price: {result}")
                prices[symbol] = None
            else:
                prices[symbol] = result
                
        return prices
        
    async def get_exchange_info(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get exchange information from Bluefin Exchange.
        
        Returns:
            list: List of available symbols and their metadata
        """
        url = f"{self.base_url}/exchangeInfo"
        
        try:
            async with get_session() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.warning(f"Failed to get exchange info: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error fetching exchange info: {e}")
            
        return None
        
    async def get_sui_price(self) -> Optional[float]:
        """Quick helper to get SUI-PERP price"""
        return await self.get_price("SUI-PERP")
        
    async def get_btc_price(self) -> Optional[float]:
        """Quick helper to get BTC-PERP price"""
        return await self.get_price("BTC-PERP")
        
    async def get_eth_price(self) -> Optional[float]:
        """Quick helper to get ETH-PERP price"""
        return await self.get_price("ETH-PERP")
        
    async def get_sol_price(self) -> Optional[float]:
        """Quick helper to get SOL-PERP price"""
        return await self.get_price("SOL-PERP")

# Create a singleton instance for easy importing
market = BluefinMarket(use_testnet=os.getenv("BLUEFIN_TESTNET", "false").lower() in ["true", "1", "yes"])

# Standalone functions for easy usage without class instantiation
async def get_price(symbol: str) -> Optional[float]:
    """Get price for a single symbol"""
    return await market.get_price(symbol)

async def get_main_prices() -> Dict[str, Optional[float]]:
    """Get prices for main trading pairs"""
    return await market.get_main_prices()

async def get_all_prices() -> Dict[str, Optional[float]]:
    """Get prices for all trading pairs"""
    return await market.get_all_prices()

async def get_sui_price() -> Optional[float]:
    """Quick helper to get SUI-PERP price"""
    return await market.get_sui_price()

async def get_btc_price() -> Optional[float]:
    """Quick helper to get BTC-PERP price"""
    return await market.get_btc_price()

async def get_eth_price() -> Optional[float]:
    """Quick helper to get ETH-PERP price"""
    return await market.get_eth_price()

async def get_sol_price() -> Optional[float]:
    """Quick helper to get SOL-PERP price"""
    return await market.get_sol_price() 
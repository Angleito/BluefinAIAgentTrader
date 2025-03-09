"""
Bluefin API client implementation for PerplexityTrader.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Union, Any
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

class BluefinClientWrapper:
    """
    Wrapper for the Bluefin API client to provide a consistent interface
    and handle errors gracefully.
    """
    
    def __init__(self):
        self.client = None
        self.initialized = False
        self.network = os.getenv('BLUEFIN_NETWORK', 'SUI_PROD')
        self.private_key = os.getenv('BLUEFIN_PRIVATE_KEY')
        self.api_key = os.getenv('BLUEFIN_API_KEY')
        self.api_secret = os.getenv('BLUEFIN_API_SECRET')
        
    async def initialize(self) -> bool:
        """Initialize the Bluefin client."""
        try:
            # Import here to avoid issues if the package is not installed
            from bluefin_client_sui import BluefinClient
            
            # Create the client instance
            self.client = BluefinClient(
                network=self.network,
                private_key=self.private_key,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            # Initialize with credentials
            await self.client.initialize_with_manual_credentials()
            self.initialized = True
            logger.info("Bluefin client initialized successfully")
            return True
            
        except ImportError:
            logger.error("Failed to import BluefinClient. Make sure the package is installed.")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Bluefin client: {e}")
            return False
    
    async def ensure_initialized(self) -> bool:
        """Ensure the client is initialized before making API calls."""
        if not self.initialized:
            return await self.initialize()
        return True
    
    async def get_account_info(self) -> Dict:
        """Get account information."""
        if not await self.ensure_initialized():
            return {"error": "Client not initialized"}
        
        try:
            account_data = await self.client.get_account_data()
            return account_data
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"error": str(e)}
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions."""
        if not await self.ensure_initialized():
            return [{"error": "Client not initialized"}]
        
        try:
            account_data = await self.client.get_account_data()
            return account_data.get("positions", [])
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return [{"error": str(e)}]
    
    async def get_market_price(self, symbol: str) -> Dict:
        """Get current market price for a symbol."""
        if not await self.ensure_initialized():
            return {"error": "Client not initialized"}
        
        try:
            price = await self.client.get_market_price(symbol)
            return {"symbol": symbol, "price": price}
        except Exception as e:
            logger.error(f"Error getting market price for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        leverage: int = 1,
        reduce_only: bool = False,
        post_only: bool = False,
        order_type: str = "MARKET"
    ) -> Dict:
        """Place an order."""
        if not await self.ensure_initialized():
            return {"error": "Client not initialized"}
        
        try:
            # Prepare order parameters
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "quantity": quantity,
                "leverage": leverage,
                "reduceOnly": reduce_only,
                "postOnly": post_only,
                "orderType": order_type
            }
            
            # Add price for limit orders
            if price is not None and order_type == "LIMIT":
                params["price"] = price
            
            # Place the order
            order = await self.client.place_order(params)
            return order
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": str(e)}
    
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order by ID."""
        if not await self.ensure_initialized():
            return {"error": "Client not initialized"}
        
        try:
            result = await self.client.cancel_order(order_id)
            return result
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return {"error": str(e)}
    
    async def close_position(self, symbol: str) -> Dict:
        """Close a position for a symbol."""
        if not await self.ensure_initialized():
            return {"error": "Client not initialized"}
        
        try:
            # Get current position
            positions = await self.get_positions()
            position = next((p for p in positions if p.get("symbol") == symbol), None)
            
            if not position:
                return {"error": f"No open position for {symbol}"}
            
            # Determine side for closing (opposite of current position)
            side = "SELL" if position.get("side") == "BUY" else "BUY"
            quantity = abs(float(position.get("size", 0)))
            
            if quantity <= 0:
                return {"error": f"Invalid position size for {symbol}"}
            
            # Place order to close position
            return await self.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                reduce_only=True
            )
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return {"error": str(e)}
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """Set leverage for a symbol."""
        if not await self.ensure_initialized():
            return {"error": "Client not initialized"}
        
        try:
            result = await self.client.set_leverage(symbol, leverage)
            return result
        except Exception as e:
            logger.error(f"Error setting leverage for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_user_trades_history(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get user trade history."""
        if not await self.ensure_initialized():
            return [{"error": "Client not initialized"}]
        
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            
            trades = await self.client.get_user_trades_history(params)
            return trades
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return [{"error": str(e)}]
    
    async def close(self) -> None:
        """Close the client connection."""
        if self.client:
            try:
                await self.client.close()
                logger.info("Bluefin client closed")
            except Exception as e:
                logger.error(f"Error closing Bluefin client: {e}")
        self.initialized = False

# Singleton instance
_client_instance = None

async def create_bluefin_client() -> BluefinClientWrapper:
    """
    Create or get the Bluefin client instance.
    This ensures we only have one client instance throughout the application.
    """
    global _client_instance
    
    # Load environment variables
    load_dotenv()
    
    if _client_instance is None:
        _client_instance = BluefinClientWrapper()
        await _client_instance.initialize()
    
    return _client_instance

async def close_bluefin_client() -> None:
    """Close the Bluefin client instance."""
    global _client_instance
    
    if _client_instance:
        await _client_instance.close()
        _client_instance = None

# Example usage
async def example_usage():
    """Example of how to use the Bluefin client."""
    client = await create_bluefin_client()
    
    # Get account information
    account_info = await client.get_account_info()
    print(f"Account info: {account_info}")
    
    # Get market price
    price_info = await client.get_market_price("SUI-PERP")
    print(f"Market price: {price_info}")
    
    # Close the client
    await close_bluefin_client()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(example_usage()) 
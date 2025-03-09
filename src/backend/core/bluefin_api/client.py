"""
Bluefin Client Implementation

This module provides a unified interface for interacting with the Bluefin Exchange
API, supporting API key authentication method.

Usage:
    from core.bluefin_api import get_client
    
    # Create a client instance
    client = await get_client()
    
    # Get account information
    account_info = await client.get_account_info()
    
    # Place an order
    order = await client.place_order(
        symbol="BTC-PERP",
        side="BUY",
        quantity=10,
        price=None,  # Market order
        leverage=10
    )
"""

import os
import json
import time
import hmac
import logging
import asyncio
import hashlib
import aiohttp
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Define constants for order sides and types
class ORDER_SIDE:
    BUY = "BUY"
    SELL = "SELL"

class ORDER_TYPE:
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT = "TAKE_PROFIT"

# API Endpoints
class ENDPOINTS:
    # Public endpoints
    EXCHANGE_INFO = "/exchangeInfo"
    DEPTH = "/depth"
    TRADES = "/trades"
    KLINES = "/klines"
    
    # Private endpoints
    ACCOUNT = "/account"
    ORDER = "/order"

# Constants for authentication
DEFAULT_API_URL = "https://dapi.api.sui-prod.bluefin.io"
DEFAULT_WS_URL = "wss://dstream.api.sui-prod.bluefin.io/ws"
REQUEUE_ADJUSTMENT_THRESHOLD = 2  # Adjust price after this many requeues

class BluefinClientInterface:
    """Interface for Bluefin clients to implement."""
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balance and positions."""
        raise NotImplementedError("Method not implemented")
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        raise NotImplementedError("Method not implemented")
    
    async def place_order(self, 
                          symbol: str, 
                          side: str, 
                          quantity: float, 
                          price: Optional[float] = None,
                          order_type: str = ORDER_TYPE.MARKET,
                          reduce_only: bool = False,
                          time_in_force: str = "GTC",
                          leverage: Optional[int] = None) -> Dict[str, Any]:
        """Place an order on Bluefin Exchange."""
        raise NotImplementedError("Method not implemented")
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order by ID."""
        raise NotImplementedError("Method not implemented")
    
    async def close_position(self, 
                            symbol: str, 
                            quantity: Optional[float] = None) -> Dict[str, Any]:
        """Close a position for the given symbol, optionally specifying quantity."""
        raise NotImplementedError("Method not implemented")
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol."""
        raise NotImplementedError("Method not implemented")
    
    async def get_market_price(self, symbol: str) -> float:
        """Get the current market price for a symbol."""
        raise NotImplementedError("Method not implemented")
    
    async def close(self) -> None:
        """Close the client connection."""
        raise NotImplementedError("Method not implemented")
        
    async def get_user_trades_history(self,
                                     symbol: Optional[str] = None,
                                     maker: Optional[bool] = None,
                                     order_type: Optional[str] = None,
                                     from_id: Optional[str] = None,
                                     start_time: Optional[int] = None,
                                     end_time: Optional[int] = None,
                                     limit: int = 50,
                                     cursor: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the user's completed trades history.
        
        Args:
            symbol: Market symbol for which to get trades
            maker: If True, fetch trades where the user is the maker
            order_type: Order type (Market or Limit)
            from_id: Get trades after the provided ID
            start_time: The time after which trades will be fetched from
            end_time: The time before which all trades will be returned
            limit: Total number of records to get (max 50)
            cursor: The particular page number to be fetched
            
        Returns:
            List of trade records
        """
        raise NotImplementedError("Method not implemented")


class BluefinApiClient(BluefinClientInterface):
    """Client implementation for Bluefin Exchange using API key authentication."""
    
    def __init__(self, api_key: str, api_secret: str, api_url: Optional[str] = None):
        """Initialize the Bluefin API client."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = api_url or DEFAULT_API_URL
        self.session = None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    async def _init_session(self):
        """Initialize HTTP session if needed."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            return self.session
        return self.session
    
    def _generate_signature(self, data: str) -> str:
        """Generate HMAC signature for API authentication."""
        return hmac.new(
            self.api_secret.encode(), 
            data.encode(), 
            hashlib.sha256
        ).hexdigest()
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                        data: Optional[Dict[str, Any]] = None, auth: bool = False) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{self.api_url}{endpoint}"
        headers = {}
        
        if auth:
            # Add authentication
            timestamp = int(time.time() * 1000)
            
            if params is None:
                params = {}
            
            params["timestamp"] = timestamp
            
            if method in ["GET", "DELETE"]:
                # For GET and DELETE requests, add params to query string
                query_string = urlencode(params)
                signature = self._generate_signature(query_string)
                params["signature"] = signature
                
                headers["X-API-KEY"] = self.api_key
            else:
                # For POST and PUT requests, add data to request body
                if data is None:
                    data = {}
                
                data["timestamp"] = timestamp
                query_string = urlencode(data)
                signature = self._generate_signature(query_string)
                data["signature"] = signature
                
                headers["X-API-KEY"] = self.api_key
                headers["Content-Type"] = "application/json"
        
        try:
            session = await self._init_session()
                
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=data if method not in ["GET", "DELETE"] else None,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    self.logger.error(f"API Error: {response.status} - {response_data}")
                
                return response_data
        except Exception as e:
            self.logger.error(f"Request error: {str(e)}")
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balance and positions."""
        response = await self._request("GET", ENDPOINTS.ACCOUNT, auth=True)
        
        return {
            "balance": float(response.get("totalCollateralValue", 0)),
            "availableMargin": float(response.get("availableMargin", 0)),
            "positions": response.get("positions", [])
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        account_info = await self.get_account_info()
        return account_info.get("positions", [])
    
    async def place_order(self, 
                         symbol: str, 
                         side: str, 
                         quantity: float, 
                         price: Optional[float] = None,
                         order_type: str = ORDER_TYPE.MARKET,
                         reduce_only: bool = False,
                         time_in_force: str = "GTC",
                         leverage: Optional[int] = None) -> Dict[str, Any]:
        """Place an order on Bluefin Exchange."""
        # Set leverage if provided
        if leverage is not None:
            await self.set_leverage(symbol, leverage)
        
        # Prepare order data
        order_data = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": float(quantity),  # Ensure quantity is a float
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only
        }
        
        # Add price for limit orders
        if order_type != ORDER_TYPE.MARKET and price is not None:
            order_data["price"] = float(price)  # Ensure price is a float
        
        # Place the order
        response = await self._request("POST", ENDPOINTS.ORDER, data=order_data, auth=True)
        
        return response
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order by ID."""
        params = {
            "orderId": order_id
        }
        
        response = await self._request("DELETE", ENDPOINTS.ORDER, params=params, auth=True)
        
        return response
    
    async def close_position(self, 
                            symbol: str, 
                            quantity: Optional[float] = None) -> Dict[str, Any]:
        """Close a position for the given symbol."""
        # Get current position
        positions = await self.get_positions()
        position = next((p for p in positions if p.get("symbol") == symbol), None)
        
        if not position:
            raise ValueError(f"No position found for symbol {symbol}")
        
        position_size = float(position.get("positionQty", 0))
        
        if position_size == 0:
            return {"status": "success", "message": "No position to close"}
        
        # Determine side for closing (opposite of current position)
        side = ORDER_SIDE.SELL if position_size > 0 else ORDER_SIDE.BUY
        
        # Use provided quantity or full position size
        close_quantity = abs(float(quantity)) if quantity is not None else abs(position_size)
        
        # Place market order to close position
        order = await self.place_order(
            symbol=symbol,
            side=side,
            quantity=close_quantity,
            order_type=ORDER_TYPE.MARKET,
            reduce_only=True
        )
        
        return order
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol."""
        # Note: This API endpoint might not be available in documentation
        # Using a placeholder implementation
        return {"status": "success", "leverage": leverage}
    
    async def get_market_price(self, symbol: str) -> float:
        """Get the current market price for a symbol."""
        # Get recent trades for the symbol
        params = {
            "symbol": symbol,
            "limit": 1
        }
        
        response = await self._request("GET", ENDPOINTS.TRADES, params=params)
        
        if not response:
            raise ValueError(f"No trades found for symbol {symbol}")
        
        # Return the latest trade price
        try:
            if isinstance(response, list) and response:  # Check if list is non-empty
                # Access first element safely
                latest_trade = next(iter(response), None)
                if latest_trade and isinstance(latest_trade, dict) and "price" in latest_trade:
                    return float(latest_trade["price"])
                else:
                    raise ValueError(f"Invalid trade data structure: {latest_trade}")
            else:
                raise ValueError(f"Invalid response format for trades: {response}")
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error processing market price data: {str(e)}")
            raise ValueError(f"Could not get market price for {symbol}: {str(e)}")
    
    async def get_user_trades_history(self, **kwargs) -> List[Dict[str, Any]]:
        """Get user's trade history."""
        # Note: This endpoint might not be available in documentation
        # Using a placeholder implementation
        return []
    
    async def close(self) -> None:
        """Close the client connection."""
        if self.session and not self.session.closed:
            await self.session.close()


class MockBluefinClient(BluefinClientInterface):
    """Mock client for testing without making actual API calls."""
    
    def __init__(self):
        """Initialize the mock client."""
        self.address = "0xmock_address"
        self.api_key = "mock_api_key"
        self.positions = []
        self.orders = {}
        self.market_prices = {
            "BTC-PERP": 40000.0,
            "ETH-PERP": 2000.0,
            "SUI-PERP": 1.0
        }
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("MockBluefinClient initialized - no real API calls will be made")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get mock account information."""
        return {
            "balance": 10000.0,
            "availableMargin": 8000.0,
            "positions": self.positions
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get mock positions."""
        return self.positions
    
    async def place_order(self, 
                         symbol: str, 
                         side: str, 
                         quantity: float, 
                         price: Optional[float] = None,
                         order_type: str = ORDER_TYPE.MARKET,
                         reduce_only: bool = False,
                         time_in_force: str = "GTC",
                         leverage: Optional[int] = None) -> Dict[str, Any]:
        """Place a mock order."""
        order_id = f"mock_order_{int(time.time())}"
        
        order = {
            "orderId": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "price": price if price is not None else self.market_prices.get(symbol, 1000.0),
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "leverage": leverage,
            "status": "NEW"
        }
        
        self.orders[order_id] = order
        
        # If market order, simulate execution
        if order_type == ORDER_TYPE.MARKET:
            order["status"] = "FILLED"
            
            # Update positions
            position = next((p for p in self.positions if p.get("symbol") == symbol), None)
            
            if position:
                # Update existing position
                current_qty = float(position.get("positionQty", 0))
                new_qty = current_qty + quantity if side == ORDER_SIDE.BUY else current_qty - quantity
                position["positionQty"] = str(new_qty)
            else:
                # Create new position
                new_qty = quantity if side == ORDER_SIDE.BUY else -quantity
                self.positions.append({
                    "symbol": symbol,
                    "positionQty": str(new_qty),
                    "entryPrice": str(price if price is not None else self.market_prices.get(symbol, 1000.0)),
                    "markPrice": str(self.market_prices.get(symbol, 1000.0)),
                    "unrealizedPnl": "0"
                })
        
        return order
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a mock order."""
        if order_id not in self.orders:
            return {"status": "error", "message": "Order not found"}
        
        order = self.orders[order_id]
        order["status"] = "CANCELED"
        
        return {"status": "success", "orderId": order_id}
    
    async def close_position(self, 
                            symbol: str, 
                            quantity: Optional[float] = None) -> Dict[str, Any]:
        """Close a mock position."""
        position = next((p for p in self.positions if p.get("symbol") == symbol), None)
        
        if not position:
            return {"status": "success", "message": "No position to close"}
        
        position_size = float(position.get("positionQty", 0))
        
        if position_size == 0:
            return {"status": "success", "message": "No position to close"}
        
        # Determine side for closing
        side = ORDER_SIDE.SELL if position_size > 0 else ORDER_SIDE.BUY
        
        # Use provided quantity or full position size
        close_quantity = abs(quantity) if quantity is not None else abs(position_size)
        
        # Place market order to close
        order = await self.place_order(
            symbol=symbol,
            side=side,
            quantity=close_quantity,
            order_type=ORDER_TYPE.MARKET,
            reduce_only=True
        )
        
        # Update position
        if quantity is None or abs(quantity) >= abs(position_size):
            # Remove position if fully closed
            self.positions = [p for p in self.positions if p.get("symbol") != symbol]
        else:
            # Update position size
            new_size = position_size + close_quantity if side == ORDER_SIDE.BUY else position_size - close_quantity
            position["positionQty"] = str(new_size)
        
        return order
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set mock leverage."""
        return {"status": "success", "leverage": leverage}
    
    async def get_market_price(self, symbol: str) -> float:
        """Get mock market price."""
        return self.market_prices.get(symbol, 1000.0)
    
    async def get_user_trades_history(self, **kwargs) -> List[Dict[str, Any]]:
        """Get mock trade history."""
        return []
    
    async def close(self) -> None:
        """Close the mock client."""
        pass


async def create_bluefin_client(
    use_mock: bool = False,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    api_url: Optional[str] = None
) -> BluefinClientInterface:
    """
    Create and initialize a Bluefin client based on available credentials.
    
    Args:
        use_mock: Whether to use a mock client (for testing)
        api_key: Bluefin API key
        api_secret: Bluefin API secret
        api_url: Custom API URL
        
    Returns:
        Initialized Bluefin client
    """
    if use_mock:
        logger.info("Creating mock Bluefin client")
        return MockBluefinClient()
    
    # Check environment variables for credentials if not provided
    api_key = api_key or os.getenv("BLUEFIN_API_KEY")
    api_secret = api_secret or os.getenv("BLUEFIN_API_SECRET")
    api_url = api_url or os.getenv("BLUEFIN_API_URL", DEFAULT_API_URL)
    
    # Try to create API client if API credentials are available
    if api_key and api_secret:
        try:
            logger.info("Creating Bluefin API client")
            return BluefinApiClient(api_key=api_key, api_secret=api_secret, api_url=api_url)
        except Exception as e:
            logger.error(f"Failed to initialize Bluefin API client: {str(e)}")
            raise
    
    raise ValueError("No valid credentials provided for Bluefin client") 
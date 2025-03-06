"""
Bluefin Client Implementation

This module provides a unified interface for interacting with the Bluefin Exchange
API, supporting both private key and API key authentication methods.

Usage:
    from core.bluefin_client import create_bluefin_client
    
    # Create a client instance
    client = await create_bluefin_client()
    
    # Get account information
    account_info = await client.get_account_info()
    
    # Place an order
    order = await client.place_order(
        symbol="SUI-PERP",
        side="BUY",
        quantity=10,
        price=None,  # Market order
        leverage=10
    )
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Union, Any

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
        """Get current market price for a symbol."""
        raise NotImplementedError("Method not implemented")
    
    async def close(self) -> None:
        """Close the client connection."""
        raise NotImplementedError("Method not implemented")

class BluefinSuiClient(BluefinClientInterface):
    """Client implementation for Bluefin Exchange using SUI private key authentication."""
    
    def __init__(self, private_key: str, network: str = "MAINNET"):
        """Initialize the Bluefin SUI client."""
        try:
            from bluefin_client_sui import BluefinClient as SuiClient, Networks
            
            self.network = getattr(Networks, network, Networks.MAINNET)
            self.client = SuiClient(
                private_key=private_key,
                network=self.network
            )
            logger.info(f"Initialized Bluefin SUI client for network: {network}")
        except ImportError:
            logger.error("Failed to import bluefin_client_sui. Please install it with: "
                        "pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git")
            raise
    
    async def init(self) -> None:
        """Initialize the client connection."""
        await self.client.init(onboarding=True)
        logger.info("Bluefin SUI client initialized successfully")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balance and positions."""
        account_data = await self.client.get_user_account_data()
        margin_data = await self.client.get_user_margin()
        positions = await self.client.get_user_positions() or []
        
        return {
            "balance": float(account_data.get("totalCollateralValue", 0)),
            "availableMargin": float(margin_data.get("availableMargin", 0)),
            "positions": positions
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        return await self.client.get_user_positions() or []
    
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
        
        # Convert order parameters
        from bluefin_client_sui import ORDER_SIDE as SUI_ORDER_SIDE
        from bluefin_client_sui import ORDER_TYPE as SUI_ORDER_TYPE
        
        # Map order side
        if side.upper() == ORDER_SIDE.BUY:
            sui_side = SUI_ORDER_SIDE.BUY
        else:
            sui_side = SUI_ORDER_SIDE.SELL
        
        # Map order type
        if order_type == ORDER_TYPE.MARKET:
            sui_order_type = SUI_ORDER_TYPE.MARKET
        elif order_type == ORDER_TYPE.LIMIT:
            sui_order_type = SUI_ORDER_TYPE.LIMIT
        elif order_type == ORDER_TYPE.STOP_MARKET:
            sui_order_type = SUI_ORDER_TYPE.STOP_MARKET
        elif order_type == ORDER_TYPE.TAKE_PROFIT:
            sui_order_type = SUI_ORDER_TYPE.TAKE_PROFIT
        else:
            sui_order_type = SUI_ORDER_TYPE.MARKET
        
        # Create order signature request
        try:
            signature_request = {
                "symbol": symbol,
                "side": sui_side,
                "quantity": str(quantity),
                "type": sui_order_type,
                "reduceOnly": reduce_only,
                "timeInForce": time_in_force
            }
            
            # Add price for limit orders
            if price is not None and order_type != ORDER_TYPE.MARKET:
                signature_request["price"] = str(price)
            
            # Create and submit the order
            signed_order = self.client.create_signed_order(signature_request)
            response = await self.client.post_signed_order(signed_order)
            
            return response
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            raise
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order by ID."""
        return await self.client.cancel_order(order_id)
    
    async def close_position(self, 
                            symbol: str, 
                            quantity: Optional[float] = None) -> Dict[str, Any]:
        """Close a position for the given symbol, optionally specifying quantity."""
        positions = await self.get_positions()
        
        # Find position for the symbol
        position = next((p for p in positions if p.get("symbol") == symbol), None)
        
        if not position:
            logger.warning(f"No position found for {symbol}")
            return {"status": "error", "message": "No position found"}
        
        # Determine quantity to close
        qty_to_close = quantity or position.get("quantity", 0)
        
        # Determine side (opposite of position side)
        position_side = position.get("side")
        close_side = ORDER_SIDE.SELL if position_side == "LONG" else ORDER_SIDE.BUY
        
        # Place closing order
        return await self.place_order(
            symbol=symbol,
            side=close_side,
            quantity=qty_to_close,
            reduce_only=True
        )
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol."""
        try:
            result = await self.client.set_leverage(symbol, leverage)
            logger.info(f"Leverage set to {leverage} for {symbol}")
            return result
        except Exception as e:
            logger.error(f"Failed to set leverage: {str(e)}")
            raise
    
    async def get_market_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        market_data = await self.client.get_market_data(symbol)
        return float(market_data.get("markPrice", 0))
    
    async def close(self) -> None:
        """Close the client connection."""
        await self.client.disconnect()
        logger.info("Bluefin SUI client disconnected")

class BluefinApiClient(BluefinClientInterface):
    """Client implementation for Bluefin Exchange using API key authentication."""
    
    def __init__(self, api_key: str, api_secret: str, api_url: Optional[str] = None):
        """Initialize the Bluefin V2 API client."""
        try:
            from bluefin.v2.client import BluefinClient
            
            self.client = BluefinClient(
                api_key=api_key,
                api_secret=api_secret,
                api_url=api_url
            )
            logger.info("Initialized Bluefin V2 API client")
        except ImportError:
            logger.error("Failed to import bluefin.v2.client. Please install it with: "
                        "pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git")
            raise
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balance and positions."""
        account_info = await self.client.get_account_info()
        return account_info
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        return await self.client.get_positions()
    
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
        
        # Convert order parameters
        order_params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "reduceOnly": reduce_only,
            "timeInForce": time_in_force
        }
        
        # Add price for limit orders
        if price is not None and order_type != ORDER_TYPE.MARKET:
            order_params["price"] = price
        
        # Place the order
        return await self.client.place_order(**order_params)
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order by ID."""
        return await self.client.cancel_order(order_id)
    
    async def close_position(self, 
                            symbol: str, 
                            quantity: Optional[float] = None) -> Dict[str, Any]:
        """Close a position for the given symbol, optionally specifying quantity."""
        return await self.client.close_position(symbol, quantity)
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol."""
        return await self.client.set_leverage(symbol, leverage)
    
    async def get_market_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        market_data = await self.client.get_market_data(symbol)
        return float(market_data.get("markPrice", 0))
    
    async def close(self) -> None:
        """Close the client connection."""
        await self.client.close_session()
        logger.info("Bluefin V2 API client closed")

class MockBluefinClient(BluefinClientInterface):
    """Mock client for testing without making actual API calls."""
    
    def __init__(self):
        """Initialize the mock client."""
        self.account_balance = 10000.0
        self.positions = []
        self.orders = []
        self.next_order_id = 1
        self.next_position_id = 1
        logger.info("Initialized Mock Bluefin client")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get mock account information."""
        return {
            "balance": self.account_balance,
            "availableMargin": self.account_balance * 0.9,
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
        # Generate mock price if not provided
        if price is None:
            price = 100.0  # Mock price
        
        # Create mock order
        order_id = f"order-{self.next_order_id}"
        self.next_order_id += 1
        
        order = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "type": order_type,
            "reduceOnly": reduce_only,
            "timeInForce": time_in_force,
            "status": "FILLED",
            "timestamp": int(asyncio.get_event_loop().time() * 1000)
        }
        
        self.orders.append(order)
        
        # If it's a market order and not reduce_only, create a position
        if order_type == ORDER_TYPE.MARKET and not reduce_only:
            position_id = f"position-{self.next_position_id}"
            self.next_position_id += 1
            
            position = {
                "id": position_id,
                "symbol": symbol,
                "side": "LONG" if side == ORDER_SIDE.BUY else "SHORT",
                "entryPrice": price,
                "markPrice": price,
                "quantity": quantity,
                "leverage": leverage or 5,
                "unrealizedPnl": 0.0,
                "marginType": "ISOLATED"
            }
            
            # Update existing position or add new one
            existing_position = next((p for p in self.positions if p["symbol"] == symbol), None)
            if existing_position:
                # Update existing position
                if existing_position["side"] == position["side"]:
                    # Adding to position
                    total_qty = existing_position["quantity"] + quantity
                    avg_price = ((existing_position["entryPrice"] * existing_position["quantity"]) + 
                               (price * quantity)) / total_qty
                    existing_position["quantity"] = total_qty
                    existing_position["entryPrice"] = avg_price
                else:
                    # Reducing position
                    net_qty = existing_position["quantity"] - quantity
                    if net_qty > 0:
                        existing_position["quantity"] = net_qty
                    elif net_qty < 0:
                        # Position flipped sides
                        existing_position["side"] = position["side"]
                        existing_position["quantity"] = abs(net_qty)
                        existing_position["entryPrice"] = price
                    else:
                        # Position closed
                        self.positions.remove(existing_position)
            else:
                # Add new position
                self.positions.append(position)
        
        # If it's a reduce_only order, reduce or close the position
        elif reduce_only:
            existing_position = next((p for p in self.positions if p["symbol"] == symbol), None)
            if existing_position:
                # Calculate new quantity
                new_qty = existing_position["quantity"] - quantity
                if new_qty <= 0:
                    # Close position
                    self.positions.remove(existing_position)
                else:
                    # Reduce position
                    existing_position["quantity"] = new_qty
        
        return order
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a mock order."""
        for order in self.orders:
            if order["id"] == order_id:
                order["status"] = "CANCELED"
                return {"id": order_id, "status": "CANCELED"}
        
        return {"error": "Order not found"}
    
    async def close_position(self, 
                            symbol: str, 
                            quantity: Optional[float] = None) -> Dict[str, Any]:
        """Close a mock position."""
        position = next((p for p in self.positions if p["symbol"] == symbol), None)
        
        if not position:
            return {"error": "Position not found"}
        
        qty_to_close = quantity or position["quantity"]
        side = ORDER_SIDE.SELL if position["side"] == "LONG" else ORDER_SIDE.BUY
        
        return await self.place_order(
            symbol=symbol,
            side=side,
            quantity=qty_to_close,
            reduce_only=True
        )
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set mock leverage."""
        for position in self.positions:
            if position["symbol"] == symbol:
                position["leverage"] = leverage
        
        return {"symbol": symbol, "leverage": leverage}
    
    async def get_market_price(self, symbol: str) -> float:
        """Get mock market price."""
        return 100.0  # Mock price
    
    async def close(self) -> None:
        """Close the mock client."""
        logger.info("Mock Bluefin client closed")

async def create_bluefin_client(
    use_mock: bool = False,
    private_key: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    network: str = "MAINNET",
    api_url: Optional[str] = None
) -> BluefinClientInterface:
    """
    Create and initialize a Bluefin client based on available credentials.
    
    Args:
        use_mock: Whether to use a mock client (for testing)
        private_key: Bluefin private key (for SUI network)
        api_key: Bluefin API key
        api_secret: Bluefin API secret
        network: Network to connect to (MAINNET or TESTNET)
        api_url: Custom API URL (for v2 client)
        
    Returns:
        Initialized Bluefin client
    """
    if use_mock:
        logger.info("Creating mock Bluefin client")
        return MockBluefinClient()
    
    # Check environment variables for credentials if not provided
    private_key = private_key or os.environ.get("BLUEFIN_PRIVATE_KEY")
    api_key = api_key or os.environ.get("BLUEFIN_API_KEY")
    api_secret = api_secret or os.environ.get("BLUEFIN_API_SECRET")
    network = network or os.environ.get("BLUEFIN_NETWORK", "MAINNET")
    api_url = api_url or os.environ.get("BLUEFIN_API_URL")
    
    # Try to create SUI client if private key is available
    if private_key:
        try:
            logger.info("Creating Bluefin SUI client")
            client = BluefinSuiClient(private_key=private_key, network=network)
            await client.init()
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Bluefin SUI client: {str(e)}")
            if not (api_key and api_secret):
                raise
    
    # Try to create API client if API credentials are available
    if api_key and api_secret:
        try:
            logger.info("Creating Bluefin V2 API client")
            return BluefinApiClient(api_key=api_key, api_secret=api_secret, api_url=api_url)
        except Exception as e:
            logger.error(f"Failed to initialize Bluefin V2 API client: {str(e)}")
            raise
    
    # If we get here and no clients could be created, raise an error
    raise ValueError(
        "Unable to create Bluefin client. Please provide either a private key "
        "or API key and secret, or set them in environment variables."
    ) 
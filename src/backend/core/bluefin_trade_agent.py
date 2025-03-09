"""
Bluefin Trade Agent Implementation

This module provides a trading agent implementation for Bluefin Exchange,
using the Bluefin API client to execute trades based on signals.

Usage:
    from core.bluefin_trade_agent import BluefinTradeAgent
    
    # Create a trade agent
    agent = BluefinTradeAgent(
        api_key="your_api_key",
        api_secret="your_api_secret"
    )
    
    # Start the agent
    await agent.start()
    
    # Execute a trade based on a signal
    await agent.execute_trade(
        symbol="BTC-PERP",
        side="BUY",
        quantity=0.1,
        price=None,  # Market order
        leverage=10
    )
    
    # Stop the agent
    await agent.stop()
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Union, Any

from core.bluefin_api.client import BluefinClientInterface, create_bluefin_client
from core.bluefin_api.client import ORDER_SIDE, ORDER_TYPE

logger = logging.getLogger(__name__)

class TradeStatus:
    """Trade status constants."""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class BluefinTradeAgent:
    """
    Trading agent for Bluefin Exchange.
    
    This agent is responsible for executing trades on Bluefin Exchange
    based on signals, and managing positions.
    """
    
    def __init__(self, 
                api_key: Optional[str] = None, 
                api_secret: Optional[str] = None,
                use_mock: bool = False,
                api_url: Optional[str] = None):
        """
        Initialize the Bluefin trade agent.
        
        Args:
            api_key: Bluefin API key (defaults to environment variable)
            api_secret: Bluefin API secret (defaults to environment variable)
            use_mock: Whether to use a mock client for testing
            api_url: Custom API URL
        """
        self.api_key = api_key or os.getenv("BLUEFIN_API_KEY")
        self.api_secret = api_secret or os.getenv("BLUEFIN_API_SECRET")
        self.api_url = api_url
        self.use_mock = use_mock
        
        self.client = None
        self.running = False
        self.active_trades = {}
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the trade agent."""
        if self.running:
            self.logger.warning("Trade agent is already running")
            return
        
        self.logger.info("Starting Bluefin trade agent")
        
        try:
            self.client = await create_bluefin_client(
                use_mock=self.use_mock,
                api_key=self.api_key,
                api_secret=self.api_secret,
                api_url=self.api_url
            )
            
            # Get account info to verify connectivity
            account_info = await self.client.get_account_info()
            self.logger.info(f"Connected to Bluefin. Available margin: {account_info.get('availableMargin')}")
            
            self.running = True
        except Exception as e:
            self.logger.error(f"Failed to start trade agent: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the trade agent."""
        if not self.running:
            self.logger.warning("Trade agent is not running")
            return
        
        self.logger.info("Stopping Bluefin trade agent")
        
        try:
            if self.client:
                await self.client.close()
                self.client = None
            
            self.running = False
        except Exception as e:
            self.logger.error(f"Error stopping trade agent: {str(e)}")
            raise
    
    async def execute_trade(self,
                           symbol: str,
                           side: str,
                           quantity: float,
                           price: Optional[float] = None,
                           order_type: str = ORDER_TYPE.MARKET,
                           leverage: Optional[int] = None,
                           reduce_only: bool = False,
                           time_in_force: str = "GTC") -> Dict[str, Any]:
        """
        Execute a trade on Bluefin Exchange.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC-PERP")
            side: Order side (BUY or SELL)
            quantity: Order quantity
            price: Order price (required for limit orders)
            order_type: Order type (MARKET, LIMIT, etc.)
            leverage: Leverage to use for the trade
            reduce_only: Whether the order should only reduce position
            time_in_force: Time in force for the order
        
        Returns:
            Order information
        """
        if not self.running or not self.client:
            raise RuntimeError("Trade agent is not running")
        
        self.logger.info(f"Executing {side} {order_type} order for {quantity} {symbol}")
        
        try:
            # Place the order
            order = await self.client.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type=order_type,
                reduce_only=reduce_only,
                time_in_force=time_in_force,
                leverage=leverage
            )
            
            # Track the order
            order_id = order.get("orderId")
            if order_id:
                self.active_trades[order_id] = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "order_type": order_type,
                    "status": TradeStatus.EXECUTED if order.get("status") == "FILLED" else TradeStatus.PENDING
                }
            
            self.logger.info(f"Order executed: {order}")
            return order
        except Exception as e:
            self.logger.error(f"Failed to execute trade: {str(e)}")
            raise
    
    async def cancel_trade(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a trade by order ID.
        
        Args:
            order_id: The ID of the order to cancel
        
        Returns:
            Order cancellation information
        """
        if not self.running or not self.client:
            raise RuntimeError("Trade agent is not running")
        
        self.logger.info(f"Canceling order {order_id}")
        
        try:
            # Cancel the order
            result = await self.client.cancel_order(order_id)
            
            # Update order status
            if order_id in self.active_trades:
                self.active_trades[order_id]["status"] = TradeStatus.CANCELED
            
            self.logger.info(f"Order canceled: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to cancel trade: {str(e)}")
            raise
    
    async def close_position(self, 
                            symbol: str, 
                            quantity: Optional[float] = None) -> Dict[str, Any]:
        """
        Close a position for the given symbol.
        
        Args:
            symbol: The symbol of the position to close
            quantity: The quantity to close (if None, close entire position)
        
        Returns:
            Order information for the closing order
        """
        if not self.running or not self.client:
            raise RuntimeError("Trade agent is not running")
        
        self.logger.info(f"Closing position for {symbol}" + 
                        (f" (quantity: {quantity})" if quantity is not None else ""))
        
        try:
            # Close the position
            result = await self.client.close_position(symbol, quantity)
            
            self.logger.info(f"Position closed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to close position: {str(e)}")
            raise
    
    async def check_market_conditions(self, symbol: str) -> Dict[str, Any]:
        """
        Check market conditions for a symbol.
        
        Args:
            symbol: The symbol to check
        
        Returns:
            Market conditions information
        """
        if not self.running or not self.client:
            raise RuntimeError("Trade agent is not running")
        
        try:
            # Get current market price
            market_price = await self.client.get_market_price(symbol)
            
            # Get position information
            positions = await self.client.get_positions()
            position = next((p for p in positions if p.get("symbol") == symbol), None)
            
            # Return market conditions
            return {
                "symbol": symbol,
                "price": market_price,
                "has_position": position is not None,
                "position": position
            }
        except Exception as e:
            self.logger.error(f"Failed to check market conditions: {str(e)}")
            raise
    
    async def adjust_position(self, 
                            symbol: str, 
                            target_size: float,
                            leverage: Optional[int] = None) -> Dict[str, Any]:
        """
        Adjust position size to reach target size.
        
        Args:
            symbol: The symbol to adjust position for
            target_size: The target position size (positive for long, negative for short)
            leverage: Leverage to use
        
        Returns:
            Order information if a trade was executed
        """
        if not self.running or not self.client:
            raise RuntimeError("Trade agent is not running")
        
        self.logger.info(f"Adjusting position for {symbol} to target size: {target_size}")
        
        try:
            # Get current position
            positions = await self.client.get_positions()
            position = next((p for p in positions if p.get("symbol") == symbol), None)
            
            current_size = float(position.get("positionQty", 0)) if position else 0
            
            # If target is same as current, nothing to do
            if abs(current_size - target_size) < 0.00001:
                self.logger.info(f"Position already at target size: {current_size}")
                return {"status": "success", "message": "Position already at target size"}
            
            # Calculate size difference
            size_diff = target_size - current_size
            
            # Determine side
            side = ORDER_SIDE.BUY if size_diff > 0 else ORDER_SIDE.SELL
            
            # Place order
            order = await self.execute_trade(
                symbol=symbol,
                side=side,
                quantity=abs(size_diff),
                leverage=leverage
            )
            
            return order
        except Exception as e:
            self.logger.error(f"Failed to adjust position: {str(e)}")
            raise


async def main():
    """Example usage of the BluefinTradeAgent."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and start the agent
    agent = BluefinTradeAgent(use_mock=True)  # Use mock for testing
    
    try:
        await agent.start()
        
        # Check market conditions
        market_conditions = await agent.check_market_conditions("BTC-PERP")
        logging.info(f"Market conditions: {market_conditions}")
        
        # Execute a trade
        order = await agent.execute_trade(
            symbol="BTC-PERP",
            side=ORDER_SIDE.BUY,
            quantity=0.1,
            leverage=10
        )
        
        # Adjust position
        await agent.adjust_position(
            symbol="BTC-PERP",
            target_size=0.2,
            leverage=10
        )
        
        # Close position
        await agent.close_position("BTC-PERP")
    finally:
        # Stop the agent
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main()) 
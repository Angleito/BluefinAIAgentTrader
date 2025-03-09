import asyncio
import logging
import time
from datetime import datetime
from core.config import TRADING_PARAMS

logger = logging.getLogger(__name__)

async def check_existing_positions(client, symbol, side):
    """
    Check if there are existing positions for the given symbol with the opposite side.
    
    Args:
        client: The Bluefin client
        symbol: The trading pair symbol
        side: The side of the new trade (BUY or SELL)
        
    Returns:
        tuple: (has_opposite_position, position_size, position_details)
    """
    logger.info(f"Checking existing positions for {symbol} with opposite side of {side}")
    
    try:
        # Get current positions
        positions = await client.get_positions()
        
        # Determine the opposite side
        opposite_side = "SELL" if side == "BUY" else "BUY"
        
        # Filter positions for the given symbol and opposite side
        opposite_positions = [
            p for p in positions 
            if p["symbol"] == symbol and p["side"] == opposite_side
        ]
        
        if opposite_positions:
            position = opposite_positions[0]
            logger.info(f"Found opposite position: {position}")
            return True, float(position.get("size", 0)), position
        else:
            logger.info(f"No opposite positions found for {symbol}")
            return False, 0.0, None
            
    except Exception as e:
        logger.exception(f"Error checking existing positions: {e}")
        return False, 0.0, None

async def execute_trade(signal):
    """
    Execute a trade on Bluefin Exchange based on the processed signal.
    
    Args:
        signal: The processed signal with trade parameters
        
    Returns:
        dict: Trade execution result
    """
    if not signal:
        logger.error("No signal provided for trade execution")
        return {"success": False, "reason": "No signal provided"}
    
    try:
        # Get the Bluefin client from the global context
        # This is initialized in main.py
        from main import bluefin_client
        
        if not bluefin_client:
            logger.error("Bluefin client not initialized")
            return {"success": False, "reason": "Bluefin client not initialized"}
        
        # Set the timestamp for the trade
        signal["timestamp"] = int(time.time())
        
        # Get account balance
        account_info = await bluefin_client.get_account_info()
        available_balance = float(account_info.get("availableMargin", 0))
        
        logger.info(f"Account balance: {available_balance}")
        
        # Check for existing opposite positions
        has_opposite_position, opposite_position_size, _ = await check_existing_positions(
            bluefin_client, 
            signal["symbol"], 
            "BUY" if signal["type"].upper() == "BUY" else "SELL"
        )
        
        # Calculate position size
        position_size = calculate_actual_position_size(
            available_balance, 
            signal["position_size"], 
            signal["leverage"]
        )
        
        # Double the position size if there's an opposite position
        if has_opposite_position and TRADING_PARAMS.get("DOUBLE_SIZE_ON_OPPOSITE_POSITION", False):
            logger.info(f"Doubling position size due to existing opposite position")
            position_size *= 2
        
        # Set leverage for the symbol
        await set_leverage(bluefin_client, signal["symbol"], signal["leverage"])
        
        # Execute the trade
        if signal["type"].upper() == "BUY":
            trade_result = await open_long_position(
                bluefin_client,
                signal["symbol"],
                position_size,
                signal["stop_loss"],
                signal["take_profit"]
            )
        else:  # sell
            trade_result = await open_short_position(
                bluefin_client,
                signal["symbol"],
                position_size,
                signal["stop_loss"],
                signal["take_profit"]
            )
        
        # Log the trade
        log_trade(signal, trade_result)
        
        return {
            "success": True,
            "trade_id": trade_result.get("id", ""),
            "entry_price": float(trade_result.get("price", 0)),
            "position_size": position_size,
            "timestamp": signal["timestamp"],
            "type": signal["type"],
            "symbol": signal["symbol"],
            "doubled_size": has_opposite_position and TRADING_PARAMS.get("DOUBLE_SIZE_ON_OPPOSITE_POSITION", False)
        }
        
    except Exception as e:
        logger.exception(f"Error executing trade: {e}")
        return {"success": False, "reason": f"Error executing trade: {str(e)}"}

async def set_leverage(client, symbol, leverage):
    """
    Set the leverage for a trading pair.
    
    Args:
        client: The Bluefin client
        symbol: The trading pair symbol
        leverage: The leverage to set
        
    Returns:
        dict: The result of setting the leverage
    """
    logger.info(f"Setting leverage for {symbol} to {leverage}x")
    
    try:
        result = await client.set_leverage(symbol, leverage)
        logger.info(f"Leverage set successfully: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error setting leverage: {e}")
        raise

async def open_long_position(client, symbol, size, stop_loss_percentage, take_profit_percentage):
    """
    Open a long position on Bluefin Exchange.
    
    Args:
        client: The Bluefin client
        symbol: The trading pair symbol
        size: The position size
        stop_loss_percentage: The stop loss percentage
        take_profit_percentage: The take profit percentage
        
    Returns:
        dict: The result of opening the position
    """
    logger.info(f"Opening long position for {symbol} with size {size}")
    
    try:
        # Get current market price
        market_price = await get_market_price(client, symbol)
        
        # Calculate stop loss and take profit prices
        stop_loss_price = market_price * (1 - stop_loss_percentage)
        take_profit_price = market_price * (1 + take_profit_percentage)
        
        # Open the position
        position = await client.place_order(
            symbol=symbol,
            side="BUY",
            quantity=size,
            price=None,  # Market order
            order_type="MARKET",
            reduce_only=False
        )
        
        # Set stop loss
        await client.place_order(
            symbol=symbol,
            side="SELL",
            quantity=size,
            price=stop_loss_price,
            order_type="STOP_MARKET",
            reduce_only=True
        )
        
        # Set take profit
        await client.place_order(
            symbol=symbol,
            side="SELL",
            quantity=size,
            price=take_profit_price,
            order_type="LIMIT",
            reduce_only=True
        )
        
        logger.info(f"Long position opened successfully: {position}")
        return position
    except Exception as e:
        logger.exception(f"Error opening long position: {e}")
        raise

async def open_short_position(client, symbol, size, stop_loss_percentage, take_profit_percentage):
    """
    Open a short position on Bluefin Exchange.
    
    Args:
        client: The Bluefin client
        symbol: The trading pair symbol
        size: The position size
        stop_loss_percentage: The stop loss percentage
        take_profit_percentage: The take profit percentage
        
    Returns:
        dict: The result of opening the position
    """
    logger.info(f"Opening short position for {symbol} with size {size}")
    
    try:
        # Get current market price
        market_price = await get_market_price(client, symbol)
        
        # Calculate stop loss and take profit prices
        stop_loss_price = market_price * (1 + stop_loss_percentage)
        take_profit_price = market_price * (1 - take_profit_percentage)
        
        # Open the position
        position = await client.place_order(
            symbol=symbol,
            side="SELL",
            quantity=size,
            price=None,  # Market order
            order_type="MARKET",
            reduce_only=False
        )
        
        # Set stop loss
        await client.place_order(
            symbol=symbol,
            side="BUY",
            quantity=size,
            price=stop_loss_price,
            order_type="STOP_MARKET",
            reduce_only=True
        )
        
        # Set take profit
        await client.place_order(
            symbol=symbol,
            side="BUY",
            quantity=size,
            price=take_profit_price,
            order_type="LIMIT",
            reduce_only=True
        )
        
        logger.info(f"Short position opened successfully: {position}")
        return position
    except Exception as e:
        logger.exception(f"Error opening short position: {e}")
        raise

async def get_market_price(client, symbol):
    """
    Get the current market price for a symbol.
    
    Args:
        client: The Bluefin client
        symbol: The trading pair symbol
        
    Returns:
        float: The current market price
    """
    try:
        # Get market price using the client's method
        market_price = await client.get_market_price(symbol)
        
        logger.info(f"Current market price for {symbol}: {market_price}")
        return market_price
    except Exception as e:
        logger.exception(f"Error getting market price: {e}")
        return 0.0

def calculate_actual_position_size(balance, position_size_percentage, leverage):
    """
    Calculate the actual position size based on account balance, position size percentage, and leverage.
    
    Args:
        balance: The account balance
        position_size_percentage: The position size as a percentage of the portfolio
        leverage: The leverage to use
        
    Returns:
        float: The actual position size
    """
    # Calculate the position size in USD
    position_size_usd = balance * position_size_percentage
    
    # Apply leverage
    leveraged_position_size = position_size_usd * leverage
    
    return leveraged_position_size

def log_trade(signal, trade_result):
    """
    Log the trade details for performance tracking.
    
    Args:
        signal: The processed signal
        trade_result: The result of the trade execution
    """
    trade_log = {
        "timestamp": datetime.fromtimestamp(signal["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": signal["symbol"],
        "type": signal["type"],
        "entry_price": trade_result["price"],
        "position_size": trade_result["quantity"],
        "leverage": signal["leverage"],
        "stop_loss": signal["stop_loss"],
        "take_profit": signal["take_profit"]
    }
    
    logger.info(f"Trade logged: {trade_log}")
    
    # In a real implementation, this would write to a database or file
    # For now, just log to the console 
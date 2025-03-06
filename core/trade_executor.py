import asyncio
import logging
from bluefin_client_sui import BluefinClient
from core.risk_manager import risk_manager
from core.performance_tracker import performance_tracker

logger = logging.getLogger(__name__)

async def execute_trade(client: BluefinClient, signal: dict):
    """Execute a trade on Bluefin based on the signal."""
    symbol = signal["symbol"]
    trade_type = signal["type"]
    entry_price = signal["entry_price"]
    stop_loss = signal["stop_loss"] 
    take_profit = signal["take_profit"]
    
    # Calculate position size based on risk
    position_size = risk_manager.calculate_position_size(entry_price, stop_loss)
    
    # Check if trade can be opened
    can_open, adjusted_size, reason = risk_manager.can_open_new_trade(
        symbol, entry_price, stop_loss, position_size
    )
    
    if not can_open:
        logger.warning(f"Cannot open trade: {reason}")
        return None
    
    # Open position
    order = await client.create_market_order(
        symbol=symbol,
        side="buy" if trade_type == "buy" else "sell",
        quantity=adjusted_size,
        reduce_only=False
    )
    
    if "id" not in order:
        logger.error(f"Failed to open position: {order}")
        return None
    
    # Set stop loss and take profit
    await client.create_stop_order(
        symbol=symbol,
        side="sell" if trade_type == "buy" else "buy",
        quantity=adjusted_size,
        trigger_price=stop_loss,
        reduce_only=True
    )
    
    await client.create_limit_order(
        symbol=symbol,
        side="sell" if trade_type == "buy" else "buy",
        quantity=adjusted_size,
        price=take_profit,
        reduce_only=True
    )
    
    # Log and track the trade
    trade = {
        "symbol": symbol,
        "type": trade_type,
        "entry_price": entry_price,
        "position_size": adjusted_size,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "entry_time": int(order["timestamp"])
    }
    
    performance_tracker.log_trade_entry(trade)
    
    return trade
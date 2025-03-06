import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Get configuration from environment or config file
try:
    from config import TRADING_PARAMS, RISK_PARAMS
except ImportError:
    # Default values if config isn't available
    TRADING_PARAMS = {
        "position_size_percentage": float(os.getenv("DEFAULT_POSITION_SIZE_PCT", 0.05)),
        "leverage": int(os.getenv("DEFAULT_LEVERAGE", 7)),
        "stop_loss_percentage": float(os.getenv("DEFAULT_STOP_LOSS_PCT", 0.15)),
        "take_profit_multiplier": 2.0,
        "trading_pairs": ["BTC-PERP", "ETH-PERP", "SOL-PERP", "SUI-PERP"],
    }
    RISK_PARAMS = {
        "max_positions": int(os.getenv("DEFAULT_MAX_POSITIONS", 3)),
    }

logger = logging.getLogger(__name__)

# VuManChu Cipher B signal types
BULLISH_SIGNALS = ["GREEN_CIRCLE", "GOLD_CIRCLE", "BULL_FLAG", "BULL_DIAMOND"]
BEARISH_SIGNALS = ["RED_CIRCLE", "BEAR_FLAG", "BEAR_DIAMOND"]
AMBIGUOUS_SIGNALS = ["PURPLE_TRIANGLE", "LITTLE_CIRCLE"]

def get_trade_direction(signal_type: str, action: Optional[str] = None) -> str:
    """
    Determine if a signal is Bullish (long) or Bearish (short)
    
    Args:
        signal_type: The VuManChu Cipher B signal type
        action: BUY or SELL action, needed for ambiguous signals
        
    Returns:
        str: "buy" for long trades, "sell" for short trades
    """
    if signal_type in BULLISH_SIGNALS:
        return "buy"
    elif signal_type in BEARISH_SIGNALS:
        return "sell"
    else:
        # For ambiguous signals like PURPLE_TRIANGLE or LITTLE_CIRCLE
        # use the specified action to determine direction
        if action and action.upper() == "BUY":
            return "buy"
        elif action and action.upper() == "SELL":
            return "sell"
        else:
            # Default to buy if can't determine
            return "buy"

def map_tradingview_to_bluefin_symbol(tv_symbol: str) -> str:
    """
    Map TradingView symbol format to Bluefin format.
    
    Args:
        tv_symbol: Symbol in TradingView format (e.g., "SUI/USD")
        
    Returns:
        str: Symbol in Bluefin format (e.g., "SUI-PERP")
    """
    # Handle common formats
    if "/" in tv_symbol:
        base_currency = tv_symbol.split("/")[0]
        return f"{base_currency}-PERP"
    elif ":" in tv_symbol:
        # Handle exchange:symbol format (e.g., "BINANCE:BTCUSDT")
        base_symbol = tv_symbol.split(":")[1]
        # Extract the base currency from common formats
        if "USDT" in base_symbol:
            base_currency = base_symbol.replace("USDT", "")
        elif "USD" in base_symbol:
            base_currency = base_symbol.replace("USD", "")
        else:
            # Use as is if format is unknown
            base_currency = base_symbol
        return f"{base_currency}-PERP"
    else:
        # If no special format, assume it's already the base currency
        return f"{tv_symbol}-PERP"

def process_tradingview_alert(alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process an alert from TradingView, specifically for VuManChu Cipher B indicator.
    
    Args:
        alert_data: The alert data from TradingView webhook
        
    Returns:
        Optional[Dict[str, Any]]: Processed signal ready for trade execution, or None if invalid
    """
    logger.info(f"Processing TradingView alert: {alert_data}")
    
    # Validate required fields
    required_fields = ["symbol", "timeframe", "signal_type"]
    for field in required_fields:
        if field not in alert_data:
            logger.warning(f"Missing required field: {field}")
            return None
    
    # Get the trade direction (buy/sell)
    trade_direction = get_trade_direction(
        alert_data["signal_type"], 
        alert_data.get("action")
    )
    
    # Map the symbol to Bluefin format
    bluefin_symbol = map_tradingview_to_bluefin_symbol(alert_data["symbol"])
    
    # Ensure the symbol is supported
    if not any(bluefin_symbol.startswith(pair.split("-")[0]) for pair in TRADING_PARAMS["trading_pairs"]):
        logger.warning(f"Unsupported trading pair: {bluefin_symbol}")
        return None
    
    # Create the processed signal
    processed_signal = {
        "symbol": bluefin_symbol,
        "type": trade_direction,
        "timeframe": alert_data["timeframe"],
        "signal_type": alert_data["signal_type"],
        "entry_time": datetime.utcnow().isoformat(),
        "position_size": calculate_position_size(),
        "leverage": TRADING_PARAMS["leverage"],
        "stop_loss": calculate_stop_loss(trade_direction),
        "take_profit": calculate_take_profit(trade_direction),
        "confidence": calculate_signal_confidence(alert_data["signal_type"]),
        "original_alert": alert_data,
    }
    
    logger.info(f"Processed signal: {processed_signal}")
    return processed_signal

def calculate_position_size() -> float:
    """
    Calculate position size as a percentage of the portfolio.
    
    Returns:
        float: Position size as a decimal (e.g., 0.05 for 5%)
    """
    # For now, use the configured position size percentage
    # In a production system, this would take into account:
    # - Current portfolio value
    # - Risk per trade
    # - Volatility of the asset
    return TRADING_PARAMS["position_size_percentage"]

def calculate_stop_loss(trade_direction: str) -> float:
    """
    Calculate stop loss percentage based on the trade direction.
    
    Args:
        trade_direction: "buy" or "sell" 
        
    Returns:
        float: Stop loss percentage as a decimal
    """
    stop_loss_pct = TRADING_PARAMS["stop_loss_percentage"]
    # No need to adjust based on direction - that will be handled when placing the order
    return stop_loss_pct

def calculate_take_profit(trade_direction: str) -> float:
    """
    Calculate take profit percentage based on the trade direction and risk:reward.
    
    Args:
        trade_direction: "buy" or "sell"
        
    Returns:
        float: Take profit percentage as a decimal
    """
    # Calculate take profit based on the stop loss and the risk:reward multiplier
    stop_loss_pct = calculate_stop_loss(trade_direction)
    take_profit_pct = stop_loss_pct * TRADING_PARAMS["take_profit_multiplier"]
    return take_profit_pct

def calculate_signal_confidence(signal_type: str) -> float:
    """
    Calculate a confidence score for the signal.
    
    Args:
        signal_type: The VuManChu Cipher B signal type
        
    Returns:
        float: Confidence score between 0 and 1
    """
    # Assign confidence scores based on signal type
    # These values can be adjusted based on backtesting results
    confidence_map = {
        "GOLD_CIRCLE": 0.9,     # Highest confidence - strong buy signal
        "GREEN_CIRCLE": 0.8,    # Strong buy signal
        "RED_CIRCLE": 0.8,      # Strong sell signal
        "BULL_DIAMOND": 0.75,   # Good bullish pattern
        "BEAR_DIAMOND": 0.75,   # Good bearish pattern
        "BULL_FLAG": 0.7,       # Bullish pattern
        "BEAR_FLAG": 0.7,       # Bearish pattern
        "PURPLE_TRIANGLE": 0.6, # Divergence - moderate confidence
        "LITTLE_CIRCLE": 0.5,   # Wave crossing - lowest confidence
    }
    
    return confidence_map.get(signal_type, 0.5)

async def can_open_new_position(client) -> bool:
    """
    Check if a new position can be opened based on risk parameters.
    
    Args:
        client: Bluefin client instance
        
    Returns:
        bool: True if a new position can be opened, False otherwise
    """
    try:
        # Get account information
        account_info = await client.get_account_info()
        
        # Get current positions
        positions = account_info.get("positions", [])
        open_positions = [p for p in positions if float(p.get("quantity", 0)) > 0]
        
        # Check if max positions limit is reached
        max_positions = RISK_PARAMS.get("max_positions", 3)
        
        if len(open_positions) >= max_positions:
            logger.warning(f"Maximum number of positions ({max_positions}) reached. Cannot open new position.")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking if new position can be opened: {str(e)}")
        return False 
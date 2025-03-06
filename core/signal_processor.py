import logging
from config import TRADING_PARAMS

logger = logging.getLogger(__name__)

def process_signal(signal):
    """
    Process the incoming trading signal from TradingView.
    
    Args:
        signal: The SignalModel object containing signal data
        
    Returns:
        dict: Processed signal with additional metadata for trade execution
    """
    logger.info(f"Processing signal: {signal.type} for {signal.symbol} on {signal.timeframe}")
    
    # Validate signal type (buy/sell)
    if signal.type not in ["buy", "sell"]:
        logger.warning(f"Invalid signal type: {signal.type}. Must be 'buy' or 'sell'.")
        return None
    
    # Validate trading pair
    if signal.symbol not in TRADING_PARAMS["trading_pairs"]:
        logger.warning(f"Unsupported trading pair: {signal.symbol}. Must be one of {TRADING_PARAMS['trading_pairs']}.")
        return None
    
    # Validate confidence level
    if signal.confidence < 0.5:
        logger.warning(f"Signal confidence too low: {signal.confidence}. Minimum required is 0.5.")
        return None
    
    # Check for required indicators
    required_indicators = ["vumanchuA", "vumanchuB", "heikenAshi"]
    missing_indicators = [ind for ind in required_indicators if ind not in signal.indicators]
    
    if missing_indicators:
        logger.warning(f"Missing required indicators: {missing_indicators}")
        return None
    
    # Process the signal
    processed_signal = {
        "type": signal.type,
        "symbol": signal.symbol,
        "timeframe": signal.timeframe,
        "indicators": signal.indicators,
        "confidence": signal.confidence,
        "position_size": calculate_position_size(signal.symbol),
        "leverage": TRADING_PARAMS["leverage"],
        "stop_loss": calculate_stop_loss(signal.type, signal.indicators),
        "take_profit": calculate_take_profit(signal.type, signal.indicators),
        "timestamp": None  # Will be set when executing the trade
    }
    
    logger.info(f"Signal processed successfully: {processed_signal}")
    return processed_signal

def calculate_position_size(symbol):
    """
    Calculate the position size based on the trading parameters.
    
    Args:
        symbol: The trading pair symbol
        
    Returns:
        float: The position size as a percentage of the portfolio
    """
    # For now, use the default position size from config
    # In a real implementation, this would calculate based on account balance
    return TRADING_PARAMS["position_size_percentage"]

def calculate_stop_loss(signal_type, indicators):
    """
    Calculate the stop loss price based on the signal type and indicators.
    
    Args:
        signal_type: The type of signal (buy/sell)
        indicators: The indicator values from the signal
        
    Returns:
        float: The stop loss percentage
    """
    # For now, use the default stop loss from config
    # In a real implementation, this would calculate based on volatility and indicators
    stop_loss_percentage = TRADING_PARAMS["stop_loss_percentage"]
    
    # Adjust stop loss based on signal type
    # For buy signals, stop loss is below entry price
    # For sell signals, stop loss is above entry price
    return stop_loss_percentage

def calculate_take_profit(signal_type, indicators):
    """
    Calculate the take profit price based on the signal type and indicators.
    
    Args:
        signal_type: The type of signal (buy/sell)
        indicators: The indicator values from the signal
        
    Returns:
        float: The take profit percentage
    """
    # Calculate take profit based on risk-reward ratio
    # For now, use a simple 2:1 risk-reward ratio
    stop_loss = calculate_stop_loss(signal_type, indicators)
    take_profit = stop_loss * 2
    
    return take_profit 
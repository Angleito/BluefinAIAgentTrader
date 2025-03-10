import logging
import math
from core.performance_tracker import performance_tracker
import os

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Manage trading risk and position sizing.
    """
    
    def __init__(self, account_balance=10000, max_risk_per_trade=None, max_open_trades=5,
                 max_daily_drawdown=0.05, max_risk_per_symbol=0.1):
        """
        Initialize the RiskManager.
        
        Args:
            account_balance: Total account balance
            max_risk_per_trade: Maximum risk per trade (defaults to environment variable or 2%)
            max_open_trades: Maximum number of open trades
            max_daily_drawdown: Maximum daily drawdown percentage
            max_risk_per_symbol: Maximum risk allowed per symbol
        """
        self.account_balance = account_balance
        
        # Use environment variable or default to 2%
        self.max_risk_per_trade = max_risk_per_trade or float(os.getenv("DEFAULT_RISK_PERCENTAGE", "0.02"))
        
        self.max_open_trades = max_open_trades
        self.max_daily_drawdown = max_daily_drawdown
        self.max_risk_per_symbol = max_risk_per_symbol
        
        # Initialize tracking variables
        self.daily_pnl = 0
    
    def update_account_balance(self, new_balance):
        """
        Update the account balance.
        
        Args:
            new_balance: The new account balance
        """
        self.account_balance = new_balance
        logger.info(f"Account balance updated to {new_balance}")
    
    def reset_daily_pnl(self):
        """
        Reset the daily P&L counter.
        """
        self.daily_pnl = 0
        logger.info("Daily P&L reset")
    
    def update_daily_pnl(self, pnl):
        """
        Update the daily P&L counter.
        
        Args:
            pnl: The P&L to add to the daily counter
            
        Returns:
            bool: True if trading should continue, False if max daily drawdown reached
        """
        self.daily_pnl += pnl
        
        # Check if max daily drawdown reached
        if abs(self.daily_pnl) > self.account_balance * self.max_daily_drawdown and self.daily_pnl < 0:
            logger.warning(f"Max daily drawdown reached: {self.daily_pnl}")
            return False
        
        return True
    
    def calculate_position_size(self, entry_price, stop_loss, risk_percentage=None):
        """
        Calculate the position size based on risk parameters.
        
        Args:
            entry_price: The entry price
            stop_loss: The stop loss price
            risk_percentage: The risk percentage to use (defaults to max_risk_per_trade)
            
        Returns:
            float: The position size
        """
        if risk_percentage is None:
            risk_percentage = self.max_risk_per_trade
        
        # Calculate the risk amount
        risk_amount = self.account_balance * risk_percentage
        
        # Calculate the price difference
        price_diff = abs(entry_price - stop_loss)
        
        # Calculate the position size
        if price_diff == 0:
            logger.warning("Stop loss is equal to entry price, using default position size")
            return risk_amount / entry_price
        
        position_size = risk_amount / price_diff
        
        return position_size
    
    def can_open_new_trade(self, symbol, entry_price, stop_loss, position_size=None):
        """
        Check if a new trade can be opened based on risk parameters.
        
        Args:
            symbol: The symbol to trade
            entry_price: The entry price
            stop_loss: The stop loss price
            position_size: The position size (if None, will be calculated)
            
        Returns:
            tuple: (bool, position_size, reason) - whether the trade can be opened, the position size, and the reason if not
        """
        # Check if max open trades reached
        open_positions = performance_tracker.get_open_positions()
        if len(open_positions) >= self.max_open_trades:
            return False, 0, f"Max open trades reached: {len(open_positions)}/{self.max_open_trades}"
        
        # Check if max risk per symbol reached
        symbol_positions = [p for p in open_positions if p["symbol"] == symbol]
        symbol_risk = sum([abs(p["entry_price"] - p.get("stop_loss", 0)) * p["position_size"] for p in symbol_positions])
        
        if symbol_risk >= self.account_balance * self.max_risk_per_symbol:
            return False, 0, f"Max risk per symbol reached for {symbol}: {symbol_risk}/{self.account_balance * self.max_risk_per_symbol}"
        
        # Calculate position size if not provided
        if position_size is None:
            position_size = self.calculate_position_size(entry_price, stop_loss)
        
        # Check if the trade risk is acceptable
        trade_risk = abs(entry_price - stop_loss) * position_size
        if trade_risk > self.account_balance * self.max_risk_per_trade:
            adjusted_position_size = self.calculate_position_size(entry_price, stop_loss)
            return False, adjusted_position_size, f"Trade risk too high: {trade_risk}/{self.account_balance * self.max_risk_per_trade}, adjusted position size: {adjusted_position_size}"
        
        return True, position_size, "Trade allowed"
    
    def calculate_stop_loss(self, entry_price, direction, atr=None, atr_multiplier=2.0, fixed_percentage=0.02):
        """
        Calculate a stop loss price based on ATR or a fixed percentage.
        
        Args:
            entry_price: The entry price
            direction: The trade direction ('buy' or 'sell')
            atr: The Average True Range value (if None, fixed percentage will be used)
            atr_multiplier: The multiplier for ATR
            fixed_percentage: The fixed percentage to use if ATR is None
            
        Returns:
            float: The stop loss price
        """
        if atr is not None:
            # Calculate stop loss based on ATR
            if direction == 'buy':
                stop_loss = entry_price - (atr * atr_multiplier)
            else:
                stop_loss = entry_price + (atr * atr_multiplier)
        else:
            # Calculate stop loss based on fixed percentage
            if direction == 'buy':
                stop_loss = entry_price * (1 - fixed_percentage)
            else:
                stop_loss = entry_price * (1 + fixed_percentage)
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price, stop_loss, direction, risk_reward_ratio=2.0):
        """
        Calculate a take profit price based on risk-reward ratio.
        
        Args:
            entry_price: The entry price
            stop_loss: The stop loss price
            direction: The trade direction ('buy' or 'sell')
            risk_reward_ratio: The risk-reward ratio
            
        Returns:
            float: The take profit price
        """
        # Calculate the risk
        risk = abs(entry_price - stop_loss)
        
        # Calculate the reward
        reward = risk * risk_reward_ratio
        
        # Calculate the take profit price
        if direction == 'buy':
            take_profit = entry_price + reward
        else:
            take_profit = entry_price - reward
        
        return take_profit
    
    def should_adjust_position(self, trade, current_price):
        """
        Check if a position should be adjusted based on current price.
        
        Args:
            trade: The trade details
            current_price: The current price
            
        Returns:
            tuple: (bool, dict) - whether the position should be adjusted and the adjustment details
        """
        # Check if trailing stop should be activated
        if trade["type"] == "buy" and current_price > trade["entry_price"] * 1.05:
            # Move stop loss to break even if price has moved 5% in favor
            new_stop_loss = max(trade.get("stop_loss", 0), trade["entry_price"])
            return True, {"stop_loss": new_stop_loss}
        
        elif trade["type"] == "sell" and current_price < trade["entry_price"] * 0.95:
            # Move stop loss to break even if price has moved 5% in favor
            new_stop_loss = min(trade.get("stop_loss", float('inf')), trade["entry_price"])
            return True, {"stop_loss": new_stop_loss}
        
        return False, {}
    
    def should_close_position(self, trade, current_price):
        """
        Check if a position should be closed based on current price.
        
        Args:
            trade: The trade details
            current_price: The current price
            
        Returns:
            bool: Whether the position should be closed
        """
        # Check if stop loss hit
        if trade["type"] == "buy" and current_price <= trade.get("stop_loss", 0) and trade.get("stop_loss", 0) > 0:
            logger.info(f"Stop loss hit for {trade['id']}: {current_price} <= {trade.get('stop_loss', 0)}")
            return True
        
        elif trade["type"] == "sell" and current_price >= trade.get("stop_loss", float('inf')) and trade.get("stop_loss", float('inf')) < float('inf'):
            logger.info(f"Stop loss hit for {trade['id']}: {current_price} >= {trade.get('stop_loss', float('inf'))}")
            return True
        
        # Check if take profit hit
        if trade["type"] == "buy" and current_price >= trade.get("take_profit", float('inf')) and trade.get("take_profit", float('inf')) < float('inf'):
            logger.info(f"Take profit hit for {trade['id']}: {current_price} >= {trade.get('take_profit', float('inf'))}")
            return True
        
        elif trade["type"] == "sell" and current_price <= trade.get("take_profit", 0) and trade.get("take_profit", 0) > 0:
            logger.info(f"Take profit hit for {trade['id']}: {current_price} <= {trade.get('take_profit', 0)}")
            return True
        
        return False

# Create a singleton instance
risk_manager = RiskManager() 
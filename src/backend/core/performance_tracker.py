import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """
    Track and analyze trading performance.
    """
    
    def __init__(self, log_file="trading_log.json"):
        """
        Initialize the performance tracker.
        
        Args:
            log_file: The file to log trades to
        """
        self.log_file = log_file
        self.trades = self._load_trades()
        
    def _load_trades(self):
        """
        Load trades from the log file.
        
        Returns:
            list: The list of trades
        """
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.exception(f"Error loading trades from {self.log_file}: {e}")
                return []
        else:
            return []
    
    def _save_trades(self):
        """
        Save trades to the log file.
        """
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            logger.exception(f"Error saving trades to {self.log_file}: {e}")
    
    def log_trade_entry(self, trade):
        """
        Log a trade entry.
        
        Args:
            trade: The trade details
        """
        trade_entry = {
            "id": trade.get("trade_id", f"trade_{len(self.trades) + 1}"),
            "symbol": trade["symbol"],
            "type": trade["type"],
            "entry_time": datetime.fromtimestamp(trade["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "entry_price": trade["entry_price"],
            "position_size": trade["position_size"],
            "leverage": trade.get("leverage", 1),
            "stop_loss": trade.get("stop_loss", 0),
            "take_profit": trade.get("take_profit", 0),
            "status": "open",
            "exit_time": None,
            "exit_price": None,
            "pnl": None,
            "pnl_percentage": None
        }
        
        self.trades.append(trade_entry)
        self._save_trades()
        
        logger.info(f"Trade entry logged: {trade_entry}")
    
    def log_trade_exit(self, trade_id, exit_price, exit_timestamp):
        """
        Log a trade exit.
        
        Args:
            trade_id: The ID of the trade
            exit_price: The exit price
            exit_timestamp: The exit timestamp
        """
        for trade in self.trades:
            if trade["id"] == trade_id and trade["status"] == "open":
                trade["exit_time"] = datetime.fromtimestamp(exit_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                trade["exit_price"] = exit_price
                trade["status"] = "closed"
                
                # Calculate P&L
                if trade["type"] == "buy":
                    pnl = (exit_price - trade["entry_price"]) * trade["position_size"]
                    pnl_percentage = (exit_price - trade["entry_price"]) / trade["entry_price"] * 100
                else:  # sell
                    pnl = (trade["entry_price"] - exit_price) * trade["position_size"]
                    pnl_percentage = (trade["entry_price"] - exit_price) / trade["entry_price"] * 100
                
                trade["pnl"] = pnl
                trade["pnl_percentage"] = pnl_percentage
                
                self._save_trades()
                
                logger.info(f"Trade exit logged: {trade}")
                return True
        
        logger.warning(f"Trade {trade_id} not found or already closed")
        return False
    
    def get_performance_metrics(self):
        """
        Calculate performance metrics.
        
        Returns:
            dict: The performance metrics
        """
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "average_profit": 0,
                "average_loss": 0,
                "profit_factor": 0,
                "total_pnl": 0,
                "max_drawdown": 0
            }
        
        closed_trades = [t for t in self.trades if t["status"] == "closed"]
        winning_trades = [t for t in closed_trades if t["pnl"] > 0]
        losing_trades = [t for t in closed_trades if t["pnl"] <= 0]
        
        total_trades = len(closed_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_profit = sum(t["pnl"] for t in winning_trades)
        total_loss = sum(t["pnl"] for t in losing_trades)
        
        average_profit = total_profit / len(winning_trades) if winning_trades else 0
        average_loss = total_loss / len(losing_trades) if losing_trades else 0
        
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
        
        total_pnl = total_profit + total_loss
        
        # Calculate max drawdown
        equity_curve = []
        running_pnl = 0
        
        for trade in sorted(closed_trades, key=lambda x: x["exit_time"]):
            running_pnl += trade["pnl"]
            equity_curve.append(running_pnl)
        
        max_drawdown = 0
        peak = 0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "average_profit": average_profit,
            "average_loss": average_loss,
            "profit_factor": profit_factor,
            "total_pnl": total_pnl,
            "max_drawdown": max_drawdown
        }
    
    def get_open_positions(self):
        """
        Get all open positions.
        
        Returns:
            list: The open positions
        """
        return [t for t in self.trades if t["status"] == "open"]
    
    def get_closed_positions(self):
        """
        Get all closed positions.
        
        Returns:
            list: The closed positions
        """
        return [t for t in self.trades if t["status"] == "closed"]

# Create a singleton instance
performance_tracker = PerformanceTracker() 
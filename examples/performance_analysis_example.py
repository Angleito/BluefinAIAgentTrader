#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example script demonstrating how to use the performance tracking, risk management, and visualization modules.
"""

import sys
import os
import logging
import random
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.performance_tracker import performance_tracker
from core.risk_manager import risk_manager
from core.visualization import visualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def simulate_trades(num_trades=50, win_rate=0.6, risk_reward_ratio=2.0):
    """
    Simulate a series of trades for demonstration purposes.
    
    Args:
        num_trades: Number of trades to simulate
        win_rate: Probability of a winning trade
        risk_reward_ratio: Risk-reward ratio for winning trades
    """
    logger.info(f"Simulating {num_trades} trades with {win_rate:.0%} win rate and {risk_reward_ratio:.1f} risk-reward ratio")
    
    # List of symbols to use
    symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "BNB/USD"]
    
    # Start date for the simulation
    start_date = datetime.now() - timedelta(days=30)
    
    # Simulate trades
    for i in range(num_trades):
        # Generate random trade data
        symbol = random.choice(symbols)
        trade_type = random.choice(["buy", "sell"])
        entry_price = random.uniform(100, 10000)
        
        # Calculate stop loss and take profit
        if trade_type == "buy":
            stop_loss = entry_price * 0.98  # 2% below entry
            take_profit = entry_price * (1 + (0.02 * risk_reward_ratio))  # RR * 2% above entry
        else:
            stop_loss = entry_price * 1.02  # 2% above entry
            take_profit = entry_price * (1 - (0.02 * risk_reward_ratio))  # RR * 2% below entry
        
        # Calculate position size
        position_size = risk_manager.calculate_position_size(entry_price, stop_loss)
        
        # Check if trade can be opened
        can_open, adjusted_size, reason = risk_manager.can_open_new_trade(symbol, entry_price, stop_loss, position_size)
        
        if not can_open:
            logger.warning(f"Trade {i+1} cannot be opened: {reason}")
            continue
        
        # Generate entry timestamp
        entry_timestamp = int((start_date + timedelta(days=i*0.5)).timestamp())
        
        # Log trade entry
        trade = {
            "trade_id": f"sim_trade_{i+1}",
            "symbol": symbol,
            "type": trade_type,
            "timestamp": entry_timestamp,
            "entry_price": entry_price,
            "position_size": position_size,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
        
        performance_tracker.log_trade_entry(trade)
        logger.info(f"Opened trade {i+1}: {symbol} {trade_type} at {entry_price}")
        
        # Simulate trade outcome
        is_winner = random.random() < win_rate
        
        # Generate exit timestamp (1-3 days after entry)
        exit_timestamp = entry_timestamp + random.randint(86400, 259200)
        
        # Calculate exit price based on outcome
        if is_winner:
            exit_price = take_profit
        else:
            exit_price = stop_loss
        
        # Log trade exit
        performance_tracker.log_trade_exit(trade["trade_id"], exit_price, exit_timestamp)
        
        # Update account balance
        if trade_type == "buy":
            pnl = (exit_price - entry_price) * position_size
        else:
            pnl = (entry_price - exit_price) * position_size
        
        risk_manager.update_account_balance(risk_manager.account_balance + pnl)
        risk_manager.update_daily_pnl(pnl)
        
        logger.info(f"Closed trade {i+1}: {symbol} {trade_type} at {exit_price}, P&L: {pnl:.2f}")
    
    logger.info(f"Final account balance: {risk_manager.account_balance:.2f}")

def main():
    """
    Main function to run the example.
    """
    # Set initial account balance
    risk_manager.update_account_balance(10000)
    
    # Simulate trades
    simulate_trades(num_trades=50, win_rate=0.6, risk_reward_ratio=2.0)
    
    # Generate performance report
    report_files = visualizer.generate_performance_report()
    
    logger.info("Performance report generated:")
    for key, file in report_files.items():
        logger.info(f"- {key}: {file}")
    
    # Print performance metrics
    metrics = performance_tracker.get_performance_metrics()
    
    logger.info("\nPerformance Metrics:")
    logger.info(f"Total Trades: {metrics['total_trades']}")
    logger.info(f"Win Rate: {metrics['win_rate']:.2%}")
    logger.info(f"Average Profit: {metrics['average_profit']:.2f}")
    logger.info(f"Average Loss: {metrics['average_loss']:.2f}")
    logger.info(f"Profit Factor: {metrics['profit_factor']:.2f}")
    logger.info(f"Total P&L: {metrics['total_pnl']:.2f}")
    logger.info(f"Maximum Drawdown: {metrics['max_drawdown']:.2f}")

if __name__ == "__main__":
    main() 
from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
import logging
import requests
import time
import json
from datetime import datetime

from config import TRADING_PARAMS
from core.performance_tracker import performance_tracker
from core.risk_manager import risk_manager
from core.visualization import visualizer

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"trading_log_{int(time.time())}.log"),
            logging.StreamHandler()
        ]
    )

def initialize_risk_manager():
    risk_manager.update_account_balance(TRADING_PARAMS["initial_account_balance"])
    risk_manager.max_risk_per_trade = TRADING_PARAMS["max_risk_per_trade"]
    risk_manager.max_open_trades = TRADING_PARAMS["max_concurrent_positions"]
    risk_manager.max_daily_drawdown = TRADING_PARAMS["max_daily_drawdown"]

def extract_trade_recommendation(analysis):
    """Extract trade recommendation details from AI analysis."""
    trade_recommendation = {
        "symbol": "BTC/USD",  # Default
        "type": "buy",        # Default
        "entry_price": 0,
        "stop_loss": 0,
        "take_profit": 0,
        "confidence": 0
    }
    
    # Extract trading pair, type, prices, and confidence
    # (Simplified implementation, use more robust parsing in production)
    lines = analysis.split('\n')
    for line in lines:
        if "entry" in line.lower() and ":" in line:
            trade_recommendation["entry_price"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "stop loss" in line.lower() and ":" in line:
            trade_recommendation["stop_loss"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "take profit" in line.lower() and ":" in line:
            trade_recommendation["take_profit"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "confidence" in line.lower() and ":" in line:
            trade_recommendation["confidence"] = float(line.split(':')[1].strip().replace('/10', ''))
            
    # Fill in missing stop loss and take profit based on risk parameters
    if trade_recommendation["stop_loss"] == 0 and trade_recommendation["entry_price"] > 0:
        trade_recommendation["stop_loss"] = trade_recommendation["entry_price"] * (1 - TRADING_PARAMS["stop_loss_percentage"])
    if trade_recommendation["take_profit"] == 0 and trade_recommendation["entry_price"] > 0 and trade_recommendation["stop_loss"] > 0:
        risk = abs(trade_recommendation["entry_price"] - trade_recommendation["stop_loss"])
        trade_recommendation["take_profit"] = trade_recommendation["entry_price"] + (risk * 2)  # 1:2 risk-reward ratio
    
    return trade_recommendation

async def execute_trade(trade_recommendation):
    """Execute a trade based on the recommendation."""
    logger.info(f"Executing trade: {trade_recommendation}")
    
    # Check if the trade can be opened based on risk parameters
    entry_price = trade_recommendation["entry_price"]
    stop_loss = trade_recommendation["stop_loss"]
    position_size = risk_manager.calculate_position_size(entry_price, stop_loss)
    
    can_open, adjusted_size, reason = risk_manager.can_open_new_trade(
        trade_recommendation["symbol"], 
        entry_price, 
        stop_loss, 
        position_size
    )
    
    if not can_open:
        logger.warning(f"Trade cannot be executed: {reason}")
        return False
    
    # Prepare and log trade data
    trade = {
        "trade_id": f"trade_{int(time.time())}",
        "symbol": trade_recommendation["symbol"],
        "type": trade_recommendation["type"],
        "timestamp": int(time.time()),
        "entry_price": entry_price,
        "position_size": adjusted_size,
        "stop_loss": stop_loss,
        "take_profit": trade_recommendation["take_profit"],
        "confidence": trade_recommendation.get("confidence", 0)
    }
    
    performance_tracker.log_trade_entry(trade)
    
    logger.info(f"Trade executed successfully: {trade}")
    return True

async def main():
    """Main function to run AI analysis and execute trades."""
    try:
        # Run Perplexity agent for market analysis
        perplexity_result = "Perplexity analysis placeholder"
        
        # Run Claude agent for trading analysis
        claude_result = "Claude analysis placeholder"
        
        # Extract and execute trade recommendation if confident
        trade_recommendation = extract_trade_recommendation(claude_result)
        if trade_recommendation["confidence"] >= 7:
            await execute_trade(trade_recommendation)
        else:
            logger.info(f"Trade not executed due to low confidence: {trade_recommendation['confidence']}/10")
        
        # Save results and generate performance report
        timestamp = int(time.time())
        with open(f"trading_analysis_{timestamp}.json", "w") as f:
            json.dump({
                "timestamp": timestamp,
                "perplexity_analysis": perplexity_result,
                "claude_analysis": claude_result,
                "trade_recommendation": trade_recommendation,
                "trading_parameters": TRADING_PARAMS
            }, f, indent=2)
        
        report_files = visualizer.generate_performance_report()
        logger.info(f"Performance report generated: {report_files}")
        
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    setup_logging()
    initialize_risk_manager()
    asyncio.run(main())
from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
import logging
import json
from datetime import datetime

from bluefin_client_sui import BluefinClient
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
            logging.FileHandler(f"trading_log_{int(datetime.now().timestamp())}.log"),
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
    trade_rec = {
        "symbol": "BTC-PERP",
        "side": "buy", 
        "price": 0,
        "stopLoss": 0,
        "takeProfit": 0,
        "confidence": 0
    }
    
    for line in analysis.split('\n'):
        if "entry" in line.lower(): 
            trade_rec["price"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "stop loss" in line.lower():
            trade_rec["stopLoss"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "take profit" in line.lower(): 
            trade_rec["takeProfit"] = float(line.split(':')[1].strip().replace('$', '').replace(',', ''))
        elif "confidence" in line.lower():
            trade_rec["confidence"] = float(line.split(':')[1].strip().replace('/10', ''))
            
    if trade_rec["stopLoss"] == 0:
        trade_rec["stopLoss"] = trade_rec["price"] * (1 - TRADING_PARAMS["stop_loss_percentage"])
    if trade_rec["takeProfit"] == 0:
        risk = abs(trade_rec["price"] - trade_rec["stopLoss"])
        trade_rec["takeProfit"] = trade_rec["price"] + (risk * 2)  # 1:2 risk-reward
    
    return trade_rec

async def execute_trade(client, trade_rec):
    """Execute a trade on Bluefin based on the recommendation."""
    logger.info(f"Executing trade: {trade_rec}")
    
    # Check risk and position size
    entry_price = trade_rec["price"]
    stop_loss = trade_rec["stopLoss"] 
    pos_size = risk_manager.calculate_position_size(entry_price, stop_loss)
    
    can_open, adjusted_size, reason = risk_manager.can_open_new_trade(
        trade_rec["symbol"], entry_price, stop_loss, pos_size
    )
    
    if not can_open:
        logger.warning(f"Trade cannot be executed: {reason}")
        return False
    
    # Place order on Bluefin
    order = await client.place_order(
        symbol=trade_rec["symbol"],
        side=trade_rec["side"],
        order_type="LIMIT",
        quantity=adjusted_size,
        price=entry_price,
        stop_loss=stop_loss,
        take_profit=trade_rec["takeProfit"]
    )
    
    if order["status"] == "NEW":
        trade = {
            "trade_id": order["orderId"],
            "symbol": trade_rec["symbol"], 
            "side": trade_rec["side"],
            "timestamp": datetime.now().timestamp(),
            "entry_price": entry_price,
            "position_size": adjusted_size,
            "stop_loss": stop_loss,
            "take_profit": trade_rec["takeProfit"],
            "confidence": trade_rec["confidence"]
        }
        performance_tracker.log_trade_entry(trade)
        logger.info(f"Trade executed successfully: {trade}")
        return True
    else:
        logger.error(f"Failed to execute trade: {order}")
        return False

async def main():
    """Main function to run AI analysis and execute trades."""
    try:
        # Initialize Bluefin client
        client = BluefinClient(api_key=os.getenv("BLUEFIN_API_KEY"))
        await client.initialize()

        # Run AI analysis (placeholders for example)
        perplexity_result = "Perplexity analysis placeholder" 
        claude_result = "Claude analysis placeholder"
        
        # Extract and execute trade if confident
        trade_rec = extract_trade_recommendation(claude_result)
        if trade_rec["confidence"] >= 7:
            success = await execute_trade(client, trade_rec)
            if success:
                # Save results and generate report
                timestamp = int(datetime.now().timestamp())
                with open(f"trading_analysis_{timestamp}.json", "w") as f:
                    json.dump({
                        "timestamp": timestamp,
                        "perplexity_analysis": perplexity_result,
                        "claude_analysis": claude_result,
                        "trade_recommendation": trade_rec,
                        "trading_parameters": TRADING_PARAMS
                    }, f, indent=2)
                
                report_files = visualizer.generate_performance_report()
                logger.info(f"Performance report generated: {report_files}")
        else:
            logger.info(f"Trade not executed due to low confidence: {trade_rec['confidence']}/10") 
        
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
        raise
    finally:
        await client.close()

if __name__ == "__main__":
    setup_logging()
    initialize_risk_manager() 
    asyncio.run(main())
from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
import time
import json
import requests
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Import our new modules
from core.performance_tracker import performance_tracker
from core.risk_manager import risk_manager
from core.visualization import visualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"trading_log_{int(time.time())}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load API keys from environment variables
pplx_api_key = os.getenv("PERPLEXITY_API_KEY")
claude_api_key = os.getenv("CLAUDE_API_KEY")

if not pplx_api_key:
    raise ValueError("PERPLEXITY_API_KEY environment variable is not set")
if not claude_api_key:
    raise ValueError("CLAUDE_API_KEY environment variable is not set")

# Timestamp for logging
timestamp = int(time.time())

# Trading parameters (as specified in the comprehensive guide)
TRADING_PARAMS = {
    "position_size_percentage": 0.05,  # 5% of portfolio
    "leverage": 7,                     # 7x leverage
    "stop_loss_percentage": 0.15,      # 15% stop loss
    "max_concurrent_positions": 3,     # Max 3 positions
    "trading_pairs": ["BTC/USD", "ETH/USD", "SOL/USD", "SUI/USD"],  # Initial trading pairs
    "initial_account_balance": 10000,  # Initial account balance
    "max_risk_per_trade": 0.02,        # Maximum risk per trade (2% of account balance)
    "max_daily_drawdown": 0.05         # Maximum daily drawdown (5% of account balance)
}

# Initialize risk manager with trading parameters
risk_manager.update_account_balance(TRADING_PARAMS["initial_account_balance"])
risk_manager.max_risk_per_trade = TRADING_PARAMS["max_risk_per_trade"]
risk_manager.max_open_trades = TRADING_PARAMS["max_concurrent_positions"]
risk_manager.max_daily_drawdown = TRADING_PARAMS["max_daily_drawdown"]

# System prompts
CLAUDE_SYSTEM_PROMPT = """You are an AI trading assistant that helps analyze market data and make trading decisions.
Your task is to analyze TradingView charts, interpret technical indicators, and provide trading recommendations.
Focus on risk management, technical analysis, and clear reasoning for your trading decisions.
Always consider the current market conditions and explain your analysis in detail."""

PERPLEXITY_PROMPT = """Analyze the current Bitcoin market conditions based on the following:
1. Recent price movements and volatility
2. Market sentiment indicators
3. On-chain metrics
4. Technical indicators (RSI, MACD, Moving Averages)

Then, provide a detailed analysis of the SUI/USD trading pair on the 4-hour timeframe:
1. Identify the current trend direction
2. Analyze key support and resistance levels
3. Evaluate momentum indicators
4. Assess volume patterns
5. Recommend whether to long or short the next 4-hour candle

Your analysis should be comprehensive and include reasoning for your recommendation."""

TRADING_ANALYSIS_PROMPT = """Analyze the following trading pair: {trading_pair} on the {timeframe} timeframe.
Look at key technical indicators including:
1. Moving Averages (50, 100, 200)
2. RSI
3. MACD
4. Volume
5. Support and resistance levels

Provide a detailed analysis and trading recommendation with:
- Current price and trend direction
- Key support and resistance levels
- Entry price recommendation
- Stop loss level (15% from entry)
- Take profit targets
- Risk/reward ratio
- Confidence level (1-10)

Your analysis should be comprehensive and include reasoning for your recommendation."""

def call_perplexity_api(prompt):
    """Call the Perplexity API directly"""
    logger.info("Calling Perplexity API for market analysis...")
    
    headers = {
        "Authorization": f"Bearer {pplx_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a professional crypto market analyst with expertise in technical analysis."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        logger.info("Perplexity API analysis completed successfully")
        return content
    else:
        error_msg = f"Error calling Perplexity API: {response.status_code} - {response.text}"
        logger.error(error_msg)
        return error_msg

def call_claude_api(system_prompt, user_prompt):
    """Call the Claude API directly"""
    logger.info("Calling Claude API for trading analysis...")
    
    headers = {
        "x-api-key": claude_api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 4000,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result["content"][0]["text"]
        logger.info("Claude API analysis completed successfully")
        return content
    else:
        error_msg = f"Error calling Claude API: {response.status_code} - {response.text}"
        logger.error(error_msg)
        return error_msg

def extract_trade_recommendation(analysis):
    """
    Extract trade recommendation from AI analysis.
    
    Args:
        analysis: The AI analysis text
        
    Returns:
        dict: The extracted trade recommendation
    """
    # This is a simple implementation - in a real system, you would use more sophisticated parsing
    trade_recommendation = {
        "symbol": "BTC/USD",  # Default
        "type": "buy",        # Default
        "entry_price": 0,
        "stop_loss": 0,
        "take_profit": 0,
        "confidence": 0
    }
    
    # Extract trading pair
    if "BTC/USD" in analysis:
        trade_recommendation["symbol"] = "BTC/USD"
    elif "ETH/USD" in analysis:
        trade_recommendation["symbol"] = "ETH/USD"
    elif "SOL/USD" in analysis:
        trade_recommendation["symbol"] = "SOL/USD"
    elif "SUI/USD" in analysis:
        trade_recommendation["symbol"] = "SUI/USD"
    
    # Extract trade type
    if "long" in analysis.lower() or "buy" in analysis.lower():
        trade_recommendation["type"] = "buy"
    elif "short" in analysis.lower() or "sell" in analysis.lower():
        trade_recommendation["type"] = "sell"
    
    # Extract prices (this is a simplified implementation)
    # In a real system, you would use more sophisticated parsing techniques
    lines = analysis.split('\n')
    for line in lines:
        if "entry" in line.lower() and "price" in line.lower() and ":" in line:
            try:
                price_str = line.split(':')[1].strip().replace('$', '').replace(',', '')
                trade_recommendation["entry_price"] = float(price_str)
            except:
                pass
        
        if "stop loss" in line.lower() and ":" in line:
            try:
                price_str = line.split(':')[1].strip().replace('$', '').replace(',', '')
                trade_recommendation["stop_loss"] = float(price_str)
            except:
                pass
        
        if "take profit" in line.lower() and ":" in line:
            try:
                price_str = line.split(':')[1].strip().replace('$', '').replace(',', '')
                trade_recommendation["take_profit"] = float(price_str)
            except:
                pass
        
        if "confidence" in line.lower() and ":" in line:
            try:
                confidence_str = line.split(':')[1].strip().replace('/10', '')
                trade_recommendation["confidence"] = float(confidence_str)
            except:
                pass
    
    # If we couldn't extract stop loss, calculate it based on entry price and stop loss percentage
    if trade_recommendation["stop_loss"] == 0 and trade_recommendation["entry_price"] > 0:
        if trade_recommendation["type"] == "buy":
            trade_recommendation["stop_loss"] = trade_recommendation["entry_price"] * (1 - TRADING_PARAMS["stop_loss_percentage"])
        else:
            trade_recommendation["stop_loss"] = trade_recommendation["entry_price"] * (1 + TRADING_PARAMS["stop_loss_percentage"])
    
    # If we couldn't extract take profit, calculate it based on entry price and risk-reward ratio
    if trade_recommendation["take_profit"] == 0 and trade_recommendation["entry_price"] > 0 and trade_recommendation["stop_loss"] > 0:
        risk = abs(trade_recommendation["entry_price"] - trade_recommendation["stop_loss"])
        if trade_recommendation["type"] == "buy":
            trade_recommendation["take_profit"] = trade_recommendation["entry_price"] + (risk * 2)  # 1:2 risk-reward ratio
        else:
            trade_recommendation["take_profit"] = trade_recommendation["entry_price"] - (risk * 2)  # 1:2 risk-reward ratio
    
    return trade_recommendation

def execute_trade(trade_recommendation):
    """
    Execute a trade based on the recommendation.
    
    Args:
        trade_recommendation: The trade recommendation
        
    Returns:
        bool: Whether the trade was executed successfully
    """
    # In a real system, this would interact with the Bluefin Exchange API
    # For now, we'll just log the trade and track it in our performance tracker
    
    logger.info(f"Executing trade: {trade_recommendation}")
    
    # Check if the trade can be opened based on risk parameters
    entry_price = trade_recommendation["entry_price"]
    stop_loss = trade_recommendation["stop_loss"]
    
    # Calculate position size based on risk parameters
    position_size = risk_manager.calculate_position_size(entry_price, stop_loss)
    
    # Check if the trade can be opened
    can_open, adjusted_size, reason = risk_manager.can_open_new_trade(
        trade_recommendation["symbol"], 
        entry_price, 
        stop_loss, 
        position_size
    )
    
    if not can_open:
        logger.warning(f"Trade cannot be executed: {reason}")
        return False
    
    # Prepare trade data
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
    
    # Log the trade entry
    performance_tracker.log_trade_entry(trade)
    
    logger.info(f"Trade executed successfully: {trade}")
    return True

def main():
    """Main function to run both agents and execute trades"""
    try:
        # Run Perplexity agent for market analysis
        perplexity_result = call_perplexity_api(PERPLEXITY_PROMPT)
        
        # Run Claude agent for trading analysis
        formatted_prompt = TRADING_ANALYSIS_PROMPT.format(
            trading_pair="SUI/USD",
            timeframe="4h"
        )
        claude_result = call_claude_api(CLAUDE_SYSTEM_PROMPT, formatted_prompt)
        
        # Extract trade recommendation from Claude analysis
        trade_recommendation = extract_trade_recommendation(claude_result)
        
        # Execute the trade if confidence is high enough
        if trade_recommendation["confidence"] >= 7:
            execute_trade(trade_recommendation)
        else:
            logger.info(f"Trade not executed due to low confidence: {trade_recommendation['confidence']}/10")
        
        # Save results to a file
        with open(f"trading_analysis_{timestamp}.json", "w") as f:
            json.dump({
                "timestamp": timestamp,
                "perplexity_analysis": perplexity_result,
                "claude_analysis": claude_result,
                "trade_recommendation": trade_recommendation,
                "trading_parameters": TRADING_PARAMS
            }, f, indent=2)
        
        logger.info(f"Results saved to trading_analysis_{timestamp}.json")
        
        # Generate performance report
        report_files = visualizer.generate_performance_report()
        logger.info(f"Performance report generated: {report_files}")
        
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    main()
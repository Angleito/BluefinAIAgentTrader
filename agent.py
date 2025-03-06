from dotenv import load_dotenv
load_dotenv()
import os
import asyncio
import time
import json
import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load API keys from environment variables
pplx_api_key = os.getenv("PERPLEXITY_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not pplx_api_key:
    raise ValueError("PERPLEXITY_API_KEY environment variable is not set")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Timestamp for logging
timestamp = int(time.time())

# Trading parameters (as specified in the comprehensive guide)
TRADING_PARAMS = {
    "position_size_percentage": 0.05,  # 5% of portfolio
    "leverage": 7,                     # 7x leverage
    "stop_loss_percentage": 0.15,      # 15% stop loss
    "max_concurrent_positions": 3,     # Max 3 positions
    "trading_pairs": ["BTC/USD", "ETH/USD", "SOL/USD", "SUI/USD"]  # Initial trading pairs
}

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
    print("Calling Perplexity API for market analysis...")
    
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
        print("\n--- Perplexity API Results ---")
        print(content)
        return content
    else:
        error_msg = f"Error calling Perplexity API: {response.status_code} - {response.text}"
        print(error_msg)
        return error_msg

def call_openai_api(system_prompt, user_prompt):
    """Call the OpenAI API directly"""
    print("Calling OpenAI API for trading analysis...")
    
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4o",
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
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print("\n--- OpenAI API Results ---")
        print(content)
        return content
    else:
        error_msg = f"Error calling OpenAI API: {response.status_code} - {response.text}"
        print(error_msg)
        return error_msg

def main():
    """Main function to run both agents"""
    try:
        # Run Perplexity agent for market analysis
        perplexity_result = call_perplexity_api(PERPLEXITY_PROMPT)
        
        # Run OpenAI agent for trading analysis
        formatted_prompt = TRADING_ANALYSIS_PROMPT.format(
            trading_pair="SUI/USD",
            timeframe="4h"
        )
        openai_result = call_openai_api(CLAUDE_SYSTEM_PROMPT, formatted_prompt)
        
        # Save results to a file
        with open(f"trading_analysis_{timestamp}.json", "w") as f:
            json.dump({
                "timestamp": timestamp,
                "perplexity_analysis": perplexity_result,
                "openai_analysis": openai_result,
                "trading_parameters": TRADING_PARAMS
            }, f, indent=2)
        
        print(f"\nResults saved to trading_analysis_{timestamp}.json")
        
    except Exception as e:
        print(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    main()
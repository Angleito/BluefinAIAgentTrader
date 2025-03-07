import asyncio
import logging
import base64
import requests
import json
from config import PERPLEXITY_CONFIG

logger = logging.getLogger(__name__)

async def analyze_chart(chart_image):
    """
    Analyze the TradingView chart screenshot using Perplexity AI.
    
    Args:
        chart_image: The screenshot image of the TradingView chart
        
    Returns:
        dict: Analysis result with trade confirmation and reasoning
    """
    if not chart_image:
        error_msg = "No chart image provided for analysis"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    try:
        # Convert image to base64 for API request
        image_base64 = base64.b64encode(chart_image).decode('utf-8')
        
        # Prepare the prompt for Perplexity
        prompt = create_analysis_prompt(image_base64)
        
        # Call Perplexity API
        analysis_result = await call_perplexity_api(prompt)
        
        # Parse the analysis result
        parsed_result = parse_analysis_result(analysis_result)
        
        logger.info(f"Chart analysis completed: {parsed_result['trade_confirmed']}")
        return parsed_result
        
    except Exception as e:
        error_msg = f"Error analyzing chart: {str(e)}"
        logger.exception(error_msg)
        return {"status": "error", "message": error_msg}

def create_analysis_prompt(image_base64):
    """
    Create the prompt for Perplexity to analyze the chart.
    
    Args:
        image_base64: The base64-encoded image
        
    Returns:
        str: The prompt for Perplexity
    """
    return f"""
    Analyze this TradingView chart with VumanChu Cipher A and B indicators and Heiken Ashi candles.
    
    Focus on:
    1. The current trend direction based on Heiken Ashi candles
    2. VumanChu Cipher A indicator (green and red dots)
    3. VumanChu Cipher B indicator (histogram and lines)
    4. Support and resistance levels
    5. Volume patterns
    
    Determine if this is a valid trading signal. A valid signal should have:
    - For BUY signals: Green Heiken Ashi candles, green dots above price in VumanChu A, and positive histogram in VumanChu B
    - For SELL signals: Red Heiken Ashi candles, red dots below price in VumanChu A, and negative histogram in VumanChu B
    
    Provide your analysis and explicitly state whether you confirm this trade (YES/NO) and your confidence level (1-10).
    
    [Chart Image: data:image/png;base64,{image_base64}]
    """

async def call_perplexity_api(prompt):
    """
    Call the Perplexity API to analyze the chart.
    
    Args:
        prompt: The prompt for Perplexity
        
    Returns:
        str: The analysis result from Perplexity
        
    Raises:
        PerplexityAPIError: If there is an error calling the API or parsing the response
    """
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_CONFIG['api_key']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": PERPLEXITY_CONFIG["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are a professional crypto trader with expertise in technical analysis, particularly with VumanChu Cipher indicators and Heiken Ashi candles."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            error_msg = f"Perplexity API returned an error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise PerplexityAPIError(error_msg)
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return content
    
    except Exception as e:
        error_msg = f"Error calling Perplexity API: {str(e)}"
        logger.exception(error_msg) 
        raise PerplexityAPIError(error_msg)

def parse_analysis_result(analysis_text):
    """
    Parse the analysis result from Perplexity.
    
    Args:
        analysis_text: The text response from Perplexity
        
    Returns:
        dict: Parsed analysis result with trade confirmation and reasoning
    """
    if not analysis_text:
        return {"trade_confirmed": False, "reason": "No analysis result from Perplexity"}
    
    # Default values
    trade_confirmed = False
    confidence = 0
    reason = analysis_text
    
    # Look for explicit confirmation
    if "YES" in analysis_text.upper() and "CONFIDENCE" in analysis_text.upper():
        trade_confirmed = True
        
        # Try to extract confidence level
        try:
            confidence_text = analysis_text.upper().split("CONFIDENCE")[1].split("\n")[0]
            confidence_numbers = [int(s) for s in confidence_text.split() if s.isdigit()]
            if confidence_numbers:
                confidence = confidence_numbers[0]
        except:
            confidence = 7  # Default if parsing fails
    
    return {
        "trade_confirmed": trade_confirmed,
        "confidence": confidence,
        "reason": reason
    }

class PerplexityAPIError(Exception):
    """Custom exception for Perplexity API errors."""
    pass 
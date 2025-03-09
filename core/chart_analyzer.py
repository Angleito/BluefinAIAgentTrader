import asyncio
import logging
import base64
import requests
import json
import os
import datetime
from typing import Dict, Any, Optional

import anthropic
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Logging setup
logger = logging.getLogger(__name__)

# Anthropic configuration
CLAUDE_CONFIG = {
    "api_key": os.getenv("ANTHROPIC_API_KEY"),
    "model": os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
}

# Perplexity configuration
PERPLEXITY_CONFIG = {
    "api_key": os.getenv("PERPLEXITY_API_KEY"),
    "model": os.getenv("PERPLEXITY_MODEL", "sonar-pro")
}

def capture_tradingview_screenshot(symbol: Optional[str] = None, timeframe: Optional[str] = None) -> Optional[bytes]:
    """
    Capture a screenshot of the TradingView chart with VuManChu Cipher A/B indicators.
    
    Args:
        symbol: Optional trading symbol override (e.g., 'SUI-PERP')
        timeframe: Optional timeframe override (e.g., '5m', '15m')
        
    Returns:
        Screenshot image data, or None if capture fails
    """
    try:
        # Load environment variables if not already loaded
        if not os.getenv('BLUEFIN_DEFAULT_SYMBOL'):
            load_dotenv()
            
        # Get symbol from env if not provided
        if not symbol:
            symbol = os.getenv('BLUEFIN_DEFAULT_SYMBOL', 'SUI-PERP')
        
        # Get timeframe from env if not provided
        if not timeframe:
            timeframe = os.getenv('BLUEFIN_DEFAULT_TRADE_INTERVAL', os.getenv('DEFAULT_TIMEFRAME', '15m'))
            
        # Convert symbol format: SUI-PERP -> SUIUSD
        tv_symbol = symbol.split('-')[0] + 'USD'
        
        logger.info(f"Capturing TradingView screenshot for {tv_symbol} on {timeframe} timeframe")
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            
            # Navigate to TradingView
            page.goto("https://www.tradingview.com/chart/", timeout=60000)
            page.wait_for_load_state("networkidle")
            
            # Wait for chart to load
            page.wait_for_selector('.chart-container', timeout=30000)
            
            # Set symbol with PYTH as source
            page.click('.js-button-text >> text="Symbol"', timeout=5000)
            page.fill('.js-search-input', tv_symbol)
            # Wait for search results and select PYTH source when available
            page.wait_for_selector('span:has-text("PYTH")', timeout=5000)
            page.click('span:has-text("PYTH")', timeout=5000)
            
            # Wait for chart to update
            page.wait_for_timeout(2000)
            
            # Set timeframe
            # Note: Mapping environment variable format to TradingView format
            tv_timeframe_map = {
                '1m': '1',
                '5m': '5',
                '15m': '15',
                '30m': '30',
                '1h': '60',
                '4h': '240',
                '1d': 'D',
                '1w': 'W'
            }
            tv_timeframe = tv_timeframe_map.get(timeframe, '15')
            
            # Click on timeframe selector and select the appropriate timeframe
            page.click('[data-name="time-interval-button"]')
            page.click(f'[data-value="{tv_timeframe}"]')
            
            # Set Heiken Ashi candles
            page.click('[data-name="chart-types"]')
            page.click('[data-name="Heikin Ashi"]')
            
            # Add VuManChu Cipher A indicator
            page.click('[data-name="insert-indicator-button"]')
            page.fill('.js-search-input', 'VuManChu Cipher A')
            page.keyboard.press('Enter')
            page.wait_for_timeout(1000)
            
            # Add VuManChu Cipher B indicator
            page.click('[data-name="insert-indicator-button"]')
            page.fill('.js-search-input', 'VuManChu Cipher B')
            page.keyboard.press('Enter')
            page.wait_for_timeout(3000)  # Wait for indicators to load
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{tv_symbol}_{timeframe}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Capture screenshot
            screenshot_bytes = page.screenshot(path=filepath)
            logger.info(f"Screenshot saved to {filepath}")
            
            # Close browser
            browser.close()
            
            return screenshot_bytes
    
    except Exception as e:
        logger.error(f"Error capturing TradingView screenshot: {str(e)}")
        return None

async def analyze_chart_with_claude(chart_image: bytes) -> Dict[str, Any]:
    """
    Analyze the chart screenshot using Claude AI.
    
    Args:
        chart_image: The screenshot image of the TradingView chart
        
    Returns:
        Claude's analysis result
    """
    if not chart_image:
        error_msg = "No chart image provided for Claude analysis"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}
    
    try:
        # Convert image to base64 for API request
        image_base64 = base64.b64encode(chart_image).decode('utf-8')
        
        # Prepare the prompt for Claude
        prompt = create_claude_analysis_prompt()
        
        # Call Claude API
        client = anthropic.Anthropic(api_key=CLAUDE_CONFIG["api_key"])
        response = client.messages.create(
            model=CLAUDE_CONFIG["model"],
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        # Extract text from response content
        claude_analysis = str(response.content)
        
        parsed_result = parse_claude_analysis_result(claude_analysis)
        
        logger.info(f"Claude chart analysis completed: {parsed_result}")
        return parsed_result
        
    except Exception as e:
        error_msg = f"Error analyzing chart with Claude: {str(e)}"
        logger.exception(error_msg)
        return {"status": "error", "message": error_msg}

def create_claude_analysis_prompt() -> str:
    """
    Create the prompt for Claude to analyze the chart.
    
    Returns:
        The prompt for Claude
    """
    return """
    **Chart Analysis Using VuManChu Cipher B Methodology**

    ### **Trade Management Based on Dots**

    1. **Dot Interpretation Guidelines:**
        - Do NOT blindly reverse trades upon new dot appearances
        - Confirm dots with divergences and momentum wave strength
        - Prioritize dots that align with strong trends

    2. **Dot Analysis Criteria:**
        - *Green Dots*: 
            - Follow ONLY when accompanied by bullish divergence
            - Confirm with strong upward momentum waves
            - Assess overall trend context

        - *Red Dots*: 
            - Follow ONLY when paired with bearish divergence
            - Confirm with strong downward momentum waves
            - Assess overall trend context

    3. **Avoid Trading Signals:**
        - Ignore dots during choppy or sideways market movement
        - Do not enter trades without clear momentum confirmation

    ### **Detailed Chart Analysis**
    Analyze this TradingView chart with VumanChu Cipher A and B indicators, focusing on:
    - Current trend direction
    - Momentum wave strength
    - Divergence patterns
    - Support and resistance levels
    - Volume confirmation

    Provide a comprehensive analysis that explicitly addresses:
    - Trade confirmation (YES/NO)
    - Confidence level (1-10)
    - Reasoning based on the markdown guidelines
    """

def parse_claude_analysis_result(analysis_text: str) -> Dict[str, Any]:
    """
    Parse the analysis result from Claude.
    
    Args:
        analysis_text: The text response from Claude
        
    Returns:
        Parsed analysis result with trade confirmation and reasoning
    """
    if not analysis_text:
        return {"trade_confirmed": False, "reason": "No analysis result from Claude"}
    
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

async def analyze_chart(chart_image: bytes) -> Dict[str, Any]:
    """
    Analyze the TradingView chart screenshot using Claude and Perplexity.
    
    Args:
        chart_image: The screenshot image of the TradingView chart
        
    Returns:
        Combined analysis result
    """
    # First, analyze with Claude
    claude_result = await analyze_chart_with_claude(chart_image)
    
    # If Claude confirms, proceed with Perplexity analysis
    if claude_result.get('trade_confirmed', False):
        perplexity_result = await call_perplexity_api(
            create_analysis_prompt(base64.b64encode(chart_image).decode('utf-8'))
        )
        
        # Combine results
        claude_result['perplexity_analysis'] = perplexity_result
    
    return claude_result

def create_analysis_prompt(image_base64: str) -> str:
    """
    Create the prompt for Perplexity to analyze the chart.
    
    Args:
        image_base64: The base64-encoded image
        
    Returns:
        The prompt for Perplexity
    """
    return f"""
    **Chart Analysis Using VuManChu Cipher B Methodology**

    ### **Trade Management Based on Dots**

    1. **Dot Interpretation Guidelines:**
        - Do NOT blindly reverse trades upon new dot appearances
        - Confirm dots with divergences and momentum wave strength
        - Prioritize dots that align with strong trends

    2. **Dot Analysis Criteria:**
        - *Green Dots*: 
            - Follow ONLY when accompanied by bullish divergence
            - Confirm with strong upward momentum waves
            - Assess overall trend context

        - *Red Dots*: 
            - Follow ONLY when paired with bearish divergence
            - Confirm with strong downward momentum waves
            - Assess overall trend context

    3. **Avoid Trading Signals:**
        - Ignore dots during choppy or sideways market movement
        - Do not enter trades without clear momentum confirmation

    ### **Detailed Chart Analysis**
    Analyze this TradingView chart with VumanChu Cipher A and B indicators, focusing on:
    - Current trend direction
    - Momentum wave strength
    - Divergence patterns
    - Support and resistance levels
    - Volume confirmation

    Provide a comprehensive analysis that explicitly addresses:
    - Trade confirmation (YES/NO)
    - Confidence level (1-10)
    - Reasoning based on the markdown guidelines

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
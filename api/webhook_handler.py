import asyncio
import logging
import os
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
from core.signal_processor import process_signal
from core.chart_analyzer import analyze_chart
from core.trade_executor import execute_trade

logger = logging.getLogger(__name__)

class SignalModel(BaseModel):
    type: str
    symbol: str
    timeframe: str
    indicators: dict
    confidence: float

router = APIRouter()

@router.post("/webhook")
async def tradingview_webhook(signal: SignalModel):
    logger.info(f"Received signal: {signal}")

    try:
        # Process the signal
        processed_signal = process_signal(signal)
        
        if not processed_signal:
            logger.warning("Signal rejected")
            return {"status": "rejected", "reason": "Signal processing failed"}

        # Analyze the chart with Perplexity
        analysis_result = await analyze_chart(processed_signal)

        if analysis_result["trade_confirmed"]:
            # Get Bluefin client from global context
            from main import bluefin_client
            
            # Execute the trade
            trade_result = await execute_trade(bluefin_client, processed_signal)
            
            if trade_result:
                logger.info(f"Trade executed: {trade_result}")
                return {"status": "success", "trade": trade_result}
            else:
                logger.warning("Trade execution failed")
                return {"status": "failed", "reason": "Trade execution failed"}
        else:
            logger.info(f"Trade not confirmed: {analysis_result['reason']}")
            return {"status": "rejected", "reason": "Trade not confirmed"}

    except Exception as e:
        logger.exception(f"Error processing signal: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

async def take_chart_screenshot(signal):
    """Take a screenshot of the TradingView chart."""
    logger.info(f"Taking screenshot of {signal['symbol']} {signal['timeframe']}")
    
    try:
        timestamp = int(time.time())
        filename = f"chart_{signal['symbol']}_{signal['timeframe']}_{timestamp}.png"
        filepath = os.path.join(os.getcwd(), "screenshots", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto("https://www.tradingview.com/chart/")
            await page.wait_for_selector(".chart-container")
            
            await page.click(".chart-controls-bar-buttons .button-2ioYhFEY")
            await page.fill(".search-ZXzPWlJ1 input", signal['symbol'])
            await page.click(f"text={signal['symbol']}")
            
            timeframe_map = {
                "1m": "1",
                "5m": "5",
                "15m": "15", 
                "30m": "30",
                "1h": "60",
                "4h": "240",
                "1d": "D",
                "1w": "W"
            }
            
            tf = timeframe_map.get(signal['timeframe'], "D")
            await page.click(f"button[data-value='{tf}']")
            
            await page.click(".chart-controls-bar-buttons .button-2ioYhFEY")
            await page.click("text=Heiken Ashi")
            
            await page.click("button.addIndicator-2U9QKwgs")
            await page.fill(".search-ZXzPWlJ1 input", "VumanChu Cipher A")
            await page.click("text=VumanChu Cipher A")
            
            await page.click("button.addIndicator-2U9QKwgs")
            await page.fill(".search-ZXzPWlJ1 input", "VumanChu Cipher B") 
            await page.click("text=VumanChu Cipher B")
            
            await asyncio.sleep(5)
            
            await page.screenshot(path=filepath)
            await browser.close()
            
            with open(filepath, "rb") as f:
                screenshot_data = f.read()
            
            logger.info(f"Screenshot saved to {filepath}")
            return screenshot_data
            
    except Exception as e:
        logger.exception(f"Error taking screenshot: {e}")
        return None 
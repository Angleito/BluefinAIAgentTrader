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

# Import the strategy manager
from core.strategy_manager import strategy_manager

logger = logging.getLogger(__name__)

class SignalModel(BaseModel):
    type: str
    symbol: str
    timeframe: str
    indicators: dict = {}
    confidence: float = 0.5
    strategy: str = None  # Optional field to specify which strategy to use

router = APIRouter()

@router.post("/webhook")
async def tradingview_webhook(signal: SignalModel):
    logger.info(f"Received signal: {signal}")

    try:
        # If a specific strategy is provided, process with that strategy
        if signal.strategy == "momentum":
            # Process using momentum strategy directly
            logger.info("Processing with momentum strategy")
            from core.chart_analyzer import analyze_chart_with_momentum
            
            momentum_analysis = await analyze_chart_with_momentum(
                symbol=signal.symbol,
                timeframe=signal.timeframe
            )
            
            if not momentum_analysis or not momentum_analysis.get("success", False):
                logger.warning("Momentum analysis failed")
                return {"status": "rejected", "reason": "Momentum analysis failed"}
            
            processed_signal = {
                "symbol": signal.symbol,
                "type": "buy" if momentum_analysis.get("signal") in ["BUY", "STRONG_BUY"] else 
                        "sell" if momentum_analysis.get("signal") in ["SELL", "STRONG_SELL"] else "hold",
                "timeframe": signal.timeframe,
                "signal_type": momentum_analysis.get("signal"),
                "entry_price": momentum_analysis.get("entry_price"),
                "stop_loss": momentum_analysis.get("stop_loss"),
                "take_profit": momentum_analysis.get("take_profit"),
                "confidence": momentum_analysis.get("confidence", 0.5),
                "signal_source": "momentum",
                "metrics": momentum_analysis.get("metrics", {})
            }
        else:
            # Use strategy manager to get combined signals from all active strategies
            logger.info("Processing with strategy manager")
            trading_signal = await strategy_manager.get_trading_signal(
                symbol=signal.symbol,
                timeframe=signal.timeframe
            )
            
            if not trading_signal or trading_signal.get("signal") == "HOLD":
                logger.info("No actionable signal from strategy manager")
                return {"status": "rejected", "reason": "No actionable signal"}
            
            processed_signal = {
                "symbol": trading_signal.get("symbol"),
                "type": "buy" if trading_signal.get("signal") in ["BUY", "STRONG_BUY"] else 
                        "sell" if trading_signal.get("signal") in ["SELL", "STRONG_SELL"] else "hold",
                "timeframe": trading_signal.get("timeframe"),
                "signal_type": trading_signal.get("signal"),
                "entry_price": trading_signal.get("entry_price"),
                "stop_loss": trading_signal.get("stop_loss"),
                "take_profit": trading_signal.get("take_profit"),
                "confidence": trading_signal.get("confidence", 0.5),
                "signal_source": trading_signal.get("signal_source"),
                "contributing_strategies": trading_signal.get("contributing_strategies", [])
            }
        
        # Skip holding signals
        if processed_signal["type"] == "hold":
            logger.info("Hold signal - no trade execution needed")
            return {"status": "hold", "reason": "Hold signal"}
        
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
            
            # Add momentum indicators
            indicators_to_add = ["RSI", "MACD", "OBV", "Bollinger Bands"]
            for indicator in indicators_to_add:
                await page.click("button.addIndicator-2U9QKwgs")
                await page.fill(".search-ZXzPWlJ1 input", indicator)
                await page.click(f"text={indicator}")
                await asyncio.sleep(0.5)
            
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
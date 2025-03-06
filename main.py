import asyncio
import logging
import logging.config
from fastapi import FastAPI
from bluefin_client_sui import BluefinClient, Networks
from config import BLUEFIN_CONFIG, LOGGING_CONFIG, TRADINGVIEW_WEBHOOK_CONFIG
from api.webhook_handler import router as webhook_router

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Bluefin client...")
    global bluefin_client
    bluefin_client = BluefinClient(
        True,  # Agree to terms and conditions
        Networks[BLUEFIN_CONFIG["network"]],
        BLUEFIN_CONFIG["private_key"]
    )
    await bluefin_client.init(True)
    logger.info("Bluefin client initialized.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing Bluefin client...")
    await bluefin_client.close()
    logger.info("Bluefin client closed.")

app.include_router(webhook_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=TRADINGVIEW_WEBHOOK_CONFIG["host"],
        port=TRADINGVIEW_WEBHOOK_CONFIG["port"],
        reload=True
    ) 
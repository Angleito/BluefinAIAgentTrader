import asyncio
import logging
import logging.config
import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from bluefin_client_sui import BluefinClient, Networks
from core.config import (
    BLUEFIN_CONFIG, 
    LOGGING_CONFIG, 
    TRADINGVIEW_WEBHOOK_CONFIG, 
    TRADING_PARAMS,
    PERFORMANCE_TRACKING_CONFIG,
    RISK_MANAGEMENT_CONFIG,
    RISK_PARAMS,
    AI_PARAMS,
    validate_config
)
from api.webhook_handler import router as webhook_router
from core.performance_tracker import performance_tracker
from core.risk_manager import risk_manager
from core.visualization import visualizer

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Bluefin client...")
    global bluefin_client
    
    # Initialize the Bluefin client according to the documentation
    bluefin_client = BluefinClient(
        True,  # Agree to terms and conditions
        Networks[BLUEFIN_CONFIG["network"]],  # Network configuration
        BLUEFIN_CONFIG["private_key"]  # Wallet private key
    )
    
    # Initialize the client with onboarding
    logger.info("Initializing client with onboarding...")
    await bluefin_client.init(True)  # onboard user if first time
    
    # Get public address
    address = bluefin_client.get_public_address()
    logger.info(f'Connected to Bluefin with account address: {address}')
    
    # Get account data
    logger.info("Getting user account data...")
    account_data = await bluefin_client.get_user_account_data()
    
    if account_data:
        wallet_balance = account_data.get("walletBalance", "0")
        logger.info(f"Wallet balance: {int(wallet_balance) / 10**18:.6f} USDC")
    
    logger.info("Bluefin client initialized successfully.")
    
    # Initialize risk manager with trading parameters
    logger.info("Initializing risk manager...")
    risk_manager.update_account_balance(TRADING_PARAMS["initial_account_balance"])
    risk_manager.max_risk_per_trade = TRADING_PARAMS["max_risk_per_trade"]
    risk_manager.max_open_trades = TRADING_PARAMS["max_concurrent_positions"]
    risk_manager.max_risk_per_symbol = TRADING_PARAMS["max_risk_per_symbol"]
    risk_manager.max_daily_drawdown = TRADING_PARAMS["max_daily_drawdown"]
    logger.info("Risk manager initialized.")
    
    # Initialize performance tracker
    logger.info("Initializing performance tracker...")
    # Create a custom instance with the configured log file
    global performance_tracker
    performance_tracker = performance_tracker
    logger.info("Performance tracker initialized.")
    
    # Initialize visualizer
    logger.info("Initializing visualizer...")
    # Create visualizations directory if it doesn't exist
    os.makedirs(PERFORMANCE_TRACKING_CONFIG["visualizations_dir"], exist_ok=True)
    global visualizer
    visualizer = visualizer
    logger.info("Visualizer initialized.")

    # Load saved configuration if available
    config_dir = "config"
    config_file = os.path.join(config_dir, "config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            saved_config = json.load(f)
            TRADING_PARAMS.update(saved_config.get("TRADING_PARAMS", {}))
            RISK_PARAMS.update(saved_config.get("RISK_PARAMS", {}))
            AI_PARAMS.update(saved_config.get("AI_PARAMS", {}))

    # Validate loaded configuration 
    validate_config(TRADING_PARAMS, "TRADING_PARAMS")  
    validate_config(RISK_PARAMS, "RISK_PARAMS")
    validate_config(AI_PARAMS, "AI_PARAMS")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing Bluefin client...")
    await bluefin_client.apis.close_session()
    logger.info("Bluefin client closed.")
    
    # Generate final performance report
    logger.info("Generating final performance report...")
    report_files = visualizer.generate_performance_report()
    logger.info(f"Performance report generated: {report_files}")
    
    # Log performance metrics
    metrics = performance_tracker.get_performance_metrics()
    logger.info("Final performance metrics:")
    logger.info(f"Total Trades: {metrics['total_trades']}")
    logger.info(f"Win Rate: {metrics['win_rate']:.2%}")
    logger.info(f"Average Profit: {metrics['average_profit']:.2f}")
    logger.info(f"Average Loss: {metrics['average_loss']:.2f}")
    logger.info(f"Profit Factor: {metrics['profit_factor']:.2f}")
    logger.info(f"Total P&L: {metrics['total_pnl']:.2f}")
    logger.info(f"Maximum Drawdown: {metrics['max_drawdown']:.2f}")

app.include_router(webhook_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=TRADINGVIEW_WEBHOOK_CONFIG["host"],
        port=TRADINGVIEW_WEBHOOK_CONFIG["port"],
        reload=True
    ) 
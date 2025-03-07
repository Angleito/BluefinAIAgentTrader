#!/usr/bin/env python3
"""
PerplexityTrader Agent - Main Entry Point
-----------------------------------------
This script imports and runs the trading agent from the core module.
"""

import asyncio
import logging
import os
import sys
import threading
from pathlib import Path

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/agent.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("agent")

# Create necessary directories
os.makedirs("alerts", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("analysis", exist_ok=True)

# Set environment variable for mock trading
os.environ["MOCK_TRADING"] = os.environ.get("MOCK_TRADING", "True")
mock_trading = os.environ.get("MOCK_TRADING", "True").lower() in ("true", "1", "t", "yes")
if mock_trading:
    logger.info("Running in MOCK TRADING mode - no real trades will be executed")
else:
    logger.info("Running in LIVE TRADING mode - REAL trades will be executed")

# Import the main function from core.agent
try:
    # Import the main function from core.agent
    from core.agent import main, app, start_api_server
    import uvicorn
    logger.info("Successfully imported main function from core.agent")
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

# Function to run the API server in a separate thread
def run_api_server():
    """Run the API server in a separate thread."""
    try:
        # Use port 5002 for the agent API to avoid conflicts
        uvicorn.run(app, host="0.0.0.0", port=5002, log_level="info")
    except Exception as e:
        logger.error(f"API server error: {e}")

if __name__ == "__main__":
    logger.info("Starting PerplexityTrader Agent")
    
    # Start the API server in a separate thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    logger.info("API server started on port 5002")
    
    try:
        # Run the main function from core.agent
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent encountered an error: {e}", exc_info=True)
        sys.exit(1) 
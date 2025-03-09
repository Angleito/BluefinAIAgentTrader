"""
Bluefin Exchange API Module

This module provides an interface for interacting with the Bluefin Exchange API
for trading cryptocurrency futures, accessing market data, and managing accounts.
"""

import os
from typing import Optional

from core.bluefin_client import (
    BluefinClientInterface,
    BluefinApiClient,
    MockBluefinClient,
    create_bluefin_client,
    ORDER_SIDE, 
    ORDER_TYPE,
    ENDPOINTS
)

# Default URLs
DEFAULT_API_URL = "https://dapi.api.sui-prod.bluefin.io"
DEFAULT_WS_URL = "wss://dstream.api.sui-prod.bluefin.io/ws"

# Get configuration from environment variables
CONFIG = {
    "api_url": os.getenv("BLUEFIN_API_URL", DEFAULT_API_URL),
    "ws_url": os.getenv("BLUEFIN_WS_URL", DEFAULT_WS_URL),
    "api_key": os.getenv("BLUEFIN_API_KEY"),
    "api_secret": os.getenv("BLUEFIN_API_SECRET"),
}

# Module version
__version__ = "1.0.0"

async def get_client(use_mock: bool = False,
                   api_key: Optional[str] = None,
                   api_secret: Optional[str] = None,
                   api_url: Optional[str] = None) -> BluefinClientInterface:
    """
    Convenience function to get a pre-configured Bluefin client.
    
    Args:
        use_mock: Whether to use a mock client (for testing)
        api_key: Bluefin API key, defaults to environment variable
        api_secret: Bluefin API secret, defaults to environment variable
        api_url: API URL, defaults to environment variable or default URL
        
    Returns:
        Initialized Bluefin client
    """
    return await create_bluefin_client(
        use_mock=use_mock,
        api_key=api_key or CONFIG["api_key"],
        api_secret=api_secret or CONFIG["api_secret"],
        api_url=api_url or CONFIG["api_url"]
    )

__all__ = [
    'BluefinClientInterface',
    'BluefinApiClient',
    'MockBluefinClient',
    'create_bluefin_client',
    'get_client',
    'ORDER_SIDE',
    'ORDER_TYPE',
    'ENDPOINTS',
    'DEFAULT_API_URL',
    'DEFAULT_WS_URL',
] 
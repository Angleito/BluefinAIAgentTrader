import os

# Trading parameters
TRADING_PARAMS = {
    "position_size_percentage": 0.05,  # 5% of portfolio
    "leverage": 7,                     # 7x leverage
    "stop_loss_percentage": 0.15,      # 15% stop loss
    "max_concurrent_positions": 3,     # Max 3 positions
    "trading_pairs": ["BTC/USD", "ETH/USD", "SOL/USD", "SUI/USD"]  # Initial trading pairs
}

# Bluefin configuration
BLUEFIN_CONFIG = {
    "network": "SUI_PROD",
    "private_key": os.getenv("BLUEFIN_PRIVATE_KEY"),
}

# Claude configuration
CLAUDE_CONFIG = {
    "api_key": os.getenv("CLAUDE_API_KEY"),
    "model": "claude-3.7-sonnet",
    "temperature": 0,
}

# Perplexity configuration
PERPLEXITY_CONFIG = {
    "api_key": os.getenv("PERPLEXITY_API_KEY"),
    "model": "sonar-reasoning-pro",
    "timeout": 120,
}

# TradingView webhook configuration
TRADINGVIEW_WEBHOOK_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "path": "/webhook",
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  
        },
        "file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "agent.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "DEBUG",
            "propagate": True
        },
    }
} 
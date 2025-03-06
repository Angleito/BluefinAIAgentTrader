import os

# Trading parameters
TRADING_PARAMS = {
    "position_size_percentage": 0.05,  # 5% of portfolio
    "leverage": 7,                     # 7x leverage
    "stop_loss_percentage": 0.15,      # 15% stop loss
    "max_concurrent_positions": 3,     # Max 3 positions
    "trading_pairs": ["BTC/USD", "ETH/USD", "SOL/USD", "SUI/USD"],  # Initial trading pairs
    "initial_account_balance": 10000,  # Initial account balance
    "max_risk_per_trade": 0.02,        # Maximum risk per trade (2% of account balance)
    "max_risk_per_symbol": 0.05,       # Maximum risk per symbol (5% of account balance)
    "max_daily_drawdown": 0.05,        # Maximum daily drawdown (5% of account balance)
    "risk_reward_ratio": 2.0,          # Target risk-reward ratio
    "atr_multiplier": 2.0,             # ATR multiplier for stop loss calculation
}

# Risk management configuration
RISK_MANAGEMENT_CONFIG = {
    "use_atr_for_stop_loss": True,     # Use ATR for stop loss calculation
    "trailing_stop_activation": 0.05,  # Activate trailing stop when price moves 5% in favor
    "break_even_activation": 0.03,     # Move stop loss to break even when price moves 3% in favor
    "max_trades_per_day": 5,           # Maximum number of trades per day
    "min_confidence_score": 7,         # Minimum confidence score to execute a trade (1-10)
}

# Performance tracking configuration
PERFORMANCE_TRACKING_CONFIG = {
    "log_file": "trading_log.json",    # File to log trades to
    "visualizations_dir": "visualizations",  # Directory to save visualizations
    "generate_report_frequency": "daily",  # How often to generate performance reports
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
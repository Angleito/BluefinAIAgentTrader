import os

# Trading parameters
TRADING_PARAMS = {
    # Account and risk settings
    "initial_account_balance": 10000,  # Initial account balance for risk calculations
    "max_risk_per_trade": 0.02,        # Maximum risk per trade (2% of account)
    "max_concurrent_positions": 3,     # Maximum number of open positions
    "max_daily_drawdown": 0.05,        # Maximum daily drawdown (5% of account)
    
    # Default stop loss/take profit settings if not provided in analysis
    "stop_loss_percentage": 0.02,      # Default stop loss (2% from entry)
    "take_profit_percentage": 0.04,    # Default take profit (4% from entry)
    
    # Trading confidence threshold
    "min_confidence_threshold": 7,     # Minimum confidence score to execute a trade (out of 10)
    
    # TradingView chart settings
    "chart_timeframe": "5",            # Chart timeframe in minutes
    "chart_symbol": "PYTH:SUIUSD",     # Trading symbol
    "chart_indicators": [
        "VuManChu Cipher A",
        "VuManChu Cipher B"
    ],
    "chart_candle_type": "Heikin Ashi",
    
    # Trading monitoring
    "analysis_interval": 300,          # Time between analyses in seconds (5 minutes)
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

# Bluefin API default settings
BLUEFIN_DEFAULTS = {
    "network": "MAINNET",              # Use "TESTNET" or "MAINNET"
    "leverage": 5,                     # Default leverage if not specified
    "default_symbol": "BTC-PERP",      # Default trading symbol
} 
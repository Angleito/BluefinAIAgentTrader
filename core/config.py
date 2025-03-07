"""
Configuration file for the Perplexity Trader.

This file contains all configurable parameters for the trading agent.
"""

import os
from typing import Dict, Any

def validate_config(config: Dict[str, Any], section: str):
    """
    Validate a configuration dictionary.
    
    Args:
        config: The configuration dictionary to validate
        section: The name of the configuration section (for error messages)
        
    Raises:
        ValueError: If any required keys are missing or have invalid values
    """
    required_keys = {
        "TRADING_PARAMS": [
            "chart_symbol",
            "timeframe",
            "candle_type",
            "indicators",
            "min_confidence",
            "analysis_interval_seconds",
            "max_position_size_usd",
            "leverage",
            "trading_symbol",
            "stop_loss_percentage",
            "take_profit_multiplier"
        ],
        "RISK_PARAMS": [
            "max_risk_per_trade",
            "max_open_positions",
            "max_daily_loss",
            "min_risk_reward_ratio"
        ],
        "AI_PARAMS": [
            "use_perplexity",
            "use_claude",
            "perplexity_confidence_threshold",
            "claude_confidence_threshold",
            "confidence_concordance_required"
        ]
    }
    
    for key in required_keys[section]:
        if key not in config:
            raise ValueError(f"Missing required key '{key}' in {section} configuration")
            
    # Additional validation for specific keys
    if section == "TRADING_PARAMS":
        if config["min_confidence"] < 0 or config["min_confidence"] > 1:
            raise ValueError(f"min_confidence must be between 0 and 1 (got {config['min_confidence']})")
        
        if config["leverage"] < 1:
            raise ValueError(f"leverage must be greater than or equal to 1 (got {config['leverage']})")
            
        if config["stop_loss_percentage"] < 0 or config["stop_loss_percentage"] > 1:
            raise ValueError(f"stop_loss_percentage must be between 0 and 1 (got {config['stop_loss_percentage']})")
            
    elif section == "RISK_PARAMS":
        if config["max_risk_per_trade"] < 0 or config["max_risk_per_trade"] > 1:
            raise ValueError(f"max_risk_per_trade must be between 0 and 1 (got {config['max_risk_per_trade']})")
            
        if config["max_open_positions"] < 1:
            raise ValueError(f"max_open_positions must be greater than or equal to 1 (got {config['max_open_positions']})")
            
        if config["max_daily_loss"] < 0 or config["max_daily_loss"] > 1:
            raise ValueError(f"max_daily_loss must be between 0 and 1 (got {config['max_daily_loss']})")
            
        if config["min_risk_reward_ratio"] < 1:
            raise ValueError(f"min_risk_reward_ratio must be greater than or equal to 1 (got {config['min_risk_reward_ratio']})")
            
    elif section == "AI_PARAMS":
        if config["perplexity_confidence_threshold"] < 0 or config["perplexity_confidence_threshold"] > 1:
            raise ValueError(f"perplexity_confidence_threshold must be between 0 and 1 (got {config['perplexity_confidence_threshold']})")
            
        if config["claude_confidence_threshold"] < 0 or config["claude_confidence_threshold"] > 1:
            raise ValueError(f"claude_confidence_threshold must be between 0 and 1 (got {config['claude_confidence_threshold']})")

# Trading parameters
TRADING_PARAMS = {
    # Chart analysis parameters
    "chart_symbol": "BTCUSDT",  # Symbol to analyze on TradingView
    "timeframe": "1h",          # Chart timeframe (e.g., 1m, 5m, 15m, 1h, 4h, 1d)
    "candle_type": "Heikin Ashi",  # Candle type (Regular, Heikin Ashi, etc.)
    "indicators": ["MACD", "RSI", "Bollinger Bands"],  # Indicators to add to chart
    
    # Trading execution parameters
    "trading_symbol": "BTC-PERP",  # Symbol to trade on Bluefin
    "leverage": 5,                 # Leverage to use for trades
    "min_confidence": 0.7,         # Minimum confidence score to execute a trade (0.0-1.0)
    "max_position_size_usd": 1000, # Maximum position size in USD
    "stop_loss_percentage": 0.02,  # Default stop loss percentage if not provided by AI
    "take_profit_multiplier": 2,   # Take profit as multiple of risk (risk:reward ratio)
    
    # Operational parameters
    "analysis_interval_seconds": 300,  # Time between analyses in seconds (5 minutes)
}

# Risk management parameters
RISK_PARAMS = {
    "max_risk_per_trade": 0.02,     # Maximum risk per trade (2% of account)
    "max_open_positions": 3,        # Maximum number of open positions
    "max_daily_loss": 0.05,         # Maximum daily loss (5% of account)
    "min_risk_reward_ratio": 2.0,   # Minimum risk:reward ratio
}

# AI analysis parameters
AI_PARAMS = {
    "use_perplexity": True,         # Whether to use Perplexity for analysis
    "use_claude": True,             # Whether to use Claude for analysis
    "perplexity_confidence_threshold": 0.7,  # Minimum confidence for Perplexity
    "claude_confidence_threshold": 0.7,      # Minimum confidence for Claude
    "confidence_concordance_required": True, # Require both AIs to agree
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
    "api_key": os.getenv("ANTHROPIC_API_KEY"),
    "model": os.getenv("CLAUDE_MODEL", "claude-3.7-sonnet"),
    "temperature": float(os.getenv("CLAUDE_TEMPERATURE", 0.2)),
    "max_tokens": int(os.getenv("CLAUDE_MAX_TOKENS", 8000)),
    "rate_limits": {
        "requests_per_minute": int(os.getenv("CLAUDE_REQUESTS_PER_MINUTE", 50)),
        "input_tokens_per_minute": int(os.getenv("CLAUDE_INPUT_TOKENS_PER_MINUTE", 20000)),
        "output_tokens_per_minute": int(os.getenv("CLAUDE_OUTPUT_TOKENS_PER_MINUTE", 8000))
    }
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

# Validate configurations
validate_config(TRADING_PARAMS, "TRADING_PARAMS")
validate_config(RISK_PARAMS, "RISK_PARAMS")
validate_config(AI_PARAMS, "AI_PARAMS") 
"""
Configuration file for the Perplexity Trader.

This file contains all configurable parameters for the trading agent.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Environment variables with defaults
# Server configuration
PORT = int(os.getenv("PORT", "5000"))
SOCKET_PORT = int(os.getenv("SOCKET_PORT", "5008"))
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "5004"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t", "yes")
FLASK_ENV = os.getenv("FLASK_ENV", "production")
AGENT_API_URL = os.getenv("AGENT_API_URL", f"http://localhost:{SOCKET_PORT}/api/process_alert")

# Security settings
JWT_SECRET = os.getenv("JWT_SECRET", "default_jwt_secret_change_in_production")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Trading settings
MOCK_TRADING = os.getenv("MOCK_TRADING", "True").lower() in ("true", "1", "t", "yes")
DEFAULT_SYMBOL = os.getenv("DEFAULT_SYMBOL", "SUI/USD")
DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "5m")
DEFAULT_LEVERAGE = int(os.getenv("DEFAULT_LEVERAGE", "5"))
DEFAULT_POSITION_SIZE_PCT = float(os.getenv("DEFAULT_POSITION_SIZE_PCT", "0.05"))
DEFAULT_STOP_LOSS_PCT = float(os.getenv("DEFAULT_STOP_LOSS_PCT", "0.15"))
DEFAULT_TAKE_PROFIT_PCT = float(os.getenv("DEFAULT_TAKE_PROFIT_PCT", "0.3"))
DEFAULT_MAX_POSITIONS = int(os.getenv("DEFAULT_MAX_POSITIONS", "3"))

# Tunnel configuration
USE_LOCALTUNNEL = os.getenv("USE_LOCALTUNNEL", "False").lower() in ("true", "1", "t", "yes")
LOCALTUNNEL_SUBDOMAIN = os.getenv("LOCALTUNNEL_SUBDOMAIN", "")
LOCALTUNNEL_URL = os.getenv("LOCALTUNNEL_URL", "")
LOCALTUNNEL_HTTPS_URL = os.getenv("LOCALTUNNEL_HTTPS_URL", "")

# Bore-specific configuration
USE_BORE = os.getenv("USE_BORE", "False").lower() in ("true", "1", "t", "yes")
BORE_SERVER = os.getenv("BORE_SERVER", "bore.digital")
BORE_PORT = int(os.getenv("BORE_PORT", "2200"))
BORE_LOCAL_HOST = os.getenv("BORE_LOCAL_HOST", "localhost")
BORE_LOCAL_PORT = int(os.getenv("BORE_LOCAL_PORT", "5001"))
BORE_TUNNEL_ID = os.getenv("BORE_TUNNEL_ID", "")
BORE_PASSWORD = os.getenv("BORE_PASSWORD", "")

# Logging configuration
DEBUG_LOGS = os.getenv("DEBUG_LOGS", "False").lower() in ("true", "1", "t", "yes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Trading parameters
TRADING_PARAMS = {
    # Chart analysis parameters
    "chart_symbol": os.getenv("DEFAULT_SYMBOL", "BTCUSDT").split("/")[0] + "USDT",  # Symbol to analyze on TradingView
    "timeframe": os.getenv("DEFAULT_TIMEFRAME", "1h"),          # Chart timeframe (e.g., 1m, 5m, 15m, 1h, 4h, 1d)
    "candle_type": "Heikin Ashi",  # Candle type (Regular, Heikin Ashi, etc.)
    "indicators": ["MACD", "RSI", "Bollinger Bands"],  # Indicators to add to chart
    
    # Trading execution parameters
    "trading_symbol": os.getenv("DEFAULT_SYMBOL", "BTC-PERP"),  # Symbol to trade on Bluefin
    "leverage": int(os.getenv("DEFAULT_LEVERAGE", "5")),        # Leverage to use for trades
    "min_confidence": 0.7,         # Minimum confidence score to execute a trade (0.0-1.0)
    "max_position_size_usd": 1000, # Maximum position size in USD
    "stop_loss_percentage": float(os.getenv("DEFAULT_STOP_LOSS_PCT", "0.02")),  # Default stop loss percentage if not provided by AI
    "take_profit_multiplier": 2,   # Take profit as multiple of risk (risk:reward ratio)
    "DOUBLE_SIZE_ON_OPPOSITE_POSITION": True,  # Double the position size if an opposite position exists
    
    # Analysis interval
    "analysis_interval_seconds": 3600,  # How often to analyze the chart (in seconds)
}

# Risk management parameters
RISK_PARAMS = {
    "max_risk_per_trade": 0.02,     # Maximum risk per trade (2% of account)
    "max_open_positions": int(os.getenv("DEFAULT_MAX_POSITIONS", "3")),  # Maximum number of open positions
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
    "network": os.getenv("BLUEFIN_NETWORK", "SUI_PROD"),
    "private_key": os.getenv("BLUEFIN_PRIVATE_KEY", ""),
    "api_key": os.getenv("BLUEFIN_API_KEY", ""),
    "api_secret": os.getenv("BLUEFIN_API_SECRET", ""),
    "api_url": os.getenv("BLUEFIN_API_URL", "https://dapi.api.sui-prod.bluefin.io"),
}

# Claude configuration
CLAUDE_CONFIG = {
    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "model": os.getenv("CLAUDE_MODEL", "claude-3.7-sonnet"),
    "fallback_model": os.getenv("CLAUDE_FALLBACK_MODEL", "claude-3-haiku-20240307"),
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
    "api_key": os.getenv("PERPLEXITY_API_KEY", ""),
    "primary_model": os.getenv("PERPLEXITY_PRIMARY_MODEL", "sonar-pro"),
    "fallback_model": os.getenv("PERPLEXITY_FALLBACK_MODEL", "sonar"),
    "timeout": 120,
}

# TradingView webhook configuration
TRADINGVIEW_WEBHOOK_CONFIG = {
    "host": WEBHOOK_HOST,
    "port": WEBHOOK_PORT,
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
            "level": LOG_LEVEL,
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",  
        },
        "file": {
            "level": "DEBUG" if DEBUG_LOGS else LOG_LEVEL,
            "formatter": "standard",
            "class": "logging.FileHandler",
            "filename": "agent.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "DEBUG" if DEBUG_LOGS else LOG_LEVEL,
            "propagate": True
        },
    }
}

# Bluefin API default settings
BLUEFIN_DEFAULTS = {
    "network": os.getenv("BLUEFIN_NETWORK", "SUI_PROD"),
    "leverage": DEFAULT_LEVERAGE,
    "default_symbol": DEFAULT_SYMBOL,
}

# Validate configurations
validate_config(TRADING_PARAMS, "TRADING_PARAMS")
validate_config(RISK_PARAMS, "RISK_PARAMS")
validate_config(AI_PARAMS, "AI_PARAMS") 
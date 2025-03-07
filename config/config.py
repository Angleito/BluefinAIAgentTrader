"""
Configuration file for the PerplexityTrader agent.
"""

# Trading parameters
TRADING_PARAMS = {
    "chart_symbol": "SUI/USD",
    "timeframe": "5m",
    "candle_type": "Heikin Ashi",
    "indicators": ["VuManChu Cipher B"],
    "min_confidence": 0.7,
    "analysis_interval_seconds": 300,
    "max_position_size_usd": 1000,
    "leverage": 12,
    "trading_symbol": "SUI-PERP",
    "stop_loss_percentage": 0.15,
    "take_profit_multiplier": 2
}

# Risk parameters
RISK_PARAMS = {
    "max_risk_per_trade": 0.02,  # 2% of account balance
    "max_open_positions": 3,
    "max_daily_loss": 0.05,  # 5% of account balance
    "min_risk_reward_ratio": 2.0
}

# AI parameters
AI_PARAMS = {
    "use_perplexity": True,
    "use_claude": True,
    "perplexity_confidence_threshold": 0.7,
    "claude_confidence_threshold": 0.7,
    "confidence_concordance_required": True
}

# Claude configuration
CLAUDE_CONFIG = {
    "model": "claude-3.7-sonnet",
    "temperature": 0.2,
    "max_tokens": 4000,
    "input_tokens_per_minute": 20000,
    "output_tokens_per_minute": 8000,
    "requests_per_minute": 50
} 
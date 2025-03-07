# PerplexityTrader: AI-Powered Crypto Trading Agent

An advanced trading agent that uses Claude and Perplexity AI to analyze TradingView charts and execute trades on the Bluefin Exchange.

![Trading Agent Architecture](architecture_diagram.png)

## Features

- **AI-Powered Analysis**: Utilizes Claude 3.7 Sonnet and Perplexity's sonar-pro models for chart analysis
- **Multi-Exchange Support**: Works with Bluefin Exchange (SUI and V2 APIs)
- **Resilient Design**: Multiple fallback mechanisms and error recovery
- **Risk Management**: Configurable risk parameters and position sizing
- **Docker Integration**: Easy deployment in containerized environments
- **Mock Trading Mode**: Test strategies without risking real funds
- **API Monitoring**: Track agent status and performance via REST API

## Architecture

The trading agent consists of these key components:

### Core Components

1. **Bluefin Client Interface**: Connect to trading platforms (`core/bluefin_client.py`)
2. **Chart Analysis System**: AI-powered technical analysis (`core/chart_analyzer.py`, `core/perplexity_client.py`)
3. **Alert Processing System**: Handle trading signals (`core/alert_processor.py`)
4. **Risk Management System**: Control position sizing and risk (`core/risk_manager.py`)
5. **API Server**: Monitor and control the agent (`api/server.py`)

Additional files:
- `config.py`: Configuration settings
- `mock_perplexity.py`: Mocked Perplexity client for testing
- `test_*.py`: Unit and integration tests

### Trading Process Flow

1. **Alert Triggering**: Monitor for new trading signals
2. **Chart Analysis**: Capture and analyze charts with AI
3. **Trade Confirmation**: Double-check signals before execution
4. **Position Sizing**: Calculate appropriate trade size
5. **Trade Execution**: Place orders on the exchange
6. **Position Management**: Monitor and adjust open positions

## Installation

### Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)

### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/perplexitytrader.git
cd perplexitytrader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright
python -m playwright install chromium
```

### Option 2: Docker Installation

```bash
# Build the Docker image
docker build -t perplexitytrader .

# Run the container
docker run -d --name perplexitytrader \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/alerts:/app/alerts \
  --env-file .env \
  perplexitytrader
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```
# API Keys
CLAUDE_API_KEY=your_claude_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Bluefin Configuration - Choose One:
# Option 1: SUI Client
BLUEFIN_PRIVATE_KEY=your_private_key_here
BLUEFIN_NETWORK=testnet  # or mainnet

# Option 2: V2 Client
BLUEFIN_API_KEY=your_api_key_here
BLUEFIN_API_SECRET=your_api_secret_here

# Trading Parameters
DEFAULT_POSITION_SIZE=0.1
DEFAULT_POSITION_SIZE_PCT=0.05
MOCK_TRADING=true  # Set to false for real trading
```

### Trading Parameters (config.py)

Customize trading behavior in `config.py`:

```python
# Trading parameters
TRADING_PARAMS = {
    "chart_symbol": "BTCUSDT",  # Symbol to analyze
    "timeframe": "1h",          # Chart timeframe
    "trading_symbol": "BTC-PERP", # Symbol to trade
    "leverage": 5,              # Leverage to use
    "stop_loss_percentage": 0.02, # Default stop loss
    "take_profit_multiplier": 2,  # Take profit as multiple of risk
}

# Risk management parameters
RISK_PARAMS = {
    "max_risk_per_trade": 0.02,  # 2% of account per trade
    "max_open_positions": 3,     # Maximum concurrent positions
    "max_daily_loss": 0.05,      # 5% max daily drawdown
}
```

## Usage

### Starting the Agent

```bash
# Start the agent
python agent.py
```

### Creating Alerts

The agent processes alert files placed in the `alerts` directory. Create alert files in this format:

```json
{
  "symbol": "BTCUSDT",
  "type": "buy_signal",
  "timestamp": "20240605_123456"
}
```

Example alert files:
- `alerts/example_buy_signal.json`
- `alerts/example_sell_signal.json`
- `alerts/example_close_position.json`
- `alerts/example_technical_analysis.json`

Alert types:
- `buy_signal`: Execute a buy/long order
- `sell_signal`: Execute a sell/short order
- `close_position`: Close an existing position
- `technical_analysis`: Perform chart analysis without trading

### API Endpoints

Monitor the agent using the built-in API:

- **Status Check**: `GET http://localhost:5000/status`
- **Root Endpoint**: `GET http://localhost:5000/`

## Development

### Project Structure

```
perplexitytrader/
├── agent.py             # Main agent code
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── Dockerfile           # Docker build configuration
├── docker-compose.yml   # Docker Compose configuration
├── mock_perplexity.py   # Mocked Perplexity client for testing
├── core/                # Core components
│   ├── alert_processor.py  # Alert processing logic
│   ├── bluefin_client.py   # Bluefin client interface
│   ├── chart_analyzer.py   # Chart analysis logic
│   ├── perplexity_client.py # Perplexity API client
│   └── risk_manager.py     # Risk management logic
├── api/                 # API components  
│   └── server.py           # FastAPI server
└── test/                # Unit and integration tests
    ├── test_alert_processor.py
    ├── test_bluefin_client.py
    ├── test_chart_analyzer.py
    └── test_risk_manager.py
```

### Recommendations for Improvement

1. **Code Organization**: Move more functionality to the `core/` directory for better separation of concerns.

2. **Tests**: Add more comprehensive unit and integration tests for critical components in the `test/` directory.

3. **Error Handling**: Further improve error handling, especially in API calls and chart analysis. Use consistent error response formats.

4. **Logging**: Enhance logging with more structured formats and levels. Use appropriate log levels for different types of messages.

5. **Rate Limiting**: Implement more sophisticated rate limiting for API calls to avoid hitting rate limits.

6. **Documentation**: Add inline documentation to explain complex trading logic and algorithms.

7. **Configuration Validation**: Add validation for configuration parameters to catch invalid settings early.

### Mock Trading Mode

By default, the agent runs in mock trading mode, which simulates trades without executing real orders. This is ideal for testing strategies and configurations.

To enable real trading:
1. Set `MOCK_TRADING=false` in your `.env` file
2. Provide valid API credentials

### Playwright for Chart Capture

The agent uses Playwright to capture screenshots of TradingView charts. Make sure Playwright is properly installed:

```bash
python -m playwright install chromium
```

## Security Considerations

- **API Keys**: Store securely in environment variables, never hardcode
- **Risk Limits**: Configure appropriate risk parameters
- **Testing**: Always test new strategies in mock mode first
- **Rate Limits**: Be aware of API rate limits for Claude and Perplexity
- **Permissions**: Use least-privilege access for API keys

## Troubleshooting

### Common Issues

1. **Missing Screenshots**:
   - Check Playwright installation
   - Verify TradingView URL access

2. **Authentication Errors**:
   - Verify API keys in .env file
   - Check for expired or revoked credentials

3. **No Trades Executed**:
   - Confirm `MOCK_TRADING=false` for real trading
   - Check alert files format and processing

### Logs

Logs are stored in the `logs/` directory and provide detailed information about the agent's activities.

## License

[MIT License](LICENSE)

## Acknowledgements

- [Bluefin Exchange](https://bluefin.io/) for their trading API
- [Anthropic](https://www.anthropic.com/) for Claude AI
- [Perplexity](https://www.perplexity.ai/) for their AI services
- [TradingView](https://www.tradingview.com/) for chart data
# PerplexityTrader

PerplexityTrader is an AI-powered cryptocurrency trading platform that leverages advanced AI models and real-time market data to make intelligent trading decisions. The system combines webhook integrations, websocket communication, and AI analysis to provide a comprehensive trading solution.

This project was developed with the assistance of [Cursor](https://cursor.sh/), an AI-powered code editor.

## System Overview

PerplexityTrader consists of several interconnected components:

1. **Webhook Service**: Receives external alerts and trading signals (e.g., from TradingView)
2. **WebSocket Service**: Provides real-time updates to the user interface
3. **Agent Service**: Core AI-powered trading engine that processes market data and executes trades
4. **Web Interface**: User dashboard for monitoring and controlling the trading system

## Project Structure

```
perplexitytrader/
├── api/                         # API implementations
├── bluefin_env/                 # Bluefin Exchange integration
├── config/                      # Configuration files
├── core/                        # Core trading logic and strategies
├── examples/                    # Example scripts and configurations
├── frontend/                    # Web UI components and assets
├── infrastructure/              # Infrastructure configurations
│   └── docker/                  # All Docker configuration and services
│       ├── docker-compose.yml            # Main Docker Compose configuration
│       ├── docker-compose.simple.yml     # Simplified Docker Compose for easier startup
│       ├── docker-compose.prod.yml       # Production-ready Docker Compose config
│       ├── Dockerfile                    # Main service Dockerfile
│       ├── Dockerfile.agent              # AI agent-specific Dockerfile
│       ├── requirements.txt              # Python dependencies
│       ├── app.py                        # Main application entry point
│       ├── simple_agent.py               # Simplified agent implementation
│       ├── simple_webhook.py             # Simplified webhook implementation
│       ├── simple_websocket.py           # Simplified websocket implementation
│       ├── webhook_server.py             # Full webhook server implementation
│       ├── websocket_server.py           # Full websocket server implementation
│       ├── healthcheck.sh                # Health check script for containers
│       ├── check_services_docker.sh      # Service monitoring script
│       └── nginx.conf                    # Nginx web server configuration
├── logs/                        # System logs
├── src/                         # Source code for main application
├── test/                        # Test files and test configurations
├── .env.example                 # Example environment variables file
├── .gitignore                   # Git ignore rules
└── README.md                    # This documentation file
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Angleito/perplextrader.git
   cd perplextrader
   ```

2. Copy the example environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

3. Build and start the services:
   ```bash
   cd infrastructure/docker
   docker-compose -f docker-compose.simple.yml up
   ```

## Running the Agent Stack

The entire agent stack can be started using Docker Compose from the `infrastructure/docker` directory:

```bash
cd infrastructure/docker
docker-compose -f docker-compose.simple.yml up
```

For production deployments, use:
```bash
cd infrastructure/docker
docker-compose -f docker-compose.prod.yml up -d
```

For testing configurations:
```bash
cd infrastructure/docker
docker-compose -f docker-compose.test.yml up
```

## Component Overview

### Webhook Service (port 5004)
Receives external signals and alerts, processes them, and forwards to the agent for action. Access at `http://localhost:5004/webhook`.

The webhook service is implemented in two versions:
- `simple_webhook.py`: A simplified version for quick testing
- `webhook_server.py`: The full-featured implementation

### WebSocket Service (port 5008)
Provides real-time updates and notifications to the web interface. Connect at `ws://localhost:5008/socket.io`.

The websocket service is implemented in two versions:
- `simple_websocket.py`: A simplified version for quick testing
- `websocket_server.py`: The full-featured implementation

### Agent Service (port 5003)
The AI-powered trading engine that analyzes market data and executes trades. API available at `http://localhost:5003/api`.

The agent service is implemented in:
- `simple_agent.py`: A simplified version for quick testing
- `app.py`: The main application that integrates all services

### Web Interface (port 8080)
User dashboard for monitoring and controlling the trading system. Access at `http://localhost:8080`.

## Configuration

Key configuration options are controlled through environment variables in the `.env` file:

- `NGINX_PORT`: Web interface port (default: 8080)
- `FLASK_APP_PORT`: Agent API port (default: 5003)
- `WEBHOOK_PORT`: Webhook service port (default: 5004)
- `SOCKET_PORT`: WebSocket service port (default: 5008)
- `MOCK_TRADING`: Enable mock trading mode (default: true)
- `ANTHROPIC_API_KEY`: API key for Claude AI services
- `PERPLEXITY_API_KEY`: API key for Perplexity AI services
- `BLUEFIN_API_KEY`: API key for Bluefin Exchange
- `BLUEFIN_API_SECRET`: API secret for Bluefin Exchange
- `BLUEFIN_PRIVATE_KEY`: Private key for Bluefin Exchange transactions

## AI Models and Integrations

PerplexityTrader leverages several powerful AI models and integrations:

- **Claude by Anthropic**: Powers advanced market analysis and decision-making
- **Perplexity AI**: Provides research capabilities and market insights
- **Bluefin Exchange**: Used for cryptocurrency trading through their API

## External Dependencies

The project relies on several external Git repositories:

- [Bluefin Client Python SUI](https://github.com/fireflyprotocol/bluefin-client-python-sui.git)
- [Bluefin V2 Client Python](https://github.com/fireflyprotocol/bluefin-v2-client-python.git)

## Security

The project incorporates several security measures:

- Regular dependency updates to patch vulnerabilities
- Non-root user execution in Docker containers
- Read-only file systems for containers where possible
- Security-focused Docker settings (no-new-privileges, read-only, tmpfs)
- Volume mount permissions that limit write access
- Health checks for all services
- Secure package versions to prevent known vulnerabilities
- Automated security scanning tools

### Running Security Checks

You can run security checks on the project using the provided script:

```bash
./security_checker.sh
```

This script checks for:
- Outdated packages
- Known vulnerabilities in dependencies
- Exposed secrets or API keys
- Docker security best practices
- File permissions

## Health Monitoring

The project includes health monitoring features:

```bash
# Run the health check script directly
./infrastructure/docker/healthcheck.sh

# View health status from running containers
docker ps -a
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

Special thanks to:
- Anthropic for the Claude AI model
- Perplexity AI for research capabilities
- Bluefin Exchange for their trading API

## Agent Trading Workflow

The PerplexityTrader's AI agent follows a sophisticated workflow for making and executing trading decisions on Bluefin Exchange. Below is a detailed explanation of the entire process from signal reception to trade execution and monitoring.

### Signal Reception and Processing

1. **External Signal Reception**:
   - Trading signals are received through the webhook server (`webhook_server.py`), typically from TradingView or other signal providers
   - Signals contain information like asset pair, direction (long/short), entry price, stop loss, take profit, and confidence level
   - The webhook server validates the signature and structure of incoming signals before processing

2. **Signal Enrichment**:
   - Raw signals are enriched with additional market data from various sources
   - The system fetches current market conditions, liquidity depth, recent price action, and volatility metrics
   - Historical performance of similar signals is analyzed for pattern recognition

3. **AI Analysis**:
   - Enriched signals are passed to the AI model (Claude by Anthropic) through the agent service
   - The AI performs multi-factor analysis including:
     - Technical analysis confirmation (trend direction, support/resistance levels)
     - Market sentiment analysis from news and social media
     - Pattern recognition from historical similar market conditions
     - Risk assessment based on current portfolio exposure

### Decision Making Process

1. **Signal Qualification**:
   - The agent first determines if a signal meets the minimum qualifications for consideration
   - Checks include: signal freshness, source reputation, minimum confidence threshold
   - Signals that don't meet basic criteria are logged but not acted upon

2. **Position Sizing Calculation**:
   - For qualified signals, the agent calculates appropriate position size based on:
     - Current portfolio value and allocation limits
     - Risk parameters (maximum drawdown allowed per trade)
     - Volatility-adjusted position sizing to maintain consistent risk
     - Kelly criterion application for optimal position sizing

3. **Trade Decision**:
   - The final decision incorporates:
     - AI model recommendation (confidence score from 0-1)
     - Current account exposure and diversification
     - Market conditions (volatility, liquidity, spread)
     - Risk management rules (maximum drawdown, maximum positions)
   - Decision outputs include: trade/no trade, direction, position size, entry price range, stop loss, take profit

### Bluefin Exchange Integration

1. **Authentication and Connection**:
   - The agent connects to Bluefin Exchange using the Bluefin API client libraries
   - Authentication is performed using API key, secret, and private key credentials stored in `.env`
   - A secure websocket connection is established for real-time order book and execution updates

2. **Market Data Retrieval**:
   - Before execution, the agent retrieves:
     - Current order book depth to assess liquidity
     - Recent trades to identify potential slippage
     - Funding rates for perpetual contracts
     - Open interest and liquidation levels

3. **Order Preparation**:
   - The agent constructs order parameters including:
     - Symbol/market pair (e.g., BTC-USDT)
     - Order type (limit, market, stop, etc.)
     - Direction (buy/sell)
     - Quantity (in base or quote currency)
     - Price (for limit orders)
     - Time in force settings
     - Stop loss and take profit parameters

4. **Order Execution**:
   - Based on market conditions, the agent may use different execution strategies:
     - Direct market orders for immediate execution
     - Limit orders at optimized price levels
     - TWAP (Time-Weighted Average Price) for larger positions
     - Iceberg orders for minimizing market impact

5. **Order Confirmation and Verification**:
   - All orders are logged with unique identifiers
   - Order status updates are received via websocket connection
   - Filled orders are verified against expected parameters
   - Any discrepancies trigger alerts to the monitoring system

### Position Management

1. **Active Position Monitoring**:
   - Open positions are continuously monitored for:
     - Price movement relative to entry
     - Distance to stop loss and take profit levels
     - Changes in market conditions or volatility
     - New signals that might contradict current positions

2. **Dynamic Position Adjustment**:
   - The agent can modify existing positions based on:
     - Trailing stop adjustments as profit accumulates
     - Partial take profits at predefined levels
     - Position size increases/decreases based on conviction changes
     - Hedging with correlated assets when necessary

3. **Risk Management Enforcement**:
   - Real-time risk monitoring ensures:
     - Maximum drawdown limits are not exceeded
     - Exposure to single assets stays within limits
     - Portfolio margin requirements are maintained
     - Liquidation prices remain at safe distances

4. **Exit Strategy Execution**:
   - Positions are closed based on:
     - Stop loss or take profit triggers
     - Time-based exits for trades exceeding maximum duration
     - Signal reversal from the AI model
     - Overall portfolio rebalancing requirements

### Notification and Reporting

1. **Real-time WebSocket Updates**:
   - All trading activities trigger real-time updates via websocket server (`websocket_server.py`)
   - The frontend dashboard displays current positions, orders, and performance metrics
   - Alerts are pushed for significant events (trade entries, exits, risk thresholds)

2. **Performance Tracking**:
   - Each trade is logged with comprehensive metadata for later analysis
   - Performance metrics are calculated including:
     - Win/loss ratio
     - Average profit/loss
     - Maximum drawdown
     - Sharpe and Sortino ratios
     - Return on investment (ROI)

3. **AI Model Feedback Loop**:
   - Trade outcomes are fed back to the AI system for continuous learning
   - Pattern recognition improves with each completed trade
   - Strategy effectiveness is regularly evaluated and adjusted

### Fail-safe Mechanisms

1. **Connection Monitoring**:
   - Continuous heartbeat checks with Bluefin Exchange
   - Automatic reconnection with exponential backoff
   - Fallback servers in case of primary connection failure

2. **Emergency Shutdown**:
   - Circuit breaker triggers for:
     - Excessive losses within defined periods
     - Unusual market volatility
     - API or system errors exceeding thresholds
     - Liquidity concerns on the exchange

3. **Disaster Recovery**:
   - Regular state snapshots for system recovery
   - Secure backup of all open positions and orders
   - Clear procedures for manual intervention

## Infrastructure Setup

```
perplexitytrader/
├── api/                         # API implementations
├── bluefin_env/                 # Bluefin Exchange integration
├── config/                      # Configuration files
├── core/                        # Core trading logic and strategies
├── examples/                    # Example scripts and configurations
├── frontend/                    # Web UI components and assets
├── infrastructure/              # Infrastructure configurations
│   └── docker/                  # All Docker configuration and services
│       ├── docker-compose.yml            # Main Docker Compose configuration
│       ├── docker-compose.simple.yml     # Simplified Docker Compose for easier startup
│       ├── docker-compose.prod.yml       # Production-ready Docker Compose config
│       ├── Dockerfile                    # Main service Dockerfile
│       ├── Dockerfile.agent              # AI agent-specific Dockerfile
│       ├── requirements.txt              # Python dependencies
│       ├── app.py                        # Main application entry point
│       ├── simple_agent.py               # Simplified agent implementation
│       ├── simple_webhook.py             # Simplified webhook implementation
│       ├── simple_websocket.py           # Simplified websocket implementation
│       ├── webhook_server.py             # Full webhook server implementation
│       ├── websocket_server.py           # Full websocket server implementation
│       ├── healthcheck.sh                # Health check script for containers
│       ├── check_services_docker.sh      # Service monitoring script
│       └── nginx.conf                    # Nginx web server configuration
├── logs/                        # System logs
├── src/                         # Source code for main application
├── test/                        # Test files and test configurations
├── .env.example                 # Example environment variables file
├── .gitignore                   # Git ignore rules
└── README.md                    # This documentation file
``` 
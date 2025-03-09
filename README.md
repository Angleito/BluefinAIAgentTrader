# PerplexityTrader

PerplexityTrader is an AI-powered cryptocurrency trading platform that leverages advanced AI models and real-time market data to make intelligent trading decisions. The system combines webhook integrations, websocket communication, and AI analysis to provide a comprehensive trading solution.

## System Overview

PerplexityTrader consists of several interconnected components:

1. **Webhook Service**: Receives external alerts and trading signals (e.g., from TradingView)
2. **WebSocket Service**: Provides real-time updates to the user interface
3. **Agent Service**: Core AI-powered trading engine that processes market data and executes trades
4. **Web Interface**: User dashboard for monitoring and controlling the trading system

## Project Structure

```
perplexitytrader/
├── infrastructure/docker/   # Docker configuration and service definitions
│   ├── docker-compose.yml   # Main Docker Compose configuration
│   ├── Dockerfile           # Main service Dockerfile
│   ├── Dockerfile.agent     # AI agent-specific Dockerfile
│   ├── requirements.txt     # Python dependencies
│   ├── simple_agent.py      # Simplified agent implementation
│   ├── simple_webhook.py    # Simplified webhook implementation
│   └── simple_websocket.py  # Simplified websocket implementation
├── core/                    # Core trading logic and strategies
├── alerts/                  # Alert configurations and history
├── logs/                    # System logs
├── config/                  # Configuration files
├── bluefin_env/             # Bluefin Exchange integration
└── api/                     # API implementations
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

## Component Overview

### Webhook Service (port 5004)
Receives external signals and alerts, processes them, and forwards to the agent for action. Access at `http://localhost:5004/webhook`.

### WebSocket Service (port 5008)
Provides real-time updates and notifications to the web interface. Connect at `ws://localhost:5008/socket.io`.

### Agent Service (port 5003)
The AI-powered trading engine that analyzes market data and executes trades. API available at `http://localhost:5003/api`.

### Web Interface (port 8080)
User dashboard for monitoring and controlling the trading system. Access at `http://localhost:8080`.

## Configuration

Key configuration options are controlled through environment variables in the `.env` file:

- `NGINX_PORT`: Web interface port (default: 8080)
- `FLASK_APP_PORT`: Agent API port (default: 5003)
- `WEBHOOK_PORT`: Webhook service port (default: 5004)
- `SOCKET_PORT`: WebSocket service port (default: 5008)
- `MOCK_TRADING`: Enable mock trading mode (default: true)

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

Special thanks to:
- Anthropic for the Claude AI model
- Perplexity AI for research capabilities
- Bluefin Exchange for their trading API 
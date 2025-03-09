# PerplexityTrader

PerplexityTrader is an AI-powered crypto trading platform that combines the analytical capabilities of Claude and Perplexity AI to make informed trading decisions in the cryptocurrency market.

## System Architecture

The system consists of the following components:

1. **Web Server (Nginx)**: Serves the web interface and proxies requests to the backend services.
2. **Trading Agent**: Analyzes market data and executes trades.
3. **Webhook Service**: Receives alerts from external sources like TradingView.
4. **WebSocket Service**: Provides real-time updates to the web interface.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Bash shell

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/perplexitytrader.git
   cd perplexitytrader
   ```

2. Start the Docker environment:
   ```bash
   ./start_docker.sh
   ```

3. Access the web interface at http://localhost:8080

### Usage

- **Web Interface**: Access the web interface at http://localhost:8080
- **Agent API**: Access the agent API at http://localhost:8080/api/
- **Webhook**: Send alerts to http://localhost:8080/webhook
- **WebSocket**: Connect to the WebSocket at http://localhost:8080/ws

### Scripts

- `start_docker.sh`: Starts the Docker environment
- `stop_docker.sh`: Stops the Docker environment
- `check_status.sh`: Checks the status of the Docker environment

## Development

### Directory Structure

- `infrastructure/docker/`: Docker configuration files
- `core/`: Core trading logic
- `logs/`: Log files
- `analysis/`: Analysis results

### Environment Variables

The following environment variables can be set in the `.env` file:

- `NGINX_PORT`: Port for the web server (default: 8080)
- `AGENT_PORT`: Port for the trading agent (default: 5003)
- `WEBHOOK_PORT`: Port for the webhook service (default: 5004)
- `WEBSOCKET_PORT`: Port for the WebSocket service (default: 5008)
- `MOCK_TRADING`: Enable mock trading (default: true)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Claude AI](https://www.anthropic.com/claude) for providing the AI analysis
- [Perplexity AI](https://www.perplexity.ai/) for providing the AI analysis
- [Bluefin Exchange](https://www.bluefin.io/) for the trading API

## Multi-Architecture Docker Builds

### Prerequisites
- Docker 19.03 or newer
- Docker BuildX plugin
- Docker Compose v2

### Building Multi-Architecture Images

#### Local Build and Test
```bash
# Build for current architecture
docker build -t perplexitytrader-webhook:latest .

# Build for specific platforms locally
docker buildx build \
  --platform linux/amd64 \
  -t perplexitytrader-webhook:latest \
  --load .
```

#### Pushing Multi-Architecture Images
```bash
# Use the provided build script to build and push
./build.sh [optional-tag]

# Or manually build and push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t perplexitytrader-webhook:latest \
  --push .
```

### Supported Architectures
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM 64-bit)

### Caching Strategies
- Local build cache: `/tmp/.buildx-cache`
- Registry build cache: `perplexitytrader/webhook:buildcache`

### Troubleshooting
- Ensure Docker BuildX is installed: `docker buildx version`
- Check available builders: `docker buildx ls`
- Create a new builder: `docker buildx create --use`
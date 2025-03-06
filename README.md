# Trading Agent with AI Analysis

A comprehensive trading agent that uses Claude 3.7 Sonnet (with Perplexity as fallback) to analyze TradingView charts and execute trades on the Bluefin Exchange.

## Features

- Chart analysis using Claude 3.7 Sonnet and Perplexity AI
- TradingView webhook integration for automated trade signals
- Bluefin Exchange API integration for real trading
- Docker deployment for 24/7 autonomous operation
- Public webhook endpoint via ngrok

## Prerequisites

- Docker and Docker Compose
- Bluefin Exchange account with API keys
- Anthropic API key (for Claude)
- Perplexity API key
- ngrok account with authtoken

## Setup

### 1. Configure Environment Variables

Create a `.env` file with the following variables:

```
# Bluefin API Keys
BLUEFIN_PRIVATE_KEY=your_private_key_here
BLUEFIN_NETWORK=MAINNET

# AI API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Claude Configuration
CLAUDE_MODEL=claude-3.7-sonnet
CLAUDE_MAX_TOKENS=8000
CLAUDE_TEMPERATURE=0.2

# ngrok Configuration
NGROK_AUTHTOKEN=your_ngrok_authtoken_here
NGROK_DOMAIN=your_custom_domain_if_available
```

### 2. Build and Start Docker Containers

```bash
docker-compose up -d
```

This will start three services:
- `web`: Flask app that handles webhooks (port 5000)
- `trader`: The trading agent that processes analysis requests
- `ngrok`: Creates a public URL for your webhook

### 3. Get Your Public Webhook URL

Access the ngrok dashboard at http://localhost:4040 to find your public URL.

### 4. Configure TradingView Alerts

Set up TradingView alerts with webhooks using the following format:

1. In TradingView, create a new alert
2. Set your conditions (price action, indicators, etc.)
3. Under "Webhook URL", enter your ngrok URL + "/webhook"
   Example: `https://your-domain.ngrok.io/webhook`
4. Set the alert message format to JSON:
   ```json
   {
     "ticker": "{{ticker}}",
     "price": "{{close}}",
     "alert_type": "buy_signal",
     "timeframe": "5m"
   }
   ```
5. Save the alert

## Usage

Once everything is set up, the system will:

1. Receive webhooks from TradingView
2. Capture and analyze chart screenshots using Claude 3.7 Sonnet (or Perplexity if Claude fails)
3. Generate trading recommendations
4. Execute trades on Bluefin Exchange when appropriate

## Monitoring

- Logs are stored in the `logs` directory
- Screenshots are saved in the `screenshots` directory
- Analysis reports are saved in the `analysis` directory

You can monitor these files to track the agent's performance.

## Troubleshooting

- **Webhook errors**: Check the `logs/webhook_server.log` file
- **Trading errors**: Check the `logs/bluefin_agent.log` file
- **API issues**: Verify your API keys in the `.env` file
- **Docker issues**: Run `docker-compose logs` to see container logs

## Overview

Perplexity Trader is an automated trading system that:

1. Captures TradingView charts for technical analysis
2. Uses AI (Claude and Perplexity) to analyze trading opportunities
3. Executes trades on the Bluefin Exchange based on AI recommendations
4. Manages risk according to configurable parameters

## Requirements

- Python 3.8+
- Playwright for browser automation
- Bluefin client libraries (SUI or v2)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/perplexitytrader.git
   cd perplexitytrader
   ```

2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```
   playwright install
   ```

4. Install Bluefin client libraries (choose one):
   ```
   # For SUI client
   pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git
   
   # For v2 client
   pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git
   ```

## Configuration

1. Create a `.env` file with your API credentials:
   ```
   # For SUI client
   BLUEFIN_PRIVATE_KEY=your_private_key_here
   BLUEFIN_NETWORK=TESTNET  # or MAINNET
   
   # For v2 client
   BLUEFIN_API_KEY=your_api_key_here
   BLUEFIN_API_SECRET=your_api_secret_here
   BLUEFIN_NETWORK=testnet  # or mainnet
   ```

2. Customize trading parameters in `config.py`:
   - `TRADING_PARAMS`: Chart settings, trading execution parameters
   - `RISK_PARAMS`: Risk management settings
   - `AI_PARAMS`: AI analysis configuration

## Usage

Run the trading agent:
```
python agent.py
```

The agent will:
1. Connect to the Bluefin Exchange
2. Analyze TradingView charts at regular intervals
3. Execute trades when AI analysis meets confidence thresholds
4. Log all activities and save trade analysis

## Directory Structure

- `agent.py`: Main trading agent code
- `config.py`: Configuration parameters
- `logs/`: Log files
- `screenshots/`: Chart screenshots
- `analysis/`: Trade analysis results

## API Security Best Practices

- Never commit your API keys or private keys to version control
- Use environment variables or a `.env` file to store sensitive credentials
- Set appropriate permissions on your `.env` file (chmod 600)
- Regularly rotate your API keys
- Use testnet for development and testing

## License

MIT

## Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves significant risk. Use at your own risk.

## AI Decision Process

The Perplexity Trader uses a two-step AI process for making trading decisions:

1. **Claude 3.7 Sonnet**: The primary AI for analyzing market data and generating initial trading decisions. Claude 3.7 Sonnet is Anthropic's most advanced model, capable of nuanced reasoning and analysis. It receives market data as input and outputs a structured decision including the action (buy/sell/hold) and reasoning.

2. **Perplexity**: Acts as a confirmation step for Claude's decisions. The initial decision from Claude is passed to Perplexity, which assesses if it agrees with the decision and reasoning. If Perplexity confirms the decision, the trade is executed. If Perplexity disagrees, the trade is cancelled or modified based on predefined logic.

This combination of Claude's deep reasoning capabilities and Perplexity's confirmation step helps ensure trading decisions are robust and well-justified. The two AIs provide an additional layer of scrutiny to avoid impulsive or poorly reasoned trades.

Configuration for the AI models can be found in `config.py`. The `CLAUDE_CONFIG` dictionary specifies the model version, API key, and generation parameters for Claude. Perplexity configuration is under `PERPLEXITY_CONFIG`.
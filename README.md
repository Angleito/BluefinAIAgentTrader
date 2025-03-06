# AI Trading Agent for Bluefin

This project implements an AI trading agent that utilizes Claude Sonnet 3.7 for decision making and Perplexity AI for analyzing TradingView charts and confirming trades. The agent integrates with the Bluefin Exchange on the Sui network for order execution and account management.

## Features

- AI decision engine powered by Claude Sonnet 3.7
- Trade signal generation using TradingView webhooks with VumanChu Cipher A and B indicators and Heiken Ashi candles
- Trade confirmation and chart analysis using Perplexity AI
- Integration with Bluefin Exchange API for order execution and account management
- Configurable trading parameters (leverage, position size, stop loss)
- Comprehensive logging and error handling

## Architecture

The system consists of the following core components:

1. Bluefin Exchange API integration for order execution and account management
2. TradingView webhook listener for receiving trading signals 
3. AI decision-making engine powered by Claude Sonnet 3.7
4. Perplexity AI for analyzing TradingView charts and confirming trades
5. Performance tracking and logging system

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/perpleixtytrader.git
cd perpleixtytrader
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
**IMPORTANT**: Make sure you have installed all the dependencies before proceeding. The agent will not work without the required packages.

3. Set up your environment variables by creating a `.env` file:
```
CLAUDE_API_KEY="your_claude_api_key"
PERPLEXITY_API_KEY="your_perplexity_api_key" 
BLUEFIN_PRIVATE_KEY="your_bluefin_private_key"
```

## Usage

1. Configure the trading parameters in `config.py`

2. Run the agent with:
```bash
python main.py
```

The agent will:
1. Listen for TradingView webhook signals
2. Analyze the signals using Claude Sonnet 3.7
3. Confirm the trade using Perplexity AI chart analysis
4. Execute the trade on Bluefin Exchange if confirmed
5. Log all activity and track performance metrics

## Trading Parameters

The default trading parameters are:
- Position size: 5% of portfolio
- Leverage: 7x
- Stop loss: 15% from entry
- Maximum concurrent positions: 3
- Trading pairs: BTC/USD, ETH/USD, SOL/USD, SUI/USD

These parameters can be modified in the `config.py` file.

## Future Enhancements

- Implement a web interface for monitoring trades and performance
- Add more advanced risk management techniques
- Support additional exchanges and trading pairs
- Enhance the AI models with ongoing training and optimization

## License

MIT
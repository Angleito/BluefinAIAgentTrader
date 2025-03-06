# AI Trading Agent for Bluefin

This project implements an AI trading agent that utilizes Claude Sonnet 3.7 for decision making and Perplexity AI for analyzing TradingView charts and confirming trades. The agent integrates with the Bluefin Exchange on the Sui network for order execution and account management.

## Features

- AI decision engine powered by Claude Sonnet 3.7
- Trade signal generation using TradingView webhooks with VumanChu Cipher A and B indicators and Heiken Ashi candles
- Trade confirmation and chart analysis using Perplexity AI
- Integration with Bluefin Exchange API for order execution and account management
- Advanced risk management and position sizing
- Performance tracking and visualization tools
- Configurable trading parameters (leverage, position size, stop loss)
- Comprehensive logging and error handling

## Architecture

The system consists of the following core components:

1. Bluefin Exchange API integration for order execution and account management
2. TradingView webhook listener for receiving trading signals 
3. AI decision-making engine powered by Claude Sonnet 3.7
4. Perplexity AI for analyzing TradingView charts and confirming trades
5. Risk management system for controlling trading risk
6. Performance tracking and visualization system
7. Trade execution module for opening and closing positions
8. Comprehensive logging system

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
4. Apply risk management rules to determine position size and risk parameters
5. Execute the trade on Bluefin Exchange if confirmed
6. Set stop loss and take profit orders
7. Track performance and generate visualizations
8. Log all activity and track performance metrics

## Trading Parameters

The default trading parameters are:
- Position size: 5% of portfolio
- Leverage: 7x
- Stop loss: 15% from entry
- Maximum concurrent positions: 3
- Trading pairs: BTC/USD, ETH/USD, SOL/USD, SUI/USD

These parameters can be modified in the `config.py` file.

## Core Modules

### Performance Tracking

The performance tracking module (`core/performance_tracker.py`) logs and analyzes trading performance, providing metrics such as:

- Win rate
- Profit factor
- Average profit/loss
- Maximum drawdown
- Total P&L

### Risk Management

The risk management module (`core/risk_manager.py`) helps control trading risk and position sizing, providing functionality to:

- Calculate position sizes based on risk parameters
- Check if new trades can be opened based on risk limits
- Calculate stop loss and take profit levels
- Determine when positions should be adjusted or closed

### Visualization

The visualization module (`core/visualization.py`) generates charts and graphs for trading performance analysis, including:

- Equity curves
- Win/loss distributions
- Monthly performance
- Drawdown analysis

### Trade Execution

The trade execution module (`core/trade_executor.py`) handles the execution of trades through the Bluefin API, providing functionality to:

- Open and close positions based on processed trading signals
- Integrate with the risk manager to control position sizing
- Set stop loss and take profit orders
- Log executed trades for performance tracking

See the `core/README.md` file for more detailed information on these modules.

## Examples

The `examples` directory contains example scripts demonstrating how to use the various modules:

- `performance_analysis_example.py`: Demonstrates how to use the performance tracking, risk management, and visualization modules

## Future Enhancements

- Implement a web interface for monitoring trades and performance
- Add more advanced risk management techniques
- Support additional exchanges and trading pairs
- Enhance the AI models with ongoing training and optimization
- Implement portfolio optimization algorithms

## License

MIT
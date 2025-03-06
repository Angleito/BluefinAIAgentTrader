# Core Trading Modules

This directory contains core modules for trading performance tracking, risk management, visualization, and trade execution.

## Modules

### Performance Tracker (`performance_tracker.py`)

The Performance Tracker module logs and analyzes trading performance. It provides functionality to:

- Log trade entries and exits
- Calculate performance metrics (win rate, profit factor, etc.)
- Track open and closed positions

```python
from core.performance_tracker import performance_tracker

# Log a trade entry
trade = {
    "trade_id": "trade_1",
    "symbol": "BTC/USD",
    "type": "buy",
    "timestamp": 1646092800,  # Unix timestamp
    "entry_price": 40000,
    "position_size": 0.1,
    "stop_loss": 39000,
    "take_profit": 42000
}
performance_tracker.log_trade_entry(trade)

# Log a trade exit
performance_tracker.log_trade_exit("trade_1", 42000, 1646179200)

# Get performance metrics
metrics = performance_tracker.get_performance_metrics()
print(f"Win Rate: {metrics['win_rate']:.2%}")
```

### Risk Manager (`risk_manager.py`)

The Risk Manager module helps control trading risk and position sizing. It provides functionality to:

- Calculate position sizes based on risk parameters
- Check if new trades can be opened based on risk limits
- Calculate stop loss and take profit levels
- Determine when positions should be adjusted or closed

```python
from core.risk_manager import risk_manager

# Update account balance
risk_manager.update_account_balance(10000)

# Calculate position size
position_size = risk_manager.calculate_position_size(40000, 39000)

# Check if a new trade can be opened
can_open, adjusted_size, reason = risk_manager.can_open_new_trade("BTC/USD", 40000, 39000)
if can_open:
    print(f"Trade allowed with position size: {adjusted_size}")
else:
    print(f"Trade not allowed: {reason}")

# Calculate stop loss and take profit
stop_loss = risk_manager.calculate_stop_loss(40000, "buy", atr=1000)
take_profit = risk_manager.calculate_take_profit(40000, stop_loss, "buy")
```

### Visualization (`visualization.py`)

The Visualization module generates charts and graphs for trading performance analysis. It provides functionality to:

- Plot equity curves
- Visualize win/loss distributions
- Show monthly performance
- Track drawdowns
- Generate comprehensive performance reports

```python
from core.visualization import visualizer

# Plot equity curve
equity_curve_file = visualizer.plot_equity_curve()

# Plot win/loss distribution
win_loss_file = visualizer.plot_win_loss_distribution()

# Generate a comprehensive performance report
report_files = visualizer.generate_performance_report()
```

### Trade Executor (`trade_executor.py`)

The Trade Executor module handles the execution of trades through the Bluefin API. It provides functionality to:

- Open and close positions based on processed trading signals
- Integrate with the risk manager to control position sizing
- Set stop loss and take profit orders
- Log executed trades for performance tracking

```python
from core.trade_executor import execute_trade

# Assume bluefin_client is initialized and signal is processed
trade_result = await execute_trade(bluefin_client, signal)

if trade_result:
    print(f"Trade executed: {trade_result}")
else:
    print("Trade execution failed")
```

## Example Usage

See the `examples/performance_analysis_example.py` file for a complete example of how to use these modules together.

To run the example:

```bash
python examples/performance_analysis_example.py
```

This will simulate a series of trades, track performance, and generate visualization reports.

## Dependencies

These modules require the following dependencies:

- pandas
- numpy
- matplotlib
- seaborn
- python-dateutil

You can install them using pip:

```bash
pip install -r requirements.txt
``` 
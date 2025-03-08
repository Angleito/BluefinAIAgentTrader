# PerplexityTrader

An automated trading system that uses TradingView alerts to execute trades on the Bluefin Exchange.

## Features

- Receives webhook alerts from TradingView
- Processes VuManChu Cipher B signals
- Executes trades on Bluefin Exchange
- Supports real money trading
- 24/7 operation with automatic monitoring and restart

## Position Doubling Feature

When the system executes a trade in live mode, it checks for any open positions in the same ticker. If there is an existing position in the opposite direction (e.g., a LONG position when trying to execute a SELL trade), the system will double the position size to both close the existing position and open a new one in the opposite direction.

This feature ensures that:

1. Existing positions are properly closed before opening new ones in the opposite direction
2. The position size is automatically adjusted to handle the position flip
3. The system can seamlessly transition between long and short positions

### How It Works

1. Before executing a trade, the system checks for existing positions in the same symbol
2. If an existing position is found in the opposite direction, the system doubles the position size
3. This doubled position size is used to:
   - Close the existing position (using the first half of the size)
   - Open a new position in the opposite direction (using the second half of the size)

### Example

If you have a LONG position of 1.0 SUI-PERP and the system receives a signal to SELL:

1. The system detects the existing LONG position of size 1.0
2. It doubles the position size to 2.0
3. The first 1.0 closes the existing LONG position
4. The second 1.0 opens a new SHORT position

This ensures smooth position flipping without having to manually close positions before opening new ones in the opposite direction.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git
   pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git
   ```
3. Set up environment variables in `.env` file:
   ```
   BLUEFIN_PRIVATE_KEY=your_private_key
   BLUEFIN_NETWORK=MAINNET
   MOCK_TRADING=False
   ```

## Running the System

### Using Background Scripts (Recommended)

1. Start the services:
   ```
   ./start_services.sh
   ```

2. Check the status:
   ```
   ./check_status.sh
   ```

3. Stop the services:
   ```
   ./stop_services.sh
   ```

### Using Systemd Services (Linux Only)

1. Install the services:
   ```
   sudo ./install_services.sh
   ```

2. Check the status:
   ```
   systemctl status perplexitytrader.service perplexitytrader-webhook.service
   ```

3. View logs:
   ```
   journalctl -u perplexitytrader.service -f
   journalctl -u perplexitytrader-webhook.service -f
   ```

## TradingView Setup

1. Create a TradingView alert with the following webhook URL:
   ```
   https://your-ngrok-domain/webhook
   ```

2. Format the alert message as JSON:
   ```json
   {
     "indicator": "vmanchu_cipher_b",
     "symbol": "{{ticker}}",
     "timeframe": "{{interval}}",
     "signal_type": "GREEN_CIRCLE",
     "action": "{{strategy.order.action}}",
     "price": {{close}},
     "timestamp": "{{timenow}}"
   }
   ```

## Monitoring

The system includes automatic monitoring and restart capabilities:

- `check_services.sh` - Checks if services are running and restarts them if needed
- `crontab_setup.sh` - Sets up a cron job to run the check script every 5 minutes

## Configuration

Edit `config/config.py` to customize trading parameters:

- Trading parameters (leverage, position size, etc.)
- Risk parameters (max risk per trade, max open positions, etc.)
- AI parameters (confidence thresholds, etc.)

## Logs

Logs are stored in the `logs` directory:

- `logs/webhook.log` - Webhook server logs
- `logs/agent.log` - Trading agent logs
- `logs/webhook_nohup.log` - Webhook server nohup logs
- `logs/agent_nohup.log` - Trading agent nohup logs
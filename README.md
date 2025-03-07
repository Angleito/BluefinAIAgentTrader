# PerplexityTrader

An automated trading system that uses TradingView alerts to execute trades on the Bluefin Exchange.

## Features

- Receives webhook alerts from TradingView
- Processes VuManChu Cipher B signals
- Executes trades on Bluefin Exchange
- Supports real money trading
- 24/7 operation with automatic monitoring and restart

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
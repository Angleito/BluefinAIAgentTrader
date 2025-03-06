# TradingView Webhook Server for Bluefin Trading Agent

This webhook server receives alerts from TradingView and forwards them to the Bluefin trading agent for processing and execution.

## Features

- Receives TradingView webhook alerts
- Validates and processes alerts, particularly for VuManChu Cipher B indicators
- Forwards processed alerts to the trading agent
- Saves alerts to files for backup and later processing
- Provides health check and testing endpoints
- Supports multiple signal types from VuManChu Cipher B

## Installation

1. Make sure you have Python 3.8+ installed
2. Clone this repository and navigate to the project directory
3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Set up your environment variables in `.env` or export them:

```
WEBHOOK_PORT=5001
AGENT_API_URL=http://localhost:5000/api/process_alert
FLASK_ENV=production  # Use 'development' for development mode with debug features
FLASK_DEBUG=false     # Set to 'true' to enable Flask debug mode
```

## Running the Webhook Server

To start the webhook server:

```bash
python webhook_server.py
```

Or use the provided shell script:

```bash
./start_webhook_server.sh
```

## Setting Up TradingView Alerts

1. Create a TradingView alert with VuManChu Cipher B indicators
2. Set up the alert to trigger on the conditions you want to trade on (e.g., GREEN_CIRCLE for buy signals)
3. Configure the webhook URL to point to your server:
   - If using ngrok: `https://your-ngrok-domain.ngrok.io/webhook`
   - If using a hosted server: `https://your-server.com/webhook`
4. Set the alert message format to JSON with the following structure:

```json
{
    "indicator": "vmanchu_cipher_b",
    "symbol": "{{ticker}}",
    "timeframe": "{{interval}}",
    "signal_type": "GREEN_CIRCLE",
    "action": "BUY"
}
```

Replace `"GREEN_CIRCLE"` and `"BUY"` with the appropriate signal type and action based on your alert conditions.

## Valid Signal Types

The webhook server supports the following VuManChu Cipher B signal types:

- `GREEN_CIRCLE`: Bullish - Wavetrend waves at oversold level and crossed up
- `RED_CIRCLE`: Bearish - Wavetrend waves at overbought level and crossed down
- `GOLD_CIRCLE`: Strong Bullish - RSI below 20, WaveTrend <= -80, crossed up after bullish divergence
- `PURPLE_TRIANGLE`: Bullish or Bearish - Divergence with WT crosses at overbought/oversold
- `LITTLE_CIRCLE`: Bullish or Bearish - All WaveTrend wave crossings
- `BULL_FLAG`: Bullish - MFI+RSI>0, WT<0 and crossed up, VWAP>0 on higher timeframe
- `BEAR_FLAG`: Bearish - MFI+RSI<0, WT>0 and crossed down, VWAP<0 on higher timeframe
- `BULL_DIAMOND`: Bullish - Pattern with HT green candle
- `BEAR_DIAMOND`: Bearish - Pattern with HT red candle

For ambiguous signals like `PURPLE_TRIANGLE` and `LITTLE_CIRCLE`, you must include the `"action"` field with either `"BUY"` or `"SELL"` to specify the direction.

## Testing the Webhook Server

### Using the Test Endpoints

The server provides a `/test` endpoint to verify that it's running:

```bash
curl http://localhost:5001/test
```

### Sending a Test Alert

Use the provided script to send a test alert:

```bash
python test/send_test_alert.py
```

You can customize the test alert with command line arguments:

```bash
python test/send_test_alert.py --symbol "BTC/USD" --signal "GOLD_CIRCLE" --timeframe "1h" --action "BUY"
```

### Running Integration Tests

To run integration tests between the webhook server and the signal processor:

```bash
FLASK_ENV=development python -m test.test_webhook_integration
```

To test against a running webhook server:

```bash
TEST_LIVE=true WEBHOOK_URL=http://localhost:5001/webhook python -m test.test_webhook_integration
```

## API Endpoints

- `GET /health`: Health check endpoint
- `GET /test`: Test endpoint with server information
- `POST /webhook`: Main webhook endpoint for TradingView alerts
- `POST /simulate`: (Development mode only) Simulate a webhook alert for testing

## Integration with Bluefin Trading Agent

The webhook server integrates with the Bluefin trading agent by:

1. Processing incoming TradingView alerts
2. Converting the alerts to a format the agent can understand
3. Saving the processed alerts to the `alerts/` directory
4. Notifying the agent via HTTP POST to the agent's API endpoint

You can configure the agent API URL in the `.env` file or environment variables:

```
AGENT_API_URL=http://localhost:5000/api/process_alert
```

## Using ngrok for TradingView Webhooks

To expose your local webhook server to the internet for TradingView alerts:

1. Install ngrok: https://ngrok.com/download
2. Start the webhook server: `python webhook_server.py`
3. In another terminal, start ngrok:

```bash
ngrok http 5001
```

4. Use the HTTPS URL provided by ngrok in your TradingView alert settings

## Docker Support

You can run the webhook server using Docker:

```bash
docker build -t bluefin-webhook-server .
docker run -p 5001:5001 -v $(pwd)/alerts:/app/alerts --env-file .env bluefin-webhook-server
```

Or with docker-compose:

```bash
docker-compose -f docker-compose.webhook.yml up -d
```

## Troubleshooting

- **Alert Not Received**: Check that TradingView is sending the alert correctly and the webhook URL is accessible
- **Alert Received but Not Processed**: Check the logs for validation errors, ensure the alert JSON format is correct
- **Agent Not Receiving Alerts**: Verify that the agent API URL is correct and the agent server is running 
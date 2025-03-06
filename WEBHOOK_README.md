# TradingView Webhook Server for VuManChu Cipher B

This webhook server is designed to receive and process alerts from the VuManChu Cipher B indicator in TradingView and trigger trading actions in the PerplexityTrader agent.

## Prerequisites

- Docker and Docker Compose installed
- ngrok account with auth token
- TradingView account with VuManChu Cipher B indicator

## Setup

1. Configure your environment variables in the `.env` file:

```
# Required ngrok configuration
NGROK_AUTHTOKEN=your_ngrok_auth_token

# TradingView Webhook Configuration
TV_WEBHOOK_SECRET=your_secret_passphrase
WEBHOOK_PORT=5001
```

2. Run the webhook server setup script:

```bash
./start_webhook_server.sh
```

This script will:
- Start the webhook server in Docker
- Start ngrok to create a secure HTTPS tunnel
- Display the webhook URL and instructions for TradingView

## TradingView Alert Setup

1. In TradingView, create a new alert for the VuManChu Cipher B indicator
2. Select "Webhook URL" as the alert action
3. Enter the webhook URL displayed by the setup script
4. Set the message format to JSON with this format:

```json
{
  "passphrase": "your_secret_passphrase",
  "indicator": "vmanchu_cipher_b",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "action": "{{strategy.order.action}}",
  "signal_type": "WAVE1"
}
```

You can customize `signal_type` based on the specific VuManChu Cipher B signal (WAVE1, WAVE2, RSI_BULL, etc.).

## Testing the Webhook

Use the included test script to verify the webhook is working:

```bash
python test_webhook.py --url 'https://your-ngrok-url.ngrok.io/webhook' --action BUY --symbol SUI/USD
```

## How it Works

1. TradingView sends an alert to your webhook when VuManChu Cipher B signals a trade
2. The webhook server validates the alert data
3. The alert is saved to disk and forwarded to the trading agent
4. The agent analyzes the chart and makes a trading decision based on the alert
5. If appropriate, the agent executes the trade

## Debugging

To view logs from the webhook server:

```bash
docker-compose -f docker-compose.webhook.yml logs -f webhook
```

To view ngrok logs:

```bash
docker-compose -f docker-compose.webhook.yml logs -f ngrok
```

## Security Considerations

- The webhook includes a passphrase for basic security
- ngrok provides a secure HTTPS connection
- All alerts are logged for audit purposes

## Customizing Alert Response

You can customize how the agent responds to different VuManChu Cipher B signals by modifying the `process_cipher_b_signal` function in `app.py`. 
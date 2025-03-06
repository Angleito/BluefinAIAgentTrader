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

# Webhook server port
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

## VuManChu Cipher B Signal Types

The VuManChu Cipher B indicator generates several important signals that can be turned into alerts. Each signal is classified as either **Bullish** (triggers long trades) or **Bearish** (triggers short trades):

### Bullish Signals (Long Trades)

1. **GREEN_CIRCLE**: Bullish signal - Wavetrend waves are at the oversold level and have crossed up.
2. **GOLD_CIRCLE**: Strong bullish signal - RSI is below 20, WaveTrend waves are below or equal to -80, and have crossed up after good bullish divergence. Note: The indicator creator recommends NOT buying immediately when this signal appears.
3. **BULL_FLAG**: Bullish pattern - MFI+RSI Area are above 0, Wavetrend waves are below 0 and cross up, VWAP Area are above 0 on higher timeframe.
4. **BULL_DIAMOND**: Bullish pattern with Heikin Ashi green candle.

### Bearish Signals (Short Trades)

1. **RED_CIRCLE**: Bearish signal - Wavetrend waves are at the overbought level and have crossed down.
2. **BEAR_FLAG**: Bearish pattern - MFI+RSI Area are below 0, Wavetrend waves are above 0 and cross down, VWAP Area are below 0 on higher timeframe.
3. **BEAR_DIAMOND**: Bearish pattern with Heikin Ashi red candle.

### Signals That Can Be Either Bullish or Bearish

These signals require specifying the "action" field as either "BUY" (for Bullish/long) or "SELL" (for Bearish/short):

1. **PURPLE_TRIANGLE**: Divergence signal - Appears when a bullish or bearish divergence is formed and WaveTrend waves cross at overbought and oversold points.
2. **LITTLE_CIRCLE**: Basic signal - Appears at all WaveTrend wave crossings.

## TradingView Alert Setup

1. In TradingView, create a new alert for the VuManChu Cipher B indicator
2. Select "Webhook URL" as the alert action
3. Enter the webhook URL displayed by the setup script
4. Set the message format to JSON with this format:

```json
{
  "indicator": "vmanchu_cipher_b",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "action": "BUY",
  "signal_type": "GREEN_CIRCLE"
}
```

Replace `GREEN_CIRCLE` with the appropriate signal type for your alert (see the "VuManChu Cipher B Signal Types" section above). Make sure to use HTTPS for the webhook URL to ensure TradingView can connect securely.

## Testing the Webhook

Use the included test script to verify the webhook is working:

```bash
python test_webhook.py --url 'https://your-ngrok-url.ngrok.io/webhook' --action BUY --symbol SUI/USD --signal-type GREEN_CIRCLE
```

You can test different signals by using the `--signal-type` parameter with any of the signal types listed above.

## How it Works

1. TradingView sends an alert to your webhook when VuManChu Cipher B produces a signal
2. The webhook server validates the alert data and the signal type
3. The server automatically adds a "trade_direction" tag (either "Bullish" or "Bearish") based on the signal type
4. The alert is saved to disk and forwarded to the trading agent
5. The agent analyzes the chart and makes a trading decision based on the alert type
6. If appropriate, the agent executes the trade (long for Bullish signals, short for Bearish signals)

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

- SSL certificate validation ensures secure connections
- ngrok provides a secure HTTPS connection
- All alerts are logged for audit purposes

## Customizing Alert Response

You can customize how the agent responds to different VuManChu Cipher B signals by modifying the `process_cipher_b_signal` function in `app.py`. Each signal type may require different trading parameters or conditions. 
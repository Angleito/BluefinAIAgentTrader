# Using TCP Tunnels with TradingView Webhooks

This guide explains how to use Ngrok TCP tunnels with TradingView webhooks for the PerplexityTrader application.

## Why TCP Tunnels?

TCP tunnels offer several advantages over HTTP tunnels:

1. **Lower Latency**: TCP tunnels have less overhead, potentially reducing latency for time-sensitive trading signals.
2. **More Reliable**: TCP tunnels can be more reliable in certain network environments.
3. **Simpler Protocol**: TCP is a simpler protocol without HTTP-specific complexities.

## Setup Instructions

### 1. Start the TCP Tunnel

The application is now configured to use TCP tunnels by default when Ngrok is enabled. When you start the application with `USE_NGROK=true`, a TCP tunnel will be created automatically.

### 2. Get the TCP Tunnel Address

When the application starts, it will display the TCP tunnel address in the logs. It will look something like:

```
Ngrok TCP tunnel established: tcp://0.tcp.ngrok.io:12345
```

### 3. Configure TradingView Webhooks

When setting up webhooks in TradingView, you need to make some specific configurations for TCP tunnels:

1. **Webhook URL**: Use the full TCP address provided (e.g., `tcp://0.tcp.ngrok.io:12345`) without any additional path.
2. **Message Format**: Set to `JSON` in TradingView alert settings.
3. **Alert Message**: Include all required fields in your alert message JSON:

```json
{
  "indicator": "vmanchu_cipher_b",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "action": "{{strategy.order.action}}",
  "signal_type": "GREEN_CIRCLE",
  "timestamp": "{{time}}"
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Make sure the webhook server is running and listening on the configured port.
2. **Timeout**: Check if your Ngrok authtoken is valid and properly configured.
3. **Invalid JSON**: Ensure your TradingView alert message is properly formatted as valid JSON.

### Checking Tunnel Status

You can check the status of your Ngrok tunnels by visiting the Ngrok dashboard at http://localhost:4040 when the tunnel is running.

## Additional Notes

- TCP tunnels with custom domains require a paid Ngrok plan.
- For production use, consider using a dedicated server with a static IP or a proper reverse proxy setup. 
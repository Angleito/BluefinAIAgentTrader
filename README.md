# Perplexity Trader - AI-Powered Trading Agent for Bluefin Exchange

This automated trading agent analyzes TradingView charts for trading opportunities, confirms signals with AI models (Claude and Perplexity), and executes trades on the Bluefin Exchange.

## Features

- **Chart Analysis**: Analyzes TradingView charts for SUI/USD with specialized indicators (VuManChu Cipher A/B)
- **AI Confirmation**: Uses multiple AI models to confirm trading signals and reduce false positives
- **Automated Trading**: Executes trades on Bluefin Exchange with proper risk management
- **Performance Tracking**: Tracks trade performance and generates visualization reports

## Requirements

1. **Python 3.8+**
2. **Required Python Libraries**:
   ```
   pip install python-dotenv playwright asyncio backoff
   python -m playwright install
   ```

3. **Bluefin Client Library** (choose one based on your needs):
   ```
   # For SUI integration
   pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git
   
   # OR for general v2 integration
   pip install git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git
   ```

4. **Environment Variables** (create a `.env` file in the project root):
   ```
   # For SUI client
   BLUEFIN_PRIVATE_KEY=your_private_key_here
   BLUEFIN_NETWORK=MAINNET  # or TESTNET
   
   # For v2 client
   BLUEFIN_API_KEY=your_api_key_here
   BLUEFIN_API_SECRET=your_api_secret_here
   BLUEFIN_API_URL=optional_custom_url_here
   
   # AI API keys
   CLAUDE_API_KEY=your_claude_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   ```

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/perplexity-trader.git
   cd perplexity-trader
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys as shown above.

4. Test the Bluefin API connection:
   ```
   python test_bluefin_connection.py
   ```

## Configuration

Edit `config.py` to customize trading parameters:

- **Account and Risk Settings**: Initial balance, risk per trade, max positions, daily drawdown
- **TradingView Chart Settings**: Symbol, timeframe, indicators, candle type
- **Trading Confidence**: Minimum threshold to execute trades
- **Analysis Interval**: Time between analyses

## Usage

Run the trading agent:

```
python agent.py
```

The agent will:
1. Connect to the Bluefin Exchange
2. Analyze TradingView charts for SUI/USD with specified indicators
3. Generate trading signals and confirm with AI models
4. Execute trades based on the analysis and confidence level
5. Track performance and generate reports

## Project Structure

- `agent.py`: Main trading agent implementation
- `config.py`: Configuration parameters
- `test_bluefin_connection.py`: Test script for API connectivity
- `core/`: Core modules
  - `performance_tracker.py`: Track trade performance
  - `risk_manager.py`: Manage trading risk and position sizing
  - `visualization.py`: Generate performance reports and charts

## Troubleshooting

If you encounter any issues:

1. **API Connection Issues**:
   - Verify your API keys in `.env` file
   - Run `test_bluefin_connection.py` to check connectivity
   - Ensure you're using the correct network (testnet/mainnet)

2. **TradingView Chart Analysis Issues**:
   - Make sure Playwright is properly installed
   - Check if TradingView selectors have changed

3. **Trade Execution Issues**:
   - Check account balance and available margin
   - Verify trading parameters in `config.py`

## API Security Best Practices

To ensure your trading account remains secure:

1. **API Key Management**:
   - Never commit your `.env` file to version control
   - Rotate your API keys regularly (every 30-90 days)
   - Use different keys for development and production

2. **Permissions and Access**:
   - Use keys with the minimum necessary permissions
   - Consider read-only keys for monitoring and separate keys for trading
   - If supported by Bluefin, restrict API key usage to specific IP addresses

3. **Environment Separation**:
   - Start with testnet for all testing and development
   - Use separate keys for testnet and mainnet environments
   - Implement additional safeguards when using mainnet (e.g., lower position sizes)

4. **Secure Storage**:
   - Store your `.env` file with restricted permissions (e.g., `chmod 600 .env`)
   - Consider using a secrets manager for production deployments
   - Never share your private keys or API secrets with others

5. **Monitoring and Alerts**:
   - Monitor for unauthorized API access or unusual trading activity
   - Set up alerts for large trades or account balance changes
   - Regularly review trading logs for suspicious activity

For a comprehensive security checklist, see [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md).

## References

- [Bluefin API Documentation](https://bluefin-exchange.readme.io/reference/introduction)
- [Playwright Documentation](https://playwright.dev/python/docs/intro)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
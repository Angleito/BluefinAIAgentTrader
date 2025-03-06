#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   TradingView Webhook Server Setup    ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found. Please create it with required environment variables.${NC}"
    exit 1
fi

# Source environment variables
source .env

# Check required environment variables
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo -e "${YELLOW}Warning: NGROK_AUTHTOKEN is not set. Ngrok may not work properly.${NC}"
    echo -e "${YELLOW}Get your auth token at https://dashboard.ngrok.com/get-started/your-authtoken${NC}"
fi

# Create necessary directories
mkdir -p logs alerts

# Start Docker services
echo -e "${GREEN}Starting webhook server and ngrok...${NC}"
docker-compose -f docker-compose.webhook.yml down || true
docker-compose -f docker-compose.webhook.yml up -d

# Wait for ngrok to start
echo -e "${YELLOW}Waiting for ngrok to start...${NC}"
sleep 5

# Set the static ngrok URL
NGROK_URL="https://awake-drake-bursting.ngrok-free.app"
WEBHOOK_URL="${NGROK_URL}/webhook"
    
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}   Webhook URL: ${WEBHOOK_URL}${NC}"
echo -e "${GREEN}============================================================${NC}"
echo -e "${YELLOW}To test the webhook, run:${NC}"
echo -e "${BLUE}python test_webhook.py --url '${WEBHOOK_URL}' --signal-type GREEN_CIRCLE${NC}"
echo -e "${YELLOW}To view logs, run:${NC}"
echo -e "${BLUE}docker-compose -f docker-compose.webhook.yml logs -f${NC}"
echo -e "${GREEN}============================================================${NC}"
    
# Instructions for TradingView
echo -e "${YELLOW}TradingView Alert Instructions:${NC}"
echo -e "${GREEN}1. Create a new alert in TradingView${NC}"
echo -e "${GREEN}2. In the alert settings, select 'Webhook URL' and enter:${NC}"
echo -e "${BLUE}   ${WEBHOOK_URL}${NC}"
echo -e "${GREEN}3. Set the webhook message format to JSON with one of these formats:${NC}"
    
echo -e "${CYAN}=== BULLISH SIGNALS (LONG TRADES) ===${NC}"
    
# Examples for Bullish signals
echo -e "${YELLOW}For GREEN_CIRCLE (Bullish - WT oversold crossed up):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"BUY\",\"signal_type\":\"GREEN_CIRCLE\"}${NC}"
    
echo -e "${YELLOW}For GOLD_CIRCLE (Strong Bullish - RSI<20, WT<=-80, crossed up):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"BUY\",\"signal_type\":\"GOLD_CIRCLE\"}${NC}"
    
echo -e "${YELLOW}For BULL_FLAG (Bullish Pattern):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"BUY\",\"signal_type\":\"BULL_FLAG\"}${NC}"

echo -e "${YELLOW}For BULL_DIAMOND (Bullish Pattern with HT green candle):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"BUY\",\"signal_type\":\"BULL_DIAMOND\"}${NC}"
    
echo -e "${CYAN}=== BEARISH SIGNALS (SHORT TRADES) ===${NC}"
    
# Examples for Bearish signals
echo -e "${YELLOW}For RED_CIRCLE (Bearish - WT overbought crossed down):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"SELL\",\"signal_type\":\"RED_CIRCLE\"}${NC}"
    
echo -e "${YELLOW}For BEAR_FLAG (Bearish Pattern):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"SELL\",\"signal_type\":\"BEAR_FLAG\"}${NC}"

echo -e "${YELLOW}For BEAR_DIAMOND (Bearish Pattern with HT red candle):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"SELL\",\"signal_type\":\"BEAR_DIAMOND\"}${NC}"
    
echo -e "${CYAN}=== SIGNALS THAT CAN BE EITHER BULLISH OR BEARISH ===${NC}"
    
# Examples for ambiguous signals
echo -e "${YELLOW}For PURPLE_TRIANGLE (Divergence - can be Bullish or Bearish):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"BUY\",\"signal_type\":\"PURPLE_TRIANGLE\"}${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"SELL\",\"signal_type\":\"PURPLE_TRIANGLE\"}${NC}"
    
echo -e "${YELLOW}For LITTLE_CIRCLE (All WT crossings - can be Bullish or Bearish):${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"BUY\",\"signal_type\":\"LITTLE_CIRCLE\"}${NC}"
echo -e "${BLUE}   {\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"SELL\",\"signal_type\":\"LITTLE_CIRCLE\"}${NC}"
    
echo -e "${GREEN}4. Make sure to use HTTPS for your webhook URL to ensure TradingView can connect securely${NC}"
echo -e "${GREEN}5. Set your alert conditions based on the VuManChu Cipher B indicator signals${NC}"
echo -e "${GREEN}6. Save the alert${NC}"
    
echo -e "${GREEN}The webhook server is now ready to receive TradingView alerts.${NC}" 
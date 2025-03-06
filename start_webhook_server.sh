#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

if [ -z "$TV_WEBHOOK_SECRET" ]; then
    echo -e "${YELLOW}Warning: TV_WEBHOOK_SECRET is not set. Using default passphrase for TradingView alerts.${NC}"
    TV_WEBHOOK_SECRET="cipher_b_secret_key"
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

# Get the ngrok URL
echo -e "${GREEN}Fetching ngrok URL...${NC}"
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o "https://[a-zA-Z0-9.-]*.ngrok.io" || echo "")

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}Failed to get ngrok URL. Please check if ngrok is running properly.${NC}"
    echo -e "${YELLOW}You can check the ngrok admin interface at http://localhost:4040${NC}"
    echo -e "${YELLOW}Or check the logs with: docker-compose -f docker-compose.webhook.yml logs -f ngrok${NC}"
else
    WEBHOOK_URL="${NGROK_URL}/webhook"
    
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}   Webhook URL: ${WEBHOOK_URL}${NC}"
    echo -e "${GREEN}   Passphrase: ${TV_WEBHOOK_SECRET}${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${YELLOW}To test the webhook, run:${NC}"
    echo -e "${BLUE}python test_webhook.py --url '${WEBHOOK_URL}'${NC}"
    echo -e "${YELLOW}To view logs, run:${NC}"
    echo -e "${BLUE}docker-compose -f docker-compose.webhook.yml logs -f${NC}"
    echo -e "${GREEN}============================================================${NC}"
    
    # Instructions for TradingView
    echo -e "${YELLOW}TradingView Alert Instructions:${NC}"
    echo -e "${GREEN}1. Create a new alert in TradingView${NC}"
    echo -e "${GREEN}2. In the alert settings, select 'Webhook URL' and enter:${NC}"
    echo -e "${BLUE}   ${WEBHOOK_URL}${NC}"
    echo -e "${GREEN}3. Set the webhook message format to JSON:${NC}"
    echo -e "${BLUE}   {\"passphrase\":\"${TV_WEBHOOK_SECRET}\",\"indicator\":\"vmanchu_cipher_b\",\"symbol\":\"{{ticker}}\",\"timeframe\":\"{{interval}}\",\"action\":\"{{strategy.order.action}}\",\"signal_type\":\"WAVE1\"}${NC}"
    echo -e "${GREEN}4. Save the alert${NC}"
    
    echo -e "${GREEN}The webhook server is now ready to receive TradingView alerts.${NC}"
fi 
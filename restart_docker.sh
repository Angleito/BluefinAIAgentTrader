#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping existing container...${NC}"
docker stop perplexity-trader
docker rm perplexity-trader

echo -e "${YELLOW}Building new Docker image...${NC}"
docker build -t perplexitytrader:latest .

echo -e "${YELLOW}Starting container with updated configuration...${NC}"
docker run -d \
  --name perplexity-trader \
  -p 5001:5001 \
  -e BLUEFIN_PRIVATE_KEY="$BLUEFIN_PRIVATE_KEY" \
  -e BLUEFIN_NETWORK="$BLUEFIN_NETWORK" \
  -e MOCK_TRADING="$MOCK_TRADING" \
  -e NGROK_AUTHTOKEN="$NGROK_AUTHTOKEN" \
  -e USE_NGROK="$USE_NGROK" \
  -e NGROK_DOMAIN="$NGROK_DOMAIN" \
  -e FLASK_ENV="production" \
  -e FLASK_DEBUG="false" \
  -e WEBHOOK_PORT="5001" \
  perplexitytrader:latest

echo -e "${YELLOW}Waiting for container to start...${NC}"
sleep 5

echo -e "${YELLOW}Container logs:${NC}"
docker logs perplexity-trader

echo -e "${GREEN}Container restarted successfully!${NC}"
echo -e "Access the webhook API at: http://localhost:5001"
echo -e "Check container status with: docker ps -a | grep perplexity-trader"
echo -e "View logs with: docker logs perplexity-trader"
echo -e "Stop the container with: docker stop perplexity-trader"

# Check if ngrok is enabled and display TCP tunnel information
if [ "$USE_NGROK" = "true" ]; then
    echo -e "${YELLOW}Waiting for ngrok TCP tunnel to establish...${NC}"
    sleep 5
    echo -e "${YELLOW}Checking for ngrok TCP tunnel URL...${NC}"
    
    # Get the container ID
    CONTAINER_ID=$(docker ps -q -f name=perplexity-trader)
    
    if [ -n "$CONTAINER_ID" ]; then
        # Execute curl inside the container to get the ngrok URL
        NGROK_INFO=$(docker exec $CONTAINER_ID curl -s http://localhost:4040/api/tunnels 2>/dev/null)
        
        if [ -n "$NGROK_INFO" ]; then
            NGROK_URL=$(echo "$NGROK_INFO" | grep -o '"public_url":"[^"]*' | head -1 | sed 's/"public_url":"//')
            
            if [ -n "$NGROK_URL" ]; then
                echo -e "${GREEN}Ngrok TCP tunnel established: ${NGROK_URL}${NC}"
                echo -e "Use this address for your TradingView webhooks"
                echo -e "See tcp_tunnel_instructions.md for detailed setup instructions"
            else
                echo -e "${RED}Could not find ngrok tunnel URL${NC}"
            fi
        else
            echo -e "${RED}Could not get ngrok tunnel information${NC}"
        fi
    else
        echo -e "${RED}Container not found${NC}"
    fi
fi 
#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building Perplexity Trader Docker image locally...${NC}"

# Build the Docker image locally
docker build -t perplexitytrader:latest .

# Check if build was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed. Please check the errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}Docker image built successfully!${NC}"

# Check if container already exists and remove it
if [ "$(docker ps -a -q -f name=perplexity-trader)" ]; then
    echo -e "${YELLOW}Removing existing container...${NC}"
    docker rm -f perplexity-trader
fi

# Get environment variables
read -p "Enter your Bluefin private key: " BLUEFIN_PRIVATE_KEY
read -p "Enter Bluefin network (SUI_PROD, SUI_STAGING): " BLUEFIN_NETWORK
BLUEFIN_NETWORK=${BLUEFIN_NETWORK:-SUI_PROD}

read -p "Enable mock trading? (true/false): " MOCK_TRADING
MOCK_TRADING=${MOCK_TRADING:-false}

echo -e "${YELLOW}Running Perplexity Trader container...${NC}"

# Run the container using the locally built image
docker run -d \
  --name perplexity-trader \
  -p 5001:5001 \
  -e BLUEFIN_PRIVATE_KEY="$BLUEFIN_PRIVATE_KEY" \
  -e BLUEFIN_NETWORK="$BLUEFIN_NETWORK" \
  -e MOCK_TRADING="$MOCK_TRADING" \
  perplexitytrader:latest

# Check if container started successfully
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start container. Please check the errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}Container started successfully!${NC}"
echo -e "${YELLOW}Checking container logs...${NC}"

# Wait a moment for the container to start
sleep 3

# Show the container logs
docker logs perplexity-trader

echo -e "${GREEN}Perplexity Trader is now running!${NC}"
echo -e "Access the webhook API at: http://localhost:5001"
echo -e "Check container status with: docker ps -a | grep perplexity-trader"
echo -e "View logs with: docker logs perplexity-trader"
echo -e "Stop the container with: docker stop perplexity-trader" 
#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Display usage information
function show_usage {
    echo "Usage: $0 -k <private_key> [-n <network>] [-m <mock_trading>]"
    echo ""
    echo "Options:"
    echo "  -k, --key         Bluefin private key (required)"
    echo "  -n, --network     Bluefin network: SUI_PROD or SUI_STAGING (default: SUI_PROD)"
    echo "  -m, --mock        Enable mock trading: true or false (default: false)"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -k 0x123456789abcdef -n SUI_STAGING -m true"
    exit 1
}

# Parse command line arguments
BLUEFIN_PRIVATE_KEY=""
BLUEFIN_NETWORK="SUI_PROD"
MOCK_TRADING="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -k|--key)
            BLUEFIN_PRIVATE_KEY="$2"
            shift 2
            ;;
        -n|--network)
            BLUEFIN_NETWORK="$2"
            shift 2
            ;;
        -m|--mock)
            MOCK_TRADING="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check if private key is provided
if [ -z "$BLUEFIN_PRIVATE_KEY" ]; then
    echo -e "${RED}Error: Bluefin private key is required${NC}"
    show_usage
fi

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

echo -e "${YELLOW}Running Perplexity Trader container...${NC}"
echo -e "${YELLOW}Network: ${BLUEFIN_NETWORK}${NC}"
echo -e "${YELLOW}Mock Trading: ${MOCK_TRADING}${NC}"

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
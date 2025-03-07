#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking Docker status...${NC}"
docker --version

echo -e "${YELLOW}Checking if perplexity-trader container exists...${NC}"
docker ps -a | grep perplexity-trader

echo -e "${YELLOW}Removing existing container if it exists...${NC}"
docker rm -f perplexity-trader 2>/dev/null || true

echo -e "${YELLOW}Building Docker image with verbose output...${NC}"
docker build --no-cache -t perplexitytrader:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed. Please check the errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}Docker image built successfully!${NC}"

echo -e "${YELLOW}Running container in interactive mode...${NC}"
docker run -it --name perplexity-trader -p 5001:5001 perplexitytrader:latest 
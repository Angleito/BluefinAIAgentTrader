#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping PerplexityTrader Docker environment...${NC}"

# Change to the Docker directory
cd infrastructure/docker

# Stop all containers
echo -e "${YELLOW}Stopping all containers...${NC}"
docker-compose -f docker-compose.simple.yml down

echo -e "${GREEN}PerplexityTrader Docker environment has been stopped.${NC}" 
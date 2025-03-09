#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Cleaning up PerplexityTrader Docker environment...${NC}"

# Stop all containers
echo -e "${YELLOW}Stopping all containers...${NC}"
cd infrastructure/docker
docker-compose -f docker-compose.simple.yml down

# Remove all containers
echo -e "${YELLOW}Removing all containers...${NC}"
docker rm docker_nginx_1 docker_agent_1 docker_webhook_1 docker_websocket_1 2>/dev/null || true

# Remove the Docker network
echo -e "${YELLOW}Removing Docker network...${NC}"
docker network rm docker_perplexity-network 2>/dev/null || true

# Remove Docker volumes
echo -e "${YELLOW}Removing Docker volumes...${NC}"
docker volume prune -f

echo -e "${GREEN}PerplexityTrader Docker environment has been cleaned up.${NC}" 
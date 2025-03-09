#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting PerplexityTrader Docker environment...${NC}"

# Create necessary directories if they don't exist
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs alerts analysis screenshots

# Fix permissions on core directories
echo -e "${YELLOW}Fixing directory permissions...${NC}"
if [ -d "core" ]; then
    echo -e "${YELLOW}Fixing core directory permissions...${NC}"
    sudo chown -R $(whoami):$(whoami) core
    sudo chmod -R 755 core
fi

sudo chown -R $(whoami):$(whoami) logs alerts analysis screenshots
sudo chmod -R 755 logs alerts analysis screenshots

# Create the core directory if it doesn't exist
if [ ! -d "core" ]; then
    echo -e "${YELLOW}Creating core directory...${NC}"
    mkdir -p core
    sudo chown -R $(whoami):$(whoami) core
    sudo chmod -R 755 core
fi

# Ensure the .env file is in place
echo -e "${YELLOW}Ensuring .env file is in the right place...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating sample .env file...${NC}"
    cat > .env << 'EOF'
# Environment variables for PerplexityTrader
NGINX_PORT=8080
AGENT_PORT=5003
WEBHOOK_PORT=5004
WEBSOCKET_PORT=5008
MOCK_TRADING=true
EOF
fi

cp -f .env infrastructure/docker/.env

# Remove any existing Docker containers with the same names
echo -e "${YELLOW}Stopping any running containers...${NC}"
docker stop docker_nginx_1 docker_agent_1 docker_webhook_1 docker_websocket_1 2>/dev/null || true
docker rm docker_nginx_1 docker_agent_1 docker_webhook_1 docker_websocket_1 2>/dev/null || true

# Try to remove the Docker network if it exists
echo -e "${YELLOW}Cleaning up Docker network...${NC}"
docker network rm docker_perplexity-network 2>/dev/null || true

# Start the nginx container
echo -e "${YELLOW}Starting the Docker containers...${NC}"
cd infrastructure/docker
docker-compose -f docker-compose.simple.yml up -d

# Wait for containers to stabilize
echo -e "${YELLOW}Waiting for containers to start...${NC}"
sleep 5

# Check container status
echo -e "${YELLOW}Checking container status...${NC}"
docker-compose -f docker-compose.simple.yml ps

echo -e "${GREEN}PerplexityTrader Docker environment is now running!${NC}"
echo -e "Navigate to http://localhost:8080 to access the web interface." 
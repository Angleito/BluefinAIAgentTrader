#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up PerplexityTrader Docker environment...${NC}"

# Create necessary directories if they don't exist
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs alerts analysis screenshots

# Fix permissions on core directories
echo -e "${YELLOW}Fixing directory permissions...${NC}"
sudo chown -R $(whoami):$(whoami) core logs alerts analysis

# Ensure the .env file is in place
echo -e "${YELLOW}Ensuring .env file is in the right place...${NC}"
cp -f .env infrastructure/docker/.env
cp -f requirements.txt infrastructure/docker/
cp -f webhook_server.py infrastructure/docker/
cp -f websocket_server.py infrastructure/docker/
cp -f app.py infrastructure/docker/

# Copy necessary scripts
echo -e "${YELLOW}Copying necessary scripts...${NC}"
cp -f check_services_docker.sh infrastructure/docker/

# Change to the Docker directory
cd infrastructure/docker

# Stop any running containers
echo -e "${YELLOW}Stopping any running containers...${NC}"
docker-compose down

# Make sure the images are up to date
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose build

# Start containers in detached mode
echo -e "${YELLOW}Starting containers in detached mode...${NC}"
docker-compose up -d

# Wait for containers to stabilize
echo -e "${YELLOW}Waiting for containers to start...${NC}"
sleep 10

# Check container status
echo -e "${YELLOW}Checking container status...${NC}"
docker-compose ps

# Display running logs
echo -e "${YELLOW}Container logs:${NC}"
docker-compose logs --tail=20

echo -e "${GREEN}PerplexityTrader Docker environment is now running!${NC}"
echo -e "Use 'docker-compose logs -f' in the infrastructure/docker directory to follow logs."
echo -e "Navigate to http://localhost:8080 to access the web interface." 
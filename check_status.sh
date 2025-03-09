#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking PerplexityTrader Docker environment...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
  exit 1
fi

# Check if the nginx container is running
if [ -z "$(docker ps -q -f name=docker_nginx_1)" ]; then
  echo -e "${RED}Nginx container is not running.${NC}"
else
  # Check the health status
  HEALTH=$(docker inspect --format='{{.State.Health.Status}}' docker_nginx_1 2>/dev/null)
  
  if [ "$HEALTH" = "healthy" ]; then
    echo -e "${GREEN}Nginx container is running and healthy.${NC}"
  elif [ "$HEALTH" = "starting" ]; then
    echo -e "${YELLOW}Nginx container is starting...${NC}"
  else
    echo -e "${RED}Nginx container is unhealthy.${NC}"
  fi
fi

# Check the logs directory
echo -e "\n${YELLOW}Checking logs directory...${NC}"
if [ -d "logs" ]; then
  echo -e "${GREEN}Logs directory exists.${NC}"
  
  # Check if there are any log files
  LOG_COUNT=$(find logs -type f | wc -l)
  
  if [ $LOG_COUNT -gt 0 ]; then
    echo -e "${GREEN}Found $LOG_COUNT log files.${NC}"
  else
    echo -e "${YELLOW}No log files found.${NC}"
  fi
else
  echo -e "${RED}Logs directory does not exist.${NC}"
fi

# Check the web interface
echo -e "\n${YELLOW}Checking web interface...${NC}"
if curl -s http://localhost:8080/health > /dev/null; then
  echo -e "${GREEN}Web interface is accessible.${NC}"
else
  echo -e "${RED}Web interface is not accessible.${NC}"
fi

echo -e "\n${YELLOW}Docker container status:${NC}"
docker ps

echo -e "\n${YELLOW}To view the logs, run:${NC}"
echo -e "docker logs docker_nginx_1" 
#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running Bluefin WebSocket Example in Docker${NC}"
echo -e "${YELLOW}This script will build and run a Docker container to test the Bluefin WebSocket API${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Please create a .env file with the following variables:${NC}"
    echo "BLUEFIN_NETWORK=SUI_PROD"
    echo "BLUEFIN_WEBSOCKET_URL=wss://dstream.api.sui-prod.bluefin.io/ws"
    echo "BLUEFIN_PRIVATE_KEY=your_private_key"
    echo "BLUEFIN_API_KEY=your_api_key"
    echo "BLUEFIN_API_SECRET=your_api_secret"
    exit 1
fi

# Create a temporary Dockerfile
cat > Dockerfile.bluefin-websocket << EOF
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && \
    pip install python-dotenv websockets && \
    pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git

COPY bluefin_websocket_example.py /app/
COPY .env /app/

CMD ["python", "bluefin_websocket_example.py"]
EOF

echo -e "${GREEN}Building Docker image...${NC}"
docker build -t bluefin-websocket-example -f Dockerfile.bluefin-websocket .

echo -e "${GREEN}Running Docker container...${NC}"
docker run --rm \
    --name bluefin-websocket-example \
    --env-file .env \
    bluefin-websocket-example

# Clean up
echo -e "${GREEN}Cleaning up...${NC}"
rm Dockerfile.bluefin-websocket

echo -e "${GREEN}Done!${NC}" 
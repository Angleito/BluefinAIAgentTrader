#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running Bluefin API Example in Docker${NC}"
echo -e "${YELLOW}This script will build and run a Docker container to test the Bluefin API${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Please create a .env file with the following variables:${NC}"
    echo "BLUEFIN_NETWORK=SUI_PROD"
    echo "BLUEFIN_PRIVATE_KEY=your_private_key"
    echo "BLUEFIN_API_KEY=your_api_key"
    echo "BLUEFIN_API_SECRET=your_api_secret"
    exit 1
fi

# Create a temporary Dockerfile
cat > Dockerfile.bluefin-example << EOF
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && \
    pip install python-dotenv && \
    pip install git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git

COPY bluefin_api_example.py /app/
COPY .env /app/

CMD ["python", "bluefin_api_example.py"]
EOF

echo -e "${GREEN}Building Docker image...${NC}"
docker build -t bluefin-api-example -f Dockerfile.bluefin-example .

echo -e "${GREEN}Running Docker container...${NC}"
docker run --rm \
    --name bluefin-api-example \
    --env-file .env \
    bluefin-api-example

# Clean up
echo -e "${GREEN}Cleaning up...${NC}"
rm Dockerfile.bluefin-example

echo -e "${GREEN}Done!${NC}" 
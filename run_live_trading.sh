#!/bin/bash
# Script to run the trading agent in live mode with Docker

# Color variables
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error "No .env file found. Please create one based on .env.example"
    exit 1
fi

# Verify API keys are set
source .env
if [ -z "$PERPLEXITY_API_KEY" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
    print_error "Missing required API keys in .env file"
    exit 1
fi

if [ -z "$BLUEFIN_PRIVATE_KEY" ] && [ -z "$BLUEFIN_API_KEY" ]; then
    print_error "No Bluefin credentials found. Set either BLUEFIN_PRIVATE_KEY or BLUEFIN_API_KEY/BLUEFIN_API_SECRET"
    exit 1
fi

# Create necessary directories
mkdir -p logs alerts screenshots analysis

# Display warning
print_warning "⚠️  You are about to start LIVE trading ⚠️"
print_warning "This will execute REAL trades with REAL money"
read -p "Are you sure you want to continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Live trading canceled"
    exit 0
fi

# Pull latest docker images
print_info "Pulling latest Docker images..."
docker-compose -f docker-compose.live.yml pull

# Start the containers
print_info "Starting live trading containers..."
docker-compose -f docker-compose.live.yml up -d

# Show container status
print_info "Container status:"
docker-compose -f docker-compose.live.yml ps

# Display logs
print_info "Showing agent logs (Ctrl+C to exit logs but keep containers running)"
docker-compose -f docker-compose.live.yml logs -f agent 
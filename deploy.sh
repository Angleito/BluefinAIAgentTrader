#!/bin/bash
# PerplexityTrader Production Deployment Script

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
is_port_in_use() {
    lsof -i:"$1" >/dev/null 2>&1
}

# Function to check service health
check_health() {
    local service=$1
    local url=$2
    local max_attempts=$3
    local attempt=1
    
    print_info "Checking health of $service at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null; then
            print_info "$service is healthy!"
            return 0
        else
            print_warning "Health check attempt $attempt/$max_attempts for $service failed. Retrying in 5 seconds..."
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
    
    print_error "$service health check failed after $max_attempts attempts."
    return 1
}

# Check for required commands
for cmd in docker docker-compose npm node curl lsof; do
    if ! command_exists $cmd; then
        print_error "Required command '$cmd' not found. Please install it and try again."
        exit 1
    fi
done

# Check if .env file exists
if [ ! -f .env ]; then
    print_error "No .env file found. Please create one based on .env.example"
    exit 1
fi

# Load environment variables
source .env

# Check if running in production mode
if [ "$FLASK_ENV" != "production" ]; then
    print_warning "FLASK_ENV is not set to 'production' in .env file."
    read -p "Do you want to continue with deployment? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment canceled."
        exit 0
    fi
fi

# Check if JWT_SECRET is set to a non-default value
if [ "$JWT_SECRET" = "your_jwt_secret_here" ] || [ -z "$JWT_SECRET" ]; then
    print_error "JWT_SECRET is not set to a secure value in .env file."
    exit 1
fi

# Check if MOCK_TRADING is set to False for production
if [ "$MOCK_TRADING" = "False" ]; then
    print_warning "⚠️  MOCK_TRADING is set to False. This will execute REAL trades with REAL money."
    read -p "Are you sure you want to continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment canceled."
        exit 0
    fi
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs config data alerts

# Build frontend for production
print_info "Building frontend for production..."
cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    print_info "Installing frontend dependencies..."
    npm install
fi

# Build the frontend
print_info "Building frontend application..."
npm run build

if [ $? -ne 0 ]; then
    print_error "Frontend build failed."
    exit 1
fi

# Verify build directory exists and contains index.html
if [ ! -d "build" ] || [ ! -f "build/index.html" ]; then
    print_error "Frontend build directory is missing or incomplete."
    exit 1
fi

print_info "Frontend build successful."
cd ..

# Check if ports are already in use
for port in 80 443 5000 5001 8000; do
    if is_port_in_use $port; then
        print_error "Port $port is already in use. Please free it up before deploying."
        exit 1
    fi
done

# Pull latest Docker images
print_info "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build Docker images
print_info "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Start the containers
print_info "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Check container status
print_info "Container status:"
docker-compose -f docker-compose.prod.yml ps

# Perform health checks
sleep 10
check_health "Backend API" "http://localhost:5000/health" 6
backend_health=$?

check_health "Nginx" "http://localhost" 6
nginx_health=$?

# Final status
if [ $backend_health -eq 0 ] && [ $nginx_health -eq 0 ]; then
    print_info "✅ Deployment successful! PerplexityTrader is now running in production mode."
    print_info "Frontend URL: http://localhost"
    print_info "API URL: http://localhost/api"
    print_info "WebSocket URL: ws://localhost/socket.io"
    
    if [ "$USE_NGROK" = "true" ]; then
        print_info "Ngrok dashboard: http://localhost:4040"
    fi
    
    print_info "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
    print_info "To stop: docker-compose -f docker-compose.prod.yml down"
else
    print_error "❌ Deployment completed with errors. Please check the logs."
    print_info "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
fi

exit 0 
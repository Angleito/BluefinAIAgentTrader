#!/bin/bash
# Script to verify frontend connection to backend in production Docker setup

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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose.prod.yml exists
if [ ! -f "docker-compose.prod.yml" ]; then
    print_error "docker-compose.prod.yml not found. Please run this script from the project root directory."
    exit 1
fi

print_info "Verifying frontend connection to backend in production Docker setup..."

# Check if the containers are running
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_warning "Docker containers are not running. Starting them now..."
    docker-compose -f docker-compose.prod.yml up -d
    sleep 10
fi

# Check nginx container
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "nginx.*Up"; then
    print_error "Nginx container is not running. Please check the logs."
    exit 1
fi

print_info "Nginx container is running."

# Check if frontend files are mounted correctly
if ! docker-compose -f docker-compose.prod.yml exec nginx ls -la /usr/share/nginx/html/index.html > /dev/null 2>&1; then
    print_error "Frontend files are not mounted correctly in the nginx container."
    exit 1
fi

print_info "Frontend files are mounted correctly."

# Check if nginx is serving the frontend
if ! curl -s http://localhost > /dev/null; then
    print_error "Nginx is not serving the frontend. Please check the nginx configuration."
    exit 1
fi

print_info "Nginx is serving the frontend."

# Check backend API connection
if ! curl -s http://localhost/api/health > /dev/null; then
    print_error "Backend API is not accessible through nginx. Please check the nginx configuration."
    exit 1
fi

print_info "Backend API is accessible through nginx."

# Check WebSocket connection
print_info "Checking WebSocket connection..."
if ! curl -s -I http://localhost/socket.io/ | grep -q "200 OK\|101 Switching Protocols"; then
    print_warning "WebSocket endpoint might not be accessible. This could be normal if the WebSocket server requires authentication."
else
    print_info "WebSocket endpoint is accessible."
fi

# Check webhook connection
if ! curl -s http://localhost/webhook/health > /dev/null; then
    print_warning "Webhook endpoint is not accessible through nginx. This might be intentional for security reasons."
else
    print_info "Webhook endpoint is accessible through nginx."
fi

# Check agent API connection
if ! curl -s http://localhost/agent/health > /dev/null; then
    print_warning "Agent API is not accessible through nginx. Please check the nginx configuration."
else
    print_info "Agent API is accessible through nginx."
fi

# Check Bluefin API connection
if ! curl -s https://api.bluefin.exchange/v1/exchangeInfo > /dev/null; then  
    print_warning "Bluefin API is not accessible. Please check the Bluefin API URL and credentials."
else
    print_info "Bluefin API is accessible."  
fi

print_info "✅ Frontend connection verification completed."
print_info "If all checks passed, your frontend is properly connected to the backend in the production Docker setup."
print_info "If any warnings or errors were reported, please check the corresponding service logs:"
print_info "  docker-compose -f docker-compose.prod.yml logs nginx"
print_info "  docker-compose -f docker-compose.prod.yml logs backend"
print_info "  docker-compose -f docker-compose.prod.yml logs websocket"
print_info "  docker-compose -f docker-compose.prod.yml logs webhook"
print_info "  docker-compose -f docker-compose.prod.yml logs agent"

exit 0 
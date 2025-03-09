#!/bin/bash
# Health check script for Docker containers

set -e

# Configuration
WEBHOOK_URL="http://localhost:${WEBHOOK_PORT:-5004}/health"
AGENT_URL="http://localhost:${FLASK_APP_PORT:-5003}/health"
WEBSOCKET_URL="http://localhost:${SOCKET_PORT:-5008}/health"
TIMEOUT=5
MAX_RETRIES=3

# Function to check a service
check_service() {
    local url=$1
    local service_name=$2
    local retry_count=0
    
    echo "Checking $service_name at $url..."
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        if curl -s -f -m $TIMEOUT "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is healthy"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                echo "⚠️ $service_name check failed, retrying ($retry_count/$MAX_RETRIES)..."
                sleep 2
            fi
        fi
    done
    
    echo "❌ $service_name is unhealthy after $MAX_RETRIES attempts"
    return 1
}

# Main health check
main() {
    local exit_code=0
    
    check_service "$WEBHOOK_URL" "Webhook Service" || exit_code=1
    check_service "$AGENT_URL" "Agent Service" || exit_code=1
    check_service "$WEBSOCKET_URL" "WebSocket Service" || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        echo "All services are healthy!"
    else
        echo "One or more services are unhealthy!"
    fi
    
    exit $exit_code
}

# Run the health check
main 
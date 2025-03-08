#!/bin/bash

# Start Webhook Server for TradingView Alerts
# This script starts the webhook server and optionally ngrok for public access

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Set default values if not in environment
WEBHOOK_PORT=${WEBHOOK_PORT:-5001}
USE_NGROK=${USE_NGROK:-false}
NGROK_DOMAIN=${NGROK_DOMAIN:-""}
NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN:-""}

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to display help
show_help() {
    echo "Webhook Server for TradingView Alerts"
    echo "-------------------------------------"
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --port PORT        Port to listen on (default: $WEBHOOK_PORT)"
    echo "  --ngrok            Start ngrok for public access"
    echo "  --domain DOMAIN    Use custom ngrok domain (requires paid plan)"
    echo "  --help             Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)
            WEBHOOK_PORT="$2"
            shift 2
            ;;
        --ngrok)
            USE_NGROK=true
            shift
            ;;
        --domain)
            NGROK_DOMAIN="$2"
            USE_NGROK=true
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
is_port_in_use() {
    lsof -i:"$1" >/dev/null 2>&1
}

# Check if port is already in use
if is_port_in_use "$WEBHOOK_PORT"; then
    echo "Error: Port $WEBHOOK_PORT is already in use"
    echo "Please choose a different port or stop the process using this port"
    exit 1
fi

# Export variables for the webhook server
export WEBHOOK_PORT
export FLASK_APP=webhook_server.py
export FLASK_ENV=${FLASK_ENV:-"production"}
export FLASK_DEBUG=${FLASK_DEBUG:-"false"}

# Start the webhook server
echo "Starting webhook server on port $WEBHOOK_PORT..."
echo "Press Ctrl+C to stop"
echo ""

# Start the server in background
if command_exists "python3"; then
    PYTHON="python3"
elif command_exists "python"; then
    PYTHON="python"
else
    echo "Error: Python is not installed"
    exit 1
fi

# Start webhook server
WEBHOOK_PID=""
start_webhook_server() {
    echo "Starting webhook server with $PYTHON webhook_server.py"
    $PYTHON webhook_server.py &
    WEBHOOK_PID=$!
    echo "Webhook server started with PID: $WEBHOOK_PID"
}

# Start ngrok if requested
NGROK_PID=""
start_ngrok() {
    if ! command_exists "ngrok"; then
        echo "Error: ngrok is not installed"
        echo "Installing ngrok..."
        
        # Download and install ngrok if not present
        if [ ! -f ./ngrok ]; then
            curl -s https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.zip -o ngrok.zip
            unzip -o ngrok.zip
            chmod +x ./ngrok
        fi
        
        # Add to path
        export PATH=$PATH:$(pwd)
    fi

    # Check if auth token is set
    if [ -z "$NGROK_AUTHTOKEN" ]; then
        echo "Error: NGROK_AUTHTOKEN is not set"
        echo "Please set NGROK_AUTHTOKEN in your .env file or environment"
        return 1
    else
        # Configure ngrok auth token
        echo "Configuring ngrok with auth token..."
        ./ngrok config add-authtoken "$NGROK_AUTHTOKEN" || ngrok config add-authtoken "$NGROK_AUTHTOKEN"
        
        if [ $? -ne 0 ]; then
            echo "Failed to set ngrok authtoken. Trying alternative method..."
            mkdir -p ~/.ngrok2
            echo "authtoken: $NGROK_AUTHTOKEN" > ~/.ngrok2/ngrok.yml
        fi
    fi

    echo "Starting ngrok tunnel to port $WEBHOOK_PORT..."
    
    # Start ngrok with custom domain if provided
    if [ -n "$NGROK_DOMAIN" ]; then
        ./ngrok http --domain="$NGROK_DOMAIN" "$WEBHOOK_PORT" > logs/ngrok.log 2>&1 &
    else
        ./ngrok http "$WEBHOOK_PORT" > logs/ngrok.log 2>&1 &
    fi
    
    NGROK_PID=$!
    echo "ngrok started with PID: $NGROK_PID"
    
    # Wait for ngrok to start
    sleep 2
    
    # Get ngrok URL
    if [ -n "$NGROK_DOMAIN" ]; then
        NGROK_URL="https://$NGROK_DOMAIN"
    else
        # Try to get URL from ngrok API
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | head -1 | sed 's/"public_url":"//')
    fi
    
    if [ -n "$NGROK_URL" ]; then
        echo ""
        echo "=============================================="
        echo "Webhook URL for TradingView:"
        echo "$NGROK_URL/webhook"
        echo "=============================================="
        echo ""
        echo "Use this URL in your TradingView alert webhook settings"
    else
        echo "Could not determine ngrok URL"
        echo "Please check logs/ngrok.log or visit http://localhost:4040"
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping services..."
    
    if [ -n "$WEBHOOK_PID" ]; then
        echo "Stopping webhook server (PID: $WEBHOOK_PID)"
        kill $WEBHOOK_PID 2>/dev/null
    fi
    
    if [ -n "$NGROK_PID" ]; then
        echo "Stopping ngrok (PID: $NGROK_PID)"
        kill $NGROK_PID 2>/dev/null
    fi
    
    echo "Cleanup complete"
    exit 0
}

# Set up trap for cleanup on exit
trap cleanup SIGINT SIGTERM

# Start the services
start_webhook_server

# Start ngrok if requested
if [ "$USE_NGROK" = true ]; then
    start_ngrok
else
    echo ""
    echo "=============================================="
    echo "Webhook server is running at:"
    echo "http://localhost:$WEBHOOK_PORT/webhook"
    echo "=============================================="
    echo ""
    echo "This URL is only accessible from your local machine."
    echo "To receive webhooks from TradingView, consider using ngrok"
    echo "Run with --ngrok flag to start ngrok automatically"
    echo ""
fi

# Keep script running
echo "Webhook server is running. Press Ctrl+C to stop."
wait $WEBHOOK_PID 
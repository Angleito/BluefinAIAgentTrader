#!/bin/bash
# Script to monitor and maintain the live trading containers

# Color variables
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

print_status() {
    echo -e "${BLUE}[STATUS]${NC} $1"
}

# Make scripts executable
chmod +x run_live_trading.sh

# Check if containers are running
if ! docker-compose -f docker-compose.live.yml ps | grep -q "Up"; then
    print_error "Trading containers are not running. Start them with ./run_live_trading.sh"
    exit 1
fi

# Function to display menu
show_menu() {
    echo ""
    print_status "PerplexityTrader Live Trading Monitor"
    echo "------------------------------------"
    echo "1. View agent logs"
    echo "2. View webhook logs"
    echo "3. Check container status"
    echo "4. View active positions"
    echo "5. View recent trades"
    echo "6. Restart agent container"
    echo "7. Restart all containers"
    echo "8. Stop all containers"
    echo "9. Update and restart (pulls latest code)"
    echo "0. Exit"
    echo ""
}

# Function to view logs
view_logs() {
    local container=$1
    local lines=$2
    
    print_info "Showing logs for $container (Ctrl+C to return to menu)"
    docker-compose -f docker-compose.live.yml logs --tail=$lines -f $container
}

# Function to restart containers
restart_container() {
    local container=$1
    
    print_warning "Restarting $container container..."
    docker-compose -f docker-compose.live.yml restart $container
    print_info "$container container restarted"
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice: " choice
    
    case $choice in
        1)
            view_logs agent 500
            ;;
        2)
            view_logs webhook 500
            ;;
        3)
            print_info "Container status:"
            docker-compose -f docker-compose.live.yml ps
            read -p "Press Enter to continue..."
            ;;
        4)
            print_info "Checking active positions..."
            curl -s http://localhost:5000/positions | jq .
            read -p "Press Enter to continue..."
            ;;
        5)
            print_info "Checking recent trades..."
            tail -n 50 logs/trading.log | grep -E "executed|order|position"
            read -p "Press Enter to continue..."
            ;;
        6)
            restart_container agent
            ;;
        7)
            print_warning "Restarting all containers..."
            docker-compose -f docker-compose.live.yml restart
            print_info "All containers restarted"
            ;;
        8)
            print_warning "Stopping all containers..."
            docker-compose -f docker-compose.live.yml down
            print_info "All containers stopped"
            exit 0
            ;;
        9)
            print_info "Updating and restarting containers..."
            docker-compose -f docker-compose.live.yml down
            git pull
            docker-compose -f docker-compose.live.yml up -d --build
            print_info "Containers updated and restarted"
            ;;
        0)
            print_info "Exiting monitor. Containers will continue running."
            exit 0
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
done 
#!/bin/bash
# Script to verify all libraries and dependencies in Docker

set -e

echo "===== STEP 1: Building and Testing Docker Environment ====="
docker-compose -f docker-compose.test.yml build

echo "Running comprehensive environment tests..."
docker-compose -f docker-compose.test.yml run --rm test-bluefin

if [ $? -eq 0 ]; then
  echo "✅ Environment test passed!"
  
  echo "===== STEP 2: Building Agent Docker Container ====="
  docker-compose build agent
  
  echo "===== STEP 3: Verifying Webhook Server ====="
  docker-compose build webhook
  
  echo "✅ Docker setup verified!"
  echo ""
  echo "To run the full agent system with Docker:"
  echo "docker-compose up -d"
  echo ""
  echo "To monitor logs:"
  echo "docker-compose logs -f agent"
  echo ""
  echo "WARNING: This agent will execute REAL trades with real money if MOCK_TRADING=False"
  echo "Please ensure your trading parameters are properly configured in the .env file."
else
  echo "❌ Docker environment test failed!"
  echo "Please check the logs for details and fix any issues before proceeding."
  exit 1
fi 
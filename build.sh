#!/bin/bash
set -e

# Default to latest tag if not provided
TAG=${1:-latest}

# Ensure BuildX is set up
docker buildx create --use --name multiarch-builder || true
docker buildx inspect --bootstrap

# Build and push webhook service
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t perplexitytrader-webhook:$TAG \
  -f Dockerfile \
  --push \
  .

# Build and push websocket service
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t perplexitytrader-websocket:$TAG \
  -f Dockerfile \
  --push \
  .

# Build and push agent service (if using a different Dockerfile)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t perplexitytrader-agent:$TAG \
  -f infrastructure/docker/Dockerfile.agent \
  --push \
  .

echo "Multi-architecture builds completed successfully!" 
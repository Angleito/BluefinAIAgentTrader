# syntax=docker/dockerfile:1.4
# Use Python 3.10 as the base image with BuildX support
FROM --platform=$TARGETPLATFORM python:3.10-slim

# Set build arguments for multi-arch support
ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Set working directory
WORKDIR /app

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    cron \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install core dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir flask==2.0.1 werkzeug==2.0.3

# Copy requirements.txt
COPY requirements.txt .

# Install other Python dependencies with build cache and dependency resolution
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    anthropic==0.49.0 \
    gunicorn==20.1.0 \
    fastapi==0.104.1 \
    uvicorn==0.23.2 \
    requests==2.31.0 \
    backoff==2.2.1 \
    python-dotenv==0.19.2 \
    flask-cors==3.0.10 \
    flask-socketio==5.1.1 \
    flask-limiter==2.8.1 \
    python-dateutil==2.8.2 \
    numpy==1.24.3 \
    pillow==10.1.0

# Install Bluefin client libraries separately
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
    git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git \
    git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git

# Verify Flask and Werkzeug versions
RUN pip show flask werkzeug

# Install playwright browsers
RUN playwright install --with-deps chromium

# Create necessary directories
RUN mkdir -p logs alerts screenshots analysis

# Copy only the necessary application code
COPY core/ ./core/
COPY api/ ./api/
COPY *.py ./
COPY config/ ./config/
COPY check_services.sh ./
COPY check_services_docker.sh ./
COPY start_services.sh ./
COPY stop_services.sh ./

# Make scripts executable
RUN chmod +x *.sh

# Set up cron job to check services every 5 minutes
RUN echo "*/5 * * * * /app/check_services_docker.sh >> /app/logs/cron.log 2>&1" > /etc/cron.d/service-check \
    && chmod 0644 /etc/cron.d/service-check \
    && crontab /etc/cron.d/service-check

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=webhook_server.py \
    FLASK_ENV=production \
    FLASK_DEBUG=false \
    WEBHOOK_PORT=5001 \
    MOCK_TRADING=False \
    PYTHONPATH=/app

# Add healthcheck to ensure the application is running properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

# Expose the webhook port
EXPOSE 5001

# Create a wrapper script to start both cron and the webhook server
RUN echo '#!/bin/bash\nservice cron start\nexec "$@"' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Run the webhook server
CMD ["python", "webhook_server.py"] 
# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    cron \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Flask and Werkzeug versions that are known to work together
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir flask==2.0.1 werkzeug==2.0.1 && \
    pip install --no-cache-dir gunicorn==20.1.0 fastapi==0.104.1 uvicorn==0.23.2 && \
    pip install --no-cache-dir requests==2.28.2 backoff==2.2.1 python-dotenv==0.19.2 && \
    pip install --no-cache-dir flask-cors==3.0.10 flask-socketio==5.1.1 flask-limiter==2.8.1 && \
    pip install --no-cache-dir python-dateutil==2.8.2 numpy==1.24.3 pillow==10.1.0 && \
    pip install --no-cache-dir anthropic==0.49.0 && \
    pip install --no-cache-dir git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git && \
    pip install --no-cache-dir git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git && \
    pip install --no-cache-dir httpx websockets

# Create necessary directories
RUN mkdir -p logs alerts

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x *.sh

# Set up cron job to check services every 5 minutes
RUN echo "*/5 * * * * /app/check_services_docker.sh >> /app/logs/cron.log 2>&1" > /etc/cron.d/service-check \
    && chmod 0644 /etc/cron.d/service-check \
    && crontab /etc/cron.d/service-check

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production

# Expose ports (uses environment variables from .env)
EXPOSE 5003 5004 5008

# Create a wrapper script to start services
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'echo "Starting PerplexityTrader service: $@"' >> /app/entrypoint.sh && \
    echo 'echo "Current directory: $(pwd)"' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Start cron service' >> /app/entrypoint.sh && \
    echo 'service cron start' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Check if we are running the webhook server and Hookdeck is enabled' >> /app/entrypoint.sh && \
    echo 'if [[ "$1" == "webhook_server.py" && "${USE_HOOKDECK}" == "true" ]]; then' >> /app/entrypoint.sh && \
    echo '  if [[ -z "${HOOKDECK_API_KEY}" || -z "${HOOKDECK_SIGNING_SECRET}" ]]; then' >> /app/entrypoint.sh && \
    echo '    echo "WARNING: Hookdeck enabled but API key or signing secret is missing"' >> /app/entrypoint.sh && \
    echo '  else' >> /app/entrypoint.sh && \
    echo '    echo "Hookdeck integration enabled"' >> /app/entrypoint.sh && \
    echo '  fi' >> /app/entrypoint.sh && \
    echo 'fi' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# Run the python script' >> /app/entrypoint.sh && \
    echo 'python "$@"' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default to webhook server if no command specified
CMD ["webhook_server.py"]

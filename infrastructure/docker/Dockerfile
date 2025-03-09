# Use Python 3.10 as the base image
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Add non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser \
    && chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_ENV=production \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies with security best practices
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    cron \
    procps \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install Flask and Werkzeug versions that are known to work together
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories and set permissions
RUN mkdir -p logs alerts && \
    chown -R appuser:appuser /app/logs /app/alerts

# Copy application code
COPY . .
RUN chown -R appuser:appuser /app

# Make scripts executable
RUN chmod +x *.sh

# Set up cron job to check services every 5 minutes
RUN echo "*/5 * * * * /app/check_services_docker.sh >> /app/logs/cron.log 2>&1" > /etc/cron.d/service-check \
    && chmod 0644 /etc/cron.d/service-check \
    && crontab /etc/cron.d/service-check

# Create a health check script
COPY healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

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
    echo 'exec python "$@"' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user for security
USER appuser

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default to webhook server if no command specified
CMD ["webhook_server.py"]

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 CMD ["/app/healthcheck.sh"]

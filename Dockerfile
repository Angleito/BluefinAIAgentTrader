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

# Install Flask and Werkzeug with compatible versions first
RUN pip install --no-cache-dir flask==2.0.1 werkzeug==2.0.3

# Copy requirements.txt but exclude Flask and Werkzeug since we've already installed them
COPY requirements.txt .

# Install other Python dependencies
RUN grep -v "flask\|werkzeug" requirements.txt > other_requirements.txt && \
    pip install --no-cache-dir -r other_requirements.txt && \
    rm other_requirements.txt

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
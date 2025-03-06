# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs alerts

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=webhook_server.py \
    FLASK_ENV=production \
    FLASK_DEBUG=false \
    WEBHOOK_PORT=5001

# Expose the webhook port
EXPOSE 5001

# Run the webhook server
CMD ["python", "webhook_server.py"] 
FROM python:3.9-slim-bullseye

# Set environment variables to reduce Python output buffering and prevent .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies with additional reliability measures
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        cron \
        procps \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY infrastructure/docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the entrypoint
CMD ["python", "infrastructure/docker/app.py"] 
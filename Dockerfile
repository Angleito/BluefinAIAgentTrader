FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install playwright && playwright install chromium && playwright install-deps

# Copy requirements first for better cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Bluefin client libraries
RUN pip install --no-cache-dir git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git
RUN pip install --no-cache-dir git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p screenshots logs analysis

# Expose the Flask port
EXPOSE 5000

# Default command - can be overridden in docker-compose
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"] 
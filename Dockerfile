FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/fireflyprotocol/bluefin-client-python-sui.git
RUN pip install --no-cache-dir git+https://github.com/fireflyprotocol/bluefin-v2-client-python.git

COPY . .

# Create necessary directories
RUN mkdir -p logs alerts

CMD ["python", "agent.py"] 
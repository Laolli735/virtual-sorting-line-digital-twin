FROM python:3.12-slim

WORKDIR /app

# Asennetaan järjestelmäriippuvuudet psycopg2:ta ja kryptografiaa varten
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY edge-gateway/ ./edge-gateway/
COPY plc-simulator/ ./plc-simulator/
COPY web-scada/ ./web-scada/
COPY client_cert.der client_key.pem ./
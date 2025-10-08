FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY tools/ ./tools/

RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1
ENV MCP_LOG_FILE=/app/data/mcp_server.log

# Exposer le port HTTP
EXPOSE 8080

# Par défaut: auto-détection du mode
CMD ["python", "server.py"]
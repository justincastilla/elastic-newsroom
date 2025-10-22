# Elastic News - Multi-Agent Newsroom
# Dockerfile for all Python agents and services

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose ports for all services
# MCP Server: 8095
# Event Hub: 8090
# Article API: 8085
# News Chief: 8080
# Reporter: 8081
# Editor: 8082
# Researcher: 8083
# Publisher: 8084
EXPOSE 8095 8090 8085 8080 8081 8082 8083 8084

# Health check for MCP server (critical dependency)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8095/health || exit 1

# Default command - start all services
CMD ["python", "scripts/docker_entrypoint.py"]

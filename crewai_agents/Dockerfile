# Dockerfile for CrewAI Agents
#
# Builds a container for running CrewAI-based agents in the Elastic Newsroom.
# This image is optimized for the researcher_crew and can be extended for other CrewAI agents.

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy CrewAI agents module
COPY crewai_agents/ /app/crewai_agents/

# Copy shared utilities (needed for MCP client, logging, etc.)
COPY utils/ /app/utils/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port for researcher crew
EXPOSE 8083

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
    CMD curl -f http://localhost:8083/health || exit 1

# Run the CrewAI researcher server
CMD ["python", "-m", "crewai_agents.researcher_crew.main", "--host", "0.0.0.0", "--port", "8083"]

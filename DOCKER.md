# Docker Deployment Guide

Complete guide for running Elastic News in Docker containers.

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd elastic-news

# 2. Create environment file
cp .env.docker .env

# 3. Edit .env with your API key
nano .env  # or your preferred editor
# Set ANTHROPIC_API_KEY=your_key_here

# 4. Start everything
docker-compose up -d

# 5. Access the UI
open http://localhost:3001
```

## Architecture

### Containers

1. **elastic-news-agents** - All Python agents and services
   - Built from: `Dockerfile`
   - Ports: 8080-8084, 8085, 8090, 8095
   - Health check: MCP server at port 8095

2. **elastic-news-ui** - React production build
   - Built from: `react-ui/Dockerfile`
   - Port: 3001
   - Depends on: agents container (via health check)

### Network

- **elastic-news-network** - Bridge network for inter-container communication
- All services can communicate via container names
- External access via published ports

### Volumes

- **logs** - Persistent log storage (`./logs:/app/logs`)
- **articles** - Published articles (`./articles:/app/articles`)

## Configuration

### Required Environment Variables

Set in `.env` file (create from `.env.docker`):

```bash
# REQUIRED
ANTHROPIC_API_KEY=sk-ant-api03-...

# OPTIONAL: Elasticsearch
ELASTICSEARCH_ENDPOINT=https://cluster.es.region.gcp.elastic.cloud:443
ELASTICSEARCH_API_KEY=your_key
ELASTIC_ARCHIVIST_INDEX=news_archive

# OPTIONAL: Archivist
ELASTIC_ARCHIVIST_AGENT_CARD_URL=https://kb.kb.region.gcp.elastic.cloud/...
ELASTIC_ARCHIVIST_API_KEY=your_key
```

### Internal URLs (Auto-configured)

These are set automatically in `docker-compose.yml`:

- `MCP_SERVER_URL=http://localhost:8095`
- `EVENT_HUB_URL=http://localhost:8090`
- `EVENT_HUB_ENABLED=true`

## Common Commands

### Start Services

```bash
# Start in background
docker-compose up -d

# Start with logs (foreground)
docker-compose up

# Start and rebuild
docker-compose up -d --build
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f newsroom-agents
docker-compose logs -f newsroom-ui

# Last 100 lines
docker-compose logs --tail=100 newsroom-agents
```

### Stop Services

```bash
# Stop containers (preserves volumes)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove volumes (deletes logs/articles)
docker-compose down -v
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart newsroom-agents
docker-compose restart newsroom-ui
```

### Check Status

```bash
# List containers
docker-compose ps

# Check health
docker-compose ps
# Look for "healthy" status on newsroom-agents
```

### Execute Commands

```bash
# Shell into agents container
docker-compose exec newsroom-agents bash

# Shell into UI container
docker-compose exec newsroom-ui sh

# Run a command
docker-compose exec newsroom-agents python --version
```

## Troubleshooting

### MCP Server Not Starting

**Symptom**: Agents container keeps restarting

**Solution**:
```bash
# Check logs
docker-compose logs newsroom-agents | grep MCP

# Verify fastmcp is installed
docker-compose exec newsroom-agents pip list | grep fastmcp

# Rebuild with no cache
docker-compose build --no-cache newsroom-agents
docker-compose up -d
```

### UI Can't Connect to Agents

**Symptom**: UI loads but shows connection errors

**Solution**:
```bash
# Check agents health
docker-compose ps

# Verify network
docker-compose exec newsroom-ui wget -qO- http://newsroom-agents:8080/health

# Check Event Hub
curl http://localhost:8090/health
```

### Port Already in Use

**Symptom**: `Error: bind: address already in use`

**Solution**:
```bash
# Find process using port
lsof -i :8080  # or whatever port

# Stop conflicting process
kill <PID>

# Or change port in docker-compose.yml
ports:
  - "8180:8080"  # Map to different external port
```

### Logs/Articles Not Persisting

**Symptom**: Logs disappear after restart

**Solution**:
```bash
# Check volume mounts in docker-compose.yml
volumes:
  - ./logs:/app/logs      # Correct
  - ./articles:/app/articles  # Correct

# Verify directories exist
ls -la logs articles

# Create if missing
mkdir -p logs articles
```

### Out of Memory

**Symptom**: Container killed with exit code 137

**Solution**:
```bash
# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory > 4GB+

# Or limit per service in docker-compose.yml
services:
  newsroom-agents:
    mem_limit: 1g
```

### Environment Variables Not Loading

**Symptom**: `ANTHROPIC_API_KEY not set` errors

**Solution**:
```bash
# Verify .env file exists
ls -la .env

# Check docker-compose picks it up
docker-compose config | grep ANTHROPIC

# Rebuild and restart
docker-compose down
docker-compose up -d
```

## Development Workflow

### Making Code Changes

1. **Edit code locally**
   ```bash
   vim agents/reporter.py
   ```

2. **Rebuild and restart**
   ```bash
   docker-compose up -d --build
   ```

3. **Check logs**
   ```bash
   docker-compose logs -f newsroom-agents
   ```

### Testing Changes

```bash
# Run tests in container
docker-compose exec newsroom-agents pytest -v

# Or run tests locally (requires dependencies)
pytest -v
```

### Hot Reload (Development)

For faster iteration without rebuilding:

```bash
# Mount code as volume in docker-compose.yml
services:
  newsroom-agents:
    volumes:
      - ./agents:/app/agents:ro  # Read-only mount
      - ./utils:/app/utils:ro
      - ./mcp_servers:/app/mcp_servers:ro
      # ... other code directories
```

Then restart specific services:
```bash
docker-compose restart newsroom-agents
```

## Production Deployment

### Best Practices

1. **Use specific image tags**
   ```yaml
   image: elastic-news-agents:1.0.0
   ```

2. **Set resource limits**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: '1.0'
   ```

3. **Use secrets for API keys**
   ```yaml
   secrets:
     - anthropic_api_key
   ```

4. **Enable logging driver**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

5. **Set restart policy**
   ```yaml
   restart: unless-stopped
   ```

### Health Monitoring

```bash
# Check health status
docker inspect elastic-news-agents | grep -A 10 Health

# Auto-restart unhealthy containers
# (Already configured in docker-compose.yml)
```

### Backup

```bash
# Backup volumes
docker run --rm -v elastic-news_logs:/data -v $(pwd):/backup alpine tar czf /backup/logs-backup.tar.gz -C /data .

# Backup articles
tar czf articles-backup.tar.gz articles/
```

### Scaling

To run multiple instances behind a load balancer:

```bash
# Scale agents (with load balancer)
docker-compose up -d --scale newsroom-agents=3

# Note: Requires load balancer configuration
# and stateless design (no in-memory state)
```

## Performance Optimization

### Build Optimization

```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker-compose build

# Multi-stage builds (already configured)
# - Reduces final image size
# - Faster deployments
```

### Runtime Optimization

```yaml
# In docker-compose.yml
services:
  newsroom-agents:
    environment:
      - PYTHONUNBUFFERED=1  # Better logging
      - PYTHONDONTWRITEBYTECODE=1  # No .pyc files
```

## Security

### API Keys

```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use Docker secrets in production
docker secret create anthropic_key .env
```

### Network Security

```yaml
# Restrict network access
networks:
  elastic-news-network:
    internal: true  # No external access
```

### Read-only Filesystem

```yaml
services:
  newsroom-agents:
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

## Monitoring

### Health Checks

```bash
# Check all health statuses
docker-compose ps

# Monitor continuously
watch -n 5 'docker-compose ps'
```

### Resource Usage

```bash
# Live stats
docker stats

# One-time snapshot
docker stats --no-stream
```

### Logs Analysis

```bash
# Error count
docker-compose logs newsroom-agents | grep ERROR | wc -l

# Recent errors
docker-compose logs --tail=100 newsroom-agents | grep ERROR
```

## Clean Up

### Remove Containers

```bash
# Stop and remove
docker-compose down

# Remove with volumes
docker-compose down -v
```

### Remove Images

```bash
# Remove project images
docker rmi elastic-news-agents elastic-news-ui

# Remove all unused images
docker image prune -a
```

### Full Cleanup

```bash
# Nuclear option - removes everything
docker-compose down -v
docker system prune -a --volumes
```

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Verify health: `docker-compose ps`
- See main README.md for project documentation
- Check CLAUDE.md for development guide

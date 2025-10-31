# Docker Quick Start Guide

Get Elastic News running in 5 minutes with Docker.

## Prerequisites

- Docker Engine 20.10+ installed
- Docker Compose 2.0+ installed
- Anthropic API key

## Installation

### 1. Setup Environment

```bash
# Copy environment template
cp .env.docker .env

# Edit with your API key
nano .env  # or use your preferred editor
```

Add your Anthropic API key:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your_key_here
```

### 2. Start Services

```bash
# Start all services in background
docker-compose up -d
```

### 3. Access the UI

Open your browser to: **http://localhost:3001**

## Quick Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart after code changes
docker-compose up -d --build

# Check status
docker-compose ps
```

## What's Running?

After `docker-compose up -d`, you'll have:

### Services
- **MCP Server** (port 8095) - Tool provider ✅ REQUIRED
- **Event Hub** (port 8090) - Real-time events
- **Article API** (port 8085) - Article data
- **News Chief** (port 8080) - Coordinator
- **Reporter** (port 8081) - Article writer
- **Editor** (port 8082) - Content reviewer
- **Researcher** (port 8083) - Fact gatherer
- **Publisher** (port 8084) - Article publisher
- **React UI** (port 3001) - Web interface 🌐

### Access Points
- **Web UI**: http://localhost:3001 (main interface)
- **Logs**: `./logs/` directory
- **Articles**: `./articles/` directory

## First Steps

1. **Open UI**: http://localhost:3001
2. **Create Story**: Fill out the form
   - Topic: "Artificial Intelligence in Healthcare"
   - Angle: "Recent breakthroughs"
   - Target Length: 1000 words
3. **Submit**: Click "Assign Story"
4. **Watch Progress**: Real-time workflow visualization
5. **View Article**: Click on completed story

## Troubleshooting

### Services Not Starting?

```bash
# Check logs for errors
docker-compose logs newsroom-agents | grep ERROR

# Verify MCP server is healthy
docker-compose ps
# Should show "healthy" for newsroom-agents

# Test health endpoint directly
curl http://localhost:8095/health
# Should return: {"status": "healthy", "service": "Newsroom MCP HTTP Server"}
```

### UI Can't Connect?

```bash
# Check if agents are running
curl http://localhost:8080/health

# Restart UI container
docker-compose restart newsroom-ui
```

### Need to Reset?

```bash
# Stop and remove everything
docker-compose down -v

# Fresh start
docker-compose up -d
```

## Next Steps

- **Read DOCKER.md** for detailed documentation
- **Check CLAUDE.md** for development guide
- **See README.md** for architecture details
- **Run tests**: `docker-compose exec newsroom-agents pytest -v`

## Common Issues

| Problem | Solution |
|---------|----------|
| Port 8080 already in use | Change port in `docker-compose.yml`: `"8180:8080"` |
| Out of memory | Increase Docker memory limit to 4GB+ |
| MCP server failing | Rebuild: `docker-compose build --no-cache` |
| Logs not persisting | Check `./logs` directory exists |

## Support

Need help?
- Check logs: `docker-compose logs -f`
- Verify health: `docker-compose ps`
- See full docs: `DOCKER.md`

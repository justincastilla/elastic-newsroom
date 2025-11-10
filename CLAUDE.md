# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Elastic News is a working multi-agent AI newsroom demonstrating Agent2Agent (A2A) and Model Context Protocol (MCP) integration. Five specialized AI agents collaborate via A2A protocol to research, write, edit, and publish news articles.

**Key Technologies:**
- A2A SDK v0.3.8 for multi-agent coordination
- MCP (Model Context Protocol) for tool integration
- Anthropic Claude Sonnet 4 for AI content generation
- Elasticsearch for article indexing and historical search
- React UI (port 3001) - Primary interface with real-time monitoring
- Event Hub (port 8090) - SSE-based event broadcasting
- Uvicorn ASGI server

## Development Commands

### Docker Deployment (Recommended for Production)

See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for complete Docker documentation.

```bash
cp .env.docker .env          # Create .env file
# Edit .env with your API keys
docker-compose up -d         # Start all services
docker-compose logs -f       # View logs
docker-compose down          # Stop all services
```

**Services:** MCP Server (8095), Event Hub (8090), Article API (8085), News Chief (8080), Reporter (8081), Editor (8082), Researcher (8083), Publisher (8084), React UI (3001)

### Local Development (No Docker)
```bash
# Start all agents (5 agents on ports 8080-8084)
./scripts/start_newsroom.sh

# Start with hot reload for development
./scripts/start_newsroom.sh --reload

# Start agents + web UI
./scripts/start_newsroom.sh --with-ui

# Stop everything
./scripts/start_newsroom.sh --stop
```

### Individual Agents
```bash
# Run agents individually (useful for debugging)
uvicorn agents.news_chief:app --host localhost --port 8080 --reload
uvicorn agents.reporter:app --host localhost --port 8081 --reload
uvicorn agents.editor:app --host localhost --port 8082 --reload
uvicorn agents.researcher:app --host localhost --port 8083 --reload
uvicorn agents.publisher:app --host localhost --port 8084 --reload
```

### Web UI

# Or use the script
./start_ui.sh

# Access at http://localhost:3000
```

### Testing (Pytest Framework)
```bash
# Modern pytest-based testing (RECOMMENDED)
make test              # Fast tests (excludes slow tests)
make test-all          # All tests including slow ones
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-workflow     # Full workflow tests

# Direct pytest commands
pytest -v -m "not slow"  # Fast tests
pytest -v                # All tests
pytest tests/test_workflow_pytest.py -v  # Specific file

# Legacy test scripts
python tests/test_full_workflow.py       # Standalone workflow test
python tests/test_newsroom_workflow_comprehensive.py  # Monitoring test
python scripts/create_elasticsearch_index.py          # ES index setup
python tests/test_archivist.py                       # Archivist test
```

See `TESTING.md` for comprehensive testing documentation.

### Logs and Monitoring
```bash
# View colorized logs (recommended - real-time with color coding)
make logs-color
python scripts/view_logs.py

# View plain logs
tail -f logs/*.log

# View specific agent
tail -f logs/News_Chief.log

# Check agent health
make status

# Health check endpoints
curl http://localhost:8095/health  # MCP Server
# Response: {"status": "healthy", "service": "Newsroom MCP HTTP Server"}

curl http://localhost:8080/.well-known/agent-card.json  # Any agent (News Chief example)

# Verify environment variables in Docker
docker exec elastic-news-agents printenv | grep -E "ANTHROPIC|ELASTIC_ARCHIVIST_AGENT_URL|MCP_SERVER"

# Docker logs
docker-compose logs -f              # All services
docker-compose logs -f newsroom-agents  # Agents only
docker-compose logs -f newsroom-ui      # UI only
```

## Architecture

### Multi-Agent System (All Implemented and Working)

**Agent Ports:**
- News Chief: 8080 (coordinator)
- Reporter: 8081 (writes articles)
- Editor: 8082 (reviews content)
- Researcher: 8083 (gathers facts)
- Publisher: 8084 (indexes to Elasticsearch)

**Supporting Services:**
- Event Hub: 8090 (SSE event broadcasting for real-time UI updates)
- Article API: (part of Event Hub service - serves article data)
- MCP Server: (tool server for research, editing, and deployment operations)

**External Agent:**
- Archivist: Elastic Cloud (searches historical articles via Conversational API)

### Agent Communication Flow

```
User (Web UI or Test Script)
    ↓
News Chief (8080) - assigns story
    ↓
Reporter (8081) - coordinates writing
    ├── Researcher (8083) - gathers facts
    ├── Archivist (Elastic Cloud) - searches history
    ↓
    └── writes article with research + context
    ↓
Editor (8082) - reviews and suggests edits
    ↓
Reporter - applies edits
    ↓
Publisher (8084) - indexes to Elasticsearch + saves markdown
```

### A2A Agent Pattern

Each agent follows this structure from the A2A SDK:

```python
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

class MyAgent:
    async def invoke(self, query: str) -> Dict[str, Any]:
        # Agent logic - parse JSON query and return result
        pass

class MyAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = MyAgent()

    async def execute(self, context, event_queue):
        query = context.get_user_input()
        result = await self.agent.invoke(query)
        await event_queue.enqueue_event(
            new_agent_text_message(json.dumps(result))
        )

def create_agent_card(host, port) -> AgentCard:
    return AgentCard(
        name="Agent Name",
        description="What the agent does",
        url=f"http://{host}:{port}",
        version="1.0.0",
        skills=[...],
        capabilities=AgentCapabilities(...)
    )

app = A2AStarletteApplication(
    agent_card=create_agent_card('localhost', port),
    http_handler=DefaultRequestHandler(
        agent_executor=MyAgentExecutor(),
        task_store=InMemoryTaskStore()
    )
).build()
```

### Agent Communication (A2A Protocol)

Agents communicate via A2A using httpx and the A2A SDK client:

```python
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver, create_text_message_object

async with httpx.AsyncClient(timeout=90.0) as http_client:
    # Discover target agent
    card_resolver = A2ACardResolver(http_client, "http://localhost:8081")
    agent_card = await card_resolver.get_agent_card()

    # Create client
    client_config = ClientConfig(httpx_client=http_client, streaming=False)
    client_factory = ClientFactory(client_config)
    client = client_factory.create(agent_card)

    # Send message
    request = {"action": "write_article", "story_id": "story_123"}
    message = create_text_message_object(content=json.dumps(request))

    async for response in client.send_message(message):
        # Process response
        pass
```

### Archivist Integration (A2A Protocol)

The Reporter calls the Archivist (an Elastic Cloud Agent Builder agent) via A2A protocol to search historical articles in the `news_archive` index.

**Key Details:**
- Endpoint: `POST https://[kb-url]/api/agent_builder/a2a/{agent-id}`
- Protocol: JSONRPC 2.0 with unique `messageId` per request
- Timeout: 30 seconds with 3 retry attempts
- Implementation: `agents/reporter.py:_send_to_archivist()`

See [docs/architecture.md](docs/architecture.md) for complete JSONRPC request/response format and [Elastic Agent Builder A2A documentation](https://www.elastic.co/docs/solutions/search/agent-builder/a2a-server) for setup.

### MCP (Model Context Protocol) Integration

MCP server (port 8095) exposes reusable AI tools for research, article generation, editing, and review.

**CRITICAL:** MCP server is **REQUIRED** - all agents fail if not running. Starts automatically with `start_newsroom.sh` or manually via `python -m mcp_servers.newsroom_http_server`.

**Tools:** research_questions, generate_outline, generate_article, apply_edits, review_article, generate_tags, deploy_to_production, notify_subscribers

See [docs/architecture.md](docs/architecture.md) for complete tool descriptions and client design patterns.

### Event Hub (Real-time Updates)

The Event Hub broadcasts agent events to connected UI clients via Server-Sent Events (SSE):

**Features:**
- SSE endpoint at `http://localhost:8090/stream` for real-time client updates
- Event buffering for clients that reconnect (max 1000 events)
- Story-specific event filtering via `story_id`
- Health check endpoint at `/health`

**Architecture:**
- Agents POST events to `/events` endpoint
- UI clients connect to `/stream` for real-time updates
- Events are broadcast to all connected clients
- Optional `story_id` filtering for targeted updates

**Starting Event Hub:**
```bash
./scripts/start_event_hub.sh              # Normal start
./scripts/start_event_hub.sh --reload     # With hot reload
./scripts/start_event_hub.sh --stop       # Stop service
```

**Event Format:**
```json
{
  "timestamp": "2025-10-21T12:34:56Z",
  "agent": "Reporter",
  "event_type": "article_drafted",
  "story_id": "story_123",
  "message": "Article draft completed",
  "data": { /* event-specific payload */ }
}
```

See `services/event_hub.py` for implementation.

## Key Files

**Core Agents:**
- `agents/news_chief.py` - Coordinator agent (8080)
- `agents/reporter.py` - Article writer (8081), calls Researcher + Archivist (optimized)
- `agents/editor.py` - Content reviewer (8082)
- `agents/researcher.py` - Fact gatherer (8083)
- `agents/publisher.py` - Elasticsearch indexer (8084)
- `agents/archivist_client.py` - Client for Elastic Cloud Archivist agent
- `agents/base_agent.py` - Base class with common agent functionality

**Supporting Services:**
- `services/event_hub.py` - SSE event broadcasting (port 8090)
- `services/article_api.py` - Article data API for UI

**MCP Integration:**
- `mcp_servers/newsroom_tools.py` - MCP tool definitions
- `mcp_servers/newsroom_http_server.py` - HTTP MCP server
- `utils/mcp_client.py` - MCP client utilities

**User Interfaces:**
- `react-ui/` - Modern React UI with real-time monitoring (port 3001, primary)

**Scripts:**
- `scripts/start_newsroom.sh` - Start/stop all agents + services
- `scripts/start_event_hub.sh` - Start/stop Event Hub
- `scripts/view_logs.py` - Colorized real-time log viewer
- `scripts/create_elasticsearch_index.py` - ES index setup

**Testing:**
- `Makefile` - Convenient test and development commands
- `tests/conftest.py` - Pytest fixtures and configuration
- `tests/test_workflow_pytest.py` - Modern pytest-based tests
- `TESTING.md` - Comprehensive testing documentation

**Utilities:**
- `utils/logging.py` - Centralized logging with color-coded output
- `utils/__init__.py` - Environment config and shared utilities

**Docker:**
- `Dockerfile` - Python agents and services container
- `react-ui/Dockerfile` - React UI container (multi-stage build)
- `docker-compose.yml` - Multi-container orchestration
- `.dockerignore` - Files excluded from Docker build
- `.env.docker` - Environment variable template for Docker
- `scripts/docker_entrypoint.py` - Container startup orchestration

## Configuration

Required environment variables (in `.env`):

```bash
# AI/LLM
ANTHROPIC_API_KEY=sk-ant-api03-xxx

# Elasticsearch (Direct Write Access for Publisher)
ELASTICSEARCH_ENDPOINT=https://[cluster].es.[region].gcp.elastic.cloud:443
ELASTIC_SEARCH_API_KEY=your_es_api_key
ELASTIC_ARCHIVIST_INDEX=news_archive

# Elastic Archivist (Optional - for historical search via Reporter)
ELASTIC_ARCHIVIST_AGENT_URL=https://[kb].kb.[region].gcp.elastic.cloud/api/agent_builder/a2a/archive-agent
ELASTIC_ARCHIVIST_AGENT_CARD_URL=https://[kb].kb.[region].gcp.elastic.cloud/api/agent_builder/a2a/archive-agent.json
ELASTIC_ARCHIVIST_API_KEY=your_archivist_api_key

# MCP Server (REQUIRED - for tool integration)
MCP_SERVER_URL=http://localhost:8095
```

See `env.example` and `docs/configuration-guide.md` for details.

## Important Implementation Notes

### Agent Action Patterns

Each agent accepts JSON requests with an `action` field:

**News Chief (8080):**
- `assign_story` - Assigns story to Reporter
- `get_story_status` - Gets story status by story_id
- `list_active_stories` - Lists all active stories
- `register_reporter` - Registers a reporter

**Reporter (8081):**
- `accept_assignment` - Accepts story from News Chief
- `write_article` - Generates article (calls Researcher + Archivist)
- `submit_draft` - Submits to Editor
- `apply_edits` - Applies Editor feedback
- `publish_article` - Saves markdown file
- `get_status` - Gets assignment status

**Editor (8082):**
- `review_draft` - Reviews article content

**Researcher (8083):**
- `research_questions` - Answers list of research questions

**Publisher (8084):**
- `publish_article` - Indexes to Elasticsearch + saves file

### State Management

- **News Chief**: Maintains `active_stories` dict (singleton pattern via `get_news_chief_agent()`)
- **Reporter**: Maintains `assignments`, `drafts`, `editor_reviews`, `research_data`, `archive_data` dicts
- **Editor**: Maintains `reviews` dict
- **Researcher**: Maintains `research_sessions` dict
- **Publisher**: Stateless (publishes immediately)

State persists in-memory during agent lifetime but is lost on restart.

### Parallel Research + Archive Search

Reporter calls Researcher and Archivist in parallel using `asyncio.gather()`:

```python
import asyncio

researcher_task = self._send_to_researcher(story_id, assignment, questions)
archivist_task = self._send_to_archivist(story_id, assignment)

research_response, archive_response = await asyncio.gather(
    researcher_task,
    archivist_task,
    return_exceptions=True
)
```

See `agents/reporter.py:_write_article()` lines 213-241.

### Automatic Workflow Continuation

The Reporter automatically continues the workflow without user intervention:

1. `write_article` → auto-submits to Editor
2. Editor returns review → auto-applies edits
3. `apply_edits` → auto-sends to Publisher

See `agents/reporter.py:_write_article()` lines 272-316.

### Logging

All agents use centralized logging via `utils/logging.py`:

```python
from utils import setup_logger
logger = setup_logger("AGENT_NAME")
```

Logs go to:
- Console (stdout) with color-coded output per agent
- `logs/{Agent_Name}.log` files

**Color-coded Agent Output:**
- News Chief: Magenta
- Reporter: Cyan
- Editor: Yellow
- Researcher: Green
- Publisher: Bright Magenta
- Archivist Client: Blue
- Event Hub: White
- MCP Server: Black on bright green background

**Viewing Logs:**
```bash
# Recommended: Colorized real-time viewer
make logs-color
python scripts/view_logs.py

# Traditional tail
tail -f logs/*.log
```

UI uses `setup_ui_logger()` for UI-specific formatting.

### Hot Reload

Agents support `--reload` flag for development:

```bash
uvicorn agents.reporter:app --host localhost --port 8081 --reload --reload-dirs=./agents
```
### Timeouts

- Standard A2A calls: 90 seconds
- Archivist calls: 30 seconds (A2A protocol with retry logic)
- News Chief assignment: 60 seconds (quick handoff)

### Error Handling

- Researcher failure: Logged as warning, workflow continues
- Archivist failure: Raises exception, workflow halts (required component)
- Editor failure: Logged as warning, returns draft without edits
- Publisher failure: Logged as error, article not indexed

## Web UIs

### React UI (Primary - Port 3001)
Modern React interface with real-time SSE updates, workflow visualization, and markdown article rendering.

```bash
./scripts/start_newsroom.sh --with-ui  # Start agents + UI
# Or separately: cd react-ui && ./start.sh
# Access at http://localhost:3001
```

**Key Features:** Real-time agent status, live workflow progress, SSE event streaming from Event Hub (port 8090)

## Testing

The project uses pytest for modern, maintainable testing. See [TESTING.md](TESTING.md) for comprehensive documentation.

**Quick Commands:**
```bash
make test              # Fast tests (excludes slow tests)
make test-all          # All tests including slow ones
make test-unit         # Unit tests only
make test-coverage     # Tests with coverage report
```

## Common Development Tasks

### Troubleshooting Docker Deployments

**Container Restart Loop:**
1. Check MCP server health: `curl http://localhost:8095/health`
2. View container logs: `docker-compose logs newsroom-agents`
3. Verify MCP server has `/health` endpoint in code
4. Check health check configuration in docker-compose.yml

**Environment Variables Not Loading:**
1. Verify `.env` file exists: `ls -la .env`
2. Check explicit `env_file` directive in docker-compose.yml
3. Verify variables loaded: `docker exec elastic-news-agents printenv`
4. Rebuild containers: `docker-compose up -d --build`

**Articles Too Short (API Key Not Loaded):**
1. Check ANTHROPIC_API_KEY in `.env`: `grep ANTHROPIC_API_KEY .env`
2. Verify in container: `docker exec elastic-news-agents printenv | grep ANTHROPIC`
3. Ensure `env_file: - .env` is in docker-compose.yml for both services
4. Restart containers: `docker-compose restart`

**Archivist Integration Failing:**
1. Verify `ELASTIC_ARCHIVIST_AGENT_URL` in `.env` (not just AGENT_CARD_URL)
2. Check URL format includes `/api/agent_builder/`
3. Test API key: `curl -H "Authorization: ApiKey $ELASTIC_ARCHIVIST_API_KEY" $ELASTIC_ARCHIVIST_AGENT_URL`
4. View Reporter logs: `docker-compose logs newsroom-agents | grep Reporter`

### Adding a New Agent

1. Create `agents/new_agent.py` following the A2A pattern
2. Define `AgentCard` with skills and capabilities
3. Implement `invoke(query)` method with JSON actions
4. Create `AgentExecutor` wrapper
5. Add to `scripts/start_newsroom.sh` agent list
6. Add to `scripts/docker_entrypoint.py` AGENTS list (for Docker)
7. Update this CLAUDE.md

### Modifying Agent Actions

1. Add action handler to agent's `invoke()` method
2. Update `AgentSkill` in `create_agent_card()`
3. Update caller agents to use new action
4. Update tests if needed

### Adding MCP Tools

1. Add tool function to `mcp_servers/newsroom_tools.py` with `@mcp.tool()` decorator
2. Implement tool logic (may use Anthropic API for AI tasks)
3. Update agents to call new tool via `utils/mcp_client.py`
4. Add fallback behavior if MCP unavailable
5. Test tool in isolation before integration

### Adding New Research Questions

Modify `agents/reporter.py:_generate_outline_and_questions()` prompt to include different question types.

### Changing Article Format

Modify `agents/reporter.py:_generate_article()` prompt to adjust article structure.

### Adding New Editor Checks

Modify `agents/editor.py:_review_article()` prompt to include additional review criteria.

## Reference Materials

**Project Documentation:**
- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Docker deployment guide
- [docs/architecture.md](docs/architecture.md) - Detailed A2A/MCP/Archivist architecture
- [docs/code-patterns.md](docs/code-patterns.md) - Code optimization patterns
- [docs/configuration-guide.md](docs/configuration-guide.md) - Environment setup
- [docs/elasticsearch-schema.md](docs/elasticsearch-schema.md) - Index mapping
- [docs/archivist-integration.md](docs/archivist-integration.md) - Archivist setup

**External Resources:**
- **A2A SDK**: https://github.com/a2aproject/a2a-python
- **A2A Samples**: https://github.com/a2aproject/a2a-samples
- **Elastic Agent Builder A2A**: https://www.elastic.co/docs/solutions/search/agent-builder/a2a-server
- **Pytest Docs**: https://docs.pytest.org/

## Development Workflow

### Quick Start for Development
```bash
# 1. Start all agents with hot reload + React UI + colorized logs
make start-logs

# 2. In another terminal, check agent health
make status

# 3. Run tests
make test              # Fast tests
make test-all          # All tests including slow ones

# 4. Stop everything
make stop
```

### Monitoring and Debugging

**Real-time Log Viewing:**
```bash
make logs-color        # Colorized logs (recommended)
python scripts/view_logs.py
```

**Agent Health:**
```bash
make status            # Check all agent health
curl http://localhost:8080/.well-known/agent-card.json  # Specific agent
curl http://localhost:8095/health  # MCP server health (returns JSON)
```

**Docker Health Checks:**
```bash
# Check container health status
docker-compose ps
# Both containers should show "(healthy)"

# Verify environment variables loaded
docker exec elastic-news-agents printenv | grep -E "ANTHROPIC|ELASTIC_ARCHIVIST_AGENT_URL|MCP_SERVER"

# Check MCP health endpoint
curl http://localhost:8095/health
# Expected: {"status": "healthy", "service": "Newsroom MCP HTTP Server"}
```

**Event Hub Monitoring:**
```bash
# Watch SSE stream
curl -N http://localhost:8090/stream

# Check health
curl http://localhost:8090/health
```

**Makefile Commands:**
```bash
make help              # Show all commands
make test              # Fast tests
make test-coverage     # Tests with coverage report
make start             # Start agents with reload
make start-ui          # Start agents + React UI
make start-logs        # Start everything + show logs
make stop              # Stop all services
make clean             # Clean up generated files
make logs              # View plain logs
make logs-color        # View colorized logs
make status            # Check agent health
```


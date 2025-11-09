# CrewAI Researcher Agent

A standalone research agent powered by the CrewAI framework, providing factual information, background context, and supporting data for news articles in the Elastic Newsroom.

## Overview

The CrewAI Researcher replaces the original A2A-based researcher with a modern multi-agent framework while maintaining full backward compatibility through an A2A protocol bridge.

**Key Features:**
- CrewAI-based multi-agent architecture
- FastAPI HTTP server
- A2A protocol compatibility
- Event Hub integration for real-time monitoring
- MCP tool integration
- Docker-ready deployment

## Architecture

```
Reporter Agent (A2A)
    ↓
HTTP Request → FastAPI Server (port 8083)
    ├── A2A Protocol Bridge (/a2a/tasks)
    └── Native CrewAI Endpoints (/research)
        ↓
    ResearcherCrew
        ├── ChatAnthropic LLM (Claude Sonnet 4)
        ├── Research Tools (research_questions_tool)
        └── CrewAI Agents & Tasks
        ↓
    Research Results → Event Hub → UI
```

## Components

### Core Files

```
crewai_agents/researcher_crew/
├── main.py              # FastAPI server with HTTP endpoints
├── crew.py              # ResearcherCrew class (orchestration)
├── agents.py            # CrewAI agent definitions
├── tasks.py             # CrewAI task definitions
├── tools.py             # CrewAI tool definitions
├── config/
│   ├── agents.yaml      # Agent configurations
│   └── tasks.yaml       # Task configurations
├── tests/               # Unit tests (contained)
│   ├── test_crew.py
│   ├── test_main.py
│   ├── test_shared_utilities.py
│   └── conftest.py
└── README.md            # This file
```

### Shared Utilities

```
crewai_agents/shared/
├── event_hub_client.py  # Event Hub integration
├── a2a_bridge.py        # A2A protocol utilities
└── README.md            # Shared utilities documentation
```

## Installation & Setup

### Requirements

```bash
# Core dependencies (in requirements.txt)
crewai>=0.80.0
crewai-tools>=0.12.0
langchain-anthropic>=0.1.0
anthropic>=0.18.0
fastapi
uvicorn
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-xxx

# Optional (defaults shown)
MCP_SERVER_URL=http://localhost:8095
EVENT_HUB_URL=http://localhost:8090
EVENT_HUB_ENABLED=true
```

## Running the Agent

### Local Development

```bash
# Direct execution
python -m crewai_agents.researcher_crew.main

# With custom host/port
python -m crewai_agents.researcher_crew.main --host 0.0.0.0 --port 8083

# With hot reload
python -m crewai_agents.researcher_crew.main --reload
```

### Docker

```bash
# Build and start (with docker-compose)
docker-compose up -d researcher-crew

# View logs
docker-compose logs -f researcher-crew

# Restart
docker-compose restart researcher-crew

# Stop
docker-compose down researcher-crew
```

### Testing

```bash
# Run all tests
pytest crewai_agents/researcher_crew/tests/ -v

# Run with coverage
pytest crewai_agents/researcher_crew/tests/ --cov=crewai_agents.researcher_crew

# Run specific test file
pytest crewai_agents/researcher_crew/tests/test_crew.py -v
```

## API Endpoints

### Native CrewAI Endpoints

#### `POST /research` - Research Questions
```bash
curl -X POST http://localhost:8083/research \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "story_123",
    "topic": "Artificial Intelligence",
    "questions": [
      "What percentage of companies use AI?",
      "Who are the leading AI companies?"
    ]
  }'

# Response
{
  "status": "success",
  "research_id": "research_story_123_20251109_120000",
  "story_id": "story_123",
  "research_results": [
    {
      "question": "What percentage of companies use AI?",
      "claim_verified": true,
      "confidence": 85,
      "summary": "45% of companies use AI...",
      "facts": [...],
      "figures": {...},
      "sources": [...]
    }
  ],
  "total_questions": 2
}
```

#### `GET /status` - Get Status
```bash
curl http://localhost:8083/status

# Response
{
  "status": "success",
  "total_research_requests": 5,
  "research_history": [...]
}
```

#### `POST /history` - Get Research History
```bash
curl -X POST http://localhost:8083/history \
  -H "Content-Type: application/json" \
  -d '{"story_id": "story_123"}'
```

#### `GET /health` - Health Check
```bash
curl http://localhost:8083/health

# Response
{
  "status": "healthy",
  "service": "CrewAI Researcher",
  "implementation": "crewai",
  "version": "1.0.0"
}
```

### A2A Protocol Endpoints

#### `GET /.well-known/agent-card.json` - Agent Discovery
```bash
curl http://localhost:8083/.well-known/agent-card.json

# Returns A2A agent card for service discovery
```

#### `POST /a2a/tasks` - A2A Task Execution
```bash
curl -X POST http://localhost:8083/a2a/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "research_questions",
      "story_id": "story_123",
      "topic": "AI",
      "questions": ["What is AI?"]
    }
  }'

# Response (A2A JSONRPC format)
{
  "jsonrpc": "2.0",
  "result": {
    "parts": [{
      "text": "{\"status\": \"success\", ...}"
    }]
  }
}
```

## Usage Examples

### Research Questions

```python
from crewai_agents.researcher_crew.crew import ResearcherCrew

# Initialize crew
crew = ResearcherCrew()

# Research questions
result = await crew.research_questions(
    questions=[
        "What percentage of companies use AI?",
        "Who are the leading AI companies?"
    ],
    topic="Artificial Intelligence",
    story_id="story_123"
)

print(result["research_results"])
```

### Event Hub Integration

```python
from crewai_agents.shared.event_hub_client import EventHubClient

# Initialize client
event_hub = EventHubClient(
    event_hub_url="http://localhost:8090",
    enabled=True
)

# Publish event
await event_hub.publish_research_started(
    story_id="story_123",
    topic="AI in Journalism",
    question_count=5
)
```

## Configuration

### Agent Configuration (`config/agents.yaml`)

```yaml
researcher:
  role: Research Specialist
  goal: Gather accurate factual information...
  verbose: true
  max_iter: 10
  memory: true
```

### Task Configuration (`config/tasks.yaml`)

```yaml
research_questions:
  description: Research the provided questions...
  expected_output: A JSON array containing research results...
```

## Integration with Newsroom

### Reporter Agent Integration

The Reporter agent calls the researcher via A2A protocol:

```python
# In agents/reporter.py
async def _send_to_researcher(self, story_id, assignment, questions):
    async with httpx.AsyncClient() as http_client:
        # Discover researcher at http://localhost:8083
        researcher_client, _ = await self._create_a2a_client(
            http_client,
            self.researcher_url,
            "Researcher"
        )

        # Send research request
        request = {
            "action": "research_questions",
            "story_id": story_id,
            "topic": assignment.get("topic"),
            "questions": questions
        }

        message = create_text_message_object(content=json.dumps(request))
        result = await self._parse_a2a_response(researcher_client, message)
```

**No changes needed** - Reporter works transparently with CrewAI researcher.

### Event Hub Monitoring

The CrewAI researcher publishes events to the Event Hub:

- `research_started` - Research begins
- `research_completed` - Research succeeds
- `research_error` - Research fails

React UI subscribes to these events for real-time monitoring.

## Development

### Adding New Tools

```python
# In tools.py
from crewai_tools import tool

@tool("New Research Tool")
def new_research_tool(query: str) -> str:
    """Tool description"""
    # Implementation
    return result
```

### Adding New Agents

```python
# In agents.py
def create_new_agent(tools, llm) -> Agent:
    return Agent(
        role="New Role",
        goal="New goal",
        tools=tools,
        llm=llm
    )
```

### Adding New Tasks

```python
# In tasks.py
def create_new_task(agent, ...) -> Task:
    return Task(
        description="Task description",
        agent=agent,
        expected_output="Expected output format"
    )
```

## Troubleshooting

### Health Check Fails

```bash
# Check if service is running
docker-compose ps researcher-crew

# View logs
docker-compose logs researcher-crew

# Check endpoint
curl http://localhost:8083/health
```

### Reporter Can't Connect

```bash
# Verify port 8083 is accessible
curl http://localhost:8083/.well-known/agent-card.json

# Check Docker networking
docker exec elastic-news-reporter curl http://researcher-crew:8083/health
```

### Research Returns Mock Data

```bash
# Verify ANTHROPIC_API_KEY is set
docker exec elastic-news-researcher-crew printenv | grep ANTHROPIC

# Check MCP server is running
curl http://localhost:8095/health
```

## Performance

- **Startup Time**: ~2-3 seconds
- **Research Request**: ~10-30 seconds (depends on question complexity)
- **Concurrent Requests**: Up to 30 (configurable)
- **Memory Usage**: ~200-300 MB
- **Docker Image Size**: ~500 MB

## Security

- **API Key**: ANTHROPIC_API_KEY required, stored in environment variables
- **Network**: Isolated Docker network for internal communication
- **Ports**: Only 8083 exposed to host
- **CORS**: Configured for localhost:3000 and localhost:3001 only

## Migration from A2A Researcher

### Compatibility

| Feature | A2A Researcher | CrewAI Researcher | Compatible? |
|---------|---------------|-------------------|-------------|
| Port | 8083 | 8083 | ✅ Yes |
| Protocol | A2A JSONRPC | A2A + HTTP | ✅ Yes |
| Actions | research_questions | Same + more | ✅ Yes |
| Response Format | JSON | JSON | ✅ Yes |
| Event Hub | Yes | Yes | ✅ Yes |

### Migration Steps

1. **Deploy CrewAI researcher** (docker-compose up researcher-crew)
2. **Verify health check** (curl http://localhost:8083/health)
3. **Test with Reporter** (run full workflow test)
4. **Monitor Event Hub** (check real-time events in UI)
5. **Remove A2A researcher** (already done in docker-compose.yml)

### Rollback

```bash
# Stop CrewAI researcher
docker-compose down researcher-crew

# Re-enable A2A researcher in docker-compose.yml
# Uncomment port 8083 in newsroom-agents service

# Restart
docker-compose up -d
```

## Support

- **Documentation**: See this README and `/crewai_agents/shared/README.md`
- **Tests**: Run `pytest crewai_agents/researcher_crew/tests/ -v`
- **Logs**: `docker-compose logs -f researcher-crew`
- **Issues**: Check PHASE_REPORTS.md for implementation details

## License

Same as Elastic Newsroom project.

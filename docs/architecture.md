# Elastic News Architecture

Detailed technical architecture documentation for the Elastic News multi-agent system.

## A2A Agent Pattern

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

## Agent Communication (A2A Protocol)

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

## Archivist Integration (A2A Protocol)

The Reporter calls the Archivist via A2A protocol with JSONRPC 2.0.

### Endpoint

`POST https://[kb-url]/api/agent_builder/a2a/{agent-id}`

### Headers

- `Authorization: ApiKey {ELASTIC_ARCHIVIST_API_KEY}`
- `Content-Type: application/json`

### Request Format

```json
{
  "id": "msg-1760114787061-m2jcmx471",
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "configuration": {
      "acceptedOutputModes": ["text/plain", "video/mp4"]
    },
    "message": {
      "kind": "message",
      "messageId": "msg-1760114787061-m2jcmx471",
      "metadata": {},
      "parts": [
        {
          "kind": "text",
          "text": "Find articles about AI in healthcare."
        }
      ],
      "role": "user"
    }
  }
}
```

### Important Notes

- `messageId` must be unique for each request (uses timestamp + story_id)
- Timeout: 30 seconds (may take time to process)
- Retry logic: Up to 3 attempts if response is empty (`""`)
- Response structure: JSONRPC 2.0 result with `parts` array containing text responses

### About the Archivist

The Archivist is an agent created in Elastic Cloud using Agent Builder and exposed via the A2A protocol. It searches historical articles stored in the `news_archive` Elasticsearch index.

For details on creating your own A2A-enabled agent in Elastic and finding your agent card URL, see the [Elastic Agent Builder A2A documentation](https://www.elastic.co/docs/solutions/search/agent-builder/a2a-server).

**Implementation:** See `agents/reporter.py:_send_to_archivist()` (lines 434-645)

## MCP (Model Context Protocol) Integration

The newsroom uses MCP to expose reusable tools that agents can call.

### MCP Server

**Location:** `mcp_servers/newsroom_tools.py`

**Available Tools:**
1. `research_questions` - Answers research questions with structured data (uses Anthropic)
2. `generate_outline` - Creates article outline and identifies research needs (uses Anthropic)
3. `generate_article` - Creates article content from outline and research (uses Anthropic)
4. `apply_edits` - Applies editorial suggestions to article (uses Anthropic)
5. `review_article` - Reviews draft for grammar, tone, consistency (uses Anthropic)
6. `generate_tags` - Generates tags and categories for article (keyword extraction)
7. `deploy_to_production` - Simulates CI/CD deployment pipeline (mock)
8. `notify_subscribers` - Simulates CRM subscriber notification (mock)

### Starting MCP Server

```bash
# MCP server starts automatically with agents via start_newsroom.sh
# Or start manually:
python -m mcp_servers.newsroom_http_server
```

### Configuration

- Set `MCP_SERVER_URL` in `.env` (e.g., `http://localhost:8095`)
- MCP server is **REQUIRED** - all agents will fail if MCP is not running
- See `utils/mcp_client.py` for client implementation

### MCP is Mandatory

The MCP server is absolutely required for all agent operations. If the MCP server is not running:
- Agents will fail with clear error messages
- Error messages include instructions to start the MCP server
- No fallback mechanism exists - this is intentional

### MCP Client Design

The MCP client supports two modes of operation:
1. **Direct tool calling** via `call_tool()` - Works without Anthropic client
2. **LLM-based tool selection** via `select_and_call_tool()` - Requires Anthropic client

The Anthropic client is optional for MCP (allows direct tool calls without LLM), but the MCP server itself is mandatory.

## Event Hub (Real-time Updates)

The Event Hub broadcasts agent events to connected UI clients via Server-Sent Events (SSE).

### Features

- SSE endpoint at `http://localhost:8090/stream` for real-time client updates
- Event buffering for clients that reconnect (max 1000 events)
- Story-specific event filtering via `story_id`
- Health check endpoint at `/health`

### Architecture

- Agents POST events to `/events` endpoint
- UI clients connect to `/stream` for real-time updates
- Events are broadcast to all connected clients
- Optional `story_id` filtering for targeted updates

### Starting Event Hub

```bash
./scripts/start_event_hub.sh              # Normal start
./scripts/start_event_hub.sh --reload     # With hot reload
./scripts/start_event_hub.sh --stop       # Stop service
```

### Event Format

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

**Implementation:** See `services/event_hub.py`

## State Management

### In-Memory State

- **News Chief**: Maintains `active_stories` dict (singleton pattern via `get_news_chief_agent()`)
- **Reporter**: Maintains `assignments`, `drafts`, `editor_reviews`, `research_data`, `archive_data` dicts
- **Editor**: Maintains `reviews` dict
- **Researcher**: Maintains `research_sessions` dict
- **Publisher**: Stateless (publishes immediately)

**Note:** State persists in-memory during agent lifetime but is lost on restart.

## Parallel Processing

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

## Automatic Workflow Continuation

The Reporter automatically continues the workflow without user intervention:

1. `write_article` → auto-submits to Editor
2. Editor returns review → auto-applies edits
3. `apply_edits` → auto-sends to Publisher

See `agents/reporter.py:_write_article()` lines 272-316.

## Timeouts

- Standard A2A calls: 90 seconds
- Archivist calls: 30 seconds (A2A protocol with retry logic)
- News Chief assignment: 60 seconds (quick handoff)

## Error Handling

- **Researcher failure**: Logged as warning, workflow continues
- **Archivist failure**: Raises exception, workflow halts (required component)
- **Editor failure**: Logged as warning, returns draft without edits
- **Publisher failure**: Logged as error, article not indexed

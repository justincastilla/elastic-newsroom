# Shared Utilities for CrewAI Agents

This directory contains shared utilities used across all CrewAI-based agents in the Elastic Newsroom.

## Modules

### `event_hub_client.py`
Client for publishing events to the central Event Hub for real-time UI updates.

**Features:**
- Async event publishing via HTTP
- Silent failures (doesn't break agent execution)
- Structured event format
- Story-specific event filtering
- Convenience methods for common events

**Usage:**
```python
from crewai_agents.shared.event_hub_client import EventHubClient

# Initialize client
event_hub = EventHubClient(
    event_hub_url="http://localhost:8090",
    enabled=True
)

# Publish event
await event_hub.publish_event(
    agent_name="ResearcherCrew",
    event_type="research_started",
    story_id="story_123",
    data={"topic": "AI in Journalism", "question_count": 5}
)

# Or use convenience methods
await event_hub.publish_research_started(
    story_id="story_123",
    topic="AI in Journalism",
    question_count=5
)
```

### `a2a_bridge.py`
Utilities for bridging A2A JSONRPC protocol to CrewAI HTTP/JSON.

**Features:**
- Parse A2A requests to CrewAI format
- Format CrewAI responses as A2A JSONRPC
- Create A2A agent cards
- Validate A2A requests

**Usage:**
```python
from crewai_agents.shared.a2a_bridge import (
    parse_a2a_request,
    format_a2a_response,
    create_a2a_agent_card
)

# Parse A2A request
parsed = parse_a2a_request(a2a_message)
action = parsed["action"]
params = parsed["params"]

# Call CrewAI agent
result = await crew.research_questions(**params)

# Format as A2A response
a2a_response = format_a2a_response(result)
```

## Architecture

### Event Hub Integration

```
CrewAI Agent → EventHubClient → Event Hub (SSE) → React UI
```

Events are published asynchronously and failures do not affect agent operation.

### A2A Protocol Bridge

```
A2A Agent (Reporter) → HTTP Request → FastAPI (/a2a/tasks)
                                          ↓
                                    parse_a2a_request()
                                          ↓
                                    CrewAI Agent
                                          ↓
                                    format_a2a_response()
                                          ↓
                                    HTTP Response → A2A Agent
```

The bridge translates between A2A JSONRPC and CrewAI HTTP/JSON.

## Environment Variables

```bash
# Event Hub Configuration
EVENT_HUB_URL=http://localhost:8090
EVENT_HUB_ENABLED=true

# MCP Server (for tools)
MCP_SERVER_URL=http://localhost:8095

# Anthropic API (for LLM)
ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

## Testing

```python
import pytest
from crewai_agents.shared.event_hub_client import EventHubClient
from crewai_agents.shared.a2a_bridge import parse_a2a_request, format_a2a_response

@pytest.mark.asyncio
async def test_event_hub_client():
    client = EventHubClient(enabled=False)  # Disabled for testing
    result = await client.publish_event(
        agent_name="Test",
        event_type="test_event",
        story_id="test_123"
    )
    assert result == False  # Disabled, so returns False

def test_a2a_bridge():
    # Test parsing
    a2a_msg = {
        "input": {
            "action": "research_questions",
            "story_id": "story_123"
        }
    }
    parsed = parse_a2a_request(a2a_msg)
    assert parsed["action"] == "research_questions"

    # Test formatting
    result = {"status": "success", "data": "test"}
    a2a_response = format_a2a_response(result)
    assert a2a_response["jsonrpc"] == "2.0"
    assert "result" in a2a_response
```

## Design Principles

1. **No Code Bloat**: Only essential utilities, no unnecessary abstractions
2. **Silent Failures**: Event Hub failures don't break agent execution
3. **Type Safety**: Type hints throughout
4. **Documentation**: Comprehensive docstrings
5. **Testability**: Easy to test in isolation

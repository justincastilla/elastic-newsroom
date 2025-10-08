# News Chief Agent

## Overview

The News Chief is a coordinator agent that manages the newsroom workflow by assigning stories to reporter agents, tracking story status, and managing reporter availability.

**Agent Type**: Coordinator
**Protocol**: A2A (Agent-to-Agent)
**Transport**: JSON-RPC
**Version**: 1.0.0

## Agent Card

- **URL**: `http://localhost:8080` (default)
- **Agent Card Endpoint**: `/.well-known/agent-card.json`
- **Documentation**: https://github.com/elastic/elastic-news/blob/main/docs/news-chief-agent.md

## Capabilities

| Capability | Supported | Details |
|------------|-----------|---------|
| Streaming | ❌ No | Non-streaming responses only |
| Push Notifications | ✅ Yes | Supports A2A push notifications |
| State Transition History | ✅ Yes | Tracks task state changes |
| Max Concurrent Tasks | 50 | Can handle up to 50 concurrent tasks |

## Skills

### 1. Story Assignment (`newsroom.coordination.story_assignment`)

Assigns stories to reporter agents and coordinates the workflow.

**Input Modes**: `application/json`
**Output Modes**: `application/json`

**Example Requests**:

```json
{
  "action": "assign_story",
  "story": {
    "topic": "Renewable Energy Adoption",
    "angle": "Focus on solar panel installations",
    "target_length": 1200,
    "priority": "high",
    "deadline": "2025-10-08T18:00:00Z"
  }
}
```

**Response**:

```json
{
  "status": "success",
  "message": "Story 'Renewable Energy Adoption' assigned successfully",
  "story_id": "story_20251007_113441",
  "assignment": {
    "story_id": "story_20251007_113441",
    "topic": "Renewable Energy Adoption",
    "angle": "Focus on solar panel installations",
    "target_length": 1200,
    "deadline": "2025-10-08T18:00:00Z",
    "priority": "high",
    "assigned_to": "reporter_001",
    "status": "assigned",
    "created_at": "2025-10-07T11:34:41.123456",
    "updated_at": "2025-10-07T11:34:41.123456"
  }
}
```

**Validation Rules**:
- `topic` (required): Non-empty string
- `target_length` (optional): Positive integer, defaults to 1000
- `priority` (optional): One of `["low", "normal", "high", "urgent"]`, defaults to "normal"
- `angle` (optional): String
- `deadline` (optional): ISO 8601 datetime string

### 2. Story Status (`newsroom.coordination.story_status`)

Retrieves the status of assigned stories.

**Input Modes**: `application/json`
**Output Modes**: `application/json`

**Example Request - Get Single Story**:

```json
{
  "action": "get_story_status",
  "story_id": "story_20251007_113441"
}
```

**Response**:

```json
{
  "status": "success",
  "story": {
    "story_id": "story_20251007_113441",
    "topic": "Renewable Energy Adoption",
    "angle": "Focus on solar panel installations",
    "target_length": 1200,
    "deadline": "2025-10-08T18:00:00Z",
    "priority": "high",
    "assigned_to": "reporter_001",
    "status": "assigned",
    "created_at": "2025-10-07T11:34:41.123456",
    "updated_at": "2025-10-07T11:34:41.123456"
  }
}
```

**Example Request - List All Stories**:

```json
{
  "action": "list_active_stories"
}
```

**Response**:

```json
{
  "status": "success",
  "stories": [
    {
      "story_id": "story_20251007_113441",
      "topic": "Renewable Energy Adoption",
      "status": "assigned",
      "assigned_to": "reporter_001",
      "priority": "high",
      "created_at": "2025-10-07T11:34:41.123456"
    }
  ],
  "total_count": 1
}
```

### 3. Reporter Management (`newsroom.coordination.reporter_management`)

Manages reporter registration and availability.

**Input Modes**: `application/json`
**Output Modes**: `application/json`

**Example Request**:

```json
{
  "action": "register_reporter",
  "reporter_id": "reporter_001"
}
```

**Response**:

```json
{
  "status": "success",
  "message": "Reporter reporter_001 registered successfully",
  "available_reporters": ["reporter_001"]
}
```

## Story Lifecycle

```
┌─────────────┐
│   pending   │  Story created but no reporters available
└──────┬──────┘
       │
       ↓ Reporter available
┌─────────────┐
│  assigned   │  Story assigned to a reporter
└──────┬──────┘
       │
       ↓ Reporter working (future)
┌─────────────┐
│ in_progress │  Reporter is actively working on the story
└──────┬──────┘
       │
       ↓ Draft completed (future)
┌─────────────┐
│   review    │  Story in editorial review
└──────┬──────┘
       │
       ↓ Approved (future)
┌─────────────┐
│  published  │  Story published
└─────────────┘
```

**Current Implementation**: Only supports `pending` and `assigned` states.

## Error Handling

### Error Response Format

```json
{
  "status": "error",
  "message": "Description of the error"
}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No story data provided" | Empty or missing `story` object | Include story object with required fields |
| "Story topic is required" | Missing or empty `topic` field | Provide a non-empty topic string |
| "Invalid target_length: must be a positive integer" | Invalid target_length value | Use a positive integer for target_length |
| "Invalid priority: must be one of [...]" | Invalid priority value | Use one of: low, normal, high, urgent |
| "No story_id provided" | Missing story_id parameter | Include story_id in the request |
| "Story {id} not found" | Story doesn't exist | Verify the story_id is correct |
| "No reporter_id provided" | Missing reporter_id parameter | Include reporter_id in the request |

## Integration Example

### Python with A2A Client

```python
import asyncio
import json
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver, create_text_message_object
import httpx

async def assign_story():
    async with httpx.AsyncClient() as http_client:
        # Discover agent
        card_resolver = A2ACardResolver(http_client, "http://localhost:8080")
        agent_card = await card_resolver.get_agent_card()

        # Create client
        client_config = ClientConfig(httpx_client=http_client, streaming=False)
        client_factory = ClientFactory(client_config)
        client = client_factory.create(agent_card)

        # Prepare request
        request = {
            "action": "assign_story",
            "story": {
                "topic": "AI in Journalism",
                "priority": "high",
                "target_length": 1500
            }
        }

        # Send message
        message = create_text_message_object(content=json.dumps(request))
        async for response in client.send_message(message):
            if hasattr(response, 'parts'):
                result = json.loads(response.parts[0].root.text)
                print(f"Story assigned: {result['story_id']}")

asyncio.run(assign_story())
```

## Architecture

### Component Diagram

```
┌───────────────────────────────────────┐
│         News Chief Agent              │
├───────────────────────────────────────┤
│                                       │
│  ┌─────────────────────────────────┐ │
│  │   NewsChiefAgent                │ │
│  │   (Plain Python Class)          │ │
│  │                                 │ │
│  │   - active_stories: Dict        │ │
│  │   - available_reporters: List   │ │
│  │                                 │ │
│  │   + invoke(query) -> Dict       │ │
│  └─────────────────────────────────┘ │
│                ↑                      │
│                │                      │
│  ┌─────────────────────────────────┐ │
│  │   NewsChiefAgentExecutor        │ │
│  │   (extends AgentExecutor)       │ │
│  │                                 │ │
│  │   + execute(context, queue)     │ │
│  │   + cancel(context, queue)      │ │
│  └─────────────────────────────────┘ │
│                ↑                      │
│                │                      │
│  ┌─────────────────────────────────┐ │
│  │   A2AStarletteApplication       │ │
│  │   (A2A SDK Server)              │ │
│  │                                 │ │
│  │   - DefaultRequestHandler       │ │
│  │   - InMemoryTaskStore           │ │
│  └─────────────────────────────────┘ │
└───────────────────────────────────────┘
```

### Data Flow

```
Client Request
     ↓
A2AStarletteApplication
     ↓
DefaultRequestHandler
     ↓
NewsChiefAgentExecutor.execute()
     ↓
NewsChiefAgent.invoke()
     ↓
Action Methods (_assign_story, _get_story_status, etc.)
     ↓
Response (JSON)
     ↓
Client
```

## Future Enhancements

### Planned Features
- Integration with Reporter agents for bidirectional communication
- Story workflow state machine with transitions
- Deadline monitoring and alerts
- Story priority queue management
- Integration with Elasticsearch for story archival
- Metrics and telemetry with Elastic APM
- Multi-tenant support for multiple newsrooms

### Breaking Changes
None planned for v1.x

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/elastic/elastic-news/issues
- Documentation: See `/docs` folder
- Test Suite: Run `python test_news_chief.py`

## Version History

### v1.0.0 (2025-10-07)
- Initial release
- Story assignment functionality
- Reporter registration
- Story status tracking
- Input validation
- A2A protocol compliance

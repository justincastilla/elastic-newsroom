# News Chief Agent

## Overview

The News Chief is the **coordinator agent** that orchestrates the entire newsroom workflow. It assigns stories to specialized agents and tracks their progress through the publishing pipeline.

## Agent Details

**Name:** News Chief  
**Port:** 8080  
**URL:** `http://localhost:8080`  
**Protocol Version:** A2A SDK v0.3.8  
**Transport:** JSONRPC  

## Capabilities

- **Streaming:** No
- **Push Notifications:** Yes
- **State Transition History:** Yes
- **Max Concurrent Tasks:** 50

## Skills

### 1. Story Assignment (`newsroom.coordination.story_assignment`)

Assigns stories to reporter agents and coordinates workflow.

**Tags:** `coordination`, `story-assignment`

**Example Requests:**
```json
{
  "action": "assign_story",
  "story": {
    "topic": "Renewable Energy Adoption",
    "priority": "high"
  }
}
```

Or simple text:
```
Assign a story about climate change
```

**Response:**
```json
{
  "status": "assigned",
  "story_id": "story_20250107_120000",
  "message": "Story assigned to Reporter",
  "assignment": {
    "story_id": "story_20250107_120000",
    "topic": "Renewable Energy Adoption",
    "priority": "high",
    "target_length": 1000,
    "reporter_status": "accepted"
  }
}
```

### 2. Story Status (`newsroom.coordination.story_status`)

Retrieves the status of assigned stories.

**Tags:** `coordination`, `status`

**Example Request:**
```json
{
  "action": "get_story_status",
  "story_id": "story_123"
}
```

**Response:**
```json
{
  "status": "success",
  "story_id": "story_123",
  "story_status": {
    "story_id": "story_123",
    "topic": "...",
    "status": "writing",
    "assigned_at": "2025-01-07T12:00:00",
    "updated_at": "2025-01-07T12:15:00"
  }
}
```

### 3. List Active Stories (`newsroom.coordination.list_active`)

Returns all stories currently in progress.

**Tags:** `coordination`, `reporting`

**Example Request:**
```json
{
  "action": "list_active_stories"
}
```

**Response:**
```json
{
  "status": "success",
  "active_stories": [
    {
      "story_id": "story_123",
      "topic": "...",
      "status": "writing",
      "assigned_at": "2025-01-07T12:00:00"
    }
  ],
  "total_count": 1
}
```

### 4. Register Reporter (`newsroom.coordination.register_reporter`)

Registers a reporter agent for story assignments.

**Tags:** `coordination`, `registration`

**Example Request:**
```json
{
  "action": "register_reporter",
  "reporter_url": "http://localhost:8081"
}
```

## Workflow

```
News Chief
    │
    ├─► Assigns story to Reporter
    │   └─► Reporter accepts assignment
    │
    └─► Tracks story status through pipeline
        ├─ Writing (Reporter)
        ├─ Research (Researcher)
        ├─ Review (Editor)
        └─ Publication (Publisher)
```

## Integration with Other Agents

### Reporter Agent
- **URL:** `http://localhost:8081`
- **Interaction:** News Chief sends story assignments via A2A protocol
- **Skill Used:** `article.writing.accept_assignment`

### Communication Protocol

News Chief uses the official A2A SDK for agent-to-agent communication:

1. **Discovery:** Fetches Reporter's agent card from `.well-known/agent-card.json`
2. **Client Creation:** Creates A2A client using `ClientFactory`
3. **Message Sending:** Sends assignment as structured JSON message
4. **Response Handling:** Processes Reporter's acceptance/rejection response

## Configuration

### Environment Variables

```bash
# Default Reporter URL (optional)
REPORTER_URL=http://localhost:8081
```

### Port Configuration

The News Chief runs on port 8080 by default. This can be changed when starting the agent:

```bash
uvicorn agents.news_chief:app --host localhost --port 8080
```

## Running the Agent

### Start via Script
```bash
./start_newsroom.sh
```

### Start Individually
```bash
uvicorn agents.news_chief:app --host localhost --port 8080
```

### Start with Hot Reload (Development)
```bash
uvicorn agents.news_chief:app --host localhost --port 8080 --reload
```

## Agent Card

Access the agent card at:
```
http://localhost:8080/.well-known/agent-card.json
```

## Logging

Logs are written to `newsroom.log` with the `[NEWS_CHIEF]` prefix.

Example log output:
```
2025-01-07 12:00:00 [NEWS_CHIEF] INFO: 📥 Received query: {"action": "assign_story", ...
2025-01-07 12:00:00 [NEWS_CHIEF] INFO: 🎯 Action: assign_story
2025-01-07 12:00:01 [NEWS_CHIEF] INFO: 🔍 Discovering Reporter agent at http://localhost:8081
2025-01-07 12:00:02 [NEWS_CHIEF] INFO: ✅ Found Reporter: Reporter (v1.0.0)
```

## Error Handling

### Invalid Action
```json
{
  "status": "error",
  "message": "Unknown action: invalid_action",
  "available_actions": [
    "assign_story",
    "get_story_status",
    "list_active_stories",
    "register_reporter"
  ]
}
```

### Missing Story Data
```json
{
  "status": "error",
  "message": "No story data provided"
}
```

### Reporter Unavailable
```json
{
  "status": "error",
  "message": "Failed to contact Reporter: Connection refused"
}
```

## Testing

The News Chief is tested as part of the end-to-end workflow:

```bash
python tests/test_newsroom_workflow.py
```

Expected output:
```
✅ NEWS CHIEF: Story assigned successfully
   Story ID: story_20250107_120000
   Topic: AI Agents Transform Modern Newsrooms
```

## Best Practices

1. **Story Topics:** Provide clear, specific topics for better article quality
2. **Priority Levels:** Use `high`, `medium`, or `low` to guide urgency
3. **Target Length:** Specify word count for appropriate article depth
4. **Status Monitoring:** Check story status regularly for workflow visibility

## Future Enhancements

1. **Multiple Reporters:** Load balancing across multiple reporter agents
2. **Story Queue:** Priority-based story assignment queue
3. **Deadline Tracking:** Story deadline monitoring and alerts
4. **Performance Metrics:** Story completion time and quality metrics

# Reporter Agent

## Overview

The Reporter Agent is responsible for **writing news articles** based on story assignments from the News Chief. It uses AI-powered content generation (Claude Sonnet 4) and coordinates with the Researcher and Archivist agents to gather comprehensive information before writing.

## Agent Details

**Name:** Reporter  
**Port:** 8081  
**URL:** `http://localhost:8081`  
**Protocol Version:** A2A SDK v0.3.8  
**Transport:** JSONRPC  

## Capabilities

- **Streaming:** No
- **Push Notifications:** Yes
- **State Transition History:** Yes
- **Max Concurrent Tasks:** 10

## Skills

### 1. Accept Story Assignment (`article.writing.accept_assignment`)

Accepts story assignments from the News Chief and prepares to write.

**Tags:** `writing`, `assignment`

**Example Request:**
```json
{
  "action": "accept_assignment",
  "assignment": {
    "story_id": "story_123",
    "topic": "AI in Journalism",
    "target_length": 1000,
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "status": "accepted",
  "story_id": "story_123",
  "message": "Assignment accepted",
  "reporter_status": "ready_to_write"
}
```

### 2. Write Article (`article.writing.write_article`)

Generates article content using AI based on the assignment specifications.

**Tags:** `writing`, `ai-generation`

**Example Request:**
```json
{
  "action": "write_article",
  "story_id": "story_123"
}
```

**Response:**
```json
{
  "status": "draft_completed",
  "story_id": "story_123",
  "message": "Article written and submitted to Editor",
  "draft": {
    "headline": "...",
    "content": "...",
    "word_count": 985
  }
}
```

### 3. Submit Draft (`article.writing.submit_draft`)

Submits completed draft to the Editor agent for review.

**Tags:** `writing`, `submission`

**Example Request:**
```json
{
  "action": "submit_draft",
  "story_id": "story_123"
}
```

### 4. Revise Article (`article.writing.revise_article`)

Revises article based on Editor feedback.

**Tags:** `writing`, `revision`

**Example Request:**
```json
{
  "action": "revise_article",
  "story_id": "story_123",
  "revisions": {
    "feedback": "..."
  }
}
```

### 5. Get Status (`article.status`)

Returns current writing status and history.

**Tags:** `status`, `reporting`

**Example Request:**
```json
{
  "action": "get_status"
}
```

## Workflow

```
Reporter
    │
    ├─► Receives assignment from News Chief
    │
    ├─► Calls Researcher (parallel) ──┐
    │                                   ├─► Gathers information
    ├─► Calls Archivist (parallel) ────┘
    │
    ├─► Generates article with Claude Sonnet 4
    │
    ├─► Submits to Editor for review
    │
    ├─► Receives Editor feedback
    │
    ├─► Revises if needed
    │
    └─► Sends to Publisher
```

## Integration with Other Agents

### Researcher Agent
- **URL:** `http://localhost:8083`
- **Purpose:** Gather facts, statistics, and background information
- **Skill Used:** `research.questions.bulk_research`
- **Execution:** Parallel with Archivist

### Archivist Agent (External)
- **URL:** Configured via `ELASTIC_ARCHIVIST_AGENT_CARD_URL`
- **Purpose:** Search historical articles for context
- **Skill Used:** `platform.core.search`
- **Execution:** Parallel with Researcher
- **Optional:** System works without it

### Editor Agent
- **URL:** `http://localhost:8082`
- **Purpose:** Review draft for quality and consistency
- **Skill Used:** `editorial.review.draft_review`

### Publisher Agent
- **URL:** `http://localhost:8084`
- **Purpose:** Publish finalized article to Elasticsearch
- **Skill Used:** `publishing.article.publish`

## Parallel Research Execution

The Reporter calls both Researcher and Archivist **in parallel** for efficiency:

```python
# Execute both in parallel
research_response, archive_response = await asyncio.gather(
    researcher_task,
    archivist_task,
    return_exceptions=True
)
```

**Benefits:**
- **Speed:** Total time = max(researcher_time, archivist_time)
- **Resilience:** If one fails, the other's results are still used
- **Efficiency:** No sequential blocking

## Article Generation

### Research Questions

The Reporter generates 5 research questions based on the topic:
1. **Statistics:** Key data points and percentages
2. **Companies:** Major players and stakeholders
3. **Context:** Background and historical perspective
4. **Impact:** Effects on industry and society
5. **Future:** Trends and predictions

### Content Integration

Article generation combines:
- **Topic & Angle:** From assignment
- **Research Data:** Facts, figures, and sources from Researcher
- **Historical Context:** Past coverage from Archivist
- **AI Generation:** Claude Sonnet 4 creates cohesive narrative

### Style Guidelines

Generated articles follow professional journalism standards:
- Clear, engaging introduction (lede paragraph)
- Well-structured body paragraphs
- Natural integration of statistics and data
- Balanced and objective tone
- Fresh perspective (avoiding repetition of historical coverage)

## Configuration

### Environment Variables

```bash
# Required: Anthropic API for article generation
ANTHROPIC_API_KEY=sk-ant-api03-xxx...

# Optional: Archivist A2A agent for historical context
ELASTIC_ARCHIVIST_AGENT_CARD_URL=https://.../.well-known/a2a/agent-card.json
ELASTIC_ARCHIVIST_API_KEY=your_archivist_api_key_here

# Default agent URLs (optional)
EDITOR_URL=http://localhost:8082
RESEARCHER_URL=http://localhost:8083
PUBLISHER_URL=http://localhost:8084
```

### Port Configuration

```bash
uvicorn agents.reporter:app --host localhost --port 8081
```

## Running the Agent

### Start via Script
```bash
./start_newsroom.sh
```

### Start Individually
```bash
uvicorn agents.reporter:app --host localhost --port 8081
```

### Start with Hot Reload (Development)
```bash
uvicorn agents.reporter:app --host localhost --port 8081 --reload
```

## Agent Card

Access the agent card at:
```
http://localhost:8081/.well-known/agent-card.json
```

## Logging

Logs are written to `newsroom.log` with the `[REPORTER]` prefix.

Example log output:
```
2025-01-07 12:00:00 [REPORTER] INFO: 📥 Received query: {"action": "accept_assignment", ...
2025-01-07 12:00:05 [REPORTER] INFO: 📚 Generating 5 research questions...
2025-01-07 12:00:06 [REPORTER] INFO: 🔍 Calling Researcher and Archivist in parallel...
2025-01-07 12:00:12 [REPORTER] INFO: ✅ Received research data: 5 answers
2025-01-07 12:00:12 [REPORTER] INFO: ✅ Received archive data: 3 historical articles
2025-01-07 12:00:20 [REPORTER] INFO: ✍️  Generating article with Claude Sonnet 4...
```

## Error Handling

### Missing Anthropic API Key
If `ANTHROPIC_API_KEY` is not set:
- Warning logged: `ANTHROPIC_API_KEY not set - will use mock article generation`
- Mock article generated as fallback

### Archivist Unavailable
If Archivist is not configured or fails:
- Warning logged: `ELASTIC_ARCHIVIST_AGENT_CARD_URL not set - skipping archive search`
- Article generation continues with just research data
- System remains fully functional

### Researcher Failure
If Researcher fails:
- Error logged but article generation continues
- Uses `return_exceptions=True` in parallel execution

## Testing

The Reporter is tested as part of the end-to-end workflow:

```bash
python tests/test_newsroom_workflow.py
```

Expected output:
```
✅ REPORTER: Assignment accepted
✅ REPORTER: Article written and submitted to Editor
   Headline: AI Agents Transform Modern Newsrooms
   Word Count: 985
```

## Best Practices

1. **Research Questions:** Let the Reporter auto-generate questions for comprehensive coverage
2. **Target Length:** Provide realistic word counts (800-1500 words typical)
3. **Priority Handling:** High priority stories get more detailed research
4. **Archive Context:** Configure Archivist for richer historical perspective

## Future Enhancements

1. **Multi-Source Research:** Integrate additional research APIs
2. **Style Templates:** Support different article formats (news, feature, opinion)
3. **Draft Versioning:** Track revision history
4. **Collaborative Writing:** Multiple reporters on single article

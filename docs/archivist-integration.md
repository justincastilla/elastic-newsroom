# Archivist Integration

## Overview

The Archivist agent is an **external A2A agent hosted on Elastic Cloud** that provides access to historical news articles stored in Elasticsearch. The Reporter agent calls the Archivist in parallel with the Researcher to gather both new research data and historical context.

## Agent Details

**Name:** Archie Archivist
**Provider:** Elastic
**URL:** `<elastic_kibana_endpoint>/api/agent_builder/a2a/archive-agent`
**Protocol Version:** 0.3.0
**Authentication:** API Key (Bearer token in `Authorization` header)

## Capabilities

The Archivist supports the following skills via A2A:

1. **platform.core.search** - Full-text search and analytical queries
2. **platform.core.get_document_by_id** - Retrieve specific documents
3. **platform.core.execute_esql** - Execute ES|QL queries
4. **platform.core.generate_esql** - Generate ES|QL from natural language
5. **platform.core.get_index_mapping** - Get index mappings
6. **platform.core.list_indices** - List available indices
7. **platform.core.index_explorer** - Discover relevant indices

## Integration in Reporter Workflow

### Parallel Execution

The Reporter calls both Researcher and Archivist **in parallel** using `asyncio.gather()`:

```python
# Create tasks for parallel execution
researcher_task = self._send_to_researcher(story_id, assignment, research_questions)
archivist_task = self._send_to_archivist(story_id, assignment)

# Execute both in parallel
research_response, archive_response = await asyncio.gather(
    researcher_task,
    archivist_task,
    return_exceptions=True
)
```

### Benefits of Parallel Execution

1. **Speed**: Both agents are queried simultaneously, not sequentially
2. **Efficiency**: Total time = max(researcher_time, archivist_time) instead of researcher_time + archivist_time
3. **Resilience**: If one agent fails, the other's results are still available (via `return_exceptions=True`)

### Search Query Construction

The Archivist receives a simple text query built from the assignment:

```python
topic = assignment.get("topic", "")
angle = assignment.get("angle", "")
search_query = f"{topic} {angle}".strip()
```

Example: `"AI Agents Transform Modern Newsrooms How A2A protocol enables multi-agent collaboration in journalism"`

### Integration in Article Generation

Historical articles are provided to the Anthropic API as context:

```
HISTORICAL COVERAGE (reference for context, avoid repeating these angles):

1. [Previous article summary or title]
2. [Previous article summary or title]
...
```

The prompt instructs the AI to:
- Reference historical coverage for context
- Take a **fresh angle** to avoid repetition
- Bring a **new perspective** to the topic

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
ELASTIC_ARCHIVIST_API_KEY=your_elastic_archivist_api_key_here
```

### Reporter Initialization

The Reporter automatically connects to the Archivist:

```python
reporter = ReporterAgent(
    editor_url="http://localhost:8082",
    researcher_url="http://localhost:8083",
    archivist_url="<elastic_kibana_endpoint>/api/agent_builder/a2a/archive-agent"
)
```

The `archivist_url` defaults to the Elastic Cloud URL if not specified.

## Error Handling

The integration is designed to be resilient:

1. **Missing API Key**: Logs a warning but continues (Archivist request may fail)
2. **Archivist Failure**: Logged as error, but article writing continues with just research data
3. **Parallel Execution**: Uses `return_exceptions=True` so one agent's failure doesn't block the other
4. **Empty Results**: Article generation works even if archive search returns no results

## Example A2A Flow

```
Reporter
  │
  ├─► Researcher (parallel)
  │     └─ Returns: research_results (facts, figures, data)
  │
  ├─► Archivist (parallel)
  │     └─ Returns: archive_results (historical articles)
  │
  └─► Anthropic Claude
        └─ Input: outline + research_results + archive_results
        └─ Output: Article content
```

## Testing

The Archivist integration is automatically tested in the full workflow test:

```bash
python test_newsroom_workflow.py
```

Look for these log entries:

```
🔍 Calling Researcher and Archivist in parallel...
✅ Received research data: 5 answers
✅ Received archive data: X historical articles
```

## Future Enhancements

1. **Smart Filtering**: Filter archive results by date, relevance, or author
2. **Citation Tracking**: Track which historical articles influenced the new article
3. **Trend Analysis**: Use archive data to identify trending topics
4. **Direct MCP Integration**: Eventually replace A2A call with direct MCP server access

# Elastic News - Agent Sequence Diagram

This diagram shows the complete workflow from story assignment to publication, including all agent-to-agent (A2A) communications and MCP tool calls.

## Complete Workflow Sequence

```mermaid
sequenceDiagram
    participant NC as News Chief<br/>(8080)
    participant R as Reporter<br/>(8081)
    participant MCP as MCP Server<br/>(8095)
    participant Res as Researcher<br/>(8083)
    participant Arch as Archivist<br/>(Elastic Cloud)
    participant E as Editor<br/>(8082)
    participant P as Publisher<br/>(8084)
    participant ES as Elasticsearch

    %% Story Assignment
    Note over NC: Story assigned
    NC->>R: A2A: accept_assignment
    R-->>NC: Assignment accepted

    %% Article Generation Phase
    R->>MCP: Call tool: generate_outline
    Note over R,MCP: Generate article outline<br/>and research questions
    MCP-->>R: Outline + questions

    %% Parallel Research Phase
    par Research & Archive Search
        R->>Res: A2A: research_questions
        Res->>MCP: Call tool: research_questions
        Note over Res,MCP: Claude Sonnet 4<br/>answers research questions
        MCP-->>Res: Research answers
        Res-->>R: Research data
    and
        R->>Arch: A2A JSONRPC: message/send
        Note over R,Arch: Search news_archive index<br/>for historical context
        Arch->>ES: Search news_archive
        ES-->>Arch: Historical articles
        Arch-->>R: Archive data
    end

    R->>MCP: Call tool: generate_article
    Note over R,MCP: Generate article with<br/>research + archive context
    MCP-->>R: Article draft

    %% Editorial Phase
    R->>NC: A2A: submit_draft
    Note over R,NC: Reporter submits draft<br/>to News Chief
    NC->>E: A2A: review_draft
    Note over NC,E: News Chief routes to Editor
    E->>MCP: Call tool: review_article
    Note over E,MCP: Review grammar, tone,<br/>consistency, SEO
    MCP-->>E: Editorial feedback
    E-->>NC: Review comments
    NC-->>R: Review comments
    Note over NC,R: News Chief returns<br/>Editor feedback to Reporter

    R->>MCP: Call tool: apply_edits
    Note over R,MCP: Apply editorial<br/>suggestions
    MCP-->>R: Revised article

    %% Publication Phase
    R->>NC: Notify draft complete
    NC->>P: A2A: publish_article
    Note over NC,P: News Chief routes to Publisher
    P->>MCP: Call tool: generate_tags
    Note over P,MCP: Generate tags<br/>and categories
    MCP-->>P: Tags + categories

    P->>ES: Index article document
    ES-->>P: Index response

    P->>P: Save markdown file
    Note over P: articles/story_*.md

    P-->>NC: Publication success
    NC-->>R: Final status
    Note over NC: Workflow complete
```

## Key Components

### Agent-to-Agent (A2A) Protocol
- **News Chief → Reporter**: Story assignment
- **Reporter → Researcher**: Research request (direct)
- **Reporter → Archivist**: Historical search (JSONRPC 2.0, direct)
- **Reporter → News Chief**: Draft submission
- **News Chief → Editor**: Draft review (News Chief coordinates)
- **News Chief → Publisher**: Publication request (News Chief coordinates)

### MCP Tool Calls
All tools are provided by MCP Server (port 8095):

1. **generate_outline** (Reporter)
   - Input: Story topic, angle, target length
   - Output: Article outline + research questions

2. **research_questions** (Researcher)
   - Input: List of research questions
   - Output: Structured research data

3. **generate_article** (Reporter)
   - Input: Outline, research data, archive context
   - Output: Complete article draft

4. **review_article** (Editor)
   - Input: Article draft
   - Output: Editorial feedback + suggestions

5. **apply_edits** (Reporter)
   - Input: Article draft + editorial feedback
   - Output: Revised article

6. **generate_tags** (Publisher)
   - Input: Article content
   - Output: Tags and categories


## Parallel Processing

The Reporter performs research and archive search in parallel using `asyncio.gather()`:

```python
research_response, archive_response = await asyncio.gather(
    self._send_to_researcher(story_id, assignment, questions),
    self._send_to_archivist(story_id, assignment),
    return_exceptions=True
)
```

This reduces total workflow time by ~30 seconds.

## Timeouts

- Standard A2A calls: 90 seconds
- Archivist calls: 30 seconds (with 3 retry attempts)
- News Chief assignment: 60 seconds

## Error Handling

- **Researcher failure**: Warning logged, workflow continues
- **Archivist failure**: Exception raised, workflow halts
- **Editor failure**: Warning logged, returns draft without edits
- **Publisher failure**: Error logged, article not indexed (but saved locally)

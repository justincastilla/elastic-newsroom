# Publisher Agent

## Overview

The Publisher Agent **publishes finalized articles to Elasticsearch**, handles CI/CD deployment workflow, and sends CRM notifications. It indexes articles with auto-generated tags and categories, making them searchable in the news archive.

## Agent Details

**Name:** Publisher  
**Port:** 8084  
**URL:** `http://localhost:8084`  
**Protocol Version:** A2A SDK v0.3.8  
**Transport:** JSONRPC  

## Capabilities

- **Streaming:** No
- **Push Notifications:** Yes
- **State Transition History:** Yes
- **Max Concurrent Tasks:** 20

## Skills

### 1. Publish Article (`publishing.article.publish`)

Publishes article to Elasticsearch with auto-generated tags/categories, triggers CI/CD deployment, and sends CRM notifications.

**Tags:** `publishing`, `elasticsearch`, `deployment`

**Example Request:**
```json
{
  "action": "publish_article",
  "article": {
    "story_id": "story_123",
    "headline": "AI Agents Transform Modern Newsrooms",
    "content": "[Full article content...]",
    "word_count": 985,
    "author": "Reporter Agent",
    "assignment": {
      "topic": "AI in Journalism",
      "priority": "high"
    },
    "editor_review": {
      "approval_status": "approved",
      "tags": ["ai", "journalism", "technology"],
      "summary": "Article examines transformation..."
    }
  }
}
```

**Response:**
```json
{
  "status": "published",
  "story_id": "story_123",
  "message": "Article published successfully",
  "publication_details": {
    "elasticsearch_id": "doc_story_123_20250107",
    "index": "news_archive",
    "url_slug": "ai-agents-transform-modern-newsrooms",
    "published_at": "2025-01-07T12:00:00",
    "tags": ["ai", "journalism", "technology", "newsroom", "automation"],
    "categories": ["Technology", "Media & Publishing"],
    "build_number": "#1234",
    "deployment_status": "deployed"
  },
  "file_saved": "articles/ai-agents-transform-modern-newsrooms.md"
}
```

### 2. Unpublish Article (`publishing.article.unpublish`)

Removes article from public view by updating status in Elasticsearch.

**Tags:** `publishing`, `removal`

**Example Request:**
```json
{
  "action": "unpublish_article",
  "story_id": "story_123"
}
```

**Response:**
```json
{
  "status": "unpublished",
  "story_id": "story_123",
  "message": "Article removed from public view",
  "elasticsearch_updated": true
}
```

### 3. Get Publication Status (`publishing.status`)

Returns publication status and records.

**Tags:** `status`, `reporting`

**Example Requests:**
```json
{
  "action": "get_status"
}
```

Or for specific article:
```json
{
  "action": "get_status",
  "story_id": "story_123"
}
```

**Response:**
```json
{
  "status": "success",
  "total_published": 25,
  "recent_publications": [
    {
      "story_id": "story_123",
      "headline": "AI Agents Transform Modern Newsrooms",
      "published_at": "2025-01-07T12:00:00",
      "elasticsearch_id": "doc_story_123_20250107"
    }
  ]
}
```

## Workflow

```
Publisher
    │
    ├─► Receives approved article from Reporter
    │
    ├─► Generates tags & categories (Claude Sonnet 4)
    │
    ├─► Builds Elasticsearch document
    │   ├─ Article content and metadata
    │   ├─ Auto-generated tags
    │   ├─ Categories
    │   ├─ Publication timestamp
    │   └─ URL slug
    │
    ├─► Mock CI/CD Pipeline
    │   ├─ Build (#1234)
    │   ├─ Tests (passed)
    │   └─ Deployment (production)
    │
    ├─► Indexes to Elasticsearch
    │   └─ Index: news_archive
    │
    ├─► Saves markdown file
    │   └─ articles/[slug].md
    │
    └─► Mock CRM notification
        └─ Article published event
```

## Elasticsearch Integration

### Index Configuration

**Index Name:** `news_archive` (configurable via `ELASTIC_ARCHIVIST_INDEX`)

**Document Structure:**
```json
{
  "article_id": "story_123",
  "headline": "AI Agents Transform Modern Newsrooms",
  "content": "[Full article content...]",
  "summary": "Brief summary...",
  "author": "Reporter Agent",
  "published_date": "2025-01-07T12:00:00",
  "word_count": 985,
  "tags": ["ai", "journalism", "technology"],
  "categories": ["Technology", "Media & Publishing"],
  "url_slug": "ai-agents-transform-modern-newsrooms",
  "priority": "high",
  "status": "published",
  "metadata": {
    "story_id": "story_123",
    "build_number": "#1234"
  }
}
```

### Index Creation

Before publishing, create the index:
```bash
python scripts/create_elasticsearch_index.py
```

This creates the index with proper mappings for:
- Full-text search on content
- Tag filtering
- Date range queries
- Category aggregations

### Search Integration

Published articles become searchable via:
1. **Direct Elasticsearch API:** For custom queries
2. **Archivist Agent:** A2A protocol access for historical search
3. **Kibana:** Dashboard and analytics

## Tag & Category Generation

The Publisher uses Claude Sonnet 4 to generate:

### Tags (5-10 per article)
- Specific, searchable keywords
- Relevant to article content
- Mix of broad and specific terms
- Example: `["ai", "journalism", "newsroom", "automation", "claude", "agents"]`

### Categories (1-3 per article)
- High-level classification
- Standard taxonomy
- Example: `["Technology", "Media & Publishing"]`

### AI Prompt Structure
```
You are a content categorization specialist...

Analyze the article and provide:
1. 5-10 relevant tags (keywords)
2. 1-3 categories from standard taxonomy

Article: [content]

Return as JSON: {"tags": [...], "categories": [...]}
```

## Mock CI/CD Pipeline

The Publisher simulates a production deployment pipeline:

### Build Phase
- Build number generated
- 2-second simulation
- Status: "Build complete"

### Test Phase
- Unit tests (mock)
- Integration tests (mock)
- 3-second simulation
- Status: "All tests passed"

### Deployment Phase
- Production deployment (mock)
- 2-second simulation
- Status: "Deployed to production"

**Note:** This is simulated for demonstration. In production, integrate with actual CI/CD tools.

## Mock CRM Integration

Simulates CRM notification for article publication:
- Notification sent to editorial team
- Article metadata included
- Publication URL provided

**Note:** In production, integrate with actual CRM systems (Salesforce, HubSpot, etc.)

## File System Storage

Articles are saved as markdown files:

### Location
```
articles/[url-slug].md
```

### Format
```markdown
# [Headline]

**Published:** [Date]
**Word Count:** [N]
**Tags:** [tag1], [tag2], ...
**Categories:** [cat1], [cat2]

---

[Article content]
```

### Example
```
articles/ai-agents-transform-modern-newsrooms.md
```

## Integration with Other Agents

### Reporter Agent
- **URL:** `http://localhost:8081`
- **Interaction:** Reporter sends approved articles for publication
- **Trigger:** After Editor approval and any revisions

### Archivist Agent (External)
- **Integration:** Published articles become searchable via Archivist
- **Index:** Same `news_archive` index
- **Access:** A2A protocol for historical search

## Configuration

### Environment Variables

```bash
# Required: Elasticsearch connection
ELASTICSEARCH_ENDPOINT=https://your-cluster.es.region.gcp.elastic.cloud:443
ELASTIC_SEARCH_API_KEY=your_elasticsearch_api_key_here

# Required: Index name
ELASTIC_ARCHIVIST_INDEX=news_archive

# Required: Anthropic API for tag generation
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
```

### Port Configuration

```bash
uvicorn agents.publisher:app --host localhost --port 8084
```

## Running the Agent

### Start via Script
```bash
./start_newsroom.sh
```

### Start Individually
```bash
uvicorn agents.publisher:app --host localhost --port 8084
```

### Start with Hot Reload (Development)
```bash
uvicorn agents.publisher:app --host localhost --port 8084 --reload
```

## Agent Card

Access the agent card at:
```
http://localhost:8084/.well-known/agent-card.json
```

## Logging

Logs are written to `newsroom.log` with the `[PUBLISHER]` prefix.

Example log output:
```
2025-01-07 12:00:00 [PUBLISHER] INFO: 📥 Received query: {"action": "publish_article", ...
2025-01-07 12:00:01 [PUBLISHER] INFO: 🏷️  Generating tags and categories...
2025-01-07 12:00:05 [PUBLISHER] INFO: 📦 Building Elasticsearch document...
2025-01-07 12:00:07 [PUBLISHER] INFO: 🔨 [MOCK CI/CD] Starting build pipeline...
2025-01-07 12:00:15 [PUBLISHER] INFO: 📤 Indexing to Elasticsearch...
2025-01-07 12:00:16 [PUBLISHER] INFO: ✅ Article published successfully
```

## Error Handling

### Elasticsearch Not Configured
```json
{
  "status": "error",
  "message": "Elasticsearch not configured or unavailable"
}
```

### Index Not Found
- Check if index exists: `python scripts/create_elasticsearch_index.py`
- Verify index name in `.env` matches actual index

### Connection Timeout
```json
{
  "status": "error",
  "message": "Failed to index article: Connection timeout"
}
```

### Missing Anthropic API Key
- Tags will be empty list
- Warning logged: `ANTHROPIC_API_KEY not set - tags will be empty`
- Article still published

## Testing

The Publisher is tested as part of the end-to-end workflow:

```bash
python tests/test_newsroom_workflow.py
```

Expected output:
```
✅ PUBLISHER: Article published
   Elasticsearch ID: doc_story_123_20250107
   File: articles/ai-agents-transform-modern-newsrooms.md
   Tags: ai, journalism, technology
```

### Verify Publication

**Check Elasticsearch:**
```bash
curl -X GET "https://[endpoint]:443/news_archive/_doc/doc_story_123_20250107" \
  -H "Authorization: ApiKey [api-key]"
```

**Check File System:**
```bash
ls -la articles/
cat articles/ai-agents-transform-modern-newsrooms.md
```

## Best Practices

1. **Index Management:** Create index before first publication
2. **API Key Security:** Use write-only API key with minimal permissions
3. **Tag Quality:** Ensure Claude API is configured for better tags
4. **File Organization:** Regularly archive old articles
5. **Monitoring:** Check Elasticsearch cluster health regularly

## URL Slug Generation

Slugs are generated from headlines:
- Lowercase conversion
- Special character removal
- Space replacement with hyphens
- URL-safe format

Examples:
- "AI Agents Transform Modern Newsrooms" → `ai-agents-transform-modern-newsrooms`
- "What's New in Tech?" → `whats-new-in-tech`

## Publication Metadata

Each publication includes:
- **Elasticsearch ID:** Unique document identifier
- **URL Slug:** Human-readable article identifier
- **Published Date:** ISO 8601 timestamp
- **Tags & Categories:** Auto-generated metadata
- **Build Number:** CI/CD tracking
- **File Path:** Local storage location

## Future Enhancements

1. **Real CI/CD:** Integration with Jenkins, GitHub Actions, etc.
2. **Real CRM:** Salesforce, HubSpot notification webhooks
3. **Image Handling:** Support for article images and media
4. **Version Control:** Track article revisions and updates
5. **Analytics Integration:** Google Analytics, custom metrics
6. **Multi-Index:** Support for different publication channels
7. **Scheduled Publishing:** Article embargo and scheduled releases

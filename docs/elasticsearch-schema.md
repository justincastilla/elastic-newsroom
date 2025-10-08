# Elasticsearch Index Schema for News Articles

## Overview

The `news_archive` index stores published news articles with complete metadata, research data, editorial reviews, and workflow information. This enables the Archivist agent to search historical articles and provide context for new stories.

## Index Configuration

### Settings

- **Shards**: 1 (suitable for development/demo, increase for production)
- **Replicas**: 1 (for high availability)
- **Custom Analyzers**:
  - `article_analyzer`: Full-text analysis with stemming and stop words
  - `headline_analyzer`: Simpler analyzer for headlines (no stemming)

### Analyzers

```json
{
  "article_analyzer": {
    "tokenizer": "standard",
    "filters": ["lowercase", "asciifolding", "stop", "snowball"]
  },
  "headline_analyzer": {
    "tokenizer": "standard",
    "filters": ["lowercase", "asciifolding"]
  }
}
```

## Field Mappings

### Core Article Fields

| Field | Type | Description | Searchable |
|-------|------|-------------|------------|
| `story_id` | keyword + text | Unique story identifier | Yes |
| `headline` | text + keyword | Article headline | Yes (analyzed) |
| `content` | text | Full article body | Yes (analyzed) |
| `topic` | text + keyword | Main topic/subject | Yes |
| `angle` | text + keyword | Story angle/focus | Yes |
| `word_count` | integer | Total word count | No (filterable) |
| `target_length` | integer | Target word count | No (filterable) |

### Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `priority` | keyword | Story priority (high, medium, low) |
| `status` | keyword | Publication status (draft, published, archived) |
| `published_at` | date | Publication timestamp |
| `created_at` | date | Story creation timestamp |
| `updated_at` | date | Last update timestamp |
| `deadline` | date | Story deadline |
| `author` | keyword + text | Article author (e.g., "Reporter Agent") |
| `editor` | keyword + text | Reviewing editor (e.g., "Editor Agent") |
| `tags` | keyword[] | Article tags/keywords |
| `categories` | keyword[] | Article categories |

### Research Data (Nested Object)

Stores research gathered by the Researcher agent:

```json
{
  "research_data": [
    {
      "question": "What percentage of news orgs use AI?",
      "summary": "65% of newsrooms use AI agents...",
      "facts": ["Fact 1", "Fact 2"],
      "figures": {
        "percentages": ["65%", "42%"],
        "dollar_amounts": ["$2.3B"],
        "numbers": ["1,200 companies"],
        "dates": ["Q4 2024"],
        "companies": ["CompanyA", "CompanyB"]
      },
      "sources": ["Industry Report 2024"],
      "confidence": 85
    }
  ]
}
```

**Searchable**: Yes (facts, summary, sources)
**Filterable**: By confidence level, company names, dates

### Editorial Review (Nested Object)

Stores review data from the Editor agent:

```json
{
  "editorial_review": {
    "approval_status": "approved",
    "overall_assessment": "Well-written article...",
    "grammar_check": "No issues found",
    "tone_assessment": "Professional and balanced",
    "consistency_check": "Consistent throughout",
    "length_check": "Within target range",
    "suggested_edits_count": 3,
    "reviewed_at": "2025-10-08T12:00:00Z"
  }
}
```

**Searchable**: Yes (assessments)
**Filterable**: By approval status, edit count

### Workflow Fields

| Field | Type | Description |
|-------|------|-------------|
| `research_questions` | text[] | Questions sent to Researcher |
| `archive_references` | text | Historical articles referenced |
| `url_slug` | keyword | URL-friendly slug |
| `filepath` | keyword | Path to published markdown file |
| `version` | integer | Article version number |
| `revisions_count` | integer | Number of revisions |
| `agents_involved` | keyword[] | List of agents in workflow |
| `workflow_duration_ms` | long | Total workflow duration |

### Metadata (Dynamic Object)

Stores additional arbitrary metadata:

```json
{
  "metadata": {
    "custom_field": "value",
    "another_field": 123
  }
}
```

**Dynamic mapping enabled**: New fields can be added without schema changes

## Search Capabilities

### Full-Text Search

The index supports powerful full-text search on:
- Headlines (headline analyzer - less aggressive)
- Article content (article analyzer - with stemming)
- Topics and angles
- Research facts and summaries
- Editorial assessments

### Filtering

Filter articles by:
- Date ranges (published_at, created_at, deadline)
- Word count ranges
- Priority levels
- Publication status
- Author/Editor
- Tags and categories
- Approval status
- Confidence levels in research data

### Aggregations

Analyze trends with aggregations on:
- Publication dates (date histogram)
- Topics (term aggregation)
- Tags/Categories (term aggregation)
- Word count distribution (histogram)
- Agents involved (term aggregation)
- Workflow duration (stats aggregation)

## Example Queries

### Find articles about AI published in the last month

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "content": "artificial intelligence"
          }
        }
      ],
      "filter": [
        {
          "range": {
            "published_at": {
              "gte": "now-1M"
            }
          }
        }
      ]
    }
  }
}
```

### Find high-priority articles with specific companies mentioned

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "priority": "high"
          }
        },
        {
          "terms": {
            "research_data.figures.companies": ["OpenAI", "Anthropic"]
          }
        }
      ]
    }
  }
}
```

### Aggregate articles by topic

```json
{
  "size": 0,
  "aggs": {
    "topics": {
      "terms": {
        "field": "topic.keyword",
        "size": 10
      }
    }
  }
}
```

## Index Creation

Use the provided script to create the index:

```bash
python scripts/create_elasticsearch_index.py
```

This will:
1. Connect to Elasticsearch using credentials from `.env`
2. Check if index exists (prompt to delete if it does)
3. Create index with the mapping from `docs/elasticsearch-index-mapping.json`
4. Verify index creation and display key fields

## Publisher Integration

The Publisher agent will index articles using this schema:

```python
# Example document structure
document = {
    "story_id": "story_20251008_123456",
    "headline": "AI Agents Transform Modern Newsrooms",
    "content": "Full article content...",
    "topic": "AI Agents",
    "angle": "How A2A protocol enables collaboration",
    "word_count": 1250,
    "target_length": 1200,
    "priority": "high",
    "status": "published",
    "published_at": "2025-10-08T12:34:56Z",
    "created_at": "2025-10-08T12:00:00Z",
    "author": "Reporter Agent",
    "editor": "Editor Agent",
    "tags": ["ai", "newsroom", "agents", "a2a"],
    "categories": ["technology", "journalism"],
    "research_data": [...],  # From Researcher
    "editorial_review": {...},  # From Editor
    "filepath": "articles/ai-agents-transform-modern-newsrooms.md",
    "agents_involved": ["News Chief", "Reporter", "Researcher", "Archivist", "Editor"],
    "workflow_duration_ms": 85000
}

# Index the document
es.index(index="news_archive", document=document)
```

## Archivist Integration

The Archivist agent queries this index to provide historical context:

- Searches by topic/keywords
- Filters by date ranges
- Returns relevant articles with metadata
- Supports ES|QL queries for complex analytics

## Maintenance

### Reindexing

If you need to change the mapping, create a new index and reindex:

```bash
# Create new index with v2 suffix
python scripts/create_elasticsearch_index.py

# Reindex (manual step)
POST _reindex
{
  "source": { "index": "news_archive" },
  "dest": { "index": "news_archive_v2" }
}

# Update alias
POST _aliases
{
  "actions": [
    { "remove": { "index": "news_archive", "alias": "news_archive_current" }},
    { "add": { "index": "news_archive_v2", "alias": "news_archive_current" }}
  ]
}
```

### Cleanup

Delete old articles (optional):

```bash
# Delete articles older than 1 year
POST news_archive/_delete_by_query
{
  "query": {
    "range": {
      "published_at": {
        "lt": "now-1y"
      }
    }
  }
}
```

## Performance Considerations

1. **Sharding**: Increase shards for high-volume production
2. **Replicas**: Use 1-2 replicas for availability
3. **Refresh Interval**: Default 1s is fine for this use case
4. **Analyzers**: Custom analyzers optimize search quality
5. **Keyword Fields**: Multi-field mapping enables both search and aggregations

## Security

- Index access controlled via Elasticsearch API keys
- Publisher agent uses write-enabled API key
- Archivist agent uses read-only API key (recommended)
- Consider enabling field-level security for sensitive metadata

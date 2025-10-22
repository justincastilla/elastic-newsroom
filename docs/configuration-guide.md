# Elastic News Configuration Guide

## Environment Variables

All configuration is managed through environment variables in your `.env` file. Copy `env.example` to `.env` and fill in your values.

### Required Variables

#### Anthropic API
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
**Used by:** Reporter, Researcher, Editor, Publisher
**Purpose:** AI-powered content generation, research, editing, and tag generation

#### Elasticsearch (Direct Access)
```bash
ELASTICSEARCH_ENDPOINT=https://your-cluster.es.region.gcp.elastic.cloud:443
ELASTICSEARCH_API_KEY=your_elasticsearch_api_key_here
ELASTIC_ARCHIVIST_INDEX=news_archive
```
**Used by:** Publisher (for indexing articles)
**Purpose:** Direct write access to Elasticsearch for article indexing

### Optional Variables

#### Elastic Archivist (A2A Agent)
```bash
ELASTIC_ARCHIVIST_AGENT_CARD_URL=https://your-kb.kb.region.gcp.elastic.cloud/.well-known/a2a/agent-card.json
ELASTIC_ARCHIVIST_API_KEY=your_archivist_api_key_here
```
**Used by:** Reporter (for historical article search)
**Purpose:** A2A protocol access to search historical articles
**Note:** This is the **full agent card URL** - do not append anything to it

If not configured, the Reporter will skip archive search and continue with just research data.

## Understanding the Two Elasticsearch Configurations

### Direct Elasticsearch Access (Publisher)
- **Variable:** `ELASTICSEARCH_ENDPOINT`
- **Format:** `https://[cluster-id].es.[region].gcp.elastic.cloud:443`
- **Purpose:** Direct API access for **writing** articles
- **Agent:** Publisher
- **Operations:** Index articles, update status

### Archivist A2A Agent (Reporter)
- **Variable:** `ELASTIC_ARCHIVIST_AGENT_CARD_URL`
- **Format:** `https://[kb-id].kb.[region].gcp.elastic.cloud/.well-known/a2a/agent-card.json`
- **Purpose:** A2A protocol access for **reading** historical articles via agent card
- **Agent:** Reporter
- **Operations:** Search past coverage, get context

### Why Two Different Endpoints?

1. **Publisher uses direct ES API** because it needs low-level write access to index structured documents with specific mappings

2. **Reporter uses A2A Archivist** because it's a conversational agent that searches and summarizes historical content, not requiring direct database access

## Quick Setup

### 1. Create `.env` file
```bash
cp env.example .env
```

### 2. Fill in required variables
At minimum, you need:
- `ANTHROPIC_API_KEY`
- `ELASTICSEARCH_ENDPOINT`
- `ELASTICSEARCH_API_KEY`
- `ELASTIC_ARCHIVIST_INDEX`

### 3. Create Elasticsearch index
```bash
python scripts/create_elasticsearch_index.py
```

### 4. (Optional) Configure Archivist
If you have an Elastic Agent Builder Archivist:
- Set `ELASTIC_ARCHIVIST_AGENT_CARD_URL` to the full agent card URL
- Set `ELASTIC_ARCHIVIST_API_KEY` for authentication

Without these, the system works fine - it just won't search historical articles.

## Agent Port Configuration

Default ports (can be overridden):
```bash
A2A_DISCOVERY_PORT=8080      # News Chief
A2A_MESSAGE_PORT=8081        # Reporter
# Editor: 8082
# Researcher: 8083
# Publisher: 8084
```

## Verification

### Test Elasticsearch Connection
```bash
python scripts/create_elasticsearch_index.py
```
Should show:
- ✅ Connected to Elasticsearch
- ✅ Index created successfully

### Test Archivist Connection
Start Reporter agent and check logs:
```bash
python run_reporter.py --reload
```

If Archivist is configured:
- ✅ Will attempt to connect during article writing

If not configured:
- ⚠️  ELASTIC_ARCHIVIST_AGENT_CARD_URL not set - skipping archive search
- (This is fine - system continues without historical context)

## Common Issues

### Issue: Publisher can't connect to Elasticsearch
**Check:**
- `ELASTICSEARCH_ENDPOINT` is correct format (https://...)
- `ELASTICSEARCH_API_KEY` is valid and has write permissions
- Network connectivity to Elastic Cloud

### Issue: Archivist returns 401 Unauthorized
**Check:**
- `ELASTIC_ARCHIVIST_AGENT_CARD_URL` points to the full agent card URL
- `ELASTIC_ARCHIVIST_API_KEY` is set and valid
- API key has access to the Agent Builder

### Issue: Connection timeout to Elasticsearch
**Possible causes:**
- Network latency to Elastic Cloud
- Elasticsearch cluster under load
- Large document being indexed

**Solutions:**
- Check Elasticsearch cluster health
- Verify network connectivity
- Consider increasing timeout in Publisher code

## Security Best Practices

1. **Never commit `.env` to version control**
   - Already in `.gitignore`

2. **Use separate API keys for different agents**
   - Publisher: Write access to ES
   - Archivist: Read-only access via A2A

3. **Rotate API keys regularly**
   - Especially after sharing code or configs

4. **Use environment-specific configs**
   - `.env.development`
   - `.env.production`

## Example .env File

```bash
# AI/LLM
ANTHROPIC_API_KEY=sk-ant-api03-xxx...

# Elasticsearch (Direct Write Access)
ELASTICSEARCH_ENDPOINT=<your_es_endpoint_here>
ELASTICSEARCH_API_KEY=<your_es_api_key_here>

# Archivist (A2A Read Access) - Optional
ELASTIC_ARCHIVIST_AGENT_CARD_URL=<your_archivist_agent_card_here>
ELASTIC_ARCHIVIST_API_KEY=your_archivist_api_key_here
ELASTIC_ARCHIVIST_INDEX=news_archive

# Agent Ports (defaults shown)
A2A_DISCOVERY_PORT=8080
A2A_MESSAGE_PORT=8081
```

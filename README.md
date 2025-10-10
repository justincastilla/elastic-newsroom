# Elastic News - AI-Powered Digital Newsroom

A working demonstration of Agent2Agent (A2A) protocols in a multi-agent newsroom system, built using the official [A2A Python SDK](https://github.com/a2aproject/a2a-python) v0.3.8.

## Overview

This project implements a fully functional digital newsroom where specialized AI agents collaborate to research, write, edit, and publish news articles. The system features:

- **Official A2A SDK v0.3.8**: Multi-agent coordination and communication
- **Claude Sonnet 4**: AI-powered content generation, research, and editing
- **Elasticsearch Integration**: Historical article indexing and search via A2A Archivist
- **Complete Workflow**: End-to-end automation from story assignment to publication
- **5 Working Agents**: News Chief, Reporter, Researcher, Editor, and Publisher

## Architecture

### Agents

The newsroom consists of 5 specialized AI agents that communicate via the A2A protocol:

#### Local Agents (Ports 8080-8084)

1. **News Chief** (Port 8080)
   - Coordinator agent that assigns stories and manages workflow
   - Delegates tasks to Reporter, Researcher, Editor, and Publisher
   - Tracks story status and completion

2. **Reporter** (Port 8081)
   - Writes articles based on research data
   - Consults Archivist via Elastic Conversational API for historical context
   - Integrates research findings and historical references into cohesive narratives
   - Generates structured article data (headline, content, word count)

3. **Researcher** (Port 8083)
   - Gathers facts, statistics, and background information
   - Uses Claude Sonnet 4 for research synthesis
   - Provides structured data to Reporter

4. **Editor** (Port 8082)
   - Reviews articles for grammar, tone, and consistency
   - Checks word count against target length
   - Provides editorial feedback and suggestions
   - Generates SEO metadata (tags, summary, headline refinement)

5. **Publisher** (Port 8084)
   - Indexes articles to Elasticsearch
   - Saves articles as markdown files
   - Updates article status to "published"

#### External Agent (Elastic Cloud)

- **Archivist Agent**
  - Hosted on Elastic Cloud (Kibana Agent Builder)
  - Searches historical articles via Elastic Conversational API
  - Provides context about past coverage
  - Uses `platform.core.search` skill to query `news_archive` index
  - Returns article highlights, references, and reasoning

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt

# Optional: Install UI dependencies
cd ui && pip install -e . && cd ..
```

### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your credentials:
# - ANTHROPIC_API_KEY (required)
# - ELASTICSEARCH_ENDPOINT (required)
# - ELASTIC_SEARCH_API_KEY (required)
# - ELASTIC_ARCHIVIST_AGENT_CARD_URL (required)
# - ELASTIC_ARCHIVIST_API_KEY (required)
```

See [Configuration Guide](docs/configuration-guide.md) for detailed setup instructions.

### 3. Create Elasticsearch Index
```bash
python scripts/create_elasticsearch_index.py
```

### 4. Start All Agents
```bash
# Start all 5 agents in the background
./start_newsroom.sh

# Or with hot reload for development
./start_newsroom.sh --reload

# Start agents + web UI on port 3000
./start_newsroom.sh --with-ui

# Stop all agents (and UI if running)
./start_newsroom.sh --stop
```

**Web UI** (if started with `--with-ui`):
- Assignment Form: http://localhost:3000/
- Article Viewer: http://localhost:3000/article/{story_id}

### 5. Run the Workflow

**Option 1: Web UI** (Recommended)
```bash
# Navigate to http://localhost:3000
# Fill out the story assignment form
# View real-time progress on the status page
# Read the completed article on the article viewer page
```

**Option 2: Test Script**
```bash
python tests/test_newsroom_workflow.py
```

This will:
1. Assign a story via News Chief
2. Have Researcher gather information
3. Have Reporter write the article (consulting Archivist via Elastic Conversational API)
4. Have Editor review and refine the article
5. Have Publisher index to Elasticsearch and save to file

**Option 3: Archivist Diagnostics**
```bash
python test_archivist.py
```

Tests Archivist connectivity and search functionality directly.

## Project Structure

```
elastic-news/
├── agents/                      # A2A agents using official SDK
│   ├── __init__.py             # Agent module exports
│   ├── news_chief.py           # Story coordinator (port 8080)
│   ├── reporter.py             # Article writer (port 8081)
│   ├── researcher.py           # Research gatherer (port 8083)
│   ├── editor.py               # Content reviewer (port 8082)
│   └── publisher.py            # Article publisher (port 8084)
├── ui/                          # Web UI (Mesop)
│   ├── pages/                  # UI pages
│   │   ├── home.py             # Story assignment form
│   │   ├── status.py           # Workflow progress
│   │   └── article.py          # Article viewer
│   ├── services/               # UI services
│   │   └── news_chief_client.py # API client
│   └── state/                  # UI state management
│       └── app_state.py        # Application state
├── scripts/                     # Utility scripts
│   └── create_elasticsearch_index.py
├── tests/                       # Test suite
│   ├── test_newsroom_workflow.py    # End-to-end workflow test
│   ├── test_elasticsearch_index.py  # ES index creation test
│   └── test_archivist.py            # Archivist connectivity test
├── docs/                        # Documentation
│   ├── configuration-guide.md   # Environment setup
│   ├── elasticsearch-schema.md  # Index mapping
│   ├── news-chief-agent.md      # News Chief details
│   └── archivist-integration.md # Archivist setup
├── articles/                    # Published articles (auto-generated)
├── logs/                        # Agent logs (auto-generated)
├── start_newsroom.sh            # Start/stop all agents
├── start_ui.sh                  # Start UI only
├── requirements.txt             # Python dependencies
├── env.example                  # Environment template
└── README.md                    # This file
```

## Features

✅ **Currently Working**

- **Multi-Agent Coordination**: 5 agents communicate via A2A protocol
- **Complete Workflow**: End-to-end article production from assignment to publication
- **Web UI**: Interactive story assignment, real-time status tracking, and article viewing (port 3000)
- **Elasticsearch Integration**: Historical article indexing and search via `news_archive` index
- **Elastic Archivist Integration**: Cloud-based search agent via Conversational API
- **Claude Sonnet 4**: AI-powered research, writing, and editing
- **Process Management**: Single command to start/stop all agents
- **Comprehensive Logging**: Individual log files for each agent with detailed diagnostics
- **Hot Reload Support**: Development mode with auto-reload for agents and UI
- **Article Data Flow**: Structured article data (headline, content, word count) passed through workflow
- **Status Page**: Real-time workflow progress with manual refresh
- **Archivist Diagnostics**: Standalone test tool to verify Elastic Cloud connectivity

🔄 **In Progress**

- Additional MCP server integrations
- Enhanced error handling and retry logic
- Performance monitoring and metrics

## Documentation

- [Configuration Guide](docs/configuration-guide.md) - Environment setup and API configuration
- [Elasticsearch Schema](docs/elasticsearch-schema.md) - Index mapping and field definitions
- [News Chief Agent](docs/news-chief-agent.md) - Coordinator agent details
- [Archivist Integration](docs/archivist-integration.md) - External agent setup

## Workflow Example

```
User submits story via Web UI (http://localhost:3000)
    ↓
News Chief assigns story to Reporter
    ↓
Reporter delegates to Researcher for background information
    ↓
Researcher returns structured research data (5 key questions/answers)
    ↓
Reporter consults Archivist via Elastic Conversational API
  - Archivist searches news_archive index
  - Returns historical article highlights and references
    ↓
Reporter writes article integrating research + historical context
  - Generates headline, content, and word count
    ↓
Editor reviews article for quality and SEO
  - Checks word count, grammar, tone
  - Generates tags and metadata
    ↓
Publisher indexes article to Elasticsearch + saves markdown file
    ↓
User views completed article in Web UI
```

## Commands

### Start/Stop Agents
```bash
./start_newsroom.sh                      # Start all agents
./start_newsroom.sh --reload             # Start agents with hot reload
./start_newsroom.sh --with-ui            # Start agents + web UI
./start_newsroom.sh --with-ui --reload   # Start agents + UI with hot reload
./start_newsroom.sh --stop               # Stop all agents and UI
```

### Web UI
```bash
./start_ui.sh                    # Start UI only (agents must be running)
open http://localhost:3000       # Open UI in browser
```

**Hot Reload:** The UI has hot reload enabled by default (Mesop feature). Changes to `ui/` files reload automatically.

### View Logs
```bash
tail -f logs/*.log            # All agents
tail -f logs/News_Chief.log   # Specific agent
```

### Run Tests
```bash
python tests/test_newsroom_workflow.py    # End-to-end workflow
python tests/test_elasticsearch_index.py  # Elasticsearch index test
python test_archivist.py                  # Archivist connectivity and API test
```

### Individual Agents
```bash
uvicorn agents.news_chief:app --host localhost --port 8080
uvicorn agents.reporter:app --host localhost --port 8081
uvicorn agents.researcher:app --host localhost --port 8083
uvicorn agents.editor:app --host localhost --port 8082
uvicorn agents.publisher:app --host localhost --port 8084
```

## Agent Card URLs

Each agent exposes its capabilities via agent card:
- News Chief: `http://localhost:8080/.well-known/agent-card.json`
- Reporter: `http://localhost:8081/.well-known/agent-card.json`
- Editor: `http://localhost:8082/.well-known/agent-card.json`
- Researcher: `http://localhost:8083/.well-known/agent-card.json`
- Publisher: `http://localhost:8084/.well-known/agent-card.json`

## Archivist Integration

The Reporter agent integrates with an Elastic Cloud Archivist agent to search historical articles:

**API Endpoint**: `POST /api/agent_builder/converse`

**Request Format**:
```json
{
  "input": "Find historical news articles about: {search_query}",
  "agent_id": "archive-agent"
}
```

**Required Headers**:
- `Authorization: ApiKey {ELASTIC_ARCHIVIST_API_KEY}`
- `Content-Type: application/json`
- `kbn-xsrf: true`

**Response**: Multi-step conversational response with:
- Reasoning steps (agent's thought process)
- Tool calls (`platform.core.search` on `news_archive` index)
- Article results with highlights and references
- Conversation ID for follow-up queries

**Diagnostics**: Run `python test_archivist.py` to verify connectivity and test search functionality.

## Technology Stack

- **A2A SDK**: v0.3.8 ([a2a-python](https://github.com/a2aproject/a2a-python))
- **AI Model**: Anthropic Claude Sonnet 4
- **Search**: Elastic Serverless (Elastic Cloud)
- **Archivist API**: Elastic Conversational API (`/agent_builder/converse`)
- **Web Framework**: Starlette (via A2A SDK) + Mesop (UI)
- **Server**: Uvicorn ASGI server
- **HTTP Client**: httpx (async)
- **Language**: Python 3.10+

## License

This project is licensed under the MIT License.


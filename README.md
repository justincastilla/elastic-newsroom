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
  - Hosted on Elastic Cloud (Elastic Agent Builder)
  - Searches historical articles via Elastic Conversational API
  - Provides context about past coverage
  - Uses `platform.core.search` skill to query `news_archive` index
  - Returns article highlights, references, and reasoning

> Note: Elastic Agent Builder is enabled by default in serverless Elasticsearch projects. To begin using it, navigate to the Agents section in the navigation menu or search for "Agents" in the global search field within Kibana. 

## Quick Start

### Option 1: Docker (Recommended)

**Prerequisites:** Docker Engine 20.10+, Docker Compose 2.0+

```bash
# 1. Create environment file
cp .env.docker .env

# 2. Edit .env with your Anthropic API key
nano .env  # Add: ANTHROPIC_API_KEY=sk-ant-api03-xxx

# 3. Start all services
docker-compose up -d

# 4. Access the UI
open http://localhost:3001
```

**What's running:**
- All 5 agents (ports 8080-8084)
- MCP Server (8095), Event Hub (8090), Article API (8085)
- React UI (3001)

See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for complete Docker documentation.

### Option 2: Local Development

**Prerequisites:** Python 3.10+, Node.js 18+ (optional for UI)

```bash
# 1. Configure environment
cp env.example .env
# Edit .env with your API keys (see docs/configuration-guide.md)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start all services
make start-ui   # Start agents + React UI with hot reload

# Or start agents only
make start      # Agents with hot reload
```

Access the UI at http://localhost:3001

### Using the System

1. **Open UI**: http://localhost:3001
2. **Create Story**: Fill out the story assignment form
   - Topic: e.g., "Artificial Intelligence in Healthcare"
   - Angle: e.g., "Recent breakthroughs"
   - Target Length: e.g., 1000 words
3. **Submit**: Click "Assign Story"
4. **Watch Progress**: Real-time workflow visualization
5. **View Article**: Click on completed story

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
├── react-ui/                    # React UI
│   ├── src/                    # React source code
│   │   ├── components/         # UI components
│   │   ├── services/           # API services
│   │   └── hooks/              # Custom React hooks
│   ├── public/                 # Static assets
│   └── package.json            # Node.js dependencies
├── services/                    # Infrastructure services
│   ├── event_hub.py             # Event broadcasting (SSE)
│   └── article_api.py           # Article API for UI
├── scripts/                     # Utility scripts
│   ├── create_elasticsearch_index.py  # ES index setup
│   ├── start_newsroom.sh        # Start/stop all agents
│   └── start_event_hub.sh       # Start Event Hub
├── tests/                       # Test suite (pytest framework)
│   ├── conftest.py              # Pytest fixtures
│   ├── test_workflow_pytest.py  # Main workflow tests
│   ├── test_with_mocks.py       # Mock-based tests
│   ├── test_event_hub.py        # Event Hub tests
│   └── mocks/                   # Mock implementations
├── docs/                        # Documentation
│   ├── configuration-guide.md   # Environment setup
│   ├── elasticsearch-schema.md  # Index mapping
│   └── archivist-integration.md # Archivist setup
├── articles/                    # Published articles (auto-generated)
├── logs/                        # Agent logs (auto-generated)
├── Makefile                     # Build commands and shortcuts
├── requirements.txt             # Python dependencies
├── env.example                  # Environment template
└── README.md                    # This file
```

## Features

✅ **Currently Working**

- **Multi-Agent Coordination**: 5 agents communicate via A2A protocol
- **Complete Workflow**: End-to-end article production from assignment to publication
- **React UI**: Modern React interface with live agent monitoring and workflow visualization (port 3001)
- **Elasticsearch Integration**: Historical article indexing and search via `news_archive` index
- **Elastic Archivist Integration**: Cloud-based search agent via Conversational API
- **Claude Sonnet 4**: AI-powered research, writing, and editing
- **Process Management**: Single command to start/stop all agents
- **Comprehensive Logging**: Individual log files for each agent with detailed diagnostics
- **Hot Reload Support**: Development mode with auto-reload for agents
- **Article Data Flow**: Structured article data (headline, content, word count) passed through workflow
- **Real-time Monitoring**: Live agent status updates and workflow progress visualization
- **Archivist Diagnostics**: Standalone test tool to verify Elastic Cloud connectivity
- **Comprehensive Workflow Test**: Real-time monitoring with detailed agent activity display

🔄 **In Progress**

- Additional MCP server integrations
- Enhanced error handling and retry logic
- Performance monitoring and metrics

## Documentation

- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Docker deployment guide
- [TESTING.md](TESTING.md) - Testing documentation
- [docs/configuration-guide.md](docs/configuration-guide.md) - Environment setup
- [docs/architecture.md](docs/architecture.md) - Detailed architecture
- [docs/archivist-integration.md](docs/archivist-integration.md) - Archivist setup
- [docs/elasticsearch-schema.md](docs/elasticsearch-schema.md) - Index mapping

## Workflow Example

```
User submits story via React UI (http://localhost:3001)
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

## Common Commands

### Docker
```bash
docker-compose up -d         # Start all services
docker-compose logs -f       # View logs
docker-compose ps            # Check status
docker-compose down          # Stop all services
docker-compose up -d --build # Rebuild and restart
```

### Local Development
```bash
make start           # Start agents with hot reload
make start-ui        # Start agents + React UI
make stop            # Stop all services
make logs-color      # View colorized logs
make status          # Check agent health
make test            # Run tests
```

See `make help` for all available commands.

### Testing

```bash
make test            # Fast tests (no API keys needed!)
make test-all        # All tests including slow ones
make test-coverage   # Tests with coverage report
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Archivist Integration

The Reporter integrates with an Elastic Cloud Archivist agent (created using Agent Builder) to search historical articles via the A2A protocol.

**Key Details:**
- Searches `news_archive` Elasticsearch index
- Returns historical article highlights and references
- Created in Elastic Cloud using Agent Builder

For details on creating your own A2A-enabled agent in Elastic and finding your agent card URL, see the [Elastic Agent Builder A2A documentation](https://www.elastic.co/docs/solutions/search/agent-builder/a2a-server).

See [docs/archivist-integration.md](docs/archivist-integration.md) for complete setup guide.

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


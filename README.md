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
   - Consults Archivist for historical context
   - Integrates research findings into cohesive narratives

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

#### External Agent (A2A Protocol)

- **Archivist Agent**
  - Hosted on Elastic Cloud (Kibana Agent Builder)
  - Searches historical articles via A2A protocol
  - Provides context about past coverage
  - Accessed via agent card URL

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
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

# Stop all agents
./start_newsroom.sh --stop
```

### 5. Run the Workflow
```bash
python tests/test_newsroom_workflow.py
```

This will:
1. Assign a story via News Chief
2. Have Researcher gather information
3. Have Reporter write the article (consulting Archivist)
4. Have Editor review and refine the article
5. Have Publisher index to Elasticsearch and save to file

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
├── scripts/                     # Utility scripts
│   └── create_elasticsearch_index.py
├── tests/                       # Test suite
│   ├── test_newsroom_workflow.py    # End-to-end workflow test
│   └── test_elasticsearch_index.py  # ES index creation test
├── docs/                        # Documentation
│   ├── configuration-guide.md   # Environment setup
│   ├── elasticsearch-schema.md  # Index mapping
│   ├── news-chief-agent.md      # News Chief details
│   └── archivist-integration.md # Archivist setup
├── articles/                    # Published articles (auto-generated)
├── logs/                        # Agent logs (auto-generated)
├── start_newsroom.sh            # Start/stop all agents
├── requirements.txt             # Python dependencies
├── env.example                  # Environment template
└── README.md                    # This file
```

## Features

✅ **Currently Working**

- **Multi-Agent Coordination**: 5 agents communicate via A2A protocol
- **Complete Workflow**: End-to-end article production from assignment to publication
- **Elasticsearch Integration**: Historical article indexing and search
- **External Agent Integration**: Optional Archivist agent via A2A protocol
- **Claude Sonnet 4**: AI-powered research, writing, and editing
- **Process Management**: Single command to start/stop all agents
- **Comprehensive Logging**: Individual log files for each agent
- **Hot Reload Support**: Development mode with auto-reload

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
News Chief assigns story → Researcher gathers data →
Reporter writes article (consults Archivist) →
Editor reviews and refines → Publisher indexes to Elasticsearch
```

## Commands

### Start/Stop Agents
```bash
./start_newsroom.sh           # Start all agents
./start_newsroom.sh --reload  # Start with hot reload
./start_newsroom.sh --stop    # Stop all agents
```

### View Logs
```bash
tail -f logs/*.log            # All agents
tail -f logs/News_Chief.log   # Specific agent
```

### Run Tests
```bash
python tests/test_newsroom_workflow.py    # End-to-end workflow
python tests/test_elasticsearch_index.py  # Elasticsearch index test
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

## Technology Stack

- **A2A SDK**: v0.3.8 ([a2a-python](https://github.com/a2aproject/a2a-python))
- **AI Model**: Anthropic Claude Sonnet 4
- **Search**: Elastic Serverless
- **Web Framework**: Starlette (via A2A SDK)
- **Server**: Uvicorn ASGI server
- **Language**: Python 3.10+

## License

This project is licensed under the MIT License.


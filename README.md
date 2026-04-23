# Elastic News — AI-Powered Multi-Agent Newsroom

A multi-agent newsroom where five AI agents collaborate to research, write, edit, and publish news articles. Built on the [A2A protocol](https://github.com/a2aproject/a2a-python), [FastMCP](https://github.com/jlowin/fastmcp), [Tavily](https://tavily.com) web search, and Elasticsearch.

## How It Works

You submit a story topic through the React UI. From there, the system runs autonomously:

```
UI  →  News Chief assigns story
           ↓
       Reporter generates an outline and research questions
           ↓
       Researcher (Tavily web search) ──┐
       Archivist (Elasticsearch archive) ┘ → results sent back to Reporter
           ↓
       Reporter writes article from research + archive context
           ↓
       Editor reviews for grammar, tone, length
           ↓
       Publisher indexes to Elasticsearch, deploys, notifies subscribers
           ↓
       Article viewable in UI with source links
```

Each agent runs as its own A2A server. They discover each other via agent cards and communicate over JSON-RPC. The MCP server provides shared tools (research, outline generation, article writing, editing, tag generation) that agents call directly.

## Agents

| Agent | Port | Role |
|-------|------|------|
| News Chief | 8080 | Coordinates workflow, routes stories between agents |
| Reporter | 8081 | Writes articles, calls Researcher + Archivist in parallel |
| Editor | 8082 | Reviews drafts, suggests edits, approves for publication |
| Researcher | 8083 | Answers research questions via Tavily + Claude synthesis |
| Publisher | 8084 | Indexes to Elasticsearch, saves markdown, triggers CI/CD mock |

**Supporting services:** MCP Server (8095), Event Hub for SSE (8090), Article API (8085), React UI (3001).

**External:** An Archivist agent on Elastic Cloud (built with [Agent Builder](https://www.elastic.co/docs/solutions/search/agent-builder/a2a-server)) searches the `news_archive` index for historical context.

## Quick Start

### Docker (recommended)

```bash
cp .env.docker .env
# Edit .env — add ANTHROPIC_API_KEY and TAVILY_API_KEY at minimum
docker-compose up -d
open http://localhost:3001
```

### Local

```bash
cp env.example .env
# Edit .env with your keys (see docs/configuration-guide.md)
pip install -r requirements.txt
cd react-ui && npm install && cd ..
make start-ui        # agents + React UI with hot reload
```

Then open http://localhost:3001, fill in a topic, and hit **Assign Story**.

## Configuration

All config lives in `.env`. The required keys:

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API for content generation |
| `TAVILY_API_KEY` | Yes | Web search for research |
| `ELASTICSEARCH_ENDPOINT` | For publishing | Elasticsearch cluster URL |
| `ELASTICSEARCH_API_KEY` | For publishing | Elasticsearch auth |
| `ELASTIC_ARCHIVIST_AGENT_URL` | For archive search | Archivist A2A endpoint |
| `ELASTIC_ARCHIVIST_API_KEY` | For archive search | Archivist auth |
| `ANTHROPIC_MODEL` | No | Defaults to `claude-sonnet-4-6` |
| `LOG_FORMAT` | No | `text` (default) or `json` for structured logs |

## Elasticsearch

The Publisher indexes articles to an `news_archive` index. The mapping supports full-text search, `semantic_text` fields for vector search, and nested `research_sources` with real URLs from Tavily.

To create the index:

```bash
python scripts/create_elasticsearch_index.py
```

The Article API (`/articles/search`) supports three search modes: `keyword`, `semantic`, and `hybrid` (RRF). The Publisher also supports bulk indexing via `bulk_publish`.

## Project Structure

```
agents/              A2A agents (news_chief, reporter, editor, researcher, publisher)
agents/base_agent.py Shared utilities: A2A client, Anthropic calls, MCP, event publishing
mcp_servers/         FastMCP tool server (Tavily research, Claude writing/editing, mocks)
services/            Event Hub (SSE), Article API (FastAPI)
utils/               Logging (text + JSON), config, MCP client, env loader
react-ui/            React frontend with live workflow visualization
scripts/             Start scripts, ES index creation, Docker entrypoint
tests/               Pytest suite with mock Anthropic, Tavily, and Elasticsearch
docs/                Architecture, configuration, Archivist integration guides
```

## Tech Stack

A2A SDK 0.3.26, FastMCP 3.2.4, Anthropic Claude, Tavily 0.7.23, Elasticsearch 9.x, Starlette, React, Uvicorn, httpx.

## Common Commands

```bash
# Docker
docker-compose up -d          # start
docker-compose logs -f        # tail logs
docker-compose down           # stop

# Local
make start-ui                 # agents + UI
make stop                     # stop all
make test                     # run tests (no API keys needed)
make logs-color               # colorized log tail
```

## Docs

Detailed guides live in `docs/`: [configuration](docs/configuration-guide.md), [architecture](docs/architecture.md), [Archivist setup](docs/archivist-integration.md), [testing](TESTING.md), [Docker](DOCKER_QUICKSTART.md).

## License

MIT

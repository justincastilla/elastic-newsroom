# Elastic News - AI-Powered Digital Newsroom

A demonstration of Agent2Agent (A2A) protocols and Model Context Protocol (MCP) integration in a multi-agent newsroom system, built using the official [A2A Python SDK](https://github.com/a2aproject/a2a-python).

## Overview

This project implements a digital newsroom where specialized AI agents collaborate to research, write, edit, and publish news articles. The system showcases:

- **Official A2A SDK**: Using the [a2a-sdk](https://github.com/a2aproject/a2a-python) for multi-agent coordination and communication
- **MCP Integration**: Following the [A2A-MCP pattern](https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents/a2a_mcp) for standardized tool access
- **Reference Implementation**: Based on the [A2A-MCP Travel Agent example](https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents/a2a_mcp) which demonstrates proper A2A agent structure and MCP integration
- **Claude Sonnet 4**: Using Anthropic's latest model for AI-powered content generation and analysis
- **Elasticsearch Integration**: For historical article search and analytics
- **Complete Workflow**: From story assignment to publication

## Architecture

### Agents

#### Internal Agents (Locally Hosted)
- **News Chief** ✅: Coordinator/client agent that assigns stories and oversees workflow
- **Reporter Agent** ✅: Writes articles based on research, integrates data from multiple sources
- **Researcher Agent** ✅: Gathers facts, statistics, and background information using Anthropic
- **Editor Agent** ✅: Reviews articles for grammar, tone, consistency, and length

#### External Agents (A2A Protocol)
- **Archivist Agent** ✅: Searches historical articles using Elasticsearch (hosted on Elastic Serverless)
  - URL: `<elastic_kibana_endpoint>/api/agent_builder/a2a/archive-agent`
  - Provider: Elastic
  - Protocol: A2A 0.3.0
  - Features: Full-text search, ES|QL queries, index exploration

#### Planned Agents
- **Printer Agent**: Publishes approved articles via CI/CD

### MCP Servers (Dummy for Testing)
- News API MCP Server
- Fact-Checking MCP Server
- Grammar Checker MCP Server
- SEO Analysis MCP Server
- CMS MCP Server
- CI/CD MCP Server
- Analytics MCP Server

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys and configuration

# Start the newsroom (coming soon)
python main.py
```

## Project Structure

```
elastic-news/
├── agents/                 # A2A agents using official SDK
│   ├── news_chief.py
│   ├── reporter.py
│   ├── researcher.py
│   ├── archive.py
│   ├── editor.py
│   └── printer.py
├── mcp_servers/           # MCP server implementations
│   ├── news_api/
│   ├── fact_checking/
│   ├── grammar/
│   ├── seo/
│   ├── cms/
│   └── analytics/
├── elasticsearch/         # Elasticsearch integration
│   ├── client.py
│   └── queries.py
├── config/                # Configuration files
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Development Status

🚧 **In Development** - This project is being built iteratively:

1. ✅ **Project Setup** - Basic structure and official A2A SDK integration
2. 🔄 **Single Agent** - Creating first A2A agent (News Chief)
3. ⏳ **Agent Communication** - Adding second agent and testing A2A communication
4. ⏳ **MCP Integration** - Adding MCP servers following A2A-MCP pattern
5. ⏳ **Full Newsroom** - Complete workflow implementation

## Features (Planned)

- Multi-agent coordination via official A2A SDK
- Standardized tool access via MCP servers
- Elasticsearch-powered historical article search
- Complete newsroom workflow automation
- Real-time agent communication and status tracking
- Comprehensive error handling and retry logic

## Documentation

- [Setup Guide](docs/setup.md) (coming soon)
- [API Reference](docs/api.md) (coming soon)
- [Agent Communication](docs/a2a-protocol.md) (coming soon)
- [MCP Integration](docs/mcp-servers.md) (coming soon)
- [Workflow Examples](docs/workflows.md) (coming soon)

## Contributing

Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


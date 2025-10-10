# Elastic News UI

Web interface for the Elastic News newsroom system.

## Overview

The UI provides a simple, clean interface to:
- Assign stories to the News Chief agent
- Monitor workflow progress
- View completed articles with all metadata

## Architecture

- **Framework**: Mesop (Google's web UI framework)
- **Server**: Built-in Mesop server
- **Protocol**: A2A for agent communication
- **Port**: 3000 (configurable via `UI_PORT` env var)

## Quick Start

### Option 1: Start with Agents

```bash
# Start all agents + UI
./start_newsroom.sh --with-ui

# Start all agents with hot reload + UI
./start_newsroom.sh --with-ui --reload
```

**Note:** UI always has hot reload enabled (Mesop default). The `--reload` flag only affects agents.

### Option 2: Start UI Only

```bash
# Start just the UI (agents must already be running)
./start_ui.sh
```

**Note:** Mesop has hot reload enabled by default, so any changes to Python files in `ui/` will automatically reload the UI.

## Pages

### Home Page (`/`)
Story assignment form with fields:
- **Topic**: Main subject of the article
- **Angle**: Editorial perspective or focus
- **Target Length**: Desired word count
- **Deadline**: Publication deadline
- **Priority**: low, medium, high, or urgent

Submit button triggers the full workflow:
1. News Chief assigns to Reporter
2. Reporter requests research from Researcher
3. Reporter writes article (consulting Archivist)
4. Editor reviews and refines
5. Publisher indexes to Elasticsearch

The UI polls News Chief every 2 seconds until the article is published, then redirects to the article page.

### Article Page (`/article/{story_id}`)
Displays completed article with:

**Primary Section** (always visible):
- Headline
- Full article content
- Word count

**Metadata Sections** (expandable):
- Research Data & Sources
- Editorial Review
- Tags
- Publication timestamp
- Elasticsearch document ID

## Development

### Dependencies

Install dependencies using pip:

```bash
cd ui
pip install -e .
```

Or using the start script (auto-installs):

```bash
./start_ui.sh
```

### Project Structure

```
ui/
├── main.py                   # Entry point
├── pyproject.toml            # Dependencies
├── services/
│   └── news_chief_client.py  # A2A client for News Chief
├── state/
│   └── app_state.py          # Mesop state management
├── pages/
│   ├── home.py               # Story assignment form
│   └── article.py            # Article viewer
├── components/               # Reusable UI components (future)
└── styles/                   # Custom styles (future)
```

### Environment Variables

```bash
# UI server configuration
UI_HOST=0.0.0.0
UI_PORT=3000

# News Chief connection
NEWS_CHIEF_URL=http://localhost:8080
```

## A2A Integration

The UI communicates with News Chief via the A2A protocol:

1. **Agent Card Discovery**: Fetches `/.well-known/agent-card.json`
2. **Task Submission**: Posts to `/task` endpoint with JSON payload
3. **Status Polling**: Polls `/task` with `get_story_status` action
4. **Response Handling**: Parses A2A response and extracts article data

See `services/news_chief_client.py` for implementation details.

## Troubleshooting

### UI won't start

**Check if port 3000 is available:**
```bash
lsof -ti:3000
```

**Kill process on port 3000:**
```bash
kill -9 $(lsof -ti:3000)
```

### Can't connect to News Chief

**Verify News Chief is running:**
```bash
curl http://localhost:8080/.well-known/agent-card.json
```

**Start agents:**
```bash
./start_newsroom.sh
```

### Article not displaying

**Check story data structure:**
The UI expects the following fields in the response:
- `article.headline` or `headline`
- `article.content` or `content`
- `article.word_count` or `word_count`
- `research_data` (optional)
- `editorial_review` (optional)
- `tags` (optional)
- `published_at` (optional)
- `elasticsearch_id` (optional)

## Future Enhancements (Post-MVP)

- Real-time workflow tracking with progress bar
- Story list/history page
- Agent health monitoring
- Search and filtering
- User authentication
- WebSocket support for live updates
- Markdown editor for manual article editing
- Multi-story assignment

## Contributing

The UI is completely isolated from the agents:
- No changes to agent code required
- All communication via A2A protocol
- Self-contained in `/ui` folder

To add features:
1. Create components in `ui/components/`
2. Add pages in `ui/pages/` with `@me.page` decorator
3. Update state in `ui/state/app_state.py`
4. Add services in `ui/services/` for A2A communication

## License

MIT License - same as parent project

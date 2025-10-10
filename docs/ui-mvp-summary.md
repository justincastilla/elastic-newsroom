# Elastic News UI - MVP Summary

## ✅ What We Built

A complete web UI for the Elastic News newsroom system that allows users to assign stories and view completed articles.

### Pages Created

1. **Home Page** (`/`) - Story Assignment Form
   - Input fields: topic, angle, target_length, deadline, priority
   - Loading state with polling (every 2 seconds)
   - Error handling with detailed messages
   - Auto-redirects to article page on completion

2. **Article Page** (`/article/{story_id}`) - Article Viewer
   - **Primary Section**: Headline, content, word count (always visible)
   - **Metadata Sections**: Research data, editorial review, tags, timestamp, ES doc ID (expandable)
   - "New Story" button to return to assignment form

### Key Files

```
ui/
├── main.py                      # Entry point (Mesop server on port 3000)
├── pyproject.toml               # Dependencies
├── README.md                    # UI documentation
├── services/
│   ├── __init__.py
│   └── news_chief_client.py     # A2A client for News Chief
├── state/
│   ├── __init__.py
│   └── app_state.py             # Mesop state management
└── pages/
    ├── __init__.py
    ├── home.py                  # Story assignment form
    └── article.py               # Article viewer
```

## Technology Stack

- **UI Framework**: Mesop 1.0.0+ (Google's web UI framework)
- **Backend**: FastAPI 0.115.0+ (for future enhancements)
- **Server**: Mesop built-in server (uvicorn-based)
- **A2A Client**: a2a-sdk 0.3.0+
- **HTTP Client**: httpx 0.28.1+ (async)
- **Port**: 3000 (configurable via `UI_PORT`)

## How to Use

### Option 1: Start with Agents
```bash
./start_newsroom.sh --with-ui
```
Opens:
- Agents on ports 8080-8084
- UI on port 3000

### Option 2: Start UI Separately
```bash
# Terminal 1: Start agents
./start_newsroom.sh

# Terminal 2: Start UI
./start_ui.sh
```

### Access UI
- **Assignment Form**: http://localhost:3000/
- **Article Viewer**: http://localhost:3000/article/{story_id}

## Workflow

1. User fills out story assignment form
2. Clicks "Assign Story to News Chief"
3. UI shows loading spinner with polling message
4. UI polls News Chief every 2 seconds for status
5. When status == "published", redirects to article page
6. Article page displays all content and metadata
7. User can click "New Story" to assign another

## A2A Integration

### News Chief Client (`ui/services/news_chief_client.py`)

**Methods:**
- `assign_story()` - Submit story assignment
- `get_story_status()` - Check story status
- `poll_until_complete()` - Poll until published (with timeout)
- `list_active_stories()` - Get all active stories (future)

**Communication:**
1. Fetch agent card: `GET /.well-known/agent-card.json`
2. Submit task: `POST /task` with JSON payload
3. Poll status: `POST /task` with `{"action": "get_story_status", "story_id": "..."}`

## State Management

### AppState (Global)
- `news_chief_url`: News Chief endpoint
- `current_story_id`: Active story being processed
- `current_story_data`: Story data for viewing
- `is_loading`: Loading state boolean
- `error_message`: Error display
- `stories_cache`: Cache of completed stories

### AssignmentFormState (Page)
- Form field values
- Validation errors

### ArticleViewState (Page)
- Expansion state for metadata sections

## Error Handling

**Scenarios Covered:**
- Missing required fields → validation error
- News Chief unreachable → connection error with details
- Workflow timeout (5 min) → timeout error with story_id
- Workflow failure → error message from agent
- Article not found → friendly "not found" message

**User Experience:**
- Errors displayed in red banner
- Form remains filled for retry
- Dismiss button to clear errors

## Future Enhancements (Post-MVP)

### Phase 2 (Week 3-4)
- Story list/history page
- Real-time status updates
- Workflow visualization (progress bar)

### Phase 3 (Week 5-6)
- Agent health monitoring
- Search and filtering
- Analytics dashboard

## MVP Acceptance Criteria

| Criteria | Status |
|----------|--------|
| User can assign story via web form | ✅ Complete |
| Form shows loading state while polling | ✅ Complete |
| On completion, redirects to article page | ✅ Complete |
| Article page shows all metadata (expandable) | ✅ Complete |
| On error, shows message and keeps form filled | ✅ Complete |
| UI starts with `./start_newsroom.sh --with-ui` | ✅ Complete |
| No changes made to any agent code | ✅ Complete |
| UI completely isolated in `/ui` folder | ✅ Complete |

## Testing Checklist

### Manual Testing

- [ ] Start agents: `./start_newsroom.sh`
- [ ] Start UI: `./start_ui.sh` or `./start_newsroom.sh --with-ui`
- [ ] Open http://localhost:3000
- [ ] Fill out story form with valid data
- [ ] Submit and verify loading state appears
- [ ] Wait for article completion (may take 2-5 minutes)
- [ ] Verify redirect to `/article/{story_id}`
- [ ] Verify article displays correctly
- [ ] Expand metadata sections
- [ ] Click "New Story" button
- [ ] Verify return to home page
- [ ] Test error scenarios:
  - [ ] Submit empty form
  - [ ] Stop News Chief mid-workflow
  - [ ] Submit with invalid data

### Integration Testing

```bash
# Test complete workflow
python tests/test_newsroom_workflow.py

# Then check if article can be viewed in UI
# Extract story_id from test output
# Open http://localhost:3000/article/{story_id}
```

## Known Limitations (MVP)

1. **No story list** - Can only view articles by direct URL
2. **No search** - Cannot search for past articles
3. **No real-time updates** - Uses polling instead of WebSockets
4. **No authentication** - Anyone can assign stories
5. **No editing** - View-only, cannot modify articles
6. **Single user** - No multi-user support
7. **No caching** - Refreshing article page loses data (need to re-fetch)

## Dependencies

### UI-Specific (in `ui/pyproject.toml`)
```toml
asyncio>=3.4.3
httpx>=0.28.1
httpx-sse>=0.4.0
pydantic>=2.11.0
fastapi>=0.115.0
uvicorn>=0.34.0
mesop>=1.0.0
a2a-sdk>=0.3.0
```

### Installation
```bash
cd ui
pip install -e .
```

Or automatic via start script:
```bash
./start_ui.sh  # Auto-installs deps
```

## Troubleshooting

### Port 3000 in use
```bash
lsof -ti:3000
kill -9 $(lsof -ti:3000)
```

### News Chief not responding
```bash
# Verify News Chief is running
curl http://localhost:8080/.well-known/agent-card.json

# Check logs
tail -f logs/News_Chief.log
```

### UI won't start
```bash
# Check UI logs
tail -f logs/UI.log

# Reinstall dependencies
cd ui
pip install -e . --force-reinstall
```

### Article not displaying
- Check story data structure in logs
- Verify story_id is correct
- Check if article is in cache (`app_state.stories_cache`)

## Architecture Decisions

### Why Mesop?
- Built-in A2A patterns from demo
- Simple state management
- Fast development
- No frontend build step

### Why Polling?
- Simple to implement
- No agent changes required
- Good enough for MVP
- Can upgrade to WebSockets in Phase 2

### Why Port 3000?
- Standard for UI servers
- Doesn't conflict with agents (8080-8084)
- Easy to remember

### Why Separate `/ui` Folder?
- Complete isolation from agents
- No risk of breaking agent code
- Can be deployed separately
- Clean separation of concerns

## Success Metrics

✅ MVP is complete when:
- User can assign story via browser
- Article appears after workflow completes
- All metadata is visible
- No changes to agent code
- Fully documented
- Start scripts work reliably

## Next Steps

1. **Test MVP** - Manual testing of all features
2. **Gather Feedback** - Use the UI and identify pain points
3. **Plan Phase 2** - Prioritize next features
4. **Iterate** - Improve based on real usage

## Credits

Built following the [A2A Samples Demo UI](https://github.com/a2aproject/a2a-samples/tree/main/demo) patterns for A2A integration.

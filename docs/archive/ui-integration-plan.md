# Elastic News UI Integration Plan

## Overview

This document outlines the plan to integrate a web-based UI for the Elastic News newsroom system, based on the [A2A Samples Demo UI](https://github.com/a2aproject/a2a-samples/tree/main/demo).

## Current State

**Elastic News System:**
- 5 local A2A agents running on ports 8080-8084
- News Chief as coordinator agent
- All agents communicate via A2A protocol
- No user interface (CLI/API only)

**A2A Demo UI:**
- Mesop-based web application
- Dynamic agent discovery and interaction
- Conversation-based interface
- Support for multiple agents
- Built on Google ADK + A2A SDK

## Integration Goals

1. **Newsroom-Specific UI**: Adapt the A2A demo UI to create a newsroom-focused interface
2. **Story Assignment**: Allow users to assign stories to News Chief via web interface
3. **Workflow Visibility**: Track story progress through the newsroom workflow
4. **Article Management**: View completed articles, editorial reviews, and publication status
5. **Agent Monitoring**: Monitor all 5 agents and their current tasks

## Architecture Analysis

### A2A Demo UI Structure

```
demo/ui/
├── main.py                    # FastAPI + Mesop entry point
├── pyproject.toml             # Dependencies
├── components/                # UI components
│   ├── agent_list.py         # Display A2A agents
│   ├── conversation.py       # Chat interface
│   ├── chat_bubble.py        # Message display
│   ├── header.py             # Page header
│   ├── side_nav.py           # Navigation
│   └── ...
├── pages/                     # Page components
│   ├── home.py               # Main conversation list
│   └── ...
├── service/                   # Backend services
│   ├── client/               # A2A client communication
│   ├── server/               # Server-side logic
│   └── types.py              # Data models
├── state/                     # State management
│   ├── state.py              # Global app state
│   ├── agent_state.py        # Agent-specific state
│   └── host_agent_service.py # Host agent coordination
├── styles/                    # CSS/styling
└── utils/                     # Utility functions
```

### Key Technologies

**Dependencies:**
- `mesop>=1.0.0` - Web UI framework (Google)
- `fastapi>=0.115.0` - Web server
- `uvicorn>=0.34.0` - ASGI server
- `a2a-sdk>=0.3.0` - A2A protocol (matches our version 0.3.8)
- `google-adk[a2a]>=1.7.0` - Google Agent Development Kit
- `google-genai>=1.9.0` - Gemini AI (for host agent intelligence)
- `httpx>=0.28.1` - Async HTTP client
- `pandas>=2.2.0` - Data display
- `pydantic>=2.11.0` - Data validation

**Key Differences from Elastic News:**
- They use Google ADK + Gemini, we use direct A2A SDK + Claude
- They use a "host agent" pattern, we have News Chief as coordinator
- They support dynamic agent discovery, we have fixed 5 agents

## Integration Strategy

### Option 1: Fork and Customize (Recommended)

**Approach:** Use the A2A demo UI as a starting point, customize for newsroom workflow

**Pros:**
- Proven A2A integration
- Mature UI components
- Established patterns for agent communication
- Less development time

**Cons:**
- Dependency on Google ADK (can be replaced)
- Some components may not fit newsroom UX
- Need to adapt state management

**Effort:** Medium (2-3 weeks)

### Option 2: Build Custom UI

**Approach:** Build newsroom-specific UI from scratch using same tech stack

**Pros:**
- Tailored exactly to newsroom workflow
- No unnecessary dependencies
- Complete control over UX

**Cons:**
- More development time
- Need to implement A2A client from scratch
- Risk of bugs in custom A2A integration

**Effort:** High (4-6 weeks)

### Option 3: Hybrid Approach (RECOMMENDED)

**Approach:** Use A2A demo's service layer + state management, build custom newsroom UI components

**Pros:**
- Reuse proven A2A communication code
- Custom newsroom-focused UX
- Avoid Google ADK dependency
- Faster than Option 2

**Cons:**
- Need to understand demo's architecture deeply
- Some refactoring required

**Effort:** Medium-High (3-4 weeks)

## MVP Scope (Finalized)

**Goal:** Minimal viable UI that can interact with News Chief and view completed articles

**Core Features:**
1. **Communicate with News Chief** - Send story assignments via web form
2. **News Chief Triggers Workflow** - Assignment automatically triggers full workflow (Researcher → Reporter → Editor → Publisher)
3. **View Article** - Redirect to dedicated article page when complete

**Technical Decisions:**
- ✅ **Display Method:** Redirect to article page (`/article/{story_id}`)
- ✅ **Completion Detection:** Polling News Chief every 2-3 seconds
- ✅ **Error Handling:** Show detailed error message, keep form filled for retry
- ✅ **Article Metadata:** Show ALL metadata
  - Primary (always visible): Headline, content, word count
  - Secondary (expandable section): Research data, editorial review, tags, timestamp, ES doc ID
- ✅ **Technology Stack:** Mesop (from A2A demo) + FastAPI
- ✅ **Styling:** Bootstrap or Tailwind for clean, professional look
- ✅ **UI Port:** 3000 (standard UI port)
- ✅ **Start Script:** Flag-based (`./start_newsroom.sh --with-ui`)
- ✅ **Development Priority:** Speed (copy from A2A demo, iterate later)
- ✅ **Article Source:** A2A responses only (not filesystem)

**Out of Scope for MVP:**
- Real-time workflow tracking
- Agent health monitoring
- Search/filtering
- Analytics
- Multi-story management
- Article list/history

**Key Principle:**
- UI is completely self-contained in `/ui` folder
- No changes to existing agents
- UI communicates with agents only via A2A protocol
- Agents remain unchanged and continue to work via CLI/API

## Recommended Implementation Plan

### Phase 1: Setup and Analysis (Week 1)

1. **Clone and Run A2A Demo**
   - Set up local demo UI
   - Test with our existing agents
   - Document agent interaction patterns

2. **Create UI Directory Structure**
   ```
   elastic-news/
   ├── ui/                          # New directory
   │   ├── main.py                  # FastAPI + Mesop entry
   │   ├── pyproject.toml           # UI-specific dependencies
   │   ├── components/              # Newsroom UI components
   │   ├── pages/                   # Newsroom pages
   │   ├── services/                # A2A client services (from demo)
   │   ├── state/                   # State management (adapted)
   │   └── styles/                  # Newsroom styling
   ```

3. **Dependencies Analysis**
   - Remove Google ADK dependency
   - Keep: mesop, fastapi, uvicorn, a2a-sdk, httpx
   - Add: anthropic (for UI-side Claude calls if needed)

### Phase 2: Core A2A Integration (Week 2)

1. **Adapt Service Layer**
   - Extract A2A client code from demo
   - Replace Google ADK host agent with News Chief client
   - Implement agent card discovery for our 5 agents
   - Test basic A2A communication

2. **State Management**
   - Create `NewsroomState` class
   - Track: active stories, agent statuses, workflow stages
   - Implement real-time updates via polling or websockets

3. **News Chief Client**
   - Create `NewsChiefClient` service
   - Methods: `assign_story()`, `get_status()`, `list_stories()`
   - Handle A2A protocol interactions

### Phase 3: Newsroom UI Components (Week 3)

1. **Story Assignment Form**
   - Component: `components/story_form.py`
   - Fields: topic, angle, target_length, deadline, priority
   - Submit handler calls News Chief

2. **Story Dashboard**
   - Component: `components/story_dashboard.py`
   - Display active stories with status
   - Show which agent is working on each story
   - Real-time status updates

3. **Workflow Visualizer**
   - Component: `components/workflow_view.py`
   - Visual pipeline: Assignment → Research → Writing → Editing → Publishing
   - Highlight current stage for each story
   - Show agent activity

4. **Article Viewer**
   - Component: `components/article_viewer.py`
   - Display completed articles
   - Show editorial reviews
   - View research data and sources

5. **Agent Monitor**
   - Component: `components/agent_monitor.py`
   - Grid of 5 agents with status indicators
   - Health checks
   - Current tasks

### Phase 4: Pages and Navigation (Week 4)

1. **Dashboard Page** (`pages/dashboard.py`)
   - Overview of all active stories
   - Quick stats (articles in progress, completed today, etc.)
   - Recent activity feed

2. **New Story Page** (`pages/new_story.py`)
   - Story assignment form
   - Templates for common story types
   - Quick assign to News Chief

3. **Stories Page** (`pages/stories.py`)
   - List all stories (active + completed)
   - Filters: by status, by topic, by date
   - Search functionality

4. **Article Page** (`pages/article.py`)
   - Full article view
   - Editorial review details
   - Research sources
   - Publication metadata

5. **Agents Page** (`pages/agents.py`)
   - Agent status monitoring
   - View agent cards
   - Test agent connectivity

### Phase 5: Polish and Deploy (Week 5-6)

1. **Styling and UX**
   - Newsroom-themed design
   - Responsive layout
   - Loading states and error handling

2. **Real-time Updates**
   - Implement polling or websockets
   - Auto-refresh story statuses
   - Notifications for completed articles

3. **Testing**
   - End-to-end workflow tests
   - Component tests
   - A2A communication tests

4. **Documentation**
   - UI setup guide
   - User guide
   - Developer documentation

5. **Deployment**
   - Containerize UI application
   - Update `start_newsroom.sh` to include UI
   - Environment configuration

## Technical Implementation Details

### News Chief Client Service

```python
# ui/services/news_chief_client.py
class NewsChiefClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.agent_card_url = f"{base_url}/.well-known/agent-card.json"

    async def assign_story(
        self,
        topic: str,
        angle: str,
        target_length: int,
        deadline: str,
        priority: str
    ) -> dict:
        """Assign a new story via A2A protocol"""
        # Implementation using A2A SDK

    async def get_story_status(self, story_id: str) -> dict:
        """Get status of a specific story"""

    async def list_active_stories(self) -> list[dict]:
        """List all active stories"""
```

### Newsroom State

```python
# ui/state/newsroom_state.py
@dataclass
class Story:
    story_id: str
    topic: str
    angle: str
    status: str  # assigned, researching, writing, editing, publishing, published
    current_agent: str
    assigned_at: datetime
    updated_at: datetime
    article: Optional[str] = None
    research_data: Optional[dict] = None
    editorial_review: Optional[dict] = None

class NewsroomState:
    stories: dict[str, Story] = {}
    agents_status: dict[str, dict] = {}

    def add_story(self, story: Story):
        """Add new story to state"""

    def update_story_status(self, story_id: str, status: str):
        """Update story status"""

    def get_active_stories(self) -> list[Story]:
        """Get all active stories"""
```

### Story Assignment Component

```python
# ui/components/story_form.py
@me.component
def story_form():
    state = me.state(PageState)

    with me.box(style=FORM_STYLE):
        me.input(
            label="Topic",
            value=state.topic,
            on_input=on_topic_change
        )
        me.input(
            label="Angle",
            value=state.angle,
            on_input=on_angle_change
        )
        me.input(
            label="Target Length (words)",
            type="number",
            value=state.target_length,
            on_input=on_length_change
        )
        me.select(
            label="Priority",
            options=["low", "medium", "high", "urgent"],
            value=state.priority,
            on_selection_change=on_priority_change
        )
        me.button(
            "Assign Story",
            on_click=assign_story
        )

def assign_story(e: me.ClickEvent):
    """Submit story to News Chief"""
    state = me.state(PageState)
    app_state = me.state(AppState)

    # Call News Chief via A2A
    result = await app_state.news_chief_client.assign_story(
        topic=state.topic,
        angle=state.angle,
        target_length=state.target_length,
        deadline=state.deadline,
        priority=state.priority
    )

    # Add to stories list
    app_state.add_story(result['story_id'])
```

## UI Mockup Structure

### Dashboard View
```
┌─────────────────────────────────────────────────────────┐
│ ELASTIC NEWS - Newsroom Dashboard                       │
├─────────────────────────────────────────────────────────┤
│ [New Story] [Stories] [Articles] [Agents]               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Active Stories (3)                                       │
│ ┌────────────────────────────────────────────────────┐  │
│ │ story_20251009_120000                               │  │
│ │ Topic: AI in Healthcare                             │  │
│ │ Status: [====●────] Editing                         │  │
│ │ Editor (8082) reviewing...                          │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ┌────────────────────────────────────────────────────┐  │
│ │ story_20251009_113000                               │  │
│ │ Topic: Quantum Computing Breakthrough               │  │
│ │ Status: [==●──────] Researching                     │  │
│ │ Researcher (8083) gathering data...                 │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ Agent Status                                             │
│ ┌──────┬──────┬──────┬──────┬──────┐                   │
│ │ News │Report│Editor│Resear│Publis│                   │
│ │ Chief│ er   │      │cher  │ her  │                   │
│ │  🟢  │  🟡  │  🟡  │  🟢  │  ⚪  │                   │
│ └──────┴──────┴──────┴──────┴──────┘                   │
└─────────────────────────────────────────────────────────┘
```

### New Story View
```
┌─────────────────────────────────────────────────────────┐
│ ELASTIC NEWS - Assign New Story                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Story Details                                            │
│ ┌────────────────────────────────────────────────────┐  │
│ │ Topic:  [________________________]                  │  │
│ │                                                     │  │
│ │ Angle:  [________________________]                  │  │
│ │                                                     │  │
│ │ Target Length: [1000] words                        │  │
│ │                                                     │  │
│ │ Deadline: [2025-10-15]                             │  │
│ │                                                     │  │
│ │ Priority: [Medium ▼]                               │  │
│ │                                                     │  │
│ │         [Assign to News Chief]                     │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ Quick Templates:                                         │
│ • Tech Product Launch                                    │
│ • Industry Analysis                                      │
│ • Executive Interview                                    │
│ • Event Coverage                                         │
└─────────────────────────────────────────────────────────┘
```

## File Structure After Integration

```
elastic-news/
├── agents/                      # Existing agents (unchanged)
│   ├── news_chief.py
│   ├── reporter.py
│   ├── researcher.py
│   ├── editor.py
│   └── publisher.py
├── ui/                          # NEW: Web UI
│   ├── main.py                  # FastAPI + Mesop app
│   ├── pyproject.toml           # UI dependencies
│   ├── requirements.txt         # Generated from pyproject.toml
│   ├── components/              # UI components
│   │   ├── __init__.py
│   │   ├── story_form.py
│   │   ├── story_dashboard.py
│   │   ├── workflow_view.py
│   │   ├── article_viewer.py
│   │   ├── agent_monitor.py
│   │   ├── chat_bubble.py       # From A2A demo
│   │   └── header.py            # From A2A demo
│   ├── pages/                   # Page components
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── new_story.py
│   │   ├── stories.py
│   │   ├── article.py
│   │   └── agents.py
│   ├── services/                # Backend services
│   │   ├── __init__.py
│   │   ├── news_chief_client.py
│   │   ├── agent_client.py      # Generic A2A client (from demo)
│   │   └── types.py
│   ├── state/                   # State management
│   │   ├── __init__.py
│   │   ├── newsroom_state.py
│   │   └── app_state.py
│   ├── styles/                  # CSS/styling
│   │   ├── __init__.py
│   │   └── newsroom_theme.py
│   └── utils/                   # Utilities
│       ├── __init__.py
│       └── formatting.py
├── scripts/
├── tests/
├── docs/
│   └── ui-integration-plan.md   # This document
├── start_newsroom.sh            # Updated to include UI
├── start_ui.sh                  # NEW: Start UI separately
└── README.md                    # Updated with UI instructions
```

## Updated Start Script

```bash
# start_newsroom.sh - Add UI support

# ... existing agent startup code ...

# Start UI (port 12000)
if [ "$START_UI" != "false" ]; then
    echo -e "${YELLOW}🌐 Starting UI on port 12000...${NC}"
    cd ui
    uv run main.py > ../logs/UI.log 2>&1 &
    UI_PID=$!
    echo "UI:$UI_PID" >> "../$PID_FILE"
    cd ..
    echo -e "${GREEN}   ✅ UI started (PID: $UI_PID)${NC}"
    echo -e "${BLUE}      Logs: logs/UI.log${NC}"
    echo -e "${BLUE}      URL: http://localhost:12000${NC}"
    echo ""
fi
```

## Environment Variables

```bash
# .env additions for UI

# UI Configuration
UI_PORT=12000
UI_HOST=0.0.0.0

# News Chief connection for UI
NEWS_CHIEF_URL=http://localhost:8080

# Optional: UI-specific Claude API key (if different from agents)
UI_ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

## Testing Strategy

### Unit Tests
- Component rendering tests
- Service layer tests (A2A communication)
- State management tests

### Integration Tests
- Story assignment flow
- Workflow progression
- Agent status updates

### E2E Tests
1. Assign story via UI
2. Monitor workflow through all stages
3. View completed article
4. Verify Elasticsearch indexing

## Deployment Considerations

### Container Setup
```dockerfile
# ui/Containerfile
FROM python:3.12-slim

WORKDIR /app/ui

# Install UV
RUN pip install uv

# Copy UI files
COPY ui/ .

# Install dependencies
RUN uv sync

# Expose UI port
EXPOSE 12000

# Run UI
CMD ["uv", "run", "main.py"]
```

### Docker Compose (Future)
```yaml
version: '3.8'
services:
  news-chief:
    build: .
    command: uvicorn agents.news_chief:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"

  # ... other agents ...

  ui:
    build: ./ui
    ports:
      - "12000:12000"
    depends_on:
      - news-chief
      - reporter
      - editor
      - researcher
      - publisher
    environment:
      - NEWS_CHIEF_URL=http://news-chief:8080
```

## Migration Path (MVP-First)

### MVP: Basic Story Assignment & Article Viewing (Week 1-2)

**Pages:**
1. **Home/Assignment Page** (`/`)
   - Story assignment form with fields: topic, angle, target_length, deadline, priority
   - Submit button → calls News Chief via A2A
   - Loading spinner while workflow executes (polls every 2-3 seconds)
   - On completion → redirect to `/article/{story_id}`
   - On error → show error message, keep form filled

2. **Article Page** (`/article/{story_id}`)
   - **Primary Section** (always visible):
     - Headline
     - Article content
     - Word count
   - **Metadata Section** (expandable/collapsible):
     - Research data/sources
     - Editorial review feedback
     - Tags
     - Publication timestamp
     - Elasticsearch document ID
   - "New Story" button → back to home

**Deliverables:**
- ✅ Can assign stories via web UI
- ✅ News Chief triggers full workflow automatically
- ✅ View completed article with ALL metadata
- ✅ UI completely isolated in `/ui` folder
- ✅ Zero changes to existing agents
- ✅ Clean, professional styling (Bootstrap/Tailwind)
- ✅ Start with `./start_newsroom.sh --with-ui`

**Technical Implementation:**
1. Mesop UI framework (from A2A demo patterns)
2. FastAPI backend on port 3000
3. A2A client for News Chief communication
4. Polling mechanism using async/await
5. Bootstrap/Tailwind for styling
6. Error handling with detailed messages
7. Expandable metadata section (JavaScript accordion or Mesop component)

### Phase 2: Enhanced UX (Week 3-4) - POST-MVP
- Real-time status updates
- Story list/history
- Workflow visualization
- **Deliverable:** Track multiple stories, see progress

### Phase 3: Full Feature Set (Week 5-6) - POST-MVP
- Agent monitoring
- Search and filters
- Analytics dashboard
- **Deliverable:** Complete newsroom management UI

## Success Criteria

1. ✅ Users can assign stories via web interface
2. ✅ Real-time tracking of story workflow
3. ✅ View completed articles and metadata
4. ✅ Monitor all 5 agents health and activity
5. ✅ No impact on existing CLI/API workflow
6. ✅ Single command start for all agents + UI
7. ✅ Responsive, intuitive UX

## Open Questions

1. **State Persistence**: Should UI state persist across restarts? (Probably yes - use SQLite or file-based storage)
2. **Authentication**: Do we need user login? (Not for MVP, add later if needed)
3. **Multi-user**: Support multiple users assigning stories simultaneously? (Nice to have, not MVP)
4. **WebSockets vs Polling**: Real-time updates via WebSockets or HTTP polling? (Polling for MVP, WS for v2)
5. **Article Editing**: Should UI allow editing articles before publication? (No for MVP - view only)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| A2A demo UI incompatibility | High | Test early with our agents, have fallback to custom build |
| Mesop learning curve | Medium | Team training, start with simple components |
| Google ADK dependency | Medium | Replace with direct A2A SDK early in Phase 2 |
| Real-time update complexity | Medium | Start with simple polling, optimize later |
| UI impacting agent performance | Low | Run UI on separate process, monitor resources |

## MVP Implementation Checklist

### Week 1: Setup & Core Infrastructure

**Day 1-2: Environment Setup**
- [ ] Create `/ui` directory structure
- [ ] Set up `pyproject.toml` with Mesop, FastAPI, a2a-sdk dependencies
- [ ] Clone A2A demo UI for reference
- [ ] Test A2A demo with our News Chief agent
- [ ] Document News Chief A2A interaction patterns

**Day 3-4: A2A Client Service**
- [ ] Extract A2A client patterns from demo
- [ ] Create `ui/services/news_chief_client.py`
- [ ] Implement `assign_story()` method
- [ ] Implement `get_story_status()` polling method
- [ ] Test basic A2A communication with News Chief

**Day 5: Bootstrap UI Framework**
- [ ] Create `ui/main.py` with FastAPI + Mesop
- [ ] Set up routing for `/` and `/article/{story_id}`
- [ ] Add Bootstrap/Tailwind CSS
- [ ] Create basic page scaffold

### Week 2: UI Pages & Integration

**Day 6-7: Assignment Form Page**
- [ ] Create `ui/pages/home.py` with story form
- [ ] Add form fields (topic, angle, target_length, deadline, priority)
- [ ] Implement submit handler
- [ ] Add loading spinner during polling
- [ ] Implement error handling (show message, keep form filled)
- [ ] Test form submission → News Chief

**Day 8-9: Article Display Page**
- [ ] Create `ui/pages/article.py`
- [ ] Display primary section (headline, content, word count)
- [ ] Create expandable metadata section (research, review, tags, timestamp, ES ID)
- [ ] Add "New Story" button → redirect to home
- [ ] Style with Bootstrap/Tailwind

**Day 10: Polish & Testing**
- [ ] Add loading states
- [ ] Error message styling
- [ ] Test complete workflow: form → assign → poll → redirect → article
- [ ] Handle edge cases (agent down, timeout, invalid input)
- [ ] Update `start_newsroom.sh` with `--with-ui` flag
- [ ] Create `start_ui.sh` standalone script
- [ ] Update README.md with UI instructions

### Acceptance Criteria
- [ ] User can assign story via web form on port 3000
- [ ] Form shows loading state while polling News Chief
- [ ] On completion, redirects to article page
- [ ] Article page shows all metadata (expandable section)
- [ ] On error, shows message and keeps form filled
- [ ] UI starts with `./start_newsroom.sh --with-ui`
- [ ] No changes made to any agent code
- [ ] UI completely isolated in `/ui` folder

## Next Steps

1. **Immediate (This Week)**
   - Review and approve MVP plan
   - Decide if we start building now or later
   - Clarify any remaining questions

2. **MVP Build (Next 2 Weeks)**
   - Follow checklist above
   - Daily check-ins on progress
   - Iterative testing with News Chief

3. **Post-MVP (Week 3+)**
   - Gather user feedback
   - Plan Phase 2 features (story list, workflow tracking)
   - Consider additional polish

## Conclusion

Integrating a web UI for Elastic News will transform it from a backend-only system into a complete newsroom management platform. By leveraging the proven A2A demo UI architecture while customizing for our specific workflow, we can achieve a production-ready interface in 4-6 weeks.

**Recommended Approach:** Hybrid (Option 3)
- Reuse A2A demo's service layer and state management
- Build custom newsroom-focused UI components
- Replace Google ADK with direct News Chief integration
- Deliver in phases: MVP → Full Features → Polish

This approach balances speed, quality, and maintainability while ensuring the UI seamlessly integrates with our existing A2A agent architecture.

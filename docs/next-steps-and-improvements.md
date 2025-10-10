# Next Steps and Areas of Improvement

This document outlines recommended next steps and areas of improvement for the Elastic Newsroom project, building on the existing code quality recommendations.

## Priority 1: User Interface Development

### 1. Web-Based Dashboard

**Description:** Create a web dashboard for monitoring and managing the newsroom workflow.

**Key Features:**
- Real-time agent status display
- Story assignment interface
- Article drafts viewer
- Workflow progress tracking
- Log viewer with filtering
- Agent health status indicators

**Technology Stack:**
```python
# Add to requirements.txt
fastapi>=0.104.0
jinja2>=3.1.2
aiofiles>=23.2.1

# Frontend (static files)
# - Use vanilla JS or lightweight framework (Alpine.js, HTMX)
# - Bootstrap or Tailwind CSS for styling
```

**Implementation Structure:**
```
ui/
├── __init__.py
├── app.py                 # FastAPI app for UI server
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── dashboard.js
│   └── img/
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── story_form.html
    ├── article_view.html
    └── logs.html
```

**Example Dashboard Endpoints:**
```python
# ui/app.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx

app = FastAPI(title="Elastic Newsroom Dashboard")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")

@app.get("/")
async def dashboard(request: Request):
    """Main dashboard view"""
    agent_status = await get_agent_status()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "agents": agent_status}
    )

@app.get("/api/agents/status")
async def agent_status_api():
    """API endpoint for agent status"""
    agents = [
        {"name": "News Chief", "port": 8080, "url": "http://localhost:8080"},
        {"name": "Reporter", "port": 8081, "url": "http://localhost:8081"},
        {"name": "Editor", "port": 8082, "url": "http://localhost:8082"},
        {"name": "Researcher", "port": 8083, "url": "http://localhost:8083"},
        {"name": "Publisher", "port": 8084, "url": "http://localhost:8084"},
    ]
    
    status_list = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for agent in agents:
            try:
                response = await client.get(f"{agent['url']}/health")
                status_list.append({
                    **agent,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                })
            except:
                status_list.append({**agent, "status": "offline", "response_time": None})
    
    return {"agents": status_list}

@app.post("/api/stories/assign")
async def assign_story(story_data: dict):
    """Assign a new story via UI"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8080/assign",
            json=story_data
        )
        return response.json()
```

**Dashboard Features:**

1. **Agent Status Grid**
   ```html
   <div class="agent-grid">
     <div class="agent-card" id="agent-news-chief">
       <h3>News Chief</h3>
       <span class="status-badge online">Online</span>
       <div class="metrics">
         <p>Active Stories: 3</p>
         <p>Response Time: 45ms</p>
       </div>
     </div>
     <!-- More agent cards -->
   </div>
   ```

2. **Story Assignment Form**
   ```html
   <form id="story-form">
     <input type="text" name="topic" placeholder="Story Topic" required>
     <textarea name="angle" placeholder="Story Angle"></textarea>
     <input type="number" name="target_length" value="1000">
     <select name="priority">
       <option value="low">Low</option>
       <option value="medium" selected>Medium</option>
       <option value="high">High</option>
     </select>
     <button type="submit">Assign Story</button>
   </form>
   ```

3. **Workflow Visualization**
   - Show story progress through pipeline
   - Real-time updates via WebSocket or SSE
   - Timeline view of article lifecycle

---

## Priority 2: Convenience Methods and CLI Tools

### 2. Enhanced CLI Interface

**Description:** Create a rich CLI for managing the newsroom.

**Implementation:**
```python
# cli.py
import click
import asyncio
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

@click.group()
def cli():
    """Elastic Newsroom CLI"""
    pass

@cli.command()
def status():
    """Show status of all agents"""
    asyncio.run(show_agent_status())

async def show_agent_status():
    table = Table(title="Agent Status")
    table.add_column("Agent", style="cyan")
    table.add_column("Port", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Response Time", style="yellow")
    
    agents = [
        ("News Chief", 8080),
        ("Reporter", 8081),
        ("Editor", 8082),
        ("Researcher", 8083),
        ("Publisher", 8084),
    ]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, port in agents:
            try:
                start = time.time()
                response = await client.get(f"http://localhost:{port}/health")
                elapsed = (time.time() - start) * 1000
                status = "✅ Online" if response.status_code == 200 else "⚠️  Error"
                table.add_row(name, str(port), status, f"{elapsed:.0f}ms")
            except:
                table.add_row(name, str(port), "❌ Offline", "N/A")
    
    console.print(table)

@cli.command()
@click.option('--topic', prompt='Story topic', help='The story topic')
@click.option('--priority', default='medium', help='Priority: low, medium, high')
@click.option('--length', default=1000, help='Target word count')
def assign(topic, priority, length):
    """Assign a new story"""
    asyncio.run(assign_story_cmd(topic, priority, length))

async def assign_story_cmd(topic, priority, length):
    with Progress() as progress:
        task = progress.add_task("[cyan]Assigning story...", total=100)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            progress.update(task, advance=20)
            
            response = await client.post(
                "http://localhost:8080/assign",
                json={
                    "action": "assign_story",
                    "story": {
                        "topic": topic,
                        "priority": priority,
                        "target_length": length
                    }
                }
            )
            
            progress.update(task, advance=80)
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"[green]✓[/green] Story assigned: {result.get('story_id')}")
            else:
                console.print("[red]✗[/red] Failed to assign story")

@cli.command()
@click.argument('story_id')
def track(story_id):
    """Track story progress"""
    asyncio.run(track_story(story_id))

async def track_story(story_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8080/status/{story_id}")
        if response.status_code == 200:
            data = response.json()
            console.print(f"[bold]Story: {story_id}[/bold]")
            console.print(f"Status: {data.get('status')}")
            console.print(f"Progress: {data.get('progress', 'N/A')}")
        else:
            console.print(f"[red]Story {story_id} not found[/red]")

@cli.command()
@click.option('--agent', help='Filter logs by agent')
@click.option('--level', default='INFO', help='Log level')
@click.option('--lines', default=50, help='Number of lines')
def logs(agent, level, lines):
    """View agent logs"""
    import subprocess
    
    log_file = f"logs/{agent}.log" if agent else "logs/*.log"
    cmd = f"tail -n {lines} {log_file}"
    
    if level:
        cmd += f" | grep {level}"
    
    subprocess.run(cmd, shell=True)

if __name__ == '__main__':
    cli()
```

**Add to requirements.txt:**
```
click>=8.1.0
rich>=13.5.0
```

**Usage:**
```bash
# Show agent status
python cli.py status

# Assign a story interactively
python cli.py assign

# Track story progress
python cli.py track story_123

# View logs
python cli.py logs --agent Reporter --lines 100
```

---

### 3. Convenience Methods for Agents

**Add common utility methods to agent classes:**

```python
# agents/utils.py
"""Convenience utilities for agents"""

import asyncio
from typing import Dict, Any, Optional
import httpx
from functools import wraps
import time

def timing_decorator(func):
    """Decorator to log execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

async def call_agent_with_retry(
    url: str,
    data: Dict[str, Any],
    max_retries: int = 3,
    timeout: float = 30.0
) -> Optional[Dict[str, Any]]:
    """Call another agent with automatic retry"""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to call {url} after {max_retries} attempts: {e}")
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return None

def validate_story_data(story: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate story data structure"""
    required_fields = ['topic']
    
    for field in required_fields:
        if field not in story or not story[field]:
            return False, f"Missing required field: {field}"
    
    if 'priority' in story and story['priority'] not in ['low', 'medium', 'high']:
        return False, f"Invalid priority: {story['priority']}"
    
    if 'target_length' in story:
        length = story['target_length']
        if not isinstance(length, int) or length < 100 or length > 5000:
            return False, f"Invalid target_length: {length} (must be 100-5000)"
    
    return True, None

class AgentMetrics:
    """Track agent metrics"""
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.total_time = 0.0
        self.requests = []
    
    def record_request(self, duration: float, error: bool = False):
        self.request_count += 1
        self.total_time += duration
        if error:
            self.error_count += 1
        
        # Keep last 100 requests
        self.requests.append({
            'timestamp': time.time(),
            'duration': duration,
            'error': error
        })
        if len(self.requests) > 100:
            self.requests.pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_requests': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'avg_duration': self.total_time / max(self.request_count, 1),
            'recent_requests': len(self.requests)
        }
```

**Add to base agent class:**

```python
# agents/base.py
from agents.utils import AgentMetrics, timing_decorator

class BaseAgent:
    """Base class with convenience methods"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.metrics = AgentMetrics()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return self.metrics.get_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        return {
            "status": "healthy",
            "agent": self.agent_name,
            "metrics": await self.get_metrics(),
            "dependencies": await self._check_dependencies()
        }
    
    async def _check_dependencies(self) -> Dict[str, bool]:
        """Check if dependencies are available"""
        return {}  # Override in subclasses
```

---

## Priority 3: Advanced Features

### 4. WebSocket Support for Real-Time Updates

**Description:** Add WebSocket endpoints for live updates.

```python
# ui/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            status = await get_agent_status()
            await websocket.send_json({"type": "status_update", "data": status})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Frontend:**
```javascript
// ui/static/js/dashboard.js
const ws = new WebSocket('ws://localhost:8000/ws/updates');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'status_update') {
        updateAgentStatus(data.data);
    }
};

function updateAgentStatus(agents) {
    agents.forEach(agent => {
        const element = document.getElementById(`agent-${agent.name}`);
        element.className = `agent-card ${agent.status}`;
    });
}
```

---

### 5. Story Templates

**Description:** Pre-defined story templates for common article types.

```python
# agents/templates.py
STORY_TEMPLATES = {
    'product_launch': {
        'name': 'Product Launch',
        'questions': [
            'What is the product and what problem does it solve?',
            'Who is the target audience?',
            'What makes it different from competitors?',
            'When is the launch date and pricing?',
            'What are the key features and benefits?'
        ],
        'outline': """
        1. Introduction - Hook with the problem
        2. Product overview and key features
        3. Market positioning and competitors
        4. Pricing and availability
        5. Expert analysis and conclusion
        """,
        'target_length': 800
    },
    'executive_interview': {
        'name': 'Executive Interview',
        'questions': [
            'What is the executive\'s background?',
            'What is their current role and company?',
            'What are their key insights on the topic?',
            'What challenges does their industry face?',
            'What is their vision for the future?'
        ],
        'outline': """
        1. Introduction - Executive and company context
        2. Key insights and perspectives
        3. Industry challenges and opportunities
        4. Future outlook and predictions
        5. Conclusion - Takeaways for readers
        """,
        'target_length': 1200
    },
    'tech_trend': {
        'name': 'Technology Trend Analysis',
        'questions': [
            'What is the trend and why is it emerging now?',
            'Which companies are leading in this space?',
            'What are the key statistics and market size?',
            'What are the benefits and risks?',
            'How will this evolve in the next 2-5 years?'
        ],
        'outline': """
        1. Introduction - Trend overview and significance
        2. Current state and market analysis
        3. Key players and innovations
        4. Benefits, challenges, and risks
        5. Future predictions and implications
        """,
        'target_length': 1500
    }
}

def get_template(template_name: str) -> dict:
    """Get story template by name"""
    return STORY_TEMPLATES.get(template_name)

def list_templates() -> list:
    """List all available templates"""
    return [
        {'id': k, 'name': v['name']} 
        for k, v in STORY_TEMPLATES.items()
    ]
```

---

### 6. Article Export Formats

**Description:** Export articles in multiple formats.

```python
# agents/exporters.py
from typing import Dict, Any
import json
from datetime import datetime

def export_as_markdown(article: Dict[str, Any]) -> str:
    """Export article as Markdown"""
    return f"""# {article['headline']}

**Published:** {article.get('published_date', 'N/A')}  
**Author:** {article.get('author', 'Elastic News')}  
**Word Count:** {article.get('word_count', 0)}

---

{article['content']}

---

**Tags:** {', '.join(article.get('tags', []))}  
**Categories:** {', '.join(article.get('categories', []))}
"""

def export_as_html(article: Dict[str, Any]) -> str:
    """Export article as HTML"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{article['headline']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .meta {{ color: #666; font-size: 0.9em; margin: 20px 0; }}
        .content {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>{article['headline']}</h1>
    <div class="meta">
        <p>Published: {article.get('published_date', 'N/A')}</p>
        <p>Author: {article.get('author', 'Elastic News')}</p>
    </div>
    <div class="content">
        {article['content'].replace(chr(10), '<br>')}
    </div>
</body>
</html>
"""

def export_as_json(article: Dict[str, Any]) -> str:
    """Export article as JSON"""
    return json.dumps(article, indent=2)

EXPORTERS = {
    'markdown': export_as_markdown,
    'html': export_as_html,
    'json': export_as_json
}

def export_article(article: Dict[str, Any], format: str = 'markdown') -> str:
    """Export article in specified format"""
    exporter = EXPORTERS.get(format, export_as_markdown)
    return exporter(article)
```

---

## Priority 4: Testing & Quality

### 7. Add Comprehensive Test Suite

```bash
# tests/unit/ structure
tests/
├── unit/
│   ├── __init__.py
│   ├── test_news_chief.py
│   ├── test_reporter.py
│   ├── test_researcher.py
│   ├── test_editor.py
│   ├── test_publisher.py
│   └── test_utils.py
├── integration/
│   ├── __init__.py
│   ├── test_newsroom_workflow.py
│   └── test_agent_communication.py
└── fixtures/
    ├── __init__.py
    ├── sample_articles.py
    └── mock_responses.py
```

---

## Priority 5: Deployment & Operations

### 8. Docker Support

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080-8084 8000

CMD ["./start_newsroom.sh"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  newsroom:
    build: .
    ports:
      - "8080-8084:8080-8084"
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ELASTICSEARCH_ENDPOINT=${ELASTICSEARCH_ENDPOINT}
      - ELASTIC_SEARCH_API_KEY=${ELASTIC_SEARCH_API_KEY}
    volumes:
      - ./articles:/app/articles
      - ./logs:/app/logs
```

---

### 9. GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run linters
        run: |
          make lint
      - name: Run tests
        run: |
          make test-cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Implementation Roadmap

### Phase 1: Basic UI (1-2 weeks)
1. ✅ Set up FastAPI UI server
2. ✅ Create dashboard with agent status
3. ✅ Add story assignment form
4. ✅ Implement basic styling

### Phase 2: CLI Tools (1 week)
1. ✅ Create CLI interface with click
2. ✅ Add status, assign, and track commands
3. ✅ Implement rich terminal output

### Phase 3: Convenience Methods (1 week)
1. ✅ Extract common utilities
2. ✅ Add agent base class
3. ✅ Implement metrics tracking
4. ✅ Add health checks

### Phase 4: Advanced Features (2-3 weeks)
1. ✅ WebSocket support
2. ✅ Story templates
3. ✅ Article exporters
4. ✅ Real-time updates

### Phase 5: Testing & Deployment (1-2 weeks)
1. ✅ Comprehensive test suite
2. ✅ Docker support
3. ✅ CI/CD pipeline
4. ✅ Documentation updates

---

## Quick Start for UI Development

1. **Install UI dependencies:**
   ```bash
   pip install fastapi jinja2 aiofiles rich websockets
   ```

2. **Create basic UI structure:**
   ```bash
   mkdir -p ui/static/{css,js} ui/templates
   ```

3. **Run UI server:**
   ```bash
   uvicorn ui.app:app --port 8000 --reload
   ```

4. **Access dashboard:**
   ```
   http://localhost:8000
   ```

---

## Summary

These recommendations provide:

1. **User Interface** - Web dashboard for visual management
2. **CLI Tools** - Rich command-line interface for power users
3. **Convenience Methods** - Reusable utilities and base classes
4. **Real-Time Features** - WebSocket support for live updates
5. **Templates & Exporters** - Pre-built workflows and multi-format export
6. **Testing** - Comprehensive test coverage
7. **Deployment** - Docker and CI/CD automation

All additions are modular and can be implemented incrementally without breaking existing functionality.

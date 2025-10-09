# Code Quality Recommendations

This document outlines recommendations to improve code quality, maintainability, and best practices in the Elastic Newsroom project.

## High Priority Improvements

### 1. **Centralize Configuration Management**

**Issue:** Environment variable loading is duplicated across multiple agent files with inconsistent patterns.

**Current State:**
- `reporter.py` uses both `load_dotenv()` and `dotenv_values()`
- Other agents only use `dotenv_values()`
- `news_chief.py` doesn't load environment variables at all
- Each agent manually loops through env vars

**Recommendation:**
Create a centralized configuration module:

```python
# config.py or agents/config.py
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os

class Config:
    """Centralized configuration management"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_env()
        return cls._instance
    
    def _load_env(self):
        """Load environment variables from .env file"""
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv(env_path)
    
    @property
    def anthropic_api_key(self) -> Optional[str]:
        return os.getenv('ANTHROPIC_API_KEY')
    
    @property
    def elasticsearch_endpoint(self) -> Optional[str]:
        return os.getenv('ELASTICSEARCH_ENDPOINT')
    
    # ... add other config properties
```

**Benefits:**
- Single source of truth for configuration
- Easier to test and mock
- Type hints for configuration values
- Reduces code duplication

---

### 2. **Improve Logging Configuration**

**Issue:** Each agent calls `logging.basicConfig()` which can conflict when agents run in the same process.

**Current State:**
- Each agent independently configures logging
- Uses `force=True` in some agents but not others
- All agents write to the same `newsroom.log` file
- No log rotation configured

**Recommendation:**

```python
# agents/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_agent_logging(agent_name: str, log_dir: str = "logs"):
    """
    Setup logging for an agent with proper rotation and formatting
    
    Args:
        agent_name: Name of the agent (e.g., 'NEWS_CHIEF', 'REPORTER')
        log_dir: Directory for log files
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger for this agent
    logger = logging.getLogger(f'newsroom.{agent_name.lower()}')
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler with rotation
    log_file = os.path.join(log_dir, f'{agent_name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler for errors only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

**Usage in agents:**
```python
from agents.logging_config import setup_agent_logging

logger = setup_agent_logging('NEWS_CHIEF')
```

**Benefits:**
- Log rotation prevents disk space issues
- Per-agent log files for easier debugging
- Consistent logging format
- Error messages visible on console

---

### 3. **Add Type Hints Consistently**

**Issue:** Type hints are used inconsistently across the codebase.

**Current State:**
- Method signatures have some type hints
- Missing return types in many methods
- Internal variables lack type hints

**Recommendation:**
Add comprehensive type hints:

```python
from typing import Dict, Any, List, Optional

class NewsChiefAgent:
    def __init__(self, reporter_url: Optional[str] = None) -> None:
        self.active_stories: Dict[str, Dict[str, Any]] = {}
        self.available_reporters: List[str] = []
        self.reporter_url: str = reporter_url or "http://localhost:8081"
    
    async def invoke(self, query: str) -> Dict[str, Any]:
        """Process query and return result"""
        # Implementation
        pass
```

**Benefits:**
- Better IDE support and autocomplete
- Catch type errors before runtime
- Improved code documentation
- Easier refactoring

---

### 4. **Improve Error Handling**

**Issue:** 30 instances of broad `except Exception as e:` handlers that catch all exceptions.

**Current State:**
```python
except Exception as e:
    return {
        "status": "error",
        "message": f"Error processing request: {str(e)}"
    }
```

**Recommendation:**
Use specific exception types:

```python
from anthropic import APIError, APITimeoutError

try:
    # Anthropic API call
    response = self.anthropic_client.messages.create(...)
except APITimeoutError as e:
    logger.error(f"Anthropic API timeout: {e}")
    return {
        "status": "error",
        "error_type": "timeout",
        "message": "AI service request timed out. Please retry."
    }
except APIError as e:
    logger.error(f"Anthropic API error: {e}")
    return {
        "status": "error",
        "error_type": "api_error",
        "message": "AI service encountered an error."
    }
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    return {
        "status": "error",
        "error_type": "internal",
        "message": "An unexpected error occurred."
    }
```

**Benefits:**
- Better error messages for users
- Appropriate error handling per exception type
- Easier debugging with specific error types
- Don't hide programming errors

---

### 5. **Add Input Validation**

**Issue:** Limited validation of incoming requests and data.

**Recommendation:**
Use Pydantic for request/response validation:

```python
from pydantic import BaseModel, Field, validator

class StoryAssignment(BaseModel):
    """Story assignment request schema"""
    topic: str = Field(..., min_length=1, max_length=500)
    angle: Optional[str] = Field(None, max_length=1000)
    target_length: int = Field(1000, ge=100, le=5000)
    priority: str = Field("medium", regex="^(low|medium|high)$")
    deadline: Optional[str] = None
    
    @validator('topic')
    def topic_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Topic cannot be empty')
        return v.strip()

# Usage in agent
async def _assign_story(self, request: Dict[str, Any]) -> Dict[str, Any]:
    try:
        story = StoryAssignment(**request.get("story", {}))
        # Use validated data
        logger.info(f"Assigning story: {story.topic}")
    except ValidationError as e:
        return {
            "status": "error",
            "message": "Invalid story data",
            "errors": e.errors()
        }
```

**Benefits:**
- Automatic validation of inputs
- Clear error messages for invalid data
- Self-documenting API schemas
- Type safety

---

## Medium Priority Improvements

### 6. **Extract Common Agent Base Class**

**Issue:** Each agent has similar initialization patterns, error handling, and structure.

**Recommendation:**
```python
# agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Base class for all newsroom agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = setup_agent_logging(agent_name)
        self._initialize_clients()
    
    @abstractmethod
    def _initialize_clients(self) -> None:
        """Initialize API clients (Anthropic, ES, etc.)"""
        pass
    
    @abstractmethod
    async def invoke(self, query: str) -> Dict[str, Any]:
        """Main entry point for agent requests"""
        pass
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Common query parsing logic"""
        try:
            return json.loads(query) if query.startswith('{') else {"query": query}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
```

---

### 7. **Add Unit Tests**

**Issue:** Only integration tests exist, no unit tests for individual methods.

**Recommendation:**
Create unit tests for each agent:

```python
# tests/unit/test_news_chief.py
import pytest
from agents.news_chief import NewsChiefAgent

@pytest.fixture
def news_chief():
    return NewsChiefAgent(reporter_url="http://test:8081")

@pytest.mark.asyncio
async def test_assign_story_valid_data(news_chief):
    request = {
        "action": "assign_story",
        "story": {
            "topic": "Test Topic",
            "priority": "high"
        }
    }
    result = await news_chief._assign_story(request)
    assert result["status"] in ["assigned", "pending"]
    assert "story_id" in result

@pytest.mark.asyncio
async def test_assign_story_missing_data(news_chief):
    request = {"action": "assign_story"}
    result = await news_chief._assign_story(request)
    assert result["status"] == "error"
```

**Benefits:**
- Faster feedback during development
- Test individual components in isolation
- Higher code coverage
- Regression prevention

---

### 8. **Add API Documentation**

**Issue:** No OpenAPI/Swagger documentation for agent endpoints.

**Recommendation:**
Add OpenAPI docs using FastAPI integration:

```python
# Each agent can expose OpenAPI docs
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="News Chief Agent API",
        version="1.0.0",
        description="Coordinator agent for newsroom workflow",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

Access docs at: `http://localhost:8080/docs`

---

### 9. **Add Retry Logic for External Calls**

**Issue:** No retry mechanism for API calls that may fail transiently.

**Recommendation:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from httpx import HTTPError

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(HTTPError)
)
async def _call_researcher(self, query: Dict[str, Any]) -> Dict[str, Any]:
    """Call researcher with automatic retry on failure"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{self.researcher_url}/research",
            json=query
        )
        response.raise_for_status()
        return response.json()
```

**Benefits:**
- More resilient to transient failures
- Exponential backoff prevents overwhelming services
- Configurable retry behavior

---

### 10. **Add Health Check Endpoints**

**Issue:** No way to check if agents are running properly.

**Recommendation:**
```python
# Add to each agent
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "News Chief",
        "version": "1.0.0",
        "dependencies": {
            "anthropic": anthropic_client is not None,
            "elasticsearch": es_client is not None
        }
    }
```

---

## Low Priority / Future Improvements

### 11. **Add Metrics and Monitoring**

- Track request counts, latency, error rates
- Use Prometheus for metrics collection
- Add correlation IDs for request tracing

### 12. **Implement Caching**

- Cache research results to avoid duplicate API calls
- Cache agent cards to reduce discovery overhead
- Use Redis for distributed caching

### 13. **Add Rate Limiting**

- Protect against API abuse
- Respect external API rate limits (Anthropic, Elasticsearch)

### 14. **Security Improvements**

- Validate API keys format before use
- Add authentication between agents
- Sanitize user inputs
- Add CORS configuration

### 15. **Database for State Management**

- Replace in-memory dictionaries with persistent storage
- Use PostgreSQL or MongoDB for state
- Enables multi-instance deployments

---

## Quick Wins

These can be implemented quickly with high impact:

1. **Add `.editorconfig`** - Ensure consistent formatting across editors
2. **Add `pyproject.toml`** - Modern Python project configuration
3. **Add pre-commit hooks** - Catch issues before commit (black, flake8, mypy)
4. **Add `CONTRIBUTING.md`** - Guidelines for contributors
5. **Add GitHub Actions CI/CD** - Automated testing and linting

---

## Implementation Priority

**Phase 1 (Immediate):**
1. Centralize configuration management
2. Improve logging configuration
3. Add type hints consistently

**Phase 2 (Short-term):**
4. Improve error handling
5. Add input validation
6. Add unit tests

**Phase 3 (Medium-term):**
7. Extract common base class
8. Add API documentation
9. Add retry logic
10. Add health checks

**Phase 4 (Long-term):**
11. Add metrics and monitoring
12. Implement caching
13. Add rate limiting
14. Security improvements
15. Database for state management

---

## Tools to Add

Add these to `requirements-dev.txt`:

```txt
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Linting & Formatting
black>=23.7.0
flake8>=6.1.0
mypy>=1.5.0
isort>=5.12.0

# Type stubs
types-requests
types-redis

# Validation
pydantic>=2.0.0

# Retry logic
tenacity>=8.2.0

# Monitoring
prometheus-client>=0.17.0
```

---

## Conclusion

These recommendations will significantly improve:
- **Code maintainability** - Through better structure and patterns
- **Developer experience** - Through better tooling and documentation
- **Reliability** - Through better error handling and testing
- **Performance** - Through caching and optimization
- **Security** - Through input validation and auth

Start with Phase 1 improvements for immediate impact, then progressively implement other phases based on project priorities.

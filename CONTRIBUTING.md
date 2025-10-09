# Contributing to Elastic Newsroom

Thank you for your interest in contributing to the Elastic Newsroom project! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip and virtualenv
- Anthropic API key
- Elasticsearch instance (for full workflow)

### Setup Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/justincastilla/elastic-newsroom.git
   cd elastic-newsroom
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   make install-dev
   # Or manually:
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

5. **Verify setup:**
   ```bash
   make test
   ```

## Development Workflow

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines below

3. **Format your code:**
   ```bash
   make format
   ```

4. **Run linters:**
   ```bash
   make lint
   ```

5. **Run tests:**
   ```bash
   make test
   ```

6. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

7. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length:** 100 characters (not 79)
- **Formatting:** Use `black` for automatic formatting
- **Import sorting:** Use `isort` with black-compatible settings
- **Type hints:** Add type hints for function signatures
- **Docstrings:** Use Google-style docstrings

### Example

```python
from typing import Dict, Any, Optional

class MyAgent:
    """Brief description of the agent.
    
    Longer description if needed.
    
    Attributes:
        config: Configuration dictionary
        client: API client instance
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the agent.
        
        Args:
            config: Configuration dictionary with API keys
        """
        self.config = config
        self.client = self._create_client()
    
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming data.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed result or None if processing failed
            
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Implementation
        return {"status": "success"}
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Examples:**
```
feat: add retry logic for API calls
fix: resolve logging conflict between agents
docs: update configuration guide
refactor: extract common base class for agents
test: add unit tests for Reporter agent
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_newsroom_workflow.py

# Run specific test
pytest tests/test_newsroom_workflow.py::test_newsroom_workflow
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/`
- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Use pytest fixtures for common setup

**Example:**
```python
import pytest
from agents.news_chief import NewsChiefAgent

@pytest.fixture
def news_chief():
    """Create a NewsChiefAgent instance for testing"""
    return NewsChiefAgent(reporter_url="http://test:8081")

@pytest.mark.asyncio
async def test_assign_story_with_valid_data_returns_success(news_chief):
    """Test that assigning a story with valid data returns success status"""
    request = {
        "action": "assign_story",
        "story": {"topic": "Test Topic", "priority": "high"}
    }
    result = await news_chief._assign_story(request)
    
    assert result["status"] == "assigned"
    assert "story_id" in result
```

## Documentation

### Updating Documentation

- Update relevant `.md` files in `docs/`
- Keep README.md in sync with changes
- Add inline comments for complex logic
- Update agent documentation if APIs change

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Keep formatting consistent

## Code Review Process

### Before Submitting PR

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No unnecessary changes included
- [ ] Commit messages follow convention

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Project Structure

```
elastic-newsroom/
├── agents/              # Agent implementations
│   ├── __init__.py
│   ├── news_chief.py
│   ├── reporter.py
│   ├── researcher.py
│   ├── editor.py
│   └── publisher.py
├── scripts/             # Utility scripts
├── tests/               # Test suite
│   ├── unit/           # Unit tests (create this)
│   └── integration/    # Integration tests
├── docs/                # Documentation
├── articles/            # Published articles (generated)
├── logs/                # Log files (generated)
└── start_newsroom.sh    # Agent launcher script
```

## Common Tasks

### Adding a New Agent

1. Create new file in `agents/` directory
2. Implement agent class following existing patterns
3. Add to `agents/__init__.py`
4. Create agent documentation in `docs/`
5. Add tests in `tests/`
6. Update `start_newsroom.sh` if needed

### Adding Dependencies

1. Add to `requirements.txt` for production deps
2. Add to `requirements-dev.txt` for dev deps
3. Update `pyproject.toml` if needed
4. Document any configuration needed

### Updating Agent APIs

1. Update agent code
2. Update agent card definition
3. Update agent documentation
4. Update tests
5. Update integration tests

## Getting Help

- **Issues:** Check [existing issues](https://github.com/justincastilla/elastic-newsroom/issues)
- **Discussions:** Start a [discussion](https://github.com/justincastilla/elastic-newsroom/discussions)
- **Documentation:** Read the [docs](docs/)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the project
- Assume good intentions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Elastic Newsroom! 🎉

# Elastic News - Testing Guide

This guide covers the modern pytest-based testing framework for Elastic News.

## Quick Start

### Install Testing Dependencies

```bash
pip install -r requirements.txt
```

This installs pytest and related testing tools:
- `pytest` - Modern Python testing framework
- `pytest-asyncio` - Async/await support for pytest
- `pytest-timeout` - Timeout support for long-running tests
- `pytest-mock` - Mocking/patching support

### Mock Services (No API Keys Required!)

**By default, all tests use mocks** - no Anthropic API key or Elasticsearch instance needed!

```bash
# Run tests with mocks (default - fast and free!)
pytest tests/test_with_mocks.py -v

# Run all tests with mocks
make test
```

The mock system provides:
- ✅ No API keys required
- ✅ No external services needed
- ✅ Fast execution (~0.5s vs ~120s)
- ✅ No API costs
- ✅ Works offline

See [`tests/mocks/README.md`](tests/mocks/README.md) for detailed mock documentation.

### Run Tests with Mocks (Default)

```bash
# Run all fast tests with mocks (default)
make test

# Run mock-specific tests
pytest tests/test_with_mocks.py -v

# Run all tests with mocks
pytest -v
```

### Run Tests with Real Services (Optional)

To test against actual Anthropic API and Elasticsearch:

```bash
# Set environment variable
export USE_REAL_SERVICES=true

# Run tests
pytest tests/test_workflow_pytest.py -v

# Or inline
USE_REAL_SERVICES=true make test-all
```

**Prerequisites for real services:**
- Valid `ANTHROPIC_API_KEY` in `.env`
- Running Elasticsearch instance
- All agents running: `./scripts/start_newsroom.sh`

### Other Test Commands

```bash
# Run all fast tests (excludes slow tests)
make test

# Run all tests including slow ones
make test-all

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-workflow      # Workflow tests only

# Run with verbose output
make test-verbose

# Run with coverage report
make test-coverage
```

Or use pytest directly:

```bash
# Run all fast tests
pytest -v -m "not slow"

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_workflow_pytest.py -v

# Run specific test
pytest tests/test_workflow_pytest.py::TestWorkflowIntegration::test_complete_workflow -v

# Run with output (don't capture stdout/stderr)
pytest -v -s
```

## Test Structure

### Test Organization

```
tests/
├── conftest.py                      # Pytest configuration and fixtures
├── pytest.ini                       # Pytest settings (at project root)
├── test_workflow_pytest.py          # Main workflow tests (pytest)
├── test_full_workflow.py            # Standalone workflow test
├── test_newsroom_workflow_comprehensive.py  # Comprehensive monitoring
├── test_archivist.py                # Archivist connectivity tests
├── test_elasticsearch_index.py      # Elasticsearch setup tests
└── test_utils.py                    # Utility function tests
```

### Test Categories

Tests are organized into categories using pytest markers:

- `@pytest.mark.unit` - Fast unit tests (< 1 second)
- `@pytest.mark.integration` - Integration tests requiring agents
- `@pytest.mark.workflow` - Full workflow tests
- `@pytest.mark.slow` - Slow tests (> 30 seconds)
- `@pytest.mark.smoke` - Quick smoke tests for validation

### Test Classes

`test_workflow_pytest.py` contains:

1. **TestWorkflowIntegration** - Complete workflow tests
   - `test_complete_workflow()` - Full end-to-end workflow
   - `test_story_assignment()` - Story assignment only
   - `test_reporter_status()` - Reporter status checks
   - `test_news_chief_status()` - News Chief status checks

2. **TestAgentHealth** - Individual agent health checks
   - `test_news_chief_health()` - News Chief availability
   - `test_reporter_health()` - Reporter availability
   - `test_editor_health()` - Editor availability
   - `test_researcher_health()` - Researcher availability
   - `test_publisher_health()` - Publisher availability

3. **TestAgentCommunication** - A2A communication tests
   - `test_send_message_to_news_chief()` - Message sending
   - `test_send_message_to_reporter()` - Message sending

4. **TestSlowWorkflows** - Long-running workflow tests
   - `test_multiple_concurrent_stories()` - Concurrent story handling

## Fixtures

### Session-scoped Fixtures

Available to all tests:

- `agent_urls` - Dictionary of agent URLs
- `http_client` - Shared HTTP client for the test session
- `a2a_clients` - Pre-initialized A2A clients for all agents
- `check_agents_health` - Validates all agents are running

### Function-scoped Fixtures

Reset for each test:

- `sample_story` - Sample story data for testing

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_my_workflow(a2a_clients, sample_story):
    """Test using fixtures."""
    # a2a_clients and sample_story are automatically provided
    result = await send_message(
        a2a_clients['news_chief'],
        {"action": "assign_story", "story": sample_story}
    )
    assert result['status'] == 'success'
```

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_workflow_pytest.py

# Run specific test class
pytest tests/test_workflow_pytest.py::TestWorkflowIntegration

# Run specific test
pytest tests/test_workflow_pytest.py::TestWorkflowIntegration::test_complete_workflow
```

### Using Markers

```bash
# Run only fast tests (exclude slow tests)
pytest -v -m "not slow"

# Run only unit tests
pytest -v -m unit

# Run only integration tests
pytest -v -m integration

# Run only workflow tests
pytest -v -m workflow

# Combine markers
pytest -v -m "integration and not slow"
```

### Output Options

```bash
# Show print statements and logging
pytest -v -s

# Show local variables on failure
pytest -v --showlocals

# Show full diff on assertion failures
pytest -v --tb=long

# Quiet mode (less output)
pytest -q

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show test durations
pytest --durations=10
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Run tests in parallel (auto-detect CPUs)
pytest -n auto
```

## Writing Tests

### Basic Test Structure

```python
import pytest

class TestMyFeature:
    """Test suite for my feature."""

    @pytest.mark.asyncio
    async def test_my_async_function(self, a2a_clients):
        """Test my async function."""
        result = await my_async_function(a2a_clients['news_chief'])
        assert result is not None
        assert result['status'] == 'success'

    def test_my_sync_function(self):
        """Test my sync function."""
        result = my_sync_function()
        assert result == expected_value
```

### Using Parametrize

```python
@pytest.mark.parametrize("agent_name,expected_skills", [
    ("news_chief", ["assign_story", "get_status"]),
    ("reporter", ["write_article", "apply_edits"]),
])
@pytest.mark.asyncio
async def test_agent_skills(agent_name, expected_skills, a2a_clients):
    """Test agent has expected skills."""
    # Test implementation
    pass
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation(a2a_clients):
    """Test an async operation."""
    result = await perform_async_operation(a2a_clients['reporter'])
    assert result is not None
```

### Using Fixtures

```python
@pytest.fixture
def my_fixture():
    """Provide test data."""
    return {"key": "value"}

def test_with_fixture(my_fixture):
    """Test using custom fixture."""
    assert my_fixture['key'] == 'value'
```

### Marking Tests

```python
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.workflow
@pytest.mark.asyncio
async def test_long_workflow(a2a_clients):
    """Long-running workflow test."""
    # Test implementation
    pass
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      elasticsearch:
        image: elasticsearch:8.11.0
        env:
          discovery.type: single-node
          xpack.security.enabled: false
        ports:
          - 9200:9200

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Start agents
        run: |
          ./scripts/start_newsroom.sh
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          ELASTICSEARCH_ENDPOINT: http://localhost:9200
          ELASTIC_SEARCH_API_KEY: ""

      - name: Wait for agents
        run: sleep 10

      - name: Run tests
        run: |
          pytest -v -m "not slow"

      - name: Stop agents
        if: always()
        run: |
          ./scripts/start_newsroom.sh --stop
```

## Test Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=agents --cov=utils --cov-report=html --cov-report=term

# Or use make command
make test-coverage

# View HTML report
open htmlcov/index.html
```

### Coverage Configuration

Add to `pytest.ini`:

```ini
[coverage:run]
source = agents, utils
omit = tests/*, */venv/*, */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

## Troubleshooting

### Tests Fail with "Connection Refused"

**Cause**: Agents are not running

**Solution**:
```bash
./scripts/start_newsroom.sh
sleep 5
pytest -v
```

### Tests Timeout

**Cause**: Agents are slow or Archivist is unavailable

**Solution**:
```bash
# Increase timeout
pytest --timeout=600

# Skip slow tests
pytest -m "not slow"
```

### Async Test Errors

**Cause**: Missing `@pytest.mark.asyncio` decorator

**Solution**:
```python
@pytest.mark.asyncio  # Add this decorator
async def test_my_async_function():
    await my_async_call()
```

### Import Errors

**Cause**: Missing dependencies

**Solution**:
```bash
pip install -r requirements.txt
```

### Fixture Not Found

**Cause**: Fixture defined in wrong scope or file

**Solution**:
- Session fixtures go in `conftest.py`
- Function fixtures can be in test file
- Ensure fixture name matches parameter name

## Best Practices

1. **Use descriptive test names**
   ```python
   # Good
   def test_story_assignment_returns_valid_story_id()

   # Bad
   def test_story()
   ```

2. **One assertion per test** (when possible)
   ```python
   def test_story_id_is_string(story_id):
       assert isinstance(story_id, str)

   def test_story_id_not_empty(story_id):
       assert len(story_id) > 0
   ```

3. **Use fixtures for setup**
   ```python
   @pytest.fixture
   def story_data():
       return {"topic": "Test", "target_length": 1000}
   ```

4. **Mark slow tests**
   ```python
   @pytest.mark.slow
   def test_long_operation():
       # Long test
       pass
   ```

5. **Use parametrize for similar tests**
   ```python
   @pytest.mark.parametrize("input,expected", [
       (1, 2),
       (2, 4),
       (3, 6),
   ])
   def test_double(input, expected):
       assert double(input) == expected
   ```

6. **Clean up after tests**
   ```python
   @pytest.fixture
   def temp_file():
       file = create_temp_file()
       yield file
       # Cleanup
       file.close()
       os.remove(file.name)
   ```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Real Python - Pytest Guide](https://realpython.com/pytest-python-testing/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

## Summary

The pytest-based testing framework provides:

✅ Modern Python testing with pytest
✅ Async/await support for A2A tests
✅ Shared fixtures for common setup
✅ Test markers for organization
✅ Parallel test execution
✅ Coverage reporting
✅ CI/CD integration
✅ Clear, maintainable test code

Run `make help` to see all available commands!

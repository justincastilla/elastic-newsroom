# Test Mocks

This directory contains mock implementations for testing without external dependencies.

## Overview

The mock system allows tests to run:
- ✅ Without Anthropic API keys
- ✅ Without Elasticsearch instance
- ✅ Without network calls to external services
- ✅ Faster (no API latency)
- ✅ More reliably (no API rate limits or outages)
- ✅ Without consuming API credits

## Available Mocks

### MockAnthropicClient

Mock implementation of the Anthropic API client.

**Features:**
- Generates realistic responses based on prompt content
- Supports outline generation, article writing, and editorial revisions
- No API key required
- No network calls made
- Instant responses

**Usage:**
```python
from tests.mocks import MockAnthropicClient

# Initialize without API key
client = MockAnthropicClient()

# Generate content
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": "Write an article about AI"}]
)

# Access response
text = response.content[0].text
```

**Response Types:**

1. **Outline Generation** - Detects "outline" + "research questions" in prompt
   ```json
   {
     "outline": "Introduction, Background, Key Points, Conclusion",
     "research_questions": ["Question 1", "Question 2", ...]
   }
   ```

2. **Article Writing** - Detects "news article" or "write a" in prompt
   ```
   HEADLINE: Article Title

   Article content with multiple paragraphs...
   ```

3. **Editorial Revision** - Detects "revising your article" or "editorial feedback"
   - Returns revised article with improvements

### MockElasticsearchClient

Mock implementation of Elasticsearch client.

**Features:**
- In-memory document storage
- Supports index, get, search, delete operations
- Supports indices.create, indices.exists, indices.delete
- No ES instance required
- Instant operations

**Usage:**
```python
from tests.mocks import MockElasticsearchClient

# Initialize
es = MockElasticsearchClient()

# Index a document
es.index(
    index="news_archive",
    id="story_123",
    document={"title": "Test", "content": "Article content"}
)

# Retrieve document
doc = es.get(index="news_archive", id="story_123")
print(doc["_source"]["title"])  # "Test"

# Search
results = es.search(index="news_archive")
print(results["hits"]["total"]["value"])  # 1

# Index operations
es.indices.create(index="my_index")
es.indices.exists("my_index")  # True
es.indices.delete(index="my_index")
```

## Using Mocks in Tests

### Automatic Mock Injection

The pytest configuration (`conftest.py`) automatically mocks services for all tests:

```python
# tests/conftest.py patches these globally:
# - anthropic.Anthropic -> MockAnthropicClient
# - elasticsearch.Elasticsearch -> MockElasticsearchClient
```

This means **all tests use mocks by default** unless you explicitly opt-in to real services.

### Running Tests with Mocks (Default)

```bash
# All tests use mocks by default
pytest tests/test_with_mocks.py -v

# Run all tests (mocks enabled)
make test
```

### Running Tests with Real Services

To use actual Anthropic API and Elasticsearch:

```bash
# Set environment variable
export USE_REAL_SERVICES=true

# Run tests
pytest tests/test_workflow_pytest.py -v

# Or inline
USE_REAL_SERVICES=true pytest -v
```

**Requirements for real services:**
- Valid `ANTHROPIC_API_KEY` in `.env`
- Running Elasticsearch instance
- Valid `ELASTICSEARCH_ENDPOINT` and `ELASTICSEARCH_API_KEY`
- All agents running (`./start_newsroom.sh`)

### Writing Tests with Mocks

#### Unit Test Example

```python
import pytest
from tests.mocks import MockAnthropicClient

class TestArticleGeneration:
    """Unit tests with mocks."""

    def test_generate_outline(self):
        """Test outline generation."""
        client = MockAnthropicClient()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": "Generate an outline and research questions."
            }]
        )

        text = response.content[0].text
        assert "outline" in text.lower()
        assert "research_questions" in text.lower()
```

#### Integration Test Example

```python
import pytest
from tests.mocks import MockAnthropicClient, MockElasticsearchClient

@pytest.mark.unit
def test_article_workflow():
    """Test complete workflow with mocks."""
    # Initialize mocks
    anthropic = MockAnthropicClient()
    es = MockElasticsearchClient()

    # Generate article
    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": "Write an article."}]
    )
    article = response.content[0].text

    # Index to ES
    es.index(index="articles", id="1", document={"content": article})

    # Verify
    doc = es.get(index="articles", id="1")
    assert doc["_source"]["content"] == article
```

## Mock Implementation Details

### MockAnthropicClient Architecture

```python
MockAnthropicClient
├── messages: MockMessages
│   └── create() -> MockMessage
│       ├── Analyzes prompt content
│       ├── Generates appropriate response
│       └── Returns MockMessage
└── MockMessage
    └── content: List[MockTextContent]
        └── text: str
```

**Response Generation Logic:**
1. Parse user message from prompt
2. Detect intent based on keywords:
   - "outline" + "research questions" → JSON outline
   - "news article" / "write a" → Article with headline
   - "revising" / "editorial feedback" → Revised article
3. Generate appropriate mock content
4. Return structured response

### MockElasticsearchClient Architecture

```python
MockElasticsearchClient
├── _documents: Dict[index, Dict[id, document]]
├── _indices: Dict[index, settings]
├── index() -> Index document
├── get() -> Retrieve document
├── search() -> Search documents
├── delete() -> Delete document
└── indices: MockIndicesClient
    ├── create() -> Create index
    ├── exists() -> Check index
    └── delete() -> Delete index
```

**Storage:**
- All documents stored in-memory
- Cleared between test runs
- No persistence

## Benefits of Mock Testing

### Speed
```bash
# With mocks (fast)
pytest tests/test_with_mocks.py -v
# ✅ 15 tests passed in 0.5s

# With real services (slow)
USE_REAL_SERVICES=true pytest tests/test_workflow_pytest.py -v
# ⏱️  15 tests passed in 120s
```

### Reliability
- ✅ No API rate limits
- ✅ No network timeouts
- ✅ No API outages
- ✅ Consistent results
- ✅ Works offline

### Cost
- ✅ No API credit consumption
- ✅ Can run unlimited tests
- ✅ Ideal for CI/CD

### Development
- ✅ Fast feedback loop
- ✅ Easy debugging
- ✅ Predictable behavior
- ✅ Test edge cases easily

## Extending Mocks

### Adding New Response Types

To add support for new prompt patterns:

```python
# In tests/mocks/mock_anthropic.py

class MockMessages:
    def create(self, model: str, max_tokens: int, messages: List[Dict]) -> MockMessage:
        user_message = messages[0]["content"]

        # Add your pattern
        if "your keyword" in user_message.lower():
            response_text = "Your custom response"

        return MockMessage(text=response_text, model=model)
```

### Adding New Mock Services

1. Create new mock file in `tests/mocks/`
2. Implement mock class matching real service API
3. Export in `tests/mocks/__init__.py`
4. Add global patch in `tests/conftest.py`

## Best Practices

1. **Use mocks for unit tests** - Fast, isolated testing
2. **Use real services for integration tests** - Validate actual behavior
3. **Mark tests appropriately**:
   ```python
   @pytest.mark.unit      # Mock-based unit test
   @pytest.mark.integration  # Requires real services
   ```
4. **Keep mocks simple** - Focus on realistic responses, not perfect simulation
5. **Test with real services periodically** - Ensure mocks match reality

## Troubleshooting

### Mock not being used

Check that global patches are active:
```python
# In test file
def test_check_mock(use_mock_services):
    assert use_mock_services is True  # Should be True by default
```

### Need real services for specific test

Use environment variable:
```python
@pytest.mark.skipif(
    os.getenv("USE_REAL_SERVICES") != "true",
    reason="Requires real services"
)
def test_with_real_api():
    # This test needs actual API
    pass
```

### Mock response not matching expectations

Update mock response generation in `mock_anthropic.py`:
```python
if "your specific prompt" in user_message.lower():
    response_text = "Expected response format"
```

## Summary

The mock system enables:
- ✅ Fast test execution (0.5s vs 120s)
- ✅ Zero external dependencies
- ✅ No API costs
- ✅ Reliable CI/CD
- ✅ Offline development
- ✅ Easy debugging

**Default:** All tests use mocks
**Override:** Set `USE_REAL_SERVICES=true` for real services

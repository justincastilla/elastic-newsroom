"""
Test suite demonstrating mock usage without external dependencies.

These tests run quickly without requiring:
- Anthropic API keys
- Elasticsearch instance
- External network calls

Run with: pytest tests/test_with_mocks.py -v
"""

import pytest
import sys
from pathlib import Path

# Add tests directory to path for imports
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

from mocks import MockAnthropicClient, MockElasticsearchClient


class TestMockAnthropicClient:
    """Test the mock Anthropic client."""

    def test_mock_client_initialization(self):
        """Test mock client can be initialized without API key."""
        client = MockAnthropicClient()
        assert client is not None
        assert client.api_key == "mock-api-key"

    def test_mock_client_with_custom_key(self):
        """Test mock client accepts custom API key."""
        client = MockAnthropicClient(api_key="custom-key")
        assert client.api_key == "custom-key"

    def test_mock_outline_generation(self):
        """Test mock generates appropriate outline response."""
        client = MockAnthropicClient()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": "Generate an outline and research questions for an article about AI."
            }]
        )

        assert response.content[0].text is not None
        assert "outline" in response.content[0].text.lower()
        assert "research_questions" in response.content[0].text.lower()

    def test_mock_article_generation(self):
        """Test mock generates article content."""
        client = MockAnthropicClient()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": "Write a news article about Multi-Agent AI Systems."
            }]
        )

        content = response.content[0].text
        assert "HEADLINE:" in content
        assert len(content) > 200
        assert "Multi-Agent AI Systems" in content or "multi-agent" in content.lower()

    def test_mock_editorial_revision(self):
        """Test mock handles editorial revision prompts."""
        client = MockAnthropicClient()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": """You are a reporter for Elastic News revising your article based on editorial feedback.

ORIGINAL ARTICLE:
Test article content here.

EDITORIAL REVIEW:
Please improve the clarity and flow.

Please revise the article by applying ALL the suggested edits."""
            }]
        )

        content = response.content[0].text
        assert content is not None
        assert len(content) > 100


class TestMockElasticsearchClient:
    """Test the mock Elasticsearch client."""

    def test_mock_es_initialization(self):
        """Test mock ES client can be initialized."""
        es = MockElasticsearchClient()
        assert es is not None
        assert es.ping() is True

    def test_mock_es_info(self):
        """Test mock ES returns cluster info."""
        es = MockElasticsearchClient()
        info = es.info()
        assert "version" in info
        assert info["version"]["number"] == "8.11.0"

    def test_mock_es_index_document(self):
        """Test mock ES can index documents."""
        es = MockElasticsearchClient()

        result = es.index(
            index="test_index",
            id="doc_1",
            document={"title": "Test Article", "content": "Test content"}
        )

        assert result["result"] == "created"
        assert result["_id"] == "doc_1"
        assert result["_index"] == "test_index"

    def test_mock_es_get_document(self):
        """Test mock ES can retrieve documents."""
        es = MockElasticsearchClient()

        # Index a document
        es.index(
            index="test_index",
            id="doc_1",
            document={"title": "Test Article"}
        )

        # Retrieve it
        result = es.get(index="test_index", id="doc_1")

        assert result["found"] is True
        assert result["_source"]["title"] == "Test Article"

    def test_mock_es_search(self):
        """Test mock ES can search documents."""
        es = MockElasticsearchClient()

        # Index some documents
        es.index(index="articles", id="1", document={"title": "Article 1"})
        es.index(index="articles", id="2", document={"title": "Article 2"})

        # Search
        result = es.search(index="articles")

        assert result["hits"]["total"]["value"] == 2
        assert len(result["hits"]["hits"]) == 2

    def test_mock_es_delete_document(self):
        """Test mock ES can delete documents."""
        es = MockElasticsearchClient()

        # Index a document
        es.index(index="test_index", id="doc_1", document={"title": "Test"})

        # Delete it
        result = es.delete(index="test_index", id="doc_1")

        assert result["result"] == "deleted"

        # Verify it's gone
        with pytest.raises(Exception, match="Document not found"):
            es.get(index="test_index", id="doc_1")

    def test_mock_es_create_index(self):
        """Test mock ES can create indices."""
        es = MockElasticsearchClient()

        result = es.indices.create(
            index="test_index",
            mappings={"properties": {"title": {"type": "text"}}},
            settings={"number_of_shards": 1}
        )

        assert result["acknowledged"] is True
        assert es.indices.exists("test_index") is True

    def test_mock_es_delete_index(self):
        """Test mock ES can delete indices."""
        es = MockElasticsearchClient()

        # Create index
        es.indices.create(index="test_index")

        # Delete it
        result = es.indices.delete(index="test_index")

        assert result["acknowledged"] is True
        assert es.indices.exists("test_index") is False


class TestMockIntegration:
    """Test that mocks work together in integration scenarios."""

    def test_article_workflow_with_mocks(self):
        """Test a simplified article workflow using only mocks."""
        # Initialize mock clients
        anthropic = MockAnthropicClient()
        elasticsearch = MockElasticsearchClient()

        # Step 1: Generate outline
        outline_response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": "Generate an outline and research questions about AI."
            }]
        )
        assert "outline" in outline_response.content[0].text.lower()

        # Step 2: Generate article
        article_response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": "Write a news article about AI systems."
            }]
        )
        article_content = article_response.content[0].text
        assert "HEADLINE:" in article_content

        # Step 3: Index to Elasticsearch
        es_result = elasticsearch.index(
            index="news_archive",
            id="story_123",
            document={
                "title": "AI Systems Article",
                "content": article_content,
                "word_count": len(article_content.split())
            }
        )
        assert es_result["result"] == "created"

        # Step 4: Verify indexed document
        doc = elasticsearch.get(index="news_archive", id="story_123")
        assert doc["_source"]["title"] == "AI Systems Article"
        assert doc["_source"]["word_count"] > 0

    def test_no_network_calls_made(self, monkeypatch):
        """Verify that no actual network calls are made."""
        import httpx

        # Track if any HTTP requests are made
        requests_made = []

        original_request = httpx.AsyncClient.request

        async def mock_request(*args, **kwargs):
            requests_made.append((args, kwargs))
            return await original_request(*args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)

        # Run operations with mocks
        anthropic = MockAnthropicClient()
        anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": "Test"}]
        )

        elasticsearch = MockElasticsearchClient()
        elasticsearch.index(index="test", id="1", document={"test": "data"})

        # Verify no HTTP requests were made to external services
        # (Note: This test is illustrative - actual A2A tests may make local agent calls)
        # The key is that no calls go to anthropic.com or cloud.elastic.co
        for args, kwargs in requests_made:
            url = str(kwargs.get('url', args[1] if len(args) > 1 else ''))
            assert 'anthropic.com' not in url
            assert 'elastic.co' not in url


# Marker for mock-only tests
pytestmark = pytest.mark.unit

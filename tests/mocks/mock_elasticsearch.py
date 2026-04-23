"""
Mock Elasticsearch client for testing without ES instance.

Updated for ES Python client 9.x patterns:
- Keyword args (settings=, mappings=, document=) instead of deprecated body=
- update() with doc= parameter
- bulk helper support
- get_settings() on indices API
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class MockElasticsearchClient:
    """
    Mock Elasticsearch client for testing.

    Simulates Elasticsearch operations without requiring an actual ES instance.
    Compatible with elasticsearch-py 9.x API patterns.
    """

    def __init__(self, hosts: Optional[List[str]] = None, api_key: Optional[str] = None, **kwargs):
        """Initialize mock Elasticsearch client."""
        self.hosts = hosts or ["http://localhost:9200"]
        self.api_key = api_key
        self._documents: Dict[str, Dict[str, Any]] = {}  # index -> {doc_id -> doc}
        self._indices: Dict[str, Dict[str, Any]] = {}  # index -> {mappings, settings}

    def ping(self) -> bool:
        """Mock ping - always returns True."""
        return True

    def info(self) -> Dict[str, Any]:
        """Mock cluster info."""
        return {
            "name": "mock-elasticsearch",
            "cluster_name": "mock-cluster",
            "version": {
                "number": "9.1.1",
                "build_flavor": "default"
            }
        }

    def index(
        self,
        index: str,
        id: Optional[str] = None,
        document: Optional[Dict[str, Any]] = None,
        refresh: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock document indexing."""
        doc_id = id or str(uuid.uuid4())

        # Ensure index exists in document store
        if index not in self._documents:
            self._documents[index] = {}

        # Determine if create or update
        result = "updated" if doc_id in self._documents.get(index, {}) else "created"
        version = 2 if result == "updated" else 1

        # Store document
        self._documents[index][doc_id] = document or {}

        return {
            "_index": index,
            "_id": doc_id,
            "_version": version,
            "result": result,
            "_shards": {
                "total": 1,
                "successful": 1,
                "failed": 0
            }
        }

    def get(self, index: str, id: str, **kwargs) -> Dict[str, Any]:
        """Mock document retrieval."""
        if index not in self._documents or id not in self._documents[index]:
            raise Exception(f"Document not found: {index}/{id}")

        return {
            "_index": index,
            "_id": id,
            "_version": 1,
            "found": True,
            "_source": self._documents[index][id]
        }

    def update(
        self,
        index: str,
        id: str,
        doc: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock partial document update using doc= parameter (ES 8.x+ pattern)."""
        if index not in self._documents or id not in self._documents[index]:
            raise Exception(f"Document not found for update: {index}/{id}")

        # Merge partial update into existing document
        if doc:
            self._documents[index][id].update(doc)

        return {
            "_index": index,
            "_id": id,
            "_version": 2,
            "result": "updated",
            "_shards": {
                "total": 1,
                "successful": 1,
                "failed": 0
            }
        }

    def search(
        self,
        index: Optional[str] = None,
        query: Optional[Dict[str, Any]] = None,
        sort: Optional[List] = None,
        size: Optional[int] = None,
        source: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Mock search with keyword args (ES 9.x pattern).

        Supports both new keyword args and legacy body= for backward compat.
        """
        # Handle legacy body= parameter
        body = kwargs.pop("body", None)
        if body and not query:
            query = body.get("query")
            sort = sort or body.get("sort")
            size = size or body.get("size")
            source = source or body.get("_source")

        hits = []
        target_size = size or 10

        if index and index in self._documents:
            for doc_id, doc in self._documents[index].items():
                if len(hits) >= target_size:
                    break

                hit = {
                    "_index": index,
                    "_id": doc_id,
                    "_score": 1.0,
                    "_source": doc
                }

                # Filter _source fields if specified
                if source:
                    hit["_source"] = {k: v for k, v in doc.items() if k in source}

                hits.append(hit)

        return {
            "took": 1,
            "timed_out": False,
            "_shards": {
                "total": 1,
                "successful": 1,
                "skipped": 0,
                "failed": 0
            },
            "hits": {
                "total": {"value": len(hits), "relation": "eq"},
                "max_score": 1.0 if hits else None,
                "hits": hits
            }
        }

    def delete(self, index: str, id: str, **kwargs) -> Dict[str, Any]:
        """Mock document deletion."""
        if index in self._documents and id in self._documents[index]:
            del self._documents[index][id]
            result = "deleted"
        else:
            result = "not_found"

        return {
            "_index": index,
            "_id": id,
            "_version": 2,
            "result": result
        }

    @property
    def indices(self):
        """Mock indices API."""
        return MockIndicesClient(self)


class MockIndicesClient:
    """Mock Elasticsearch indices API with ES 9.x keyword arg patterns."""

    def __init__(self, client: MockElasticsearchClient):
        """Initialize with parent client."""
        self._client = client

    def create(
        self,
        index: str,
        mappings: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock index creation using keyword args (ES 9.x pattern)."""
        # Also handle legacy body= parameter
        body = kwargs.pop("body", None)
        if body:
            mappings = mappings or body.get("mappings", {})
            settings = settings or body.get("settings", {})

        self._client._indices[index] = {
            "mappings": mappings or {},
            "settings": {
                "index": {
                    "number_of_shards": "1",
                    "number_of_replicas": "1",
                    **(settings or {})
                }
            }
        }

        # Initialize document store for this index
        if index not in self._client._documents:
            self._client._documents[index] = {}

        return {
            "acknowledged": True,
            "shards_acknowledged": True,
            "index": index
        }

    def exists(self, index: str, **kwargs) -> bool:
        """Check if index exists."""
        return index in self._client._indices

    def delete(self, index: str, **kwargs) -> Dict[str, Any]:
        """Mock index deletion."""
        if index in self._client._indices:
            del self._client._indices[index]
        if index in self._client._documents:
            del self._client._documents[index]

        return {"acknowledged": True}

    def get_mapping(self, index: str, **kwargs) -> Dict[str, Any]:
        """Get index mapping."""
        if index not in self._client._indices:
            raise Exception(f"Index not found: {index}")

        return {
            index: {
                "mappings": self._client._indices[index].get("mappings", {})
            }
        }

    def get_settings(self, index: str, **kwargs) -> Dict[str, Any]:
        """Get index settings."""
        if index not in self._client._indices:
            raise Exception(f"Index not found: {index}")

        return {
            index: {
                "settings": self._client._indices[index].get("settings", {
                    "index": {
                        "number_of_shards": "1",
                        "number_of_replicas": "1"
                    }
                })
            }
        }


# Mock bulk helper function (mirrors elasticsearch.helpers.bulk)
def mock_bulk(client, actions, refresh=None, raise_on_error=True, **kwargs):
    """
    Mock implementation of elasticsearch.helpers.bulk.

    Args:
        client: MockElasticsearchClient instance
        actions: List of action dicts with _index, _id, _source
        refresh: Refresh strategy (ignored in mock)
        raise_on_error: Whether to raise on errors

    Returns:
        Tuple of (success_count, errors)
    """
    success_count = 0
    errors = []

    for action in actions:
        try:
            index = action.get("_index")
            doc_id = action.get("_id")
            document = action.get("_source", action.get("doc", {}))

            client.index(index=index, id=doc_id, document=document)
            success_count += 1
        except Exception as e:
            errors.append({"index": {"_id": doc_id, "error": str(e)}})
            if raise_on_error:
                raise

    return success_count, errors


# Example usage in tests:
# from tests.mocks import MockElasticsearchClient
#
# def test_with_mock_elasticsearch():
#     es = MockElasticsearchClient()
#     es.index(index="test", id="1", document={"title": "Test"})
#     result = es.get(index="test", id="1")
#     assert result["_source"]["title"] == "Test"
#
# def test_update():
#     es = MockElasticsearchClient()
#     es.index(index="test", id="1", document={"title": "Old", "status": "draft"})
#     es.update(index="test", id="1", doc={"status": "published"})
#     result = es.get(index="test", id="1")
#     assert result["_source"]["status"] == "published"
#     assert result["_source"]["title"] == "Old"  # Unchanged field preserved

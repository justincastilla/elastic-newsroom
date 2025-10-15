"""
Mock Elasticsearch client for testing without ES instance.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class MockElasticsearchClient:
    """
    Mock Elasticsearch client for testing.

    Simulates Elasticsearch operations without requiring an actual ES instance.
    """

    def __init__(self, hosts: Optional[List[str]] = None, api_key: Optional[str] = None, **kwargs):
        """Initialize mock Elasticsearch client."""
        self.hosts = hosts or ["http://localhost:9200"]
        self.api_key = api_key
        self._documents: Dict[str, Dict[str, Any]] = {}  # index -> {doc_id -> doc}
        self._indices: Dict[str, Dict[str, Any]] = {}  # index -> settings

    def ping(self) -> bool:
        """Mock ping - always returns True."""
        return True

    def info(self) -> Dict[str, Any]:
        """Mock cluster info."""
        return {
            "name": "mock-elasticsearch",
            "cluster_name": "mock-cluster",
            "version": {
                "number": "8.11.0",
                "build_flavor": "default"
            }
        }

    def index(self, index: str, id: Optional[str] = None, document: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Mock document indexing."""
        doc_id = id or str(uuid.uuid4())

        # Ensure index exists
        if index not in self._documents:
            self._documents[index] = {}

        # Store document
        self._documents[index][doc_id] = document or {}

        return {
            "_index": index,
            "_id": doc_id,
            "_version": 1,
            "result": "created",
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

    def search(self, index: Optional[str] = None, query: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Mock search."""
        hits = []

        if index and index in self._documents:
            for doc_id, doc in self._documents[index].items():
                hits.append({
                    "_index": index,
                    "_id": doc_id,
                    "_score": 1.0,
                    "_source": doc
                })

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
                "max_score": 1.0,
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
    """Mock Elasticsearch indices API."""

    def __init__(self, client: MockElasticsearchClient):
        """Initialize with parent client."""
        self._client = client

    def create(self, index: str, mappings: Optional[Dict[str, Any]] = None, settings: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Mock index creation."""
        self._client._indices[index] = {
            "mappings": mappings or {},
            "settings": settings or {}
        }

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
                "mappings": self._client._indices[index]["mappings"]
            }
        }


# Example usage in tests:
# from tests.mocks import MockElasticsearchClient
#
# def test_with_mock_elasticsearch():
#     es = MockElasticsearchClient()
#     es.index(index="test", id="1", document={"title": "Test"})
#     result = es.get(index="test", id="1")
#     assert result["_source"]["title"] == "Test"

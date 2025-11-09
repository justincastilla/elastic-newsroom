"""
Unit Tests for FastAPI Researcher Server

Tests the HTTP endpoints and A2A protocol bridge.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import the FastAPI app
from crewai_agents.researcher_crew.main import app, researcher_crew


# Test client
client = TestClient(app)


class TestFastAPIEndpoints:
    """Test suite for FastAPI HTTP endpoints"""

    def test_health_check(self):
        """Test /health endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "CrewAI Researcher"
        assert data["implementation"] == "crewai"
        assert "timestamp" in data

    def test_agent_card(self):
        """Test /.well-known/agent-card.json endpoint"""
        response = client.get("/.well-known/agent-card.json")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Researcher (CrewAI)"
        assert data["version"] == "2.0.0"
        assert data["protocol_version"] == "0.3.0"
        assert data["implementation"] == "crewai"
        assert "skills" in data
        assert len(data["skills"]) == 3  # research_questions, get_history, get_status

    def test_status_endpoint(self):
        """Test /status endpoint"""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_research_requests" in data
        assert "research_history" in data

    @pytest.mark.asyncio
    async def test_research_endpoint_mock(self):
        """Test /research endpoint with mocked crew"""
        # Mock the crew's research_questions method
        with patch.object(researcher_crew, 'research_questions', new_callable=AsyncMock) as mock_research:
            mock_research.return_value = {
                "status": "success",
                "message": "Research completed",
                "research_id": "test_research_123",
                "story_id": "story_123",
                "research_results": [
                    {
                        "question": "What is AI?",
                        "confidence": 85,
                        "summary": "AI is artificial intelligence"
                    }
                ],
                "total_questions": 1
            }

            response = client.post("/research", json={
                "story_id": "story_123",
                "topic": "AI",
                "questions": ["What is AI?"]
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["story_id"] == "story_123"
            assert data["total_questions"] == 1

    def test_history_endpoint_missing_params(self):
        """Test /history endpoint with missing parameters"""
        response = client.post("/history", json={})

        # Should return error status in response body
        data = response.json()
        assert data["status"] == "error"

    def test_research_endpoint_missing_fields(self):
        """Test /research endpoint with missing required fields"""
        response = client.post("/research", json={
            "story_id": "story_123"
            # Missing topic and questions
        })

        # Should return 422 for validation error
        assert response.status_code == 422


class TestA2AProtocolBridge:
    """Test suite for A2A protocol compatibility"""

    @pytest.mark.asyncio
    async def test_a2a_tasks_research_questions(self):
        """Test /a2a/tasks endpoint with research_questions action"""
        # Mock the crew's research_questions method
        with patch.object(researcher_crew, 'research_questions', new_callable=AsyncMock) as mock_research:
            mock_research.return_value = {
                "status": "success",
                "message": "Research completed",
                "research_id": "test_research_123",
                "story_id": "story_123",
                "research_results": [{"question": "Test", "confidence": 80}],
                "total_questions": 1
            }

            response = client.post("/a2a/tasks", json={
                "input": {
                    "action": "research_questions",
                    "story_id": "story_123",
                    "topic": "Test",
                    "questions": ["Test question?"]
                }
            })

            assert response.status_code == 200
            data = response.json()

            # Verify A2A JSONRPC format
            assert data["jsonrpc"] == "2.0"
            assert "result" in data
            assert "parts" in data["result"]
            assert len(data["result"]["parts"]) == 1

            # Parse the text content
            text_content = json.loads(data["result"]["parts"][0]["text"])
            assert text_content["status"] == "success"

    def test_a2a_tasks_get_status(self):
        """Test /a2a/tasks endpoint with get_status action"""
        response = client.post("/a2a/tasks", json={
            "input": {
                "action": "get_status"
            }
        })

        assert response.status_code == 200
        data = response.json()

        # Verify A2A JSONRPC format
        assert data["jsonrpc"] == "2.0"
        assert "result" in data

        # Parse the text content
        text_content = json.loads(data["result"]["parts"][0]["text"])
        assert text_content["status"] == "success"

    def test_a2a_tasks_unknown_action(self):
        """Test /a2a/tasks endpoint with unknown action"""
        response = client.post("/a2a/tasks", json={
            "input": {
                "action": "unknown_action"
            }
        })

        # Should return 400 for unknown action
        assert response.status_code == 400

    def test_a2a_tasks_missing_input(self):
        """Test /a2a/tasks endpoint with missing input"""
        response = client.post("/a2a/tasks", json={})

        # Should return 422 for validation error
        assert response.status_code == 422


class TestCORSMiddleware:
    """Test suite for CORS configuration"""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""
        response = client.get("/health", headers={"Origin": "http://localhost:3001"})

        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

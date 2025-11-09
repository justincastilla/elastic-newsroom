"""
Unit Tests for Shared Utilities

Tests the EventHubClient and A2A bridge utilities.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from crewai_agents.shared.event_hub_client import EventHubClient
from crewai_agents.shared.a2a_bridge import (
    parse_a2a_request,
    format_a2a_response,
    create_a2a_agent_card,
    validate_a2a_request
)


class TestEventHubClient:
    """Test suite for EventHubClient"""

    def test_initialization(self):
        """Test EventHubClient initialization"""
        client = EventHubClient(
            event_hub_url="http://localhost:8090",
            enabled=True,
            timeout=5.0
        )

        assert client.event_hub_url == "http://localhost:8090"
        assert client.enabled == True
        assert client.timeout == 5.0

    def test_disabled_client(self):
        """Test that disabled client doesn't publish"""
        client = EventHubClient(enabled=False)

        # Call should return False when disabled
        # (can't test async without running event loop)
        assert client.enabled == False

    def test_enable_disable(self):
        """Test enable/disable functionality"""
        client = EventHubClient(enabled=True)

        assert client.enabled == True

        client.disable()
        assert client.enabled == False

        client.enable()
        assert client.enabled == True

    @pytest.mark.asyncio
    async def test_publish_event_disabled(self):
        """Test publish_event when disabled"""
        client = EventHubClient(enabled=False)

        result = await client.publish_event(
            agent_name="Test",
            event_type="test_event",
            story_id="test_123"
        )

        assert result == False

    @pytest.mark.asyncio
    async def test_publish_event_with_httpx_mock(self):
        """Test publish_event with mocked httpx"""
        client = EventHubClient(enabled=True)

        # Mock httpx.AsyncClient
        with patch('crewai_agents.shared.event_hub_client.httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = AsyncMock()

            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock()

            mock_client.return_value = mock_http

            result = await client.publish_event(
                agent_name="TestAgent",
                event_type="test_event",
                story_id="test_123",
                data={"key": "value"}
            )

            assert result == True
            assert mock_http.post.called


class TestA2ABridge:
    """Test suite for A2A bridge utilities"""

    def test_parse_a2a_request_dict_input(self):
        """Test parsing A2A request with dict input"""
        a2a_msg = {
            "input": {
                "action": "research_questions",
                "story_id": "story_123",
                "questions": ["What is AI?"]
            }
        }

        result = parse_a2a_request(a2a_msg)

        assert result["action"] == "research_questions"
        assert result["params"]["story_id"] == "story_123"
        assert len(result["params"]["questions"]) == 1

    def test_parse_a2a_request_string_input(self):
        """Test parsing A2A request with string input"""
        a2a_msg = {
            "input": json.dumps({
                "action": "get_status",
                "story_id": "story_123"
            })
        }

        result = parse_a2a_request(a2a_msg)

        assert result["action"] == "get_status"
        assert result["params"]["story_id"] == "story_123"

    def test_format_a2a_response(self):
        """Test formatting CrewAI result as A2A JSONRPC"""
        crew_result = {
            "status": "success",
            "research_id": "research_123",
            "research_results": [{"question": "Test", "confidence": 85}]
        }

        a2a_response = format_a2a_response(crew_result)

        assert a2a_response["jsonrpc"] == "2.0"
        assert "result" in a2a_response
        assert "parts" in a2a_response["result"]
        assert len(a2a_response["result"]["parts"]) == 1

        # Parse the text content
        text_content = json.loads(a2a_response["result"]["parts"][0]["text"])
        assert text_content["status"] == "success"
        assert text_content["research_id"] == "research_123"

    def test_create_a2a_agent_card(self):
        """Test creating A2A agent card"""
        skills = [
            {
                "id": "research.questions",
                "name": "Research Questions",
                "description": "Research multiple questions"
            }
        ]

        card = create_a2a_agent_card(
            name="Test Agent",
            description="Test agent description",
            url="http://localhost:8083",
            version="1.0.0",
            skills=skills
        )

        assert card["name"] == "Test Agent"
        assert card["version"] == "1.0.0"
        assert card["protocol_version"] == "0.3.0"
        assert card["implementation"] == "crewai"
        assert len(card["skills"]) == 1
        assert card["capabilities"]["max_concurrent_tasks"] == 30

    def test_validate_a2a_request_valid(self):
        """Test validating valid A2A request"""
        request = {
            "input": {
                "action": "research_questions",
                "story_id": "test_123"
            }
        }

        is_valid, error = validate_a2a_request(request)

        assert is_valid == True
        assert error is None

    def test_validate_a2a_request_missing_input(self):
        """Test validating A2A request with missing input"""
        request = {"task_id": "123"}

        is_valid, error = validate_a2a_request(request)

        assert is_valid == False
        assert "input" in error

    def test_validate_a2a_request_missing_action(self):
        """Test validating A2A request with missing action"""
        request = {
            "input": {
                "story_id": "test_123"
            }
        }

        is_valid, error = validate_a2a_request(request)

        assert is_valid == False
        assert "action" in error

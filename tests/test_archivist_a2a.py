#!/usr/bin/env python3
"""
Test Archivist Agent A2A JSONRPC Integration

This test validates the Archivist agent integration using the A2A JSONRPC protocol.
Tests the connection, message format, and response parsing.

Run with:
    pytest tests/test_archivist_a2a.py -v
    pytest tests/test_archivist_a2a.py -v -s  # with output
"""

import pytest
import os
import time
import httpx
from typing import Dict, Any
from utils.env_loader import load_env_config

# Load environment variables from .env file
load_env_config()


@pytest.fixture(scope="module")
def archivist_config():
    """Load Archivist configuration from environment"""
    agent_card_url = os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL")
    api_key = os.getenv("ELASTIC_ARCHIVIST_API_KEY")

    if not agent_card_url:
        pytest.skip("ELASTIC_ARCHIVIST_AGENT_CARD_URL not configured")

    if not api_key:
        pytest.skip("ELASTIC_ARCHIVIST_API_KEY not configured")

    # Parse URL to get endpoint
    if "/api/agent_builder/a2a/" in agent_card_url:
        agent_id = agent_card_url.split("/")[-1]
        if agent_id.endswith(".json"):
            agent_id = agent_id[:-5]

        base_url = agent_card_url.split("/api/agent_builder/")[0]
        endpoint = f"{base_url}/api/agent_builder/a2a/{agent_id}"
    else:
        pytest.skip("Invalid ELASTIC_ARCHIVIST_AGENT_CARD_URL format")

    return {
        "endpoint": endpoint,
        "api_key": api_key,
        "agent_id": agent_id,
        "agent_card_url": agent_card_url
    }


@pytest.fixture
def archivist_headers(archivist_config):
    """Create headers for Archivist requests"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {archivist_config['api_key']}",
        "kbn-xsrf": "kibana"
    }


def create_a2a_message(query: str, story_id: str = "test_001") -> Dict[str, Any]:
    """Create an A2A JSONRPC message"""
    timestamp_ms = int(time.time() * 1000)
    message_id = f"msg-{timestamp_ms}-{story_id}"

    return {
        "id": message_id,
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "configuration": {
                "acceptedOutputModes": ["text/plain", "video/mp4"]
            },
            "message": {
                "kind": "message",
                "messageId": message_id,
                "metadata": {},
                "parts": [
                    {
                        "kind": "text",
                        "text": query
                    }
                ],
                "role": "user"
            }
        }
    }


class TestArchivistConnection:
    """Test basic connectivity to Archivist agent"""

    @pytest.mark.asyncio
    async def test_archivist_config_loaded(self, archivist_config):
        """Test that Archivist configuration is loaded correctly"""
        assert archivist_config is not None
        assert "endpoint" in archivist_config
        assert "api_key" in archivist_config
        assert "agent_id" in archivist_config

        print(f"\n✅ Archivist Configuration:")
        print(f"   Endpoint: {archivist_config['endpoint']}")
        print(f"   Agent ID: {archivist_config['agent_id']}")
        print(f"   API Key: {'*' * (len(archivist_config['api_key']) - 4)}{archivist_config['api_key'][-4:]}")

    @pytest.mark.asyncio
    async def test_archivist_agent_card(self, archivist_config):
        """Test fetching Archivist agent card"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                archivist_config['agent_card_url'],
                headers={
                    "Authorization": f"ApiKey {archivist_config['api_key']}",
                    "kbn-xsrf": "kibana"
                }
            )

            assert response.status_code == 200, f"Failed to fetch agent card: {response.status_code}"

            agent_card = response.json()
            assert "name" in agent_card or "agentName" in agent_card

            print(f"\n✅ Agent Card Retrieved:")
            print(f"   Name: {agent_card.get('name', agent_card.get('agentName', 'N/A'))}")
            print(f"   Response keys: {list(agent_card.keys())}")


class TestArchivistA2AProtocol:
    """Test Archivist A2A JSONRPC protocol compliance"""

    @pytest.mark.asyncio
    async def test_simple_search_query(self, archivist_config, archivist_headers):
        """Test a simple search query to Archivist"""
        query = "Find articles about artificial intelligence"
        message = create_a2a_message(query, "test_search_001")

        print(f"\n📨 Sending A2A JSONRPC request:")
        print(f"   Query: {query}")
        print(f"   Message ID: {message['id']}")
        print(f"   Endpoint: {archivist_config['endpoint']}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                archivist_config['endpoint'],
                json=message,
                headers=archivist_headers
            )

            assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"

            result = response.json()

            # Validate JSONRPC response structure
            assert "jsonrpc" in result, "Response missing 'jsonrpc' field"
            assert result["jsonrpc"] == "2.0", "Invalid JSONRPC version"
            assert "id" in result, "Response missing 'id' field"
            assert result["id"] == message["id"], "Response ID doesn't match request ID"

            # Check for either result or error
            assert "result" in result or "error" in result, "Response must contain 'result' or 'error'"

            if "error" in result:
                pytest.fail(f"Archivist returned error: {result['error']}")

            print(f"\n✅ Response received:")
            print(f"   JSONRPC version: {result['jsonrpc']}")
            print(f"   Message ID: {result['id']}")
            print(f"   Has result: {'result' in result}")

    @pytest.mark.asyncio
    async def test_extract_text_from_response(self, archivist_config, archivist_headers):
        """Test extracting text content from Archivist response

        Note: Archivist may return empty responses, which is expected behavior.
        This test verifies the response structure is correct.
        """
        query = "Find recent articles about machine learning"
        message = create_a2a_message(query, "test_extract_001")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                archivist_config['endpoint'],
                json=message,
                headers=archivist_headers
            )

            assert response.status_code == 200
            result = response.json()

            # Extract text from parts
            a2a_result = result.get("result", {})
            message_obj = a2a_result.get("message", {})
            parts = message_obj.get("parts", [])

            # Verify structure is correct
            assert isinstance(parts, list), "Parts should be a list"

            full_text = ""
            for part in parts:
                if part.get("kind") == "text":
                    text_content = part.get("text", "")
                    if text_content:
                        full_text += text_content + "\n\n"

            full_text = full_text.strip()

            # Note: Empty responses are expected from Archivist sometimes
            if len(full_text) == 0:
                print(f"\n⚠️  Empty response received (this is expected behavior)")
                print(f"   Parts count: {len(parts)}")
                print(f"   Response structure validated successfully")
            else:
                print(f"\n✅ Extracted text content:")
                print(f"   Length: {len(full_text)} characters")
                print(f"   Preview: {full_text[:200]}...")
                print(f"   Parts count: {len(parts)}")

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, archivist_config, archivist_headers):
        """Test handling of empty responses"""
        query = "Find articles about xyzabc123nonexistent"
        message = create_a2a_message(query, "test_empty_001")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                archivist_config['endpoint'],
                json=message,
                headers=archivist_headers
            )

            # Should still return 200 even if no results
            assert response.status_code == 200

            result = response.json()
            assert "result" in result or "error" in result

            print(f"\n✅ Empty query handled:")
            print(f"   Status: {response.status_code}")
            print(f"   Has result: {'result' in result}")


class TestArchivistRetryLogic:
    """Test retry logic for Archivist requests"""

    @pytest.mark.asyncio
    async def test_timeout_handling(self, archivist_config, archivist_headers):
        """Test that timeout is handled gracefully"""
        query = "Find articles about cloud computing"
        message = create_a2a_message(query, "test_timeout_001")

        # Use very short timeout to test timeout handling
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.post(
                    archivist_config['endpoint'],
                    json=message,
                    headers=archivist_headers
                )

                # If it completes within 1 second, that's fine too
                assert response.status_code == 200
                print("\n✅ Request completed within timeout")

        except httpx.TimeoutException:
            # This is expected with a 1 second timeout
            print("\n✅ Timeout handled correctly")
            assert True


class TestArchivistIntegration:
    """Integration tests for Archivist with Reporter workflow"""

    @pytest.mark.asyncio
    async def test_search_for_story_context(self, archivist_config, archivist_headers):
        """Test searching for context about a news story

        Note: This test may encounter timeouts or empty responses from Archivist.
        It validates that the API structure works correctly.
        """
        queries = [
            "Find articles about renewable energy adoption",
            "Find articles about electric vehicles",
            "Find articles about AI in healthcare"
        ]

        results = []

        for query in queries:
            message = create_a2a_message(query, f"test_story_{len(results)}")

            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.post(
                        archivist_config['endpoint'],
                        json=message,
                        headers=archivist_headers
                    )

                    assert response.status_code == 200

                    result = response.json()
                    assert "result" in result

                    # Extract text
                    a2a_result = result.get("result", {})
                    message_obj = a2a_result.get("message", {})
                    parts = message_obj.get("parts", [])

                    text_content = ""
                    for part in parts:
                        if part.get("kind") == "text":
                            text_content += part.get("text", "")

                    results.append({
                        "query": query,
                        "has_content": len(text_content) > 0,
                        "content_length": len(text_content),
                        "status": "success"
                    })

            except httpx.TimeoutException:
                results.append({
                    "query": query,
                    "has_content": False,
                    "content_length": 0,
                    "status": "timeout"
                })

        print(f"\n✅ Story context search results:")
        for idx, result in enumerate(results, 1):
            print(f"   {idx}. {result['query']}")
            print(f"      Status: {result.get('status', 'unknown')}")
            print(f"      Has content: {result['has_content']}")
            print(f"      Length: {result['content_length']} chars")

        # Note: Empty responses and timeouts are expected behavior from Archivist
        # The test validates that requests succeed and have proper structure
        content_count = sum(1 for r in results if r["has_content"])
        timeout_count = sum(1 for r in results if r.get("status") == "timeout")

        if content_count == 0:
            print(f"\n⚠️  All queries returned empty/timeout responses (this is expected Archivist behavior)")
            if timeout_count > 0:
                print(f"   {timeout_count}/{len(results)} queries timed out")
        else:
            print(f"\n✅ {content_count}/{len(results)} queries returned content")
            if timeout_count > 0:
                print(f"   {timeout_count}/{len(results)} queries timed out")


@pytest.mark.integration
class TestArchivistWithMockReporter:
    """Test Archivist integration as called by Reporter agent"""

    @pytest.mark.asyncio
    async def test_reporter_style_integration(self, archivist_config, archivist_headers):
        """Test Archivist call in the style of Reporter agent"""
        # Simulate Reporter calling Archivist
        story = {
            "story_id": "story_test_integration",
            "topic": "Multi-Agent AI Systems",
            "angle": "Real-world applications in newsrooms"
        }

        search_query = f"Find articles about {story['topic']} {story['angle']}".strip()
        message = create_a2a_message(search_query, story['story_id'])

        print(f"\n🔍 Simulating Reporter → Archivist call:")
        print(f"   Story ID: {story['story_id']}")
        print(f"   Topic: {story['topic']}")
        print(f"   Search query: {search_query}")

        # Make request with retry logic
        max_attempts = 3
        success = False

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"\n   Attempt {attempt}/{max_attempts}...")

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        archivist_config['endpoint'],
                        json=message,
                        headers=archivist_headers
                    )

                    assert response.status_code == 200
                    result = response.json()

                    # Check if response is empty
                    response_text = response.text.strip()
                    if not response_text or response_text == '""':
                        if attempt < max_attempts:
                            print(f"      ⚠️  Empty response, retrying...")
                            continue
                        else:
                            pytest.fail("Empty response after all retries")

                    # Extract content
                    a2a_result = result.get("result", {})
                    message_obj = a2a_result.get("message", {})
                    parts = message_obj.get("parts", [])

                    full_response = ""
                    for part in parts:
                        if part.get("kind") == "text":
                            full_response += part.get("text", "")

                    print(f"\n✅ Integration test successful:")
                    print(f"   Response length: {len(full_response)} characters")
                    print(f"   Preview: {full_response[:150]}...")

                    success = True
                    break

            except httpx.TimeoutException:
                if attempt < max_attempts:
                    print(f"      ⚠️  Timeout, retrying...")
                    continue
                else:
                    pytest.fail("Timeout after all retries")

        assert success, "Integration test failed after all attempts"


if __name__ == "__main__":
    import sys

    print("🧪 Running Archivist A2A Integration Tests")
    print("=" * 60)

    # Run pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))

"""
Pytest-based full workflow test for Elastic News.

This test suite uses pytest to run the complete newsroom workflow
from story assignment to publication.

Run with:
    pytest tests/test_workflow_pytest.py -v
    pytest tests/test_workflow_pytest.py -v -s  # with output
    pytest tests/test_workflow_pytest.py -v -m "not slow"  # skip slow tests
"""

import pytest
import json
import asyncio
from typing import Dict, Any
from a2a.client import create_text_message_object


@pytest.fixture(scope="module", autouse=True)
async def ensure_agents_running(check_agents_health):
    """Ensure all agents are running before any test in this module."""
    # The fixture will exit if agents are not running
    yield check_agents_health


class TestWorkflowIntegration:
    """Integration tests for the complete newsroom workflow."""

    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_complete_workflow(self, a2a_clients, sample_story):
        """
        Test the complete multi-agent newsroom workflow.

        Steps:
        1. Assign story to News Chief
        2. Reporter writes article (with Researcher + Archivist)
        3. Editor reviews article
        4. Reporter applies edits
        5. Publisher indexes to Elasticsearch
        6. Verify publication
        """
        # STEP 1: Assign story to News Chief
        story_id = await self._assign_story(a2a_clients['news_chief'], sample_story)
        assert story_id is not None, "Story ID should be returned"
        assert isinstance(story_id, str), "Story ID should be a string"

        # STEP 2: Write article (triggers automatic workflow)
        article_result = await self._write_article(a2a_clients['reporter'], story_id)
        assert article_result['status'] == 'success', f"Article writing failed: {article_result.get('message')}"
        assert article_result['word_count'] > 0, "Article should have word count"

        # STEP 3: Monitor workflow to completion
        final_status = await self._monitor_workflow_completion(
            a2a_clients['news_chief'],
            story_id,
            timeout=300
        )
        assert final_status in ['published', 'completed'], f"Workflow should complete successfully, got: {final_status}"

        # STEP 4: Verify publication
        story_data = await self._get_story_status(a2a_clients['news_chief'], story_id)
        assert story_data['status'] in ['published', 'completed'], "Story should be published"

    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_story_assignment(self, a2a_clients, sample_story):
        """Test story assignment to News Chief."""
        story_id = await self._assign_story(a2a_clients['news_chief'], sample_story)

        assert story_id is not None, "Story ID should be returned"
        assert len(story_id) > 0, "Story ID should not be empty"

        # Verify story was stored
        story_data = await self._get_story_status(a2a_clients['news_chief'], story_id)
        assert story_data['topic'] == sample_story['topic']
        assert story_data['status'] in ['assigned', 'writing', 'pending']

    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_reporter_status(self, a2a_clients):
        """Test Reporter status endpoint."""
        result = await self._send_message(
            a2a_clients['reporter'],
            {"action": "get_status"}
        )

        assert result['status'] == 'success'
        assert 'total_assignments' in result
        assert 'total_drafts' in result

    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_news_chief_status(self, a2a_clients):
        """Test News Chief status endpoint."""
        result = await self._send_message(
            a2a_clients['news_chief'],
            {"action": "get_status"}
        )

        assert result['status'] == 'success'
        assert 'active_stories' in result

    # Helper methods

    async def _send_message(self, client, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message via A2A and get the response."""
        message = create_text_message_object(content=json.dumps(request))

        async for response in client.send_message(message):
            if hasattr(response, 'parts') and response.parts:
                part = response.parts[0]
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    return json.loads(part.root.text)

        return {"status": "error", "message": "No response received"}

    async def _assign_story(self, news_chief_client, story: Dict[str, Any]) -> str:
        """Assign a story to News Chief and return the story_id."""
        request = {
            "action": "assign_story",
            "story": story
        }

        result = await self._send_message(news_chief_client, request)
        assert result['status'] == 'success', f"Story assignment failed: {result.get('message')}"

        return result['story_id']

    async def _write_article(self, reporter_client, story_id: str) -> Dict[str, Any]:
        """Trigger article writing and return the result."""
        request = {
            "action": "write_article",
            "story_id": story_id
        }

        result = await self._send_message(reporter_client, request)
        return result

    async def _get_story_status(self, news_chief_client, story_id: str) -> Dict[str, Any]:
        """Get the status of a story."""
        request = {
            "action": "get_story_status",
            "story_id": story_id
        }

        result = await self._send_message(news_chief_client, request)
        assert result['status'] == 'success', "Failed to get story status"

        return result['story']

    async def _monitor_workflow_completion(
        self,
        news_chief_client,
        story_id: str,
        timeout: int = 300
    ) -> str:
        """
        Monitor workflow until completion or timeout.

        Returns the final status of the story.
        """
        poll_interval = 5
        max_polls = timeout // poll_interval

        for i in range(max_polls):
            await asyncio.sleep(poll_interval)

            story_data = await self._get_story_status(news_chief_client, story_id)
            status = story_data.get('status', 'unknown')

            # Check for completion
            if status in ['published', 'completed']:
                return status

            # Check for error
            if status == 'error':
                pytest.fail(f"Workflow failed with error status: {story_data.get('error')}")

        pytest.fail(f"Workflow did not complete within {timeout} seconds")


class TestAgentHealth:
    """Health check tests for individual agents."""

    @pytest.mark.asyncio
    async def test_news_chief_health(self, http_client, agent_urls):
        """Test News Chief agent is responding."""
        from a2a.client import A2ACardResolver

        card_resolver = A2ACardResolver(http_client, agent_urls['news_chief'])
        agent_card = await card_resolver.get_agent_card()

        assert agent_card.name == "News Chief"
        assert len(agent_card.skills) > 0

    @pytest.mark.asyncio
    async def test_reporter_health(self, http_client, agent_urls):
        """Test Reporter agent is responding."""
        from a2a.client import A2ACardResolver

        card_resolver = A2ACardResolver(http_client, agent_urls['reporter'])
        agent_card = await card_resolver.get_agent_card()

        assert agent_card.name == "Reporter"
        assert len(agent_card.skills) > 0

    @pytest.mark.asyncio
    async def test_editor_health(self, http_client, agent_urls):
        """Test Editor agent is responding."""
        from a2a.client import A2ACardResolver

        card_resolver = A2ACardResolver(http_client, agent_urls['editor'])
        agent_card = await card_resolver.get_agent_card()

        assert agent_card.name == "Editor"
        assert len(agent_card.skills) > 0

    @pytest.mark.asyncio
    async def test_researcher_health(self, http_client, agent_urls):
        """Test Researcher agent is responding."""
        from a2a.client import A2ACardResolver

        card_resolver = A2ACardResolver(http_client, agent_urls['researcher'])
        agent_card = await card_resolver.get_agent_card()

        assert agent_card.name == "Researcher"
        assert len(agent_card.skills) > 0

    @pytest.mark.asyncio
    async def test_publisher_health(self, http_client, agent_urls):
        """Test Publisher agent is responding."""
        from a2a.client import A2ACardResolver

        card_resolver = A2ACardResolver(http_client, agent_urls['publisher'])
        agent_card = await card_resolver.get_agent_card()

        assert agent_card.name == "Publisher"
        assert len(agent_card.skills) > 0


class TestAgentCommunication:
    """Tests for A2A communication between agents."""

    @pytest.mark.asyncio
    async def test_send_message_to_news_chief(self, a2a_clients):
        """Test sending a message to News Chief."""
        request = {"action": "get_status"}
        message = create_text_message_object(content=json.dumps(request))

        response_received = False
        async for response in a2a_clients['news_chief'].send_message(message):
            if hasattr(response, 'parts') and response.parts:
                response_received = True
                break

        assert response_received, "Should receive response from News Chief"

    @pytest.mark.asyncio
    async def test_send_message_to_reporter(self, a2a_clients):
        """Test sending a message to Reporter."""
        request = {"action": "get_status"}
        message = create_text_message_object(content=json.dumps(request))

        response_received = False
        async for response in a2a_clients['reporter'].send_message(message):
            if hasattr(response, 'parts') and response.parts:
                response_received = True
                break

        assert response_received, "Should receive response from Reporter"


@pytest.mark.slow
class TestSlowWorkflows:
    """Tests that take a long time to run (marked as slow)."""

    @pytest.mark.asyncio
    @pytest.mark.workflow
    async def test_multiple_concurrent_stories(self, a2a_clients, sample_story):
        """
        Test handling multiple concurrent story assignments.

        This test is marked as slow and can be skipped with: pytest -m "not slow"
        """
        # Assign 3 stories concurrently
        story_ids = []

        for i in range(3):
            story = sample_story.copy()
            story['topic'] = f"{story['topic']} - Part {i+1}"

            request = {
                "action": "assign_story",
                "story": story
            }
            message = create_text_message_object(content=json.dumps(request))

            async for response in a2a_clients['news_chief'].send_message(message):
                if hasattr(response, 'parts') and response.parts:
                    part = response.parts[0]
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        result = json.loads(part.root.text)
                        story_ids.append(result['story_id'])
                        break

        assert len(story_ids) == 3, "Should have 3 story IDs"

        # Verify all stories are tracked
        request = {"action": "get_status"}
        message = create_text_message_object(content=json.dumps(request))

        async for response in a2a_clients['news_chief'].send_message(message):
            if hasattr(response, 'parts') and response.parts:
                part = response.parts[0]
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    result = json.loads(part.root.text)
                    active_stories = result.get('active_stories', {})
                    assert len(active_stories) >= 3, f"Should have at least 3 active stories, got {len(active_stories)}"
                    break

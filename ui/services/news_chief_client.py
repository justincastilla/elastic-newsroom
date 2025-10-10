"""
News Chief A2A Client

This module provides a client for communicating with the News Chief agent via A2A protocol.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
import httpx
from a2a.types import AgentCard

logger = logging.getLogger(__name__)


class NewsChiefClient:
    """Client for interacting with News Chief agent via A2A protocol"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.agent_card_url = f"{base_url}/.well-known/agent-card.json"
        self.agent_card: Optional[AgentCard] = None
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def _get_agent_card(self) -> AgentCard:
        """Fetch and cache the agent card"""
        if self.agent_card:
            return self.agent_card

        logger.info(f"📥 Fetching agent card from: {self.agent_card_url}")
        response = await self.http_client.get(self.agent_card_url)
        response.raise_for_status()
        card_data = response.json()
        self.agent_card = AgentCard(**card_data)
        logger.info(f"✅ Agent card loaded: {self.agent_card.name}")
        return self.agent_card

    async def assign_story(
        self,
        topic: str,
        angle: str,
        target_length: int,
        deadline: str,
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        Assign a new story to the News Chief

        Args:
            topic: Story topic
            angle: Editorial angle
            target_length: Target word count
            deadline: Publication deadline
            priority: Story priority (low, medium, high, urgent)

        Returns:
            Response from News Chief with story_id
        """
        logger.info(f"📝 Assigning story: {topic}")

        # Get agent card to find the correct endpoint
        await self._get_agent_card()

        # Prepare the request payload for News Chief
        payload = {
            "action": "assign_story",
            "story": {
                "topic": topic,
                "angle": angle,
                "target_length": target_length,
                "deadline": deadline,
                "priority": priority,
            }
        }

        # Send JSON-RPC request to News Chief
        # A2A SDK uses JSON-RPC 2.0 at the root endpoint "/"
        rpc_url = f"{self.base_url}/"
        message_id = f"ui_assign_{asyncio.get_event_loop().time()}"

        logger.info(f"🚀 Sending A2A message to: {rpc_url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        # Construct JSON-RPC 2.0 message following A2A protocol
        rpc_request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"text": json.dumps(payload)}],
                }
            },
            "id": 1,
        }

        response = await self.http_client.post(
            rpc_url, json=rpc_request, headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()
        rpc_response = response.json()

        # Extract result from JSON-RPC response
        if "result" in rpc_response:
            result_message = rpc_response["result"]
            # Parse the text from the first part
            if "parts" in result_message and len(result_message["parts"]) > 0:
                text_content = result_message["parts"][0].get("text", "{}")
                result = json.loads(text_content)
                logger.info(f"✅ Story assigned successfully")
                return result

        logger.error(f"❌ Unexpected response format: {rpc_response}")
        raise Exception("Invalid response from News Chief")

    async def get_story_status(self, story_id: str) -> Dict[str, Any]:
        """
        Get the current status of a story

        Args:
            story_id: The story identifier

        Returns:
            Story status information
        """
        logger.info(f"🔍 Checking status for story: {story_id}")

        payload = {"action": "get_story_status", "story_id": story_id}

        # Send JSON-RPC request to News Chief
        rpc_url = f"{self.base_url}/"
        message_id = f"ui_status_{asyncio.get_event_loop().time()}"

        rpc_request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"text": json.dumps(payload)}],
                }
            },
            "id": 1,
        }

        response = await self.http_client.post(
            rpc_url, json=rpc_request, headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()
        rpc_response = response.json()

        # Extract result from JSON-RPC response
        if "result" in rpc_response:
            result_message = rpc_response["result"]
            if "parts" in result_message and len(result_message["parts"]) > 0:
                text_content = result_message["parts"][0].get("text", "{}")
                result = json.loads(text_content)
                logger.debug(f"Status response: {json.dumps(result, indent=2)}")
                return result

        logger.error(f"❌ Unexpected response format: {rpc_response}")
        raise Exception("Invalid response from News Chief")

    async def poll_until_complete(
        self, story_id: str, poll_interval: float = 2.0, timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Poll the News Chief until the story is complete

        Args:
            story_id: The story identifier
            poll_interval: Seconds between polls (default 2.0)
            timeout: Maximum time to wait in seconds (default 300 = 5 minutes)

        Returns:
            Final story data when status is 'published'

        Raises:
            TimeoutError: If timeout is reached
            Exception: If story fails
        """
        logger.info(f"⏳ Polling for story completion: {story_id}")
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Story {story_id} did not complete within {timeout} seconds"
                )

            status_response = await self.get_story_status(story_id)

            # Extract status from response
            # The response structure: {"status": "success", "story": {"status": "pending|published|failed", ...}}
            if isinstance(status_response, dict):
                # Get the story object from the response
                story = status_response.get("story", {})
                story_status = story.get("status")

                logger.info(f"📊 Story status: {story_status}")

                if story_status == "published":
                    logger.info(f"✅ Story complete!")
                    return story

                if story_status == "failed":
                    error_msg = story.get("error", "Unknown error")
                    raise Exception(f"Story failed: {error_msg}")

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    async def list_active_stories(self) -> Dict[str, Any]:
        """
        List all active stories

        Returns:
            List of active stories
        """
        logger.info(f"📋 Fetching active stories")

        payload = {"action": "list_active_stories"}

        # Send JSON-RPC request to News Chief
        rpc_url = f"{self.base_url}/"
        message_id = f"ui_list_{asyncio.get_event_loop().time()}"

        rpc_request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"text": json.dumps(payload)}],
                }
            },
            "id": 1,
        }

        response = await self.http_client.post(
            rpc_url, json=rpc_request, headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()
        rpc_response = response.json()

        # Extract result from JSON-RPC response
        if "result" in rpc_response:
            result_message = rpc_response["result"]
            if "parts" in result_message and len(result_message["parts"]) > 0:
                text_content = result_message["parts"][0].get("text", "{}")
                result = json.loads(text_content)
                return result

        logger.error(f"❌ Unexpected response format: {rpc_response}")
        raise Exception("Invalid response from News Chief")

    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()

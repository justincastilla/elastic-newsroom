"""
Base Agent Class

Provides common utilities and helper methods for all Elastic News agents.
Reduces code duplication and ensures consistency across agents.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import httpx
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver
from a2a.types import AgentCard
from utils import init_anthropic_client


class BaseAgent:
    """
    Base class for all Elastic News agents with common utilities.

    Provides:
    - Standardized response builders (_error_response, _success_response)
    - A2A client creation and response parsing
    - Anthropic API calls with consistent error handling
    - JSON utility methods
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize base agent with logger.

        Args:
            logger: Logger instance for this agent
        """
        self.logger = logger
        self.anthropic_client = None
        self.event_hub_url = os.getenv("EVENT_HUB_URL", "http://localhost:8090")
        self.event_hub_enabled = os.getenv("EVENT_HUB_ENABLED", "true").lower() == "true"

    # ===== Response Builders =====

    def _error_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Build standardized error response dictionary.

        Args:
            message: Error message to return
            **kwargs: Additional fields to include in response

        Returns:
            Dictionary with status="error" and message
        """
        self.logger.error(f"❌ {message}")
        return {"status": "error", "message": message, **kwargs}

    def _success_response(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        Build standardized success response dictionary.

        Args:
            message: Success message to return
            **kwargs: Additional fields to include in response

        Returns:
            Dictionary with status="success" and message
        """
        return {"status": "success", "message": message, **kwargs}

    # ===== A2A Communication Helpers =====

    async def _create_a2a_client(
        self,
        http_client: httpx.AsyncClient,
        agent_url: str,
        agent_name: str
    ) -> Tuple[Any, AgentCard]:
        """
        Create A2A client for communication with another agent.

        This method handles:
        - Agent discovery via A2ACardResolver
        - Client configuration
        - Client creation via ClientFactory

        Args:
            http_client: HTTP client to use for communication
            agent_url: URL of the target agent
            agent_name: Human-readable name for logging

        Returns:
            Tuple of (client, agent_card)

        Raises:
            Exception: If agent discovery or client creation fails
        """
        self.logger.info(f"🔍 Discovering {agent_name} agent at {agent_url}")
        card_resolver = A2ACardResolver(http_client, agent_url)
        agent_card = await card_resolver.get_agent_card()
        self.logger.info(f"✅ Found {agent_name}: {agent_card.name} (v{agent_card.version})")

        self.logger.info(f"🔧 Creating A2A client...")
        client_config = ClientConfig(httpx_client=http_client, streaming=False)
        client_factory = ClientFactory(client_config)
        client = client_factory.create(agent_card)

        return client, agent_card

    async def _parse_a2a_response(self, client, message) -> Optional[Dict[str, Any]]:
        """
        Parse JSON response from A2A client.

        Iterates through response parts and extracts the first valid JSON response.

        Args:
            client: A2A client instance
            message: Message to send to the client

        Returns:
            Parsed JSON dictionary or None if no valid response
        """
        async for response in client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    return json.loads(text_content)
        return None

    # ===== Anthropic API Helpers =====

    def _init_anthropic_client(self):
        """
        Initialize Anthropic client if not already initialized.

        Returns:
            Anthropic client instance or None if initialization fails
        """
        if self.anthropic_client is None:
            self.anthropic_client = init_anthropic_client(self.logger)
        return self.anthropic_client

    async def _call_anthropic(
        self,
        prompt: str,
        max_tokens: int = 2000,
        model: str = "claude-sonnet-4-20250514",
        fallback: Any = None
    ) -> Optional[str]:
        """
        Call Anthropic API with consistent error handling.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response
            model: Model identifier to use
            fallback: Fallback value or callable to return if API call fails

        Returns:
            Response text from Claude or fallback value
        """
        if self.anthropic_client is None:
            self._init_anthropic_client()

        if self.anthropic_client is None:
            self.logger.warning("⚠️  Anthropic client not available, using fallback")
            return fallback() if callable(fallback) else fallback

        try:
            message = self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            self.logger.error(f"❌ Anthropic API error: {e}")
            return fallback() if callable(fallback) else fallback

    # ===== JSON Utilities =====

    def _strip_json_codeblocks(self, text: str) -> str:
        """
        Remove markdown code blocks from JSON response.

        Claude sometimes wraps JSON in markdown code blocks like:
        ```json
        {...}
        ```

        This method extracts the JSON content from such blocks.

        Args:
            text: Text that may contain markdown-wrapped JSON

        Returns:
            Cleaned JSON string
        """
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text

    # ===== Event Hub Integration =====

    async def _publish_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        story_id: Optional[str] = None
    ) -> bool:
        """
        Publish event to central Event Hub for real-time UI updates.

        This allows the UI to monitor agent activity without polling individual agents.
        Events are published asynchronously and failures do not affect agent operation.

        Args:
            event_type: Type of event (e.g., "story_assigned", "article_drafted")
            data: Optional event payload with additional details
            story_id: Optional story ID if event relates to a specific story

        Returns:
            True if event was published successfully, False otherwise

        Example:
            await self._publish_event(
                event_type="research_started",
                story_id="story_123",
                data={"questions": 5, "topic": "AI in Journalism"}
            )
        """
        if not self.event_hub_enabled:
            return False

        if data is None:
            data = {}

        event = {
            "agent": self.__class__.__name__,
            "event_type": event_type,
            "story_id": story_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.event_hub_url}/events",
                    json=event
                )
                response.raise_for_status()
                return True

        except httpx.TimeoutException:
            self.logger.debug(f"Event Hub timeout for event: {event_type}")
            return False
        except httpx.HTTPError as e:
            self.logger.debug(f"Event Hub HTTP error: {e}")
            return False
        except Exception as e:
            self.logger.debug(f"Failed to publish event '{event_type}': {e}")
            return False

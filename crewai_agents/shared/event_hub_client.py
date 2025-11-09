"""
Event Hub Client for CrewAI Agents

Client for publishing events to the central Event Hub for real-time UI updates.
This allows CrewAI agents to broadcast their activities to connected UI clients.
"""

import httpx
import logging
from datetime import datetime
from typing import Dict, Any, Optional


class EventHubClient:
    """
    Client for publishing events to Event Hub from CrewAI agents.

    The Event Hub broadcasts events to connected UI clients via Server-Sent Events (SSE),
    enabling real-time monitoring of agent activities in the newsroom.

    Features:
    - Asynchronous event publishing
    - Silent failures (doesn't break agent execution)
    - Structured event format
    - Story-specific event filtering support
    """

    def __init__(
        self,
        event_hub_url: str = "http://localhost:8090",
        enabled: bool = True,
        timeout: float = 5.0
    ):
        """
        Initialize Event Hub client.

        Args:
            event_hub_url: URL of the Event Hub service (default: http://localhost:8090)
            enabled: Whether event publishing is enabled (default: True)
            timeout: HTTP request timeout in seconds (default: 5.0)
        """
        self.event_hub_url = event_hub_url
        self.enabled = enabled
        self.timeout = timeout
        self.logger = logging.getLogger("EVENT_HUB_CLIENT")

        if not self.enabled:
            self.logger.info("Event Hub publishing disabled")
        else:
            self.logger.info(f"Event Hub client initialized: {event_hub_url}")

    async def publish_event(
        self,
        agent_name: str,
        event_type: str,
        story_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> bool:
        """
        Publish event to Event Hub.

        Events are published asynchronously and failures do not affect agent operation.
        This ensures that Event Hub connectivity issues don't break the newsroom workflow.

        Args:
            agent_name: Name of the agent publishing the event (e.g., "ResearcherCrew")
            event_type: Type of event (e.g., "research_started", "research_completed")
            story_id: Optional story ID if event relates to a specific story
            data: Optional event payload with additional details
            message: Optional human-readable message describing the event

        Returns:
            True if event was published successfully, False otherwise

        Example:
            success = await client.publish_event(
                agent_name="ResearcherCrew",
                event_type="research_started",
                story_id="story_123",
                data={"topic": "AI in Journalism", "question_count": 5},
                message="Research started for AI in Journalism"
            )
        """
        if not self.enabled:
            return False

        if data is None:
            data = {}

        # Build event payload
        event = {
            "agent": agent_name,
            "event_type": event_type,
            "story_id": story_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        # Add message if provided
        if message:
            event["message"] = message

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.event_hub_url}/events",
                    json=event
                )
                response.raise_for_status()

                self.logger.debug(
                    f"✅ Event published: {event_type} "
                    f"(story: {story_id or 'N/A'})"
                )
                return True

        except httpx.TimeoutException:
            self.logger.debug(
                f"Event Hub timeout for event: {event_type} "
                f"(story: {story_id or 'N/A'})"
            )
            return False

        except httpx.HTTPError as e:
            self.logger.debug(
                f"Event Hub HTTP error for event: {event_type} - {e}"
            )
            return False

        except Exception as e:
            self.logger.debug(
                f"Failed to publish event '{event_type}': {e}"
            )
            return False

    async def publish_research_started(
        self,
        story_id: str,
        topic: str,
        question_count: int
    ) -> bool:
        """
        Convenience method: Publish research_started event.

        Args:
            story_id: Story identifier
            topic: Research topic
            question_count: Number of questions being researched

        Returns:
            True if published successfully, False otherwise
        """
        return await self.publish_event(
            agent_name="ResearcherCrew",
            event_type="research_started",
            story_id=story_id,
            data={
                "topic": topic,
                "question_count": question_count
            },
            message=f"Research started for {topic}"
        )

    async def publish_research_completed(
        self,
        story_id: str,
        topic: str,
        results_count: int,
        research_id: str
    ) -> bool:
        """
        Convenience method: Publish research_completed event.

        Args:
            story_id: Story identifier
            topic: Research topic
            results_count: Number of research results
            research_id: Unique research identifier

        Returns:
            True if published successfully, False otherwise
        """
        return await self.publish_event(
            agent_name="ResearcherCrew",
            event_type="research_completed",
            story_id=story_id,
            data={
                "topic": topic,
                "results_count": results_count,
                "research_id": research_id
            },
            message=f"Research completed for {topic}: {results_count} results"
        )

    async def publish_research_error(
        self,
        story_id: str,
        topic: str,
        error_message: str
    ) -> bool:
        """
        Convenience method: Publish research_error event.

        Args:
            story_id: Story identifier
            topic: Research topic
            error_message: Error message

        Returns:
            True if published successfully, False otherwise
        """
        return await self.publish_event(
            agent_name="ResearcherCrew",
            event_type="research_error",
            story_id=story_id,
            data={
                "topic": topic,
                "error": error_message
            },
            message=f"Research error for {topic}: {error_message}"
        )

    def disable(self):
        """Disable event publishing."""
        self.enabled = False
        self.logger.info("Event Hub publishing disabled")

    def enable(self):
        """Enable event publishing."""
        self.enabled = True
        self.logger.info("Event Hub publishing enabled")

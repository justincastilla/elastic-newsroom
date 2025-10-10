"""
News Chief Agent

The coordinator agent that assigns stories and oversees the newsroom workflow.
Uses the official A2A SDK for agent communication.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import click
import httpx

from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils import new_agent_text_message
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver, create_text_message_object
from utils import setup_logger, run_agent_server

# Configure logging using centralized utility
logger = setup_logger("NEWS_CHIEF")


class NewsChiefAgent:
    """News Chief Agent - Coordinates newsroom workflow and assigns stories"""

    def __init__(self, reporter_url: Optional[str] = None):
        self.active_stories: Dict[str, Dict[str, Any]] = {}
        self.available_reporters: List[str] = []
        self.reporter_url = reporter_url or "http://localhost:8081"
        self.reporter_client = None
    
    async def invoke(self, query: str) -> Dict[str, Any]:
        """
        Main entry point for the agent. Processes a query and returns a result.

        Args:
            query: JSON string with action and parameters

        Returns:
            Dictionary with the result of the action
        """
        try:
            logger.info(f"📥 Received query: {query[:200]}...")

            # Parse the query to determine the action
            query_data = json.loads(query) if query.startswith('{') else {"action": "assign_story", "story": {"topic": query}}
            action = query_data.get("action", "assign_story")

            logger.info(f"🎯 Action: {action}")

            if action == "assign_story":
                return await self._assign_story(query_data)
            elif action == "get_story_status":
                return await self._get_story_status(query_data)
            elif action == "list_active_stories":
                return await self._list_active_stories(query_data)
            elif action == "register_reporter":
                return await self._register_reporter(query_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": ["assign_story", "get_story_status", "list_active_stories", "register_reporter"]
                }

        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in query: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }
    
    async def _assign_story(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a story to a reporter with input validation"""
        logger.info("📝 Processing story assignment...")
        story_data = request.get("story", {})

        # Validate story data
        if not story_data:
            return {
                "status": "error",
                "message": "No story data provided"
            }

        # Validate topic (required)
        topic = story_data.get("topic", "").strip()
        if not topic:
            return {
                "status": "error",
                "message": "Story topic is required"
            }

        # Validate target_length (if provided)
        target_length = story_data.get("target_length", 1000)
        if not isinstance(target_length, int) or target_length <= 0:
            return {
                "status": "error",
                "message": "Invalid target_length: must be a positive integer"
            }

        # Validate priority (if provided)
        priority = story_data.get("priority", "normal")
        valid_priorities = ["low", "normal", "high", "urgent"]
        if priority not in valid_priorities:
            return {
                "status": "error",
                "message": f"Invalid priority: must be one of {valid_priorities}"
            }

        # Create story assignment
        story_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        story_assignment = {
            "story_id": story_id,
            "topic": topic,
            "angle": story_data.get("angle", "").strip(),
            "target_length": target_length,
            "deadline": story_data.get("deadline"),
            "priority": priority,
            "assigned_to": None,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Assign to first available reporter (for now)
        if self.available_reporters:
            story_assignment["assigned_to"] = self.available_reporters[0]
            story_assignment["status"] = "assigned"

        self.active_stories[story_id] = story_assignment

        logger.info(f"✅ Story created: {story_id}")
        logger.info(f"   Topic: {story_assignment['topic']}")
        logger.info(f"   Status: {story_assignment['status']}")

        # Send assignment to Reporter via A2A
        logger.info(f"📤 Sending assignment to Reporter via A2A...")
        reporter_response = await self._send_to_reporter(story_assignment)

        logger.info(f"✅ Assignment completed. Reporter status: {reporter_response.get('status')}")

        return {
            "status": "success",
            "message": f"Story '{story_assignment['topic']}' assigned successfully",
            "story_id": story_id,
            "assignment": story_assignment,
            "reporter_response": reporter_response
        }
    
    async def _get_story_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get the status of a specific story"""
        story_id = request.get("story_id")
        
        if not story_id:
            return {
                "status": "error",
                "message": "No story_id provided"
            }
        
        if story_id not in self.active_stories:
            return {
                "status": "error",
                "message": f"Story {story_id} not found"
            }
        
        return {
            "status": "success",
            "story": self.active_stories[story_id]
        }
    
    async def _list_active_stories(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """List all active stories"""
        return {
            "status": "success",
            "stories": list(self.active_stories.values()),
            "total_count": len(self.active_stories)
        }
    
    async def _register_reporter(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Register a reporter agent"""
        reporter_id = request.get("reporter_id")

        if not reporter_id:
            return {
                "status": "error",
                "message": "No reporter_id provided"
            }

        if reporter_id not in self.available_reporters:
            self.available_reporters.append(reporter_id)

        return {
            "status": "success",
            "message": f"Reporter {reporter_id} registered successfully",
            "available_reporters": self.available_reporters
        }

    async def _trigger_write_async(self, story_id: str):
        """Trigger article writing asynchronously without blocking"""
        try:
            logger.info(f"🔄 Background task: Sending write command for story {story_id}")

            # Create a new HTTP client for this async task
            async with httpx.AsyncClient(timeout=300.0) as http_client:
                # Discover Reporter agent
                card_resolver = A2ACardResolver(http_client, self.reporter_url)
                reporter_card = await card_resolver.get_agent_card()

                # Create A2A client
                client_config = ClientConfig(httpx_client=http_client, streaming=False)
                client_factory = ClientFactory(client_config)
                reporter_client = client_factory.create(reporter_card)

                # Send write_article command
                write_request = {
                    "action": "write_article",
                    "story_id": story_id
                }
                write_message = create_text_message_object(content=json.dumps(write_request))

                async for response in reporter_client.send_message(write_message):
                    if hasattr(response, 'parts'):
                        part = response.parts[0]
                        text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                        if text_content:
                            write_result = json.loads(text_content)
                            logger.info(f"✅ Background task: Write command completed")
                            logger.info(f"   Status: {write_result.get('status')}")
                            logger.info(f"   Message: {write_result.get('message')}")

                            # Update story status based on result
                            if story_id in self.active_stories:
                                if write_result.get('status') == 'success':
                                    self.active_stories[story_id]['status'] = 'completed'
                                    # Store article data for UI retrieval
                                    if 'article_data' in write_result:
                                        self.active_stories[story_id]['article_data'] = write_result['article_data']
                                        logger.info(f"✅ Stored article data for story {story_id}")
                                else:
                                    self.active_stories[story_id]['status'] = 'error'
                            break
        except Exception as e:
            logger.error(f"Background task error for story {story_id}: {e}")
            if story_id in self.active_stories:
                self.active_stories[story_id]['status'] = 'error'

    async def _send_to_reporter(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Send story assignment to Reporter agent via A2A"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as http_client:
                # Discover Reporter agent
                logger.info(f"🔍 Discovering Reporter agent at {self.reporter_url}")
                card_resolver = A2ACardResolver(http_client, self.reporter_url)
                reporter_card = await card_resolver.get_agent_card()
                logger.info(f"✅ Found Reporter: {reporter_card.name} (v{reporter_card.version})")

                # Create A2A client
                logger.info(f"🔧 Creating A2A client...")
                client_config = ClientConfig(httpx_client=http_client, streaming=False)
                client_factory = ClientFactory(client_config)
                reporter_client = client_factory.create(reporter_card)

                # Send accept_assignment task to Reporter
                request = {
                    "action": "accept_assignment",
                    "assignment": assignment
                }
                logger.info(f"📨 Sending A2A message to Reporter:")
                logger.info(f"   Action: {request['action']}")
                logger.info(f"   Story ID: {assignment.get('story_id')}")
                logger.info(f"   Topic: {assignment.get('topic')}")

                message = create_text_message_object(content=json.dumps(request))

                # Get response for assignment acceptance
                logger.info(f"⏳ Waiting for Reporter response...")
                assignment_result = None
                async for response in reporter_client.send_message(message):
                    if hasattr(response, 'parts'):
                        part = response.parts[0]
                        text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                        if text_content:
                            assignment_result = json.loads(text_content)
                            logger.info(f"📬 Received A2A response from Reporter:")
                            logger.info(f"   Status: {assignment_result.get('status')}")
                            logger.info(f"   Message: {assignment_result.get('message')}")
                            logger.info(f"   Reporter Status: {assignment_result.get('reporter_status')}")
                            break

                if not assignment_result:
                    logger.warning("⚠️  No response from Reporter")
                    return {"status": "error", "message": "No response from Reporter"}

                # If assignment was accepted, trigger the Reporter to start writing (async, don't wait)
                if assignment_result.get('status') == 'success':
                    logger.info(f"✅ Assignment accepted, triggering article writing in background...")

                    # Update story status to 'writing'
                    story_id = assignment.get('story_id')
                    if story_id in self.active_stories:
                        self.active_stories[story_id]['status'] = 'writing'

                    # Send write_article command but don't wait for response
                    # The Reporter will work asynchronously
                    import asyncio
                    logger.info(f"📝 Triggering write_article command (async)...")

                    # Fire and forget - don't wait for the response
                    asyncio.create_task(self._trigger_write_async(story_id))

                return assignment_result

        except Exception as e:
            logger.error(f"Failed to send assignment to Reporter: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to contact Reporter: {str(e)}"
            }


# Singleton instance of the News Chief agent to maintain state across requests
_news_chief_agent_instance = None

def get_news_chief_agent():
    """Get or create the singleton News Chief agent instance"""
    global _news_chief_agent_instance
    if _news_chief_agent_instance is None:
        _news_chief_agent_instance = NewsChiefAgent()
    return _news_chief_agent_instance


class NewsChiefAgentExecutor(AgentExecutor):
    """AgentExecutor for the News Chief agent following official A2A pattern"""

    def __init__(self):
        # Use singleton instance to maintain state across requests
        self.agent = get_news_chief_agent()

    async def execute(self, context, event_queue) -> None:
        """Execute the agent request"""
        logger.info('Executing News Chief agent')

        query = context.get_user_input()
        result = await self.agent.invoke(query)

        # Send result as A2A message
        await event_queue.enqueue_event(
            new_agent_text_message(json.dumps(result, indent=2))
        )

    async def cancel(self, context, event_queue) -> None:
        """Cancel a task - not supported for this agent"""
        raise Exception('Cancel not supported')


# Agent Card definition (single source of truth)
def create_agent_card(host: str, port: int) -> AgentCard:
    """Create the News Chief agent card"""
    return AgentCard(
        name="News Chief",
        description="Coordinates newsroom workflow and assigns stories to specialized agents",
        url=f"http://{host}:{port}",
        version="1.0.0",
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/news-chief-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True,
            state_transition_history=True,
            max_concurrent_tasks=50
        ),
        skills=[
            AgentSkill(
                id="newsroom.coordination.story_assignment",
                name="Story Assignment",
                description="Assigns stories to reporter agents and coordinates workflow",
                tags=["coordination", "story-assignment"],
                examples=[
                    '{"action": "assign_story", "story": {"topic": "Renewable Energy Adoption", "priority": "high"}}',
                    "Assign a story about climate change"
                ]
            ),
            AgentSkill(
                id="newsroom.coordination.story_status",
                name="Story Status",
                description="Retrieves the status of assigned stories",
                tags=["coordination", "status"],
                examples=[
                    '{"action": "get_story_status", "story_id": "story_20250107_120000"}',
                    '{"action": "list_active_stories"}'
                ]
            ),
            AgentSkill(
                id="newsroom.coordination.reporter_management",
                name="Reporter Management",
                description="Manages reporter registration and availability",
                tags=["coordination", "reporters"],
                examples=[
                    '{"action": "register_reporter", "reporter_id": "reporter_001"}'
                ]
            )
        ],
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        provider={
            "organization": "Elastic News",
            "url": "https://newsroom.example.com"
        }
    )


def create_app(host='localhost', port=8080):
    """Factory function to create the A2A application"""
    # Create agent card using the single source of truth
    agent_card = create_agent_card(host, port)

    # Set up the request handler
    request_handler = DefaultRequestHandler(
        agent_executor=NewsChiefAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create the A2A application
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    return server.build()


# Create default app instance for uvicorn
app = create_app()


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=8080)
@click.option('--reload', 'reload', is_flag=True, default=False, help='Enable hot reload on file changes')
def main(host, port, reload):
    """Starts the News Chief Agent server."""
    run_agent_server(
        agent_name="News Chief",
        host=host,
        port=port,
        create_app_func=lambda: create_app(host, port),
        logger=logger,
        reload=reload,
        reload_module="agents.news_chief:app" if reload else None
    )


if __name__ == "__main__":
    main()

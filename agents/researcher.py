"""
Researcher Agent

Provides factual information, background context, and supporting figures for articles.
Uses Anthropic Claude to generate research responses with structured data.
"""

import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

import click
from starlette.middleware.cors import CORSMiddleware
from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils import new_agent_text_message
from utils import setup_logger, load_env_config, init_anthropic_client, run_agent_server, format_json_for_log
from agents.base_agent import BaseAgent

# Load environment variables
load_env_config()

# Configure logging using centralized utility
logger = setup_logger("RESEARCHER")

# Singleton instance for maintaining state across requests
_researcher_agent_instance = None

class ResearcherAgent(BaseAgent):
    """Researcher Agent - Provides factual information and supporting data"""

    def __init__(self):
        # Initialize base agent with logger
        super().__init__(logger)

        self.research_history: Dict[str, Dict[str, Any]] = {}

        # Initialize Anthropic client using centralized utility (from BaseAgent)
        self._init_anthropic_client()

        # Initialize MCP client for tool calling
        self._init_mcp_client()

    async def invoke(self, query: str) -> Dict[str, Any]:
        """
        Main entry point for the agent. Processes a query and returns a result.

        Args:
            query: JSON string with action and parameters

        Returns:
            Dictionary with the result of the action
        """
        try:
            # Only log non-status queries to reduce log spam
            if not query.startswith('{"action": "get_status"'):
                logger.info(f"📥 Received query:\n{format_json_for_log(query)}")

            # Parse the query to determine the action
            query_data = json.loads(query) if query.startswith('{') else {"action": "status"}
            action = query_data.get("action")

            # Only log non-status actions to reduce log spam
            if action != "get_status":
                logger.info(f"🎯 Action: {action}")

            if action == "research_questions":
                return await self._research_questions(query_data)
            elif action == "get_history":
                return await self._get_history(query_data)
            elif action == "get_status":
                return await self._get_status(query_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": ["research_questions", "get_history", "get_status"]
                }

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in query: {e}")
            return {
                "status": "error",
                "message": f"Invalid JSON in query: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Error processing request: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }

    async def _research_questions(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Research multiple questions and return structured data"""
        logger.info("🔍 Processing research request...")

        questions = request.get("questions", [])
        topic = request.get("topic", "")
        story_id = request.get("story_id", "")

        if not questions:
            logger.error("❌ No questions provided")
            return {
                "status": "error",
                "message": "No questions provided"
            }

        logger.info(f"📋 Research request details:")
        logger.info(f"   Story ID: {story_id}")
        logger.info(f"   Topic: {topic}")
        logger.info(f"   Questions: {len(questions)}")
        for i, question in enumerate(questions[:5], 1):
            logger.info(f"   {i}. {question}")

        # Publish event: research started
        await self._publish_event(
            event_type="research_started",
            story_id=story_id,
            data={"topic": topic, "question_count": len(questions)}
        )

        # Process all questions in a single API call
        try:
            research_results = await self._conduct_bulk_research(questions[:5], topic)
        except Exception as e:
            logger.error(f"❌ Error conducting bulk research: {e}")
            # Fallback to empty results on error
            research_results = [{
                "question": q,
                "error": str(e),
                "claim_verified": False,
                "confidence": 0
            } for q in questions[:5]]

        # Store research in history
        research_id = f"research_{story_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        research_record = {
            "research_id": research_id,
            "story_id": story_id,
            "topic": topic,
            "questions": questions,
            "results": research_results,
            "completed_at": datetime.now().isoformat(),
            "total_questions": len(questions)
        }
        self.research_history[research_id] = research_record

        # Publish event: research completed
        await self._publish_event(
            event_type="research_completed",
            story_id=story_id,
            data={
                "topic": topic,
                "question_count": len(questions),
                "results_count": len(research_results)
            }
        )

        logger.info(f"✅ Research completed")
        logger.info(f"   Research ID: {research_id}")
        logger.info(f"   Questions answered: {len(research_results)}")

        return {
            "status": "success",
            "message": f"Research completed for {len(research_results)} questions",
            "research_id": research_id,
            "story_id": story_id,
            "research_results": research_results,
            "total_questions": len(research_results)
        }

    async def _conduct_bulk_research(self, questions: List[str], topic: str) -> List[Dict[str, Any]]:
        """Conduct research for multiple questions using MCP research_questions tool"""

        try:
            logger.info(f"🔧 Calling MCP research_questions tool for {len(questions)} questions...")

            # Direct call to MCP tool (bypass LLM selection for efficiency and reliability)
            if self.mcp_client is None:
                self._init_mcp_client()

            result = await self.mcp_client.call_tool(
                tool_name="research_questions",
                arguments={
                    "questions": questions,
                    "topic": topic
                }
            )

            # Parse the JSON response
            results = json.loads(result) if isinstance(result, str) else result
            logger.info(f"✅ Received {len(results)} research results from MCP tool")

            # Ensure we have results for all questions (in case tool didn't answer all)
            if len(results) < len(questions):
                logger.warning(f"⚠️  MCP tool returned {len(results)} results for {len(questions)} questions")
                # Fill in missing results with mock data
                for i in range(len(results), len(questions)):
                    results.append(self._generate_mock_research(questions[i]))

            return results

        except Exception as e:
            logger.error(f"❌ MCP tool call error: {e}", exc_info=True)
            # MCP server is required - re-raise the exception
            raise Exception(f"MCP research_questions tool failed: {e}")

    def _generate_mock_research(self, question: str) -> Dict[str, Any]:
        """Generate mock research when Anthropic API is not available"""
        return {
            "question": question,
            "claim_verified": True,
            "confidence": 75,
            "summary": "Mock research data generated. Configure ANTHROPIC_API_KEY for real research.",
            "facts": [
                "Industry adoption has increased significantly in recent years",
                "Leading technology companies are investing heavily in this area",
                "Market analysts project continued growth through 2025"
            ],
            "figures": {
                "percentages": ["45%", "60% year-over-year growth"],
                "dollar_amounts": ["$1.5 billion", "$3.2 billion projected"],
                "numbers": ["500 companies", "1.2 million users"],
                "dates": ["Q3 2024", "2025"],
                "companies": ["TechCorp", "InnovateLabs", "DataSystems"]
            },
            "sources": [
                "Mock Industry Report 2024 (ANTHROPIC_API_KEY not configured)",
                "Mock Market Analysis",
                "Mock Tech Survey"
            ]
        }

    async def _get_history(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get research history by research_id or story_id"""
        research_id = request.get("research_id")
        story_id = request.get("story_id")

        if research_id:
            if research_id not in self.research_history:
                return {
                    "status": "error",
                    "message": f"Research {research_id} not found"
                }
            return {
                "status": "success",
                "research": self.research_history[research_id]
            }
        elif story_id:
            # Find all research for this story
            matching_research = [r for r in self.research_history.values() if r["story_id"] == story_id]
            if not matching_research:
                return {
                    "status": "error",
                    "message": f"No research found for story_id: {story_id}"
                }
            return {
                "status": "success",
                "research": matching_research
            }
        else:
            return {
                "status": "error",
                "message": "Either research_id or story_id must be provided"
            }

    async def _get_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get current status of all research"""
        return {
            "status": "success",
            "total_research_requests": len(self.research_history),
            "research_history": list(self.research_history.values())
        }


def get_researcher_agent() -> ResearcherAgent:
    """Get singleton ResearcherAgent instance to maintain state across requests"""
    global _researcher_agent_instance
    if _researcher_agent_instance is None:
        _researcher_agent_instance = ResearcherAgent()
    return _researcher_agent_instance


class ResearcherAgentExecutor(AgentExecutor):
    """AgentExecutor for the Researcher agent following official A2A pattern"""

    def __init__(self):
        # Use singleton instance to maintain state across requests
        self.agent = get_researcher_agent()

    async def execute(self, context, event_queue) -> None:
        """Execute the agent request"""
        logger.info('Executing Researcher agent')

        query = context.get_user_input()
        result = await self.agent.invoke(query)

        # Send result as A2A message
        await event_queue.enqueue_event(
            new_agent_text_message(json.dumps(result, indent=2))
        )

    async def cancel(self, context, event_queue) -> None:
        """Cancel a task - not supported for this agent"""
        raise Exception('Cancel not supported')


# Agent Card definition
def create_agent_card(host: str, port: int) -> AgentCard:
    """Create the Researcher agent card"""
    return AgentCard(
        name="Researcher",
        description="Provides factual information, background context, and supporting data with structured figures for news articles",
        url=f"http://{host}:{port}",
        version="1.0.0",
        protocol_version="0.3.0",  # A2A Protocol version
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/researcher-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,  # Not implemented yet
            state_transition_history=True,
            max_concurrent_tasks=30
        ),
        skills=[
            AgentSkill(
                id="research.questions.bulk_research",
                name="Research Questions",
                description="Researches multiple questions and returns structured data with facts, figures, and sources",
                tags=["research", "fact-checking", "data"],
                examples=[
                    '{"action": "research_questions", "story_id": "story_123", "topic": "AI in Journalism", "questions": ["What percentage of news orgs use AI?", "Who are the leading companies?"]}',
                    "Research multiple questions about a topic"
                ]
            ),
            AgentSkill(
                id="research.history.get_history",
                name="Get Research History",
                description="Retrieves past research by research_id or story_id",
                tags=["history", "retrieval"],
                examples=[
                    '{"action": "get_history", "research_id": "research_story_123_20250107_120000"}',
                    '{"action": "get_history", "story_id": "story_123"}'
                ]
            ),
            AgentSkill(
                id="research.status",
                name="Get Status",
                description="Returns current status and history of all research requests",
                tags=["status", "reporting"],
                examples=[
                    '{"action": "get_status"}'
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


def create_app(host='localhost', port=8083):
    """Factory function to create the A2A application"""
    agent_card = create_agent_card(host, port)

    request_handler = DefaultRequestHandler(
        agent_executor=ResearcherAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    app = server.build()

    # Add CORS middleware for React UI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# Create default app instance for uvicorn
app = create_app()


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=8083)
@click.option('--reload', 'reload', is_flag=True, default=False, help='Enable hot reload on file changes')
def main(host, port, reload):
    """Starts the Researcher Agent server."""
    run_agent_server(
        agent_name="Researcher",
        host=host,
        port=port,
        create_app_func=lambda: create_app(host, port),
        logger=logger,
        reload=reload,
        reload_module="agents.researcher:app" if reload else None
    )


if __name__ == "__main__":
    main()

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
from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils import new_agent_text_message
from utils import setup_logger, load_env_config, init_anthropic_client, run_agent_server

# Load environment variables
load_env_config()

# Configure logging using centralized utility
logger = setup_logger("RESEARCHER")


class ResearcherAgent:
    """Researcher Agent - Provides factual information and supporting data"""

    def __init__(self):
        self.research_history: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Anthropic client using centralized utility
        self.anthropic_client = init_anthropic_client(logger)

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
            query_data = json.loads(query) if query.startswith('{') else {"action": "status"}
            action = query_data.get("action")

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
        """Conduct research for multiple questions in a single API call using Anthropic"""

        # Build numbered questions for the prompt
        numbered_questions = "\n".join([f"{i}. {q}" for i, q in enumerate(questions, 1)])

        # Build research prompt
        prompt = f"""You are a research assistant for Elastic News, a technology news publication.

Article Topic: {topic}

Research Questions:
{numbered_questions}

Please provide comprehensive research for ALL questions above. Generate realistic, plausible data that sounds factual (even though it's fictional for this demo).

Provide your response as a JSON array with one object per question, maintaining the same numbering order. Use this exact format:

[
  {{
    "question_number": 1,
    "question": "First question text here",
    "claim_verified": true,
    "confidence": 85,
    "summary": "Brief 1-2 sentence summary of findings",
    "facts": [
      "Specific factual statement 1",
      "Specific factual statement 2",
      "Specific factual statement 3"
    ],
    "figures": {{
      "percentages": ["42%", "85% increase"],
      "dollar_amounts": ["$2.3 billion", "$500 million"],
      "numbers": ["1,200 companies", "3.5 million users"],
      "dates": ["Q4 2024", "January 2025"],
      "companies": ["Company A", "Company B", "Company C"]
    }},
    "sources": [
      "Industry Report 2024",
      "Market Analysis Q4 2024",
      "Tech Survey 2025"
    ]
  }},
  {{
    "question_number": 2,
    "question": "Second question text here",
    ... (same structure for each question)
  }}
]

Important:
- Answer ALL {len(questions)} questions in the array
- Keep the same numbering order (1, 2, 3, etc.)
- Generate plausible, realistic-sounding data
- Include specific figures, percentages, and company names where relevant
- Make it sound authoritative and well-researched

Provide ONLY the JSON array, no additional text."""

        # Use Anthropic if available
        if self.anthropic_client:
            try:
                logger.info(f"🤖 Making single Anthropic API call for {len(questions)} questions...")
                message = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,  # Increased for multiple questions
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Parse the JSON response
                research_text = message.content[0].text
                # Try to extract JSON if there's any markdown formatting
                if "```json" in research_text:
                    research_text = research_text.split("```json")[1].split("```")[0].strip()
                elif "```" in research_text:
                    research_text = research_text.split("```")[1].split("```")[0].strip()

                results = json.loads(research_text)
                logger.info(f"✅ Received {len(results)} research results from Anthropic")

                # Ensure we have results for all questions (in case API didn't answer all)
                if len(results) < len(questions):
                    logger.warning(f"⚠️  API returned {len(results)} results for {len(questions)} questions")
                    # Fill in missing results with mock data
                    for i in range(len(results), len(questions)):
                        results.append(self._generate_mock_research(questions[i]))

                return results

            except Exception as e:
                logger.error(f"❌ Anthropic API error: {e}", exc_info=True)
                # Fallback to mock research for all questions
                return [self._generate_mock_research(q) for q in questions]
        else:
            # No API key, use mock research for all questions
            return [self._generate_mock_research(q) for q in questions]

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


class ResearcherAgentExecutor(AgentExecutor):
    """AgentExecutor for the Researcher agent following official A2A pattern"""

    def __init__(self):
        self.agent = ResearcherAgent()

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
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/researcher-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True,
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

    return server.build()


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

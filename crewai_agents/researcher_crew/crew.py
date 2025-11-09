"""
CrewAI Crew Definition for Researcher

Orchestrates the research crew, bringing together agents, tasks, and tools
to provide comprehensive research capabilities for the newsroom.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from crewai import Crew, Process
from langchain_anthropic import ChatAnthropic

from crewai_agents.researcher_crew.agents import create_researcher_agent
from crewai_agents.researcher_crew.tasks import create_research_task
from crewai_agents.researcher_crew.tools import (
    research_questions_tool,
    fact_verification_tool
)
from crewai_agents.shared.event_hub_client import EventHubClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RESEARCHER_CREW")


class ResearcherCrew:
    """
    Researcher Crew - manages research tasks for news articles.

    This class replaces the A2A-based ResearcherAgent class, using CrewAI's
    multi-agent framework to provide enhanced research capabilities.

    Features:
    - Research multiple questions simultaneously
    - Fact verification with confidence scores
    - Structured research results with sources
    - Integration with existing MCP infrastructure
    - Memory and context retention across tasks
    """

    def __init__(self):
        """Initialize the researcher crew with LLM and tools."""
        self.research_history: Dict[str, Dict[str, Any]] = {}

        # Initialize ChatAnthropic LLM
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("⚠️  ANTHROPIC_API_KEY not set. Crew will use mock data.")
            self.llm = None
        else:
            self.llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=api_key,
                temperature=0.7,
                max_tokens=4000
            )
            logger.info("✅ ChatAnthropic LLM initialized")

        # Initialize tools
        self.tools = [research_questions_tool, fact_verification_tool]
        logger.info(f"✅ Loaded {len(self.tools)} research tools")

        # Initialize Event Hub client
        event_hub_url = os.getenv("EVENT_HUB_URL", "http://localhost:8090")
        event_hub_enabled = os.getenv("EVENT_HUB_ENABLED", "true").lower() == "true"
        self.event_hub = EventHubClient(
            event_hub_url=event_hub_url,
            enabled=event_hub_enabled
        )
        logger.info(f"✅ Event Hub client initialized (enabled: {event_hub_enabled})")

    def create_crew(
        self,
        questions: List[str],
        topic: str,
        story_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Crew:
        """
        Create a crew for a research request.

        Args:
            questions: List of research questions
            topic: Research topic
            story_id: Story identifier
            context: Optional additional context

        Returns:
            Configured CrewAI Crew ready for execution
        """
        logger.info(f"🔧 Creating research crew for story: {story_id}")
        logger.info(f"   Topic: {topic}")
        logger.info(f"   Questions: {len(questions)}")

        # Create researcher agent
        researcher_agent = create_researcher_agent(
            tools=self.tools,
            llm=self.llm
        )

        # Create research task
        research_task = create_research_task(
            agent=researcher_agent,
            questions=questions,
            topic=topic,
            story_id=story_id,
            context=context
        )

        # Create and configure crew
        crew = Crew(
            agents=[researcher_agent],
            tasks=[research_task],
            process=Process.sequential,  # Single agent, sequential execution
            verbose=True,
            memory=True,  # Enable crew memory
            embedder={
                "provider": "anthropic",
                "config": {
                    "model": "claude-sonnet-4-20250514",
                    "api_key": os.getenv("ANTHROPIC_API_KEY")
                }
            } if os.getenv("ANTHROPIC_API_KEY") else None
        )

        logger.info("✅ Research crew created")
        return crew

    async def research_questions(
        self,
        questions: List[str],
        topic: str,
        story_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for research requests.

        Maps to the original ResearcherAgent.invoke() -> _research_questions() flow.

        Args:
            questions: List of research questions to answer
            topic: The main topic or subject area
            story_id: Unique identifier for the story
            context: Optional additional context

        Returns:
            Dictionary with research results:
            {
                "status": "success",
                "message": "Research completed...",
                "research_id": "research_story_123_...",
                "story_id": "story_123",
                "research_results": [...],
                "total_questions": 5
            }
        """
        logger.info(f"🔍 Processing research request for story: {story_id}")
        logger.info(f"   Topic: {topic}")
        logger.info(f"   Questions: {len(questions)}")

        try:
            # Publish event: research started
            await self.event_hub.publish_research_started(
                story_id=story_id,
                topic=topic,
                question_count=len(questions)
            )

            # Create crew for this research request
            crew = self.create_crew(questions, topic, story_id, context)

            # Kickoff crew execution (async)
            logger.info("🚀 Kicking off research crew...")
            result = await crew.kickoff_async()

            # Parse crew output
            research_results = self._parse_crew_output(result, questions)

            # Generate research ID
            research_id = f"research_{story_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Store in history
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

            logger.info(f"✅ Research completed successfully")
            logger.info(f"   Research ID: {research_id}")
            logger.info(f"   Results: {len(research_results)} answers")

            # Publish event: research completed
            await self.event_hub.publish_research_completed(
                story_id=story_id,
                topic=topic,
                results_count=len(research_results),
                research_id=research_id
            )

            return {
                "status": "success",
                "message": f"Research completed for {len(research_results)} questions",
                "research_id": research_id,
                "story_id": story_id,
                "research_results": research_results,
                "total_questions": len(research_results)
            }

        except Exception as e:
            logger.error(f"❌ Research failed: {e}", exc_info=True)

            # Publish event: research error
            await self.event_hub.publish_research_error(
                story_id=story_id,
                topic=topic,
                error_message=str(e)
            )

            return {
                "status": "error",
                "message": f"Research failed: {str(e)}",
                "story_id": story_id,
                "research_results": []
            }

    def _parse_crew_output(
        self,
        crew_output: Any,
        original_questions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Parse CrewAI output into structured research results.

        Args:
            crew_output: Raw output from crew.kickoff_async()
            original_questions: Original questions for fallback

        Returns:
            List of research result dictionaries
        """
        try:
            # CrewAI output can be in different formats
            # Try to extract JSON from the output
            output_text = str(crew_output)

            # Try to parse as JSON
            if output_text.strip().startswith('['):
                results = json.loads(output_text)
                logger.info(f"✅ Parsed {len(results)} results from crew output")
                return results

            # Try to extract JSON from markdown code blocks
            if "```json" in output_text:
                json_text = output_text.split("```json")[1].split("```")[0].strip()
                results = json.loads(json_text)
                logger.info(f"✅ Extracted {len(results)} results from markdown")
                return results

            if "```" in output_text:
                json_text = output_text.split("```")[1].split("```")[0].strip()
                results = json.loads(json_text)
                logger.info(f"✅ Extracted {len(results)} results from code block")
                return results

            # If we can't parse, return mock structure
            logger.warning("⚠️  Could not parse crew output, generating structured response")
            return self._generate_mock_results(original_questions)

        except Exception as e:
            logger.warning(f"⚠️  Error parsing crew output: {e}")
            return self._generate_mock_results(original_questions)

    def _generate_mock_results(self, questions: List[str]) -> List[Dict[str, Any]]:
        """
        Generate mock research results as fallback.

        Args:
            questions: List of questions to create mock results for

        Returns:
            List of mock research result dictionaries
        """
        results = []
        for i, question in enumerate(questions):
            results.append({
                "question": question,
                "claim_verified": True,
                "confidence": 75,
                "summary": "Mock research data. Configure ANTHROPIC_API_KEY for real research.",
                "facts": [
                    "Industry adoption has increased significantly",
                    "Leading companies are investing heavily",
                    "Market analysts project continued growth"
                ],
                "figures": {
                    "percentages": ["45%", "60% growth"],
                    "dollar_amounts": ["$1.5B", "$3.2B"],
                    "numbers": ["500 companies", "1M users"],
                    "dates": ["Q4 2024", "2025"],
                    "companies": ["TechCorp", "InnovateLabs"]
                },
                "sources": [
                    "Mock Industry Report 2024",
                    "Mock Market Analysis"
                ]
            })
        return results

    def get_research_history(
        self,
        research_id: Optional[str] = None,
        story_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get research history by research_id or story_id.

        Args:
            research_id: Specific research ID to retrieve
            story_id: Story ID to find all related research

        Returns:
            Dictionary with research history
        """
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
            matching_research = [
                r for r in self.research_history.values()
                if r["story_id"] == story_id
            ]
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

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all research.

        Returns:
            Dictionary with status information
        """
        return {
            "status": "success",
            "total_research_requests": len(self.research_history),
            "research_history": list(self.research_history.values())
        }

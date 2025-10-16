"""
Reporter Agent

Writes news articles based on story assignments from the News Chief.
Uses Anthropic Claude for AI-powered content generation.
"""

import json
import os
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

import click
import httpx
from starlette.middleware.cors import CORSMiddleware
from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils import new_agent_text_message
from a2a.client import create_text_message_object
from utils import setup_logger, load_env_config, run_agent_server
from agents.base_agent import BaseAgent
from agents.archivist_client import call_archivist

# Load environment variables
load_env_config()

# Configure logging using centralized utility
logger = setup_logger("REPORTER")

# Singleton instance for maintaining state across requests
_reporter_agent_instance = None

class ReporterAgent(BaseAgent):
    """Reporter Agent - Writes news articles based on assignments"""

    def __init__(self, editor_url: Optional[str] = None, researcher_url: Optional[str] = None, archivist_url: Optional[str] = None, publisher_url: Optional[str] = None):
        # Initialize base agent with logger
        super().__init__(logger)

        self.assignments: Dict[str, Dict[str, Any]] = {}
        self.drafts: Dict[str, Dict[str, Any]] = {}
        self.editor_reviews: Dict[str, Dict[str, Any]] = {}
        self.research_data: Dict[str, Dict[str, Any]] = {}
        self.archive_data: Dict[str, Dict[str, Any]] = {}
        self.archivist_status: Dict[str, str] = {}  # Track Archivist activity per story
        self.waiting_status: Dict[str, str] = {}  # Track what agent is waiting for
        self.editor_url = editor_url or "http://localhost:8082"
        self.researcher_url = researcher_url or "http://localhost:8083"
        self.publisher_url = publisher_url or "http://localhost:8084"

        # Get Archivist configuration from environment
        # Prefer direct agent URL over agent card URL
        self.archivist_agent_url = os.getenv("ELASTIC_ARCHIVIST_AGENT_URL")  # Direct endpoint (preferred)
        self.archivist_card_url = archivist_url or os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL")  # Agent card URL (fallback)
        self.archivist_api_key = os.getenv("ELASTIC_ARCHIVIST_API_KEY")

        # Initialize Anthropic client using centralized utility (from BaseAgent)
        self._init_anthropic_client()
        if not self.anthropic_client:
            logger.warning("Will use mock article generation")

    # Note: Helper methods (_error_response, _success_response, _create_a2a_client,
    # _parse_a2a_response, _strip_json_codeblocks, _call_anthropic) are now
    # inherited from BaseAgent

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
                logger.info(f"📥 Received query: {query[:200]}...")

            # Parse the query to determine the action
            query_data = json.loads(query) if query.startswith('{') else {"action": "status"}
            action = query_data.get("action")

            # Only log non-status actions to reduce log spam
            if action != "get_status":
                logger.info(f"🎯 Action: {action}")

            if action == "accept_assignment":
                return await self._accept_assignment(query_data)
            elif action == "write_article":
                return await self._write_article(query_data)
            elif action == "apply_edits":
                return await self._apply_edits(query_data)
            elif action == "get_status":
                return await self._get_status(query_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": ["accept_assignment", "write_article", "apply_edits", "get_status"]
                }

        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in query: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }

    async def _accept_assignment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Accept a story assignment from News Chief"""
        logger.info("📨 Processing assignment from News Chief...")
        assignment = request.get("assignment", {})

        # Validate assignment
        if not assignment:
            return self._error_response("No assignment data provided")

        story_id = assignment.get("story_id")
        if not story_id:
            return self._error_response("Assignment missing story_id")

        logger.info(f"📋 Assignment details:")
        logger.info(f"   Story ID: {story_id}")
        logger.info(f"   Topic: {assignment.get('topic')}")
        logger.info(f"   Target Length: {assignment.get('target_length')} words")
        logger.info(f"   Priority: {assignment.get('priority')}")

        # Store assignment
        self.assignments[story_id] = {
            **assignment,
            "accepted_at": datetime.now().isoformat(),
            "status": "accepted",
            "reporter_status": "pending"
        }

        # Publish event: assignment accepted
        await self._publish_event(
            event_type="assignment_accepted",
            story_id=story_id,
            data={
                "topic": assignment.get("topic"),
                "target_length": assignment.get("target_length"),
                "priority": assignment.get("priority", "normal")
            }
        )

        logger.info(f"✅ Assignment accepted and stored")
        logger.info(f"   Total assignments: {len(self.assignments)}")

        return self._success_response(
            f"Assignment accepted for story: {assignment.get('topic', story_id)}",
            story_id=story_id,
            estimated_completion="30 minutes",
            reporter_status="ready_to_write"
        )

    async def _write_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Write an article using Anthropic Claude with Researcher support"""
        logger.info("✍️  Starting article writing...")
        story_id = request.get("story_id")

        if not story_id:
            return self._error_response("No story_id provided")

        if story_id not in self.assignments:
            return self._error_response(f"No assignment found for story_id: {story_id}")

        assignment = self.assignments[story_id]
        logger.info(f"📝 Writing article for: {assignment.get('topic')}")

        # Update status
        self.assignments[story_id]["reporter_status"] = "researching"
        self.assignments[story_id]["started_writing_at"] = datetime.now().isoformat()

        # Generate outline and research questions
        try:
            logger.info("📋 Generating outline and identifying research needs...")
            outline_and_questions = await self._generate_outline_and_questions(assignment)
            outline = outline_and_questions.get("outline", "")
            research_questions = outline_and_questions.get("research_questions", [])

            # Publish event: outline generated
            await self._publish_event(
                event_type="outline_generated",
                story_id=story_id,
                data={"question_count": len(research_questions)}
            )

            logger.info(f"✅ Outline generated")
            logger.info(f"   Research questions identified: {len(research_questions)}")

            # Call both Researcher and Archivist in parallel
            research_results = None
            archive_results = None

            if research_questions:
                logger.info("🔍 Calling Researcher and Archivist in parallel...")

                # Publish event: research requested
                await self._publish_event(
                    event_type="research_requested",
                    story_id=story_id,
                    data={"question_count": len(research_questions)}
                )

                # Publish event: archive search started
                await self._publish_event(
                    event_type="archive_search_started",
                    story_id=story_id,
                    data={"topic": assignment.get("topic")}
                )

                # Set waiting status and Archivist status to active
                self.waiting_status[story_id] = "researcher_archivist"
                self.archivist_status[story_id] = "active"
                logger.info(f"🟡 Reporter waiting for Researcher and Archivist (story: {story_id})")

                # Create tasks for parallel execution
                researcher_task = self._send_to_researcher(story_id, assignment, research_questions)
                archivist_task = self._send_to_archivist(story_id, assignment)

                # Execute both in parallel
                research_response, archive_response = await asyncio.gather(
                    researcher_task,
                    archivist_task,
                    return_exceptions=True
                )

                # Process Researcher response
                if isinstance(research_response, Exception):
                    logger.error(f"❌ Researcher failed: {research_response}")
                elif research_response.get("status") == "success":
                    research_results = research_response.get("research_results", [])
                    self.research_data[story_id] = research_results
                    logger.info(f"✅ Received research data: {len(research_results)} answers")
                else:
                    logger.warning(f"⚠️  Research request failed: {research_response.get('message')}")

                # Process Archivist response - REQUIRED, stop workflow if it fails
                if isinstance(archive_response, Exception):
                    logger.error(f"❌ CRITICAL: Archivist failed - this is a REQUIRED component")
                    logger.error(f"   Error: {archive_response}")
                    self.archivist_status[story_id] = "error"
                    raise Exception(f"Archivist failed - this is a REQUIRED component: {archive_response}")
                elif archive_response.get("status") == "success":
                    archive_results = archive_response.get("articles", [])
                    self.archive_data[story_id] = archive_results
                    logger.info(f"✅ Received archive data: {len(archive_results)} historical articles")
                    self.archivist_status[story_id] = "completed"

                    # Publish event: archive search completed
                    await self._publish_event(
                        event_type="archive_search_completed",
                        story_id=story_id,
                        data={"articles_found": len(archive_results)}
                    )
                elif archive_response.get("status") in ["timeout", "error"]:
                    error_msg = f"Archivist {archive_response.get('status')}: {archive_response.get('error', 'Unknown error')}"
                    logger.error(f"❌ CRITICAL: {error_msg} - Archivist is REQUIRED")
                    self.archivist_status[story_id] = "error"
                    raise Exception(f"Archivist {archive_response.get('status')} - this is a REQUIRED component: {archive_response.get('error', 'Unknown error')}")
                elif archive_response.get("status") == "skipped":
                    logger.error(f"❌ CRITICAL: Archivist skipped - this is a REQUIRED component")
                    logger.error(f"   Message: {archive_response.get('message')}")
                    self.archivist_status[story_id] = "error"
                    raise Exception(f"Archivist skipped - this is a REQUIRED component: {archive_response.get('message')}")
                else:
                    error_msg = f"Archivist returned unexpected status: {archive_response.get('status')}"
                    logger.error(f"❌ CRITICAL: {error_msg} - Archivist is REQUIRED")
                    self.archivist_status[story_id] = "error"
                    raise Exception(f"Archivist returned unexpected status: {archive_response.get('status')} - this is a REQUIRED component")
            else:
                logger.info("ℹ️  No research questions needed for this article")

            # Clear waiting status and update to writing
            self.waiting_status[story_id] = "none"
            self.assignments[story_id]["reporter_status"] = "writing"
            logger.info(f"🟢 Reporter finished waiting, now writing (story: {story_id})")

            # Generate article with research and archive data
            logger.info("🤖 Calling Anthropic API to generate article...")
            article_content = await self._generate_article(assignment, outline, research_results, archive_results)
            logger.info(f"✅ Article generated: {len(article_content.split())} words")

            # Store draft
            draft = {
                "story_id": story_id,
                "assignment": assignment,
                "content": article_content,
                "word_count": len(article_content.split()),
                "created_at": datetime.now().isoformat(),
                "status": "draft"
            }
            self.drafts[story_id] = draft

            # Update assignment status
            self.assignments[story_id]["reporter_status"] = "draft_complete"
            self.assignments[story_id]["completed_at"] = datetime.now().isoformat()

            # Extract headline for event
            lines = article_content.strip().split('\n')
            headline = next((line.strip() for line in lines if line.strip() and not line.strip().startswith('#')), "Untitled Article")
            # Strip "HEADLINE:" prefix if present
            if headline.startswith("HEADLINE:"):
                headline = headline[len("HEADLINE:"):].strip()

            # Publish event: article drafted
            await self._publish_event(
                event_type="article_drafted",
                story_id=story_id,
                data={
                    "word_count": draft['word_count'],
                    "target_length": assignment.get('target_length', 1000),
                    "headline": headline[:100]  # Truncate long headlines
                }
            )

            logger.info(f"✅ Draft stored successfully")
            logger.info(f"   Word count: {draft['word_count']}")
            logger.info(f"   Total drafts: {len(self.drafts)}")

            # Submit draft to News Chief for workflow management
            logger.info("📤 Submitting draft to News Chief for workflow management...")
            news_chief_response = await self._submit_draft_to_news_chief(story_id, draft)

            if news_chief_response.get("status") == "success":
                logger.info(f"✅ Draft submitted to News Chief successfully")
                logger.info(f"   News Chief will handle editorial workflow")

                # Extract headline from article content
                lines = article_content.strip().split('\n')
                headline = next((line.strip() for line in lines if line.strip() and not line.strip().startswith('#')), "Untitled Article")
                # Strip "HEADLINE:" prefix if present
                if headline.startswith("HEADLINE:"):
                    headline = headline[len("HEADLINE:"):].strip()

                return {
                    "status": "success",
                    "message": "Article draft completed and submitted to News Chief",
                    "story_id": story_id,
                    "word_count": draft["word_count"],
                    "preview": article_content[:200] + "..." if len(article_content) > 200 else article_content,
                    "news_chief_response": news_chief_response
                }
            else:
                logger.warning(f"⚠️  Failed to submit to News Chief: {news_chief_response.get('message')}")

            # Fallback: return draft completion if News Chief submission failed
            return {
                "status": "success",
                "message": "Article draft completed (News Chief submission failed)",
                "story_id": story_id,
                "word_count": draft["word_count"],
                "preview": article_content[:200] + "..." if len(article_content) > 200 else article_content
            }

        except Exception as e:
            logger.error(f"Error generating article: {e}", exc_info=True)
            self.assignments[story_id]["reporter_status"] = "error"
            return {
                "status": "error",
                "message": f"Failed to generate article: {str(e)}",
                "story_id": story_id
            }

    async def _generate_outline_and_questions(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate article outline and identify research questions"""
        topic = assignment.get("topic", "Unknown Topic")
        angle = assignment.get("angle", "")
        target_length = assignment.get("target_length", 1000)

        prompt = f"""You are a professional journalist for Elastic News planning an article.

Topic: {topic}
Angle: {angle if angle else "General overview"}
Target Length: {target_length} words

Create a brief outline for this article and identify 3-5 research questions that would strengthen the piece with factual data, statistics, or expert insights.

Provide your response in JSON format:
{{
  "outline": "Brief 3-4 point outline of the article structure",
  "research_questions": [
    "What percentage of companies/organizations are adopting this technology?",
    "What are the key statistics or market data related to this topic?",
    "Who are the leading companies or experts in this space?",
    "What recent developments or trends are worth highlighting?"
  ]
}}

Limit to 3-5 focused research questions. Provide only the JSON, no additional text."""

        default_response = {
            "outline": "Introduction, Background, Current State, Future Outlook",
            "research_questions": []
        }

        response_text = await self._call_anthropic(prompt, max_tokens=1500, fallback=lambda: None)
        if response_text:
            try:
                response_text = self._strip_json_codeblocks(response_text)
                return json.loads(response_text)
            except Exception as e:
                logger.error(f"Error parsing outline JSON: {e}", exc_info=True)
                return default_response
        return default_response

    async def _send_to_researcher(self, story_id: str, assignment: Dict[str, Any], questions: List[str]) -> Dict[str, Any]:
        """Send research questions to Researcher agent via A2A"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as http_client:
                # Create A2A client using helper
                researcher_client, _ = await self._create_a2a_client(http_client, self.researcher_url, "Researcher")

                # Send research_questions task to Researcher
                request = {
                    "action": "research_questions",
                    "story_id": story_id,
                    "topic": assignment.get("topic"),
                    "questions": questions
                }
                logger.info(f"📨 Sending A2A message to Researcher:")
                logger.info(f"   Story ID: {story_id}")
                logger.info(f"   Questions: {len(questions)}")

                message = create_text_message_object(content=json.dumps(request))

                # Get response using helper
                logger.info(f"⏳ Waiting for Researcher response...")
                result = await self._parse_a2a_response(researcher_client, message)

                if result:
                    logger.info(f"📬 Received A2A response from Researcher:")
                    logger.info(f"   Status: {result.get('status')}")
                    logger.info(f"   Research ID: {result.get('research_id')}")
                    logger.info(f"   Questions answered: {result.get('total_questions')}")
                    return result

                logger.warning("⚠️  No response from Researcher")
                return {"status": "error", "message": "No response from Researcher"}

        except Exception as e:
            logger.error(f"Failed to send research request to Researcher: {e}", exc_info=True)
            return self._error_response(f"Failed to contact Researcher: {str(e)}")

    async def _send_to_archivist(self, story_id: str, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Search for historical articles via Archivist agent using the archivist_client module"""
        # Check if Archivist is configured
        if not self.archivist_agent_url and not self.archivist_card_url:
            logger.error("❌ Neither ELASTIC_ARCHIVIST_AGENT_URL nor ELASTIC_ARCHIVIST_AGENT_CARD_URL is set - Archivist is REQUIRED")
            raise Exception("Archivist URL not configured - Archivist is REQUIRED for workflow")

        if not self.archivist_api_key:
            logger.error("❌ ELASTIC_ARCHIVIST_API_KEY not set - Archivist is REQUIRED")
            raise Exception("Archivist API key not configured - Archivist is REQUIRED for workflow")

        # Build search query from topic and angle
        topic = assignment.get("topic", "")
        angle = assignment.get("angle", "")
        search_query = f"Find articles about {topic} {angle}".strip()

        logger.info(f"🔍 Calling Archivist via archivist_client module")
        logger.info(f"   Search query: '{search_query}'")

        # Call the archivist client (prefers direct agent URL)
        try:
            result = await call_archivist(
                query=search_query,
                story_id=story_id,
                agent_url=self.archivist_agent_url,  # Direct endpoint (preferred)
                agent_card_url=self.archivist_card_url,  # Fallback to agent card URL
                api_key=self.archivist_api_key,
                max_retries=10
            )
            return result
        except Exception as e:
            logger.error(f"❌ Archivist call failed: {e}")
            raise

    async def _generate_article(self, assignment: Dict[str, Any], outline: str = "", research_results: Optional[List[Dict[str, Any]]] = None, archive_results: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate article content using Anthropic Claude with research data"""
        topic = assignment.get("topic", "Unknown Topic")
        angle = assignment.get("angle", "")
        target_length = assignment.get("target_length", 1000)
        priority = assignment.get("priority", "normal")

        # Build research context
        research_context = ""
        if research_results:
            research_context = "\n\nRESEARCH DATA (integrate this factual information into your article):\n"
            for i, result in enumerate(research_results, 1):
                research_context += f"\nQuestion {i}: {result.get('question')}\n"
                research_context += f"Summary: {result.get('summary', 'N/A')}\n"
                research_context += "Facts:\n"
                for fact in result.get('facts', []):
                    research_context += f"  - {fact}\n"

                figures = result.get('figures', {})
                if any(figures.values()):
                    research_context += "Key Figures:\n"
                    if figures.get('percentages'):
                        research_context += f"  Percentages: {', '.join(figures['percentages'])}\n"
                    if figures.get('dollar_amounts'):
                        research_context += f"  Dollar Amounts: {', '.join(figures['dollar_amounts'])}\n"
                    if figures.get('companies'):
                        research_context += f"  Companies: {', '.join(figures['companies'])}\n"

        # Build archive context
        archive_context = ""
        if archive_results:
            # archive_results could be a list of articles or a text response
            if isinstance(archive_results, list) and len(archive_results) > 0:
                archive_context = "\n\nHISTORICAL COVERAGE (reference for context, avoid repeating these angles):\n"
                for i, article in enumerate(archive_results[:5], 1):  # Limit to 5 articles
                    archive_context += f"\n{i}. {article}\n"
            elif isinstance(archive_results, str):
                archive_context = f"\n\nHISTORICAL COVERAGE:\n{archive_results}\n"

        # Build prompt
        prompt = f"""You are a professional journalist for Elastic News, a technology news publication.

Write a news article with the following specifications:

Topic: {topic}
{f"Angle/Focus: {angle}" if angle else ""}
Target Length: approximately {target_length} words
Priority: {priority}
{f"Outline: {outline}" if outline else ""}
{research_context}
{archive_context}

Write a well-structured news article with:
- A compelling headline
- A clear and engaging introduction (lede paragraph)
- 2-3 body paragraphs with supporting details and context
- Integrate the research data naturally into the article
- Use specific statistics, percentages, and company names from the research
- If historical coverage is provided, reference it for context but take a fresh angle
- A brief conclusion

Style Guidelines:
- Professional and informative tone
- Balanced and objective reporting
- Clear and concise language
- Focus on facts and insights
- Cite data points naturally (e.g., "According to recent industry data, 65% of...")
- Avoid repeating angles from historical coverage - bring a new perspective

Format your response as:
HEADLINE: [Your headline here]

[Article body paragraphs]"""

        # Use Anthropic helper with fallback to mock
        fallback = lambda: self._generate_mock_article(topic, angle, target_length)
        result = await self._call_anthropic(prompt, max_tokens=2000, fallback=fallback)
        return result if result else fallback()

    def _generate_mock_article(self, topic: str, angle: str, target_length: int) -> str:
        """Generate a simple mock article when Anthropic API is not available"""
        return f"""HEADLINE: {topic}: A Comprehensive Analysis

{topic} has emerged as a significant development in recent news. {angle if angle else 'This story examines the key aspects and implications of this important topic.'}

Industry experts and analysts have been closely monitoring these developments, noting the potential impact on various stakeholders. The situation continues to evolve, with new information emerging regularly.

Sources familiar with the matter indicate that multiple factors are contributing to the current state of affairs. Observers suggest that the coming weeks will be crucial in determining the long-term implications.

Further updates will be provided as more information becomes available. Stakeholders are advised to monitor the situation closely and stay informed through reliable news sources.

[Article generated with mock content - ANTHROPIC_API_KEY not configured]
[Target length: {target_length} words]"""

    async def _submit_draft_to_news_chief(self, story_id: str, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Submit draft to News Chief for workflow management"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as http_client:
                # Create A2A client using helper
                news_chief_url = "http://localhost:8080"
                news_chief_client, _ = await self._create_a2a_client(http_client, news_chief_url, "News Chief")

                # Send draft submission request
                submit_request = {
                    "action": "submit_draft",
                    "story_id": story_id,
                    "draft": draft
                }
                logger.info(f"📨 Sending draft submission to News Chief:")
                logger.info(f"   Story ID: {story_id}")
                logger.info(f"   Word Count: {draft.get('word_count')}")
                logger.info(f"   Reporter assignments: {list(self.assignments.keys())}")

                message = create_text_message_object(content=json.dumps(submit_request))

                # Get response using helper
                logger.info(f"⏳ Waiting for News Chief response...")
                result = await self._parse_a2a_response(news_chief_client, message)

                if result:
                    logger.info(f"📬 Received response from News Chief:")
                    logger.info(f"   Status: {result.get('status')}")
                    logger.info(f"   Message: {result.get('message')}")
                    return result

                return self._error_response("No response from News Chief")

        except Exception as e:
            logger.error(f"Failed to submit draft to News Chief: {e}", exc_info=True)
            return self._error_response(f"Failed to contact News Chief: {str(e)}")

    async def _apply_edits(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Apply editorial suggestions to a draft using Anthropic"""
        logger.info("✏️  Applying editorial suggestions...")
        story_id = request.get("story_id")
        editor_review = request.get("editor_review", {})

        if not story_id:
            return self._error_response("No story_id provided")

        if story_id not in self.drafts:
            return self._error_response(f"No draft found for story_id: {story_id}")

        if not editor_review:
            return self._error_response(f"No editor review provided for story_id: {story_id}")

        draft = self.drafts[story_id]
        review = editor_review

        logger.info(f"📝 Applying edits for: {draft.get('assignment', {}).get('topic')}")
        logger.info(f"   Approval status: {review.get('approval_status')}")
        logger.info(f"   Suggested edits: {len(review.get('suggested_edits', []))}")

        # Apply edits using Anthropic
        try:
            logger.info("🤖 Calling Anthropic API to integrate edits...")
            revised_content = await self._integrate_edits(draft.get('content'), review)
            logger.info(f"✅ Edits applied: {len(revised_content.split())} words")

            # Update the draft
            old_word_count = draft.get("word_count")
            draft["content"] = revised_content
            draft["word_count"] = len(revised_content.split())
            draft["status"] = "revised"
            draft["revised_at"] = datetime.now().isoformat()
            draft["revisions_applied"] = len(review.get('suggested_edits', []))

            # Update assignment status
            if story_id in self.assignments:
                self.assignments[story_id]["reporter_status"] = "revised"

            # Publish event: edits applied
            await self._publish_event(
                event_type="edits_applied",
                story_id=story_id,
                data={
                    "old_word_count": old_word_count,
                    "new_word_count": draft["word_count"],
                    "revisions_applied": draft["revisions_applied"],
                    "approval_status": review.get("approval_status")
                }
            )

            logger.info(f"✅ Draft updated successfully")
            logger.info(f"   Word count: {old_word_count} → {draft['word_count']}")

            # Submit revised draft back to News Chief for workflow management
            logger.info("📤 Submitting revised draft to News Chief...")
            news_chief_response = await self._submit_draft_to_news_chief(story_id, draft)

            response = {
                "status": "success",
                "message": "Editorial suggestions applied successfully",
                "story_id": story_id,
                "old_word_count": old_word_count,
                "new_word_count": draft["word_count"],
                "revisions_applied": draft["revisions_applied"],
                "preview": revised_content[:200] + "..." if len(revised_content) > 200 else revised_content
            }

            # Include News Chief response
            if news_chief_response.get("status") == "success":
                response["news_chief_response"] = news_chief_response
                logger.info(f"✅ Revised draft submitted to News Chief successfully")
            else:
                response["news_chief_error"] = news_chief_response.get("message")
                logger.warning(f"⚠️  News Chief submission failed: {news_chief_response.get('message')}")

            return response

        except Exception as e:
            logger.error(f"❌ Error applying edits: {e}", exc_info=True)
            return self._error_response(f"Failed to apply edits: {str(e)}", story_id=story_id)

    async def _integrate_edits(self, original_content: str, review: Dict[str, Any]) -> str:
        """Integrate editorial suggestions into the article using Anthropic"""
        suggested_edits = review.get("suggested_edits", [])
        overall_assessment = review.get("overall_assessment", "")
        editor_notes = review.get("editor_notes", "")

        # Build prompt for applying edits
        prompt = f"""You are a reporter for Elastic News revising your article based on editorial feedback.

ORIGINAL ARTICLE:
{original_content}

EDITORIAL REVIEW:
{overall_assessment}

SUGGESTED EDITS:
{json.dumps(suggested_edits, indent=2)}

EDITOR'S NOTES:
{editor_notes}

Please revise the article by applying ALL the suggested edits. Make sure to:
1. Fix all grammar, spelling, and punctuation issues
2. Adjust tone where needed to maintain professionalism
3. Ensure consistency in terminology and style
4. Adjust length if needed to meet target requirements

Provide ONLY the revised article text, maintaining the same format (headline followed by body). Do not include any explanations or notes."""

        # Use Anthropic helper with fallback to simple edits
        fallback = lambda: self._apply_simple_edits(original_content, suggested_edits)
        result = await self._call_anthropic(prompt, max_tokens=3000, fallback=fallback)
        return result if result else fallback()

    def _apply_simple_edits(self, content: str, suggested_edits: List[Dict[str, Any]]) -> str:
        """Apply simple text replacements when Anthropic is not available"""
        revised = content
        for edit in suggested_edits:
            original = edit.get("original", "")
            suggested = edit.get("suggested", "")
            if original and suggested and original in revised:
                revised = revised.replace(original, suggested)
        return revised

    async def _get_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get current status of all assignments"""
        story_id = request.get("story_id")

        if story_id:
            # Return specific story status
            if story_id not in self.assignments:
                return {
                    "status": "error",
                    "message": f"No assignment found for story_id: {story_id}"
                }

            assignment = self.assignments[story_id]
            draft_info = self.drafts.get(story_id, {})
            review_info = self.editor_reviews.get(story_id, {})

            return {
                "status": "success",
                "story_id": story_id,
                "assignment": assignment,
                "draft": draft_info if draft_info else None,
                "editor_review": review_info if review_info else None,
                "archivist_status": self.archivist_status.get(story_id, "idle"),
            "waiting_status": self.waiting_status.get(story_id, "none")
            }
        else:
            # Return all assignments
            return {
                "status": "success",
                "total_assignments": len(self.assignments),
                "total_drafts": len(self.drafts),
                "total_reviews": len(self.editor_reviews),
                "assignments": list(self.assignments.values()),
                "drafts": list(self.drafts.values()),
                "reviews": list(self.editor_reviews.values()),
                "waiting_status": self.waiting_status,
                "archivist_status": self.archivist_status
            }


def get_reporter_agent() -> ReporterAgent:
    """Get singleton ReporterAgent instance to maintain state across requests"""
    global _reporter_agent_instance
    if _reporter_agent_instance is None:
        _reporter_agent_instance = ReporterAgent()
    return _reporter_agent_instance


class ReporterAgentExecutor(AgentExecutor):
    """AgentExecutor for the Reporter agent following official A2A pattern"""

    def __init__(self):
        # Use singleton instance to maintain state across requests
        self.agent = get_reporter_agent()

    async def execute(self, context, event_queue) -> None:
        """Execute the agent request"""
        logger.info('Executing Reporter agent')

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
    """Create the Reporter agent card"""
    return AgentCard(
        name="Reporter",
        description="Writes news articles based on story assignments and submits drafts to News Chief for workflow management",
        url=f"http://{host}:{port}",
        version="1.0.0",
        protocol_version="0.3.0",  # A2A Protocol version
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/reporter-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,  # Not implemented yet
            state_transition_history=True,
            max_concurrent_tasks=10
        ),
        skills=[
            AgentSkill(
                id="article.writing.accept_assignment",
                name="Accept Story Assignment",
                description="Accepts story assignments from the News Chief and prepares to write",
                tags=["writing", "assignment"],
                examples=[
                    '{"action": "accept_assignment", "assignment": {"story_id": "story_123", "topic": "AI in Journalism", "target_length": 1000}}',
                    "Accept assignment for climate change story"
                ]
            ),
            AgentSkill(
                id="article.writing.write_article",
                name="Write Article",
                description="Generates article content using AI based on the assignment specifications",
                tags=["writing", "ai-generation"],
                examples=[
                    '{"action": "write_article", "story_id": "story_123"}',
                    "Write article for assigned story"
                ]
            ),
            AgentSkill(
                id="article.writing.apply_edits",
                name="Apply Editorial Suggestions",
                description="Applies editorial feedback from News Chief and submits revised draft back to News Chief",
                tags=["editing", "revision", "ai-integration"],
                examples=[
                    '{"action": "apply_edits", "story_id": "story_123"}',
                    "Apply editor's suggestions to article"
                ]
            ),
            AgentSkill(
                id="article.writing.status",
                name="Get Status",
                description="Returns current status of assigned stories, drafts, and editor reviews",
                tags=["status", "reporting"],
                examples=[
                    '{"action": "get_status"}',
                    '{"action": "get_status", "story_id": "story_123"}'
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


def create_app(host='localhost', port=8081):
    """Factory function to create the A2A application"""
    # Create agent card using the single source of truth
    agent_card = create_agent_card(host, port)

    # Set up the request handler
    request_handler = DefaultRequestHandler(
        agent_executor=ReporterAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create the A2A application
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
@click.option('--port', 'port', default=8081)
@click.option('--reload', 'reload', is_flag=True, default=False, help='Enable hot reload on file changes')
def main(host, port, reload):
    """Starts the Reporter Agent server."""
    run_agent_server(
        agent_name="Reporter",
        host=host,
        port=port,
        create_app_func=lambda: create_app(host, port),
        logger=logger,
        reload=reload,
        reload_module="agents.reporter:app" if reload else None
    )


if __name__ == "__main__":
    main()

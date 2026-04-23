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
from utils import setup_logger, load_env_config, run_agent_server, format_json_for_log, truncate_text
from agents.base_agent import BaseAgent
from agents.archivist_client import converse, send_task

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

        # Initialize MCP client for tool calling
        self._init_mcp_client()

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
                logger.debug("Received query: %s", format_json_for_log(query))

            # Parse the query to determine the action
            query_data = json.loads(query) if query.startswith('{') else {"action": "status"}
            action = query_data.get("action")

            # Only log non-status actions to reduce log spam
            if action != "get_status":
                logger.info("Action: %s", action)

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
            logger.error("Error processing request: %s", e, exc_info=True)
            return {
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }

    async def _accept_assignment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Accept a story assignment from News Chief"""
        logger.info("Processing assignment from News Chief...")
        assignment = request.get("assignment", {})

        # Validate assignment
        if not assignment:
            return self._error_response("No assignment data provided")

        story_id = assignment.get("story_id")
        if not story_id:
            return self._error_response("Assignment missing story_id")

        logger.info("Assignment accepted: story=%s topic=%s length=%s priority=%s", story_id, assignment.get('topic'), assignment.get('target_length'), assignment.get('priority'))

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

        logger.info("Assignment stored successfully: total=%s", len(self.assignments))

        return self._success_response(
            f"Assignment accepted for story: {assignment.get('topic', story_id)}",
            story_id=story_id,
            estimated_completion="30 minutes",
            reporter_status="ready_to_write"
        )

    async def _write_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Write an article using Anthropic Claude with Researcher support"""
        logger.info("Starting article writing...")
        story_id = request.get("story_id")

        if not story_id:
            return self._error_response("No story_id provided")

        if story_id not in self.assignments:
            return self._error_response(f"No assignment found for story_id: {story_id}")

        assignment = self.assignments[story_id]
        logger.info("Writing article for: %s", assignment.get('topic'))

        # Update status
        self.assignments[story_id]["reporter_status"] = "researching"
        self.assignments[story_id]["started_writing_at"] = datetime.now().isoformat()

        # Generate outline and research questions
        try:
            logger.info("Generating outline and identifying research needs...")
            outline_and_questions = await self._generate_outline_and_questions(assignment)
            outline = outline_and_questions.get("outline", "")
            research_questions = outline_and_questions.get("research_questions", [])

            # Publish event: outline generated
            await self._publish_event(
                event_type="outline_generated",
                story_id=story_id,
                data={"question_count": len(research_questions)}
            )

            logger.info("Outline generated: questions=%s", len(research_questions))

            # Call both Researcher and Archivist in parallel
            research_results = None
            archive_results = None

            if research_questions:
                logger.info("Calling Researcher and Archivist in parallel...")

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
                logger.debug("Reporter waiting for Researcher and Archivist: story=%s", story_id)

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
                    logger.error("Researcher failed: %s", research_response)
                elif research_response.get("status") == "success":
                    research_results = research_response.get("research_results", [])
                    self.research_data[story_id] = {
                        "questions": research_questions,
                        "results": research_results
                    }
                    logger.debug("Received research data: answers=%s", len(research_results))
                else:
                    logger.warning("Research request failed: %s", research_response.get('message'))

                # Process Archivist response - REQUIRED, stop workflow if it fails
                if isinstance(archive_response, Exception):
                    error_msg = (
                        f"Workflow error: Archivist failed with exception. "
                        f"The Archivist is required for the Reporter workflow. "
                        f"Error: {archive_response}"
                    )
                    logger.error("CRITICAL: %s", error_msg)
                    self.archivist_status[story_id] = "error"
                    raise Exception(error_msg)
                elif archive_response.get("status") == "success":
                    archive_results = archive_response.get("articles", [])
                    self.archive_data[story_id] = {
                        "results": archive_results
                    }
                    logger.info("Archive search completed: articles=%s", len(archive_results))
                    self.archivist_status[story_id] = "completed"

                    # Publish event: archive search completed
                    await self._publish_event(
                        event_type="archive_search_completed",
                        story_id=story_id,
                        data={"articles_found": len(archive_results)}
                    )
                elif archive_response.get("status") in ["timeout", "error"]:
                    status = archive_response.get('status')
                    error_detail = archive_response.get('error', 'Unknown error')
                    error_msg = (
                        f"Workflow error: Archivist {status} - {error_detail}. "
                        f"The Archivist is required for the Reporter workflow to search historical articles."
                    )
                    logger.error("CRITICAL: %s", error_msg)
                    self.archivist_status[story_id] = "error"
                    raise Exception(error_msg)
                elif archive_response.get("status") == "skipped":
                    skip_message = archive_response.get('message', 'No reason provided')
                    error_msg = (
                        f"Workflow error: Archivist was skipped - {skip_message}. "
                        f"The Archivist is required for the Reporter workflow to search historical articles."
                    )
                    logger.error("CRITICAL: %s", error_msg)
                    self.archivist_status[story_id] = "error"
                    raise Exception(error_msg)
                else:
                    unexpected_status = archive_response.get('status', 'unknown')
                    error_msg = (
                        f"Workflow error: Archivist returned unexpected status '{unexpected_status}'. "
                        f"The Archivist is required for the Reporter workflow to search historical articles."
                    )
                    logger.error("CRITICAL: %s", error_msg)
                    self.archivist_status[story_id] = "error"
                    raise Exception(error_msg)
            else:
                logger.debug("No research questions needed for this article")

            # Clear waiting status and update to writing
            self.waiting_status[story_id] = "none"
            self.assignments[story_id]["reporter_status"] = "writing"
            logger.debug("Reporter finished waiting, now writing: story=%s", story_id)

            # Generate article with research and archive data
            logger.info("Generating article...")
            article_content = await self._generate_article(assignment, outline, research_results, archive_results)
            logger.info("Article generated: words=%s", len(article_content.split()))

            # Extract headline from article content
            lines = article_content.strip().split('\n')
            import re as _re
            # Priority 1: "HEADLINE: ..." prefix
            headline_line = next((l.strip() for l in lines if l.strip().startswith('HEADLINE:')), None)
            if headline_line:
                headline = headline_line.replace('HEADLINE:', '').strip()
            else:
                # Priority 2: First markdown heading (# or ##)
                heading_line = next((l.strip() for l in lines if _re.match(r'^#{1,2}\s+.+', l.strip())), None)
                if heading_line:
                    headline = _re.sub(r'^#+\s+', '', heading_line)
                else:
                    # Priority 3: First non-empty line
                    headline = next((l.strip() for l in lines if l.strip()), "Untitled Article")

            # Store draft
            draft = {
                "story_id": story_id,
                "assignment": assignment,
                "headline": headline,
                "content": article_content,
                "word_count": len(article_content.split()),
                "created_at": datetime.now().isoformat(),
                "status": "draft"
            }
            self.drafts[story_id] = draft

            # Update assignment status
            self.assignments[story_id]["reporter_status"] = "draft_complete"
            self.assignments[story_id]["completed_at"] = datetime.now().isoformat()

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

            logger.info("Draft stored: words=%s total=%s", draft['word_count'], len(self.drafts))

            # Submit draft to News Chief for workflow management
            logger.info("Submitting draft to News Chief for workflow management...")
            news_chief_response = await self._submit_draft_to_news_chief(story_id, draft)

            if news_chief_response.get("status") == "success":
                logger.info("Draft submitted to News Chief successfully")

                # Extract headline from article content
                lines = article_content.strip().split('\n')
                # Priority 1: "HEADLINE: ..." prefix
                headline_line = next((l.strip() for l in lines if l.strip().startswith('HEADLINE:')), None)
                if headline_line:
                    headline = headline_line.replace('HEADLINE:', '').strip()
                else:
                    # Priority 2: First markdown heading (# or ##)
                    heading_line = next((l.strip() for l in lines if _re.match(r'^#{1,2}\s+.+', l.strip())), None)
                    if heading_line:
                        headline = _re.sub(r'^#+\s+', '', heading_line)
                    else:
                        # Priority 3: First non-empty line
                        headline = next((l.strip() for l in lines if l.strip()), "Untitled Article")

                return {
                    "status": "success",
                    "message": "Article draft completed and submitted to News Chief",
                    "story_id": story_id,
                    "word_count": draft["word_count"],
                    "preview": article_content[:200] + "..." if len(article_content) > 200 else article_content,
                    "news_chief_response": news_chief_response
                }
            else:
                logger.warning("Failed to submit to News Chief: %s", news_chief_response.get('message'))

            # Fallback: return draft completion if News Chief submission failed
            return {
                "status": "success",
                "message": "Article draft completed (News Chief submission failed)",
                "story_id": story_id,
                "word_count": draft["word_count"],
                "preview": article_content[:200] + "..." if len(article_content) > 200 else article_content
            }

        except Exception as e:
            logger.error("Error generating article: %s", e, exc_info=True)
            self.assignments[story_id]["reporter_status"] = "error"
            return {
                "status": "error",
                "message": f"Failed to generate article: {str(e)}",
                "story_id": story_id
            }

    async def _generate_outline_and_questions(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate article outline and identify research questions using MCP generate_outline tool"""
        topic = assignment.get("topic", "Unknown Topic")
        angle = assignment.get("angle", "")
        target_length = assignment.get("target_length", 1000)

        try:
            logger.debug("Calling MCP generate_outline tool...")

            # Direct call to MCP tool (bypass LLM selection for efficiency and reliability)
            if self.mcp_client is None:
                self._init_mcp_client()

            result = await self.mcp_client.call_tool(
                tool_name="generate_outline",
                arguments={
                    "topic": topic,
                    "angle": angle,
                    "target_length": target_length
                }
            )

            # Parse the JSON response
            outline_data = json.loads(result) if isinstance(result, str) else result
            logger.debug("Outline generated: questions=%s", len(outline_data.get('research_questions', [])))
            return outline_data

        except Exception as e:
            logger.error("MCP generate_outline tool failed: %s", e, exc_info=True)
            # MCP server is REQUIRED - re-raise with clear message
            raise

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
                logger.debug("Sending A2A message to Researcher: story=%s questions=%s", story_id, len(questions))

                message = create_text_message_object(content=json.dumps(request))

                # Get response using helper
                logger.debug("Waiting for Researcher response...")
                result = await self._parse_a2a_response(researcher_client, message)

                if result:
                    logger.debug("Received A2A response from Researcher: status=%s research_id=%s answered=%s", result.get('status'), result.get('research_id'), result.get('total_questions'))
                    return result

                logger.warning("No response from Researcher")
                return {"status": "error", "message": "No response from Researcher"}

        except Exception as e:
            logger.error("Failed to send research request to Researcher: %s", e, exc_info=True)
            return self._error_response(f"Failed to contact Researcher: {str(e)}")

    async def _send_to_archivist(self, story_id: str, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for historical articles via Archivist agent using the archivist_client module.

        Raises:
            Exception: If Archivist configuration is missing (URL or API key)
        """
        # Validate Archivist configuration (required for workflow)
        if not self.archivist_agent_url and not self.archivist_card_url:
            error_msg = (
                "Configuration error: Archivist URL not configured. "
                "Set ELASTIC_ARCHIVIST_AGENT_URL or ELASTIC_ARCHIVIST_AGENT_CARD_URL environment variable. "
                "The Archivist is required for the Reporter workflow to search historical articles."
            )
            logger.error("Configuration error: %s", error_msg)
            raise Exception(error_msg)

        if not self.archivist_api_key:
            error_msg = (
                "Configuration error: Archivist API key not configured. "
                "Set ELASTIC_ARCHIVIST_API_KEY environment variable. "
                "The Archivist is required for the Reporter workflow to search historical articles."
            )
            logger.error("Configuration error: %s", error_msg)
            raise Exception(error_msg)

        # Build search query from topic and angle
        topic = assignment.get("topic", "")
        angle = assignment.get("angle", "")
        search_query = f"Find articles about {topic} {angle}".strip()

        archivist_source = "ELASTIC_ARCHIVIST_AGENT_URL" if self.archivist_agent_url else "ELASTIC_ARCHIVIST_AGENT_CARD_URL"
        logger.debug("Calling Archivist via archivist_client module: query=%s, url_source=%s", search_query, archivist_source)

        # Call the archivist client using converse() endpoint (simpler, recommended)
        # Alternative: use send_task() for A2A JSONRPC protocol
        # Passes both URLs; converse() prefers agent_url, falls back to card_url
        try:
            result = await converse(
                query=search_query,
                story_id=story_id,
                agent_url=self.archivist_agent_url,
                card_url=self.archivist_card_url,
                api_key=self.archivist_api_key,
                max_retries=10
            )
            return result
        except Exception as e:
            logger.error("Archivist call failed: %s", e)
            raise

    async def _generate_article(self, assignment: Dict[str, Any], outline: str = "", research_results: Optional[List[Dict[str, Any]]] = None, archive_results: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate article content using MCP generate_article tool"""
        topic = assignment.get("topic", "Unknown Topic")
        angle = assignment.get("angle", "")
        target_length = assignment.get("target_length", 1000)

        # Convert research results to string for MCP tool
        research_data = json.dumps(research_results) if research_results else ""

        # Convert archive results to string for MCP tool
        archive_context = ""
        if archive_results:
            if isinstance(archive_results, list) and len(archive_results) > 0:
                archive_context = "\n".join([f"{i}. {article}" for i, article in enumerate(archive_results[:5], 1)])
            elif isinstance(archive_results, str):
                archive_context = archive_results

        try:
            logger.debug("Calling MCP generate_article tool...")

            # Direct call to MCP tool (bypass LLM selection for efficiency and reliability)
            if self.mcp_client is None:
                self._init_mcp_client()

            result = await self.mcp_client.call_tool(
                tool_name="generate_article",
                arguments={
                    "topic": topic,
                    "angle": angle,
                    "target_length": target_length,
                    "outline": outline,
                    "research_data": research_data,
                    "archive_context": archive_context
                }
            )

            logger.debug("Article generated: words=%s", len(str(result).split()))
            return result

        except Exception as e:
            logger.error("MCP generate_article tool failed: %s", e, exc_info=True)
            # MCP server is required - re-raise the exception
            raise Exception(f"MCP generate_article tool failed: {e}")

    def _extract_research_sources(self, story_id: str) -> List[Dict[str, str]]:
        """Extract unique source URLs from research results for article attribution."""
        sources = []
        seen_urls = set()
        research_results = self.research_data.get(story_id, {}).get("results", [])

        for result in research_results:
            result_sources = result.get("sources", [])
            for source in result_sources:
                # Handle both dict sources (Tavily) and string sources (legacy)
                if isinstance(source, dict):
                    url = source.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        sources.append({
                            "title": source.get("title", ""),
                            "url": url,
                            "published_date": source.get("published_date", "")
                        })
                elif isinstance(source, str) and source.startswith("http"):
                    if source not in seen_urls:
                        seen_urls.add(source)
                        sources.append({"title": source, "url": source, "published_date": ""})

        return sources

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
                logger.debug("Sending draft submission to News Chief: story=%s words=%s assignments=%s", story_id, draft.get('word_count'), list(self.assignments.keys()))

                message = create_text_message_object(content=json.dumps(submit_request))

                # Get response using helper
                logger.debug("Waiting for News Chief response...")
                result = await self._parse_a2a_response(news_chief_client, message)

                if result:
                    logger.debug("Received response from News Chief: status=%s message=%s", result.get('status'), result.get('message'))
                    return result

                return self._error_response("No response from News Chief")

        except Exception as e:
            logger.error("Failed to submit draft to News Chief: %s", e, exc_info=True)
            return self._error_response(f"Failed to contact News Chief: {str(e)}")

    async def _apply_edits(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Apply editorial suggestions to a draft using Anthropic"""
        logger.info("Applying editorial suggestions...")
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

        logger.info("Applying edits: topic=%s approval=%s edits=%s", draft.get('assignment', {}).get('topic'), review.get('approval_status'), len(review.get('suggested_edits', [])))

        # Apply edits using Anthropic
        try:
            logger.info("Integrating edits...")
            revised_content = await self._integrate_edits(draft.get('content'), review)
            logger.info("Edits applied: words=%s", len(revised_content.split()))

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

            logger.info("Draft updated: words=%s→%s", old_word_count, draft['word_count'])

            # Send finalized article to Publisher (Step 17 in workflow)
            logger.info("Sending article to Publisher...")
            publisher_response = await self._send_to_publisher(story_id, draft)

            response = {
                "status": "success",
                "message": "Editorial suggestions applied and article published",
                "story_id": story_id,
                "old_word_count": old_word_count,
                "new_word_count": draft["word_count"],
                "revisions_applied": draft["revisions_applied"],
                "preview": revised_content[:200] + "..." if len(revised_content) > 200 else revised_content
            }

            # Include Publisher response
            if publisher_response.get("status") == "success":
                response["publisher_response"] = publisher_response
                logger.info("Article published successfully")
            else:
                response["publisher_error"] = publisher_response.get("message")
                logger.warning("Publishing failed: %s", publisher_response.get('message'))

            return response

        except Exception as e:
            logger.error("Error applying edits: %s", e, exc_info=True)
            return self._error_response(f"Failed to apply edits: {str(e)}", story_id=story_id)

    async def _send_to_publisher(self, story_id: str, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Send finalized article to Publisher for indexing and storage"""
        try:
            logger.info("Preparing article for publication...")

            assignment = draft.get("assignment", {})

            # Build article data for Publisher
            article_data = {
                "story_id": story_id,
                "headline": draft.get("headline", assignment.get("topic")),
                "content": draft.get("content"),
                "topic": assignment.get("topic"),
                "angle": assignment.get("angle"),
                "word_count": draft.get("word_count"),
                "target_length": assignment.get("target_length"),
                "priority": assignment.get("priority", "normal"),
                "created_at": assignment.get("created_at"),
                "published_at": datetime.now().isoformat(),
                "author": "Reporter Agent",
                "editor": "Editor Agent",
                "research_questions": self.research_data.get(story_id, {}).get("questions", []),
                "research_data": self.research_data.get(story_id, {}).get("results", []),
                "research_sources": self._extract_research_sources(story_id),
                "editorial_review": self.editor_reviews.get(story_id),
                "archive_references": self.archive_data.get(story_id, {}).get("results", []),
                "version": 1,
                "revisions_count": draft.get("revisions_applied", 0),
                "agents_involved": ["News Chief", "Reporter", "Researcher", "Archivist", "Editor", "Publisher"]
            }

            async with httpx.AsyncClient(timeout=120.0) as http_client:
                # Create A2A client for Publisher
                publisher_client, _ = await self._create_a2a_client(
                    http_client,
                    self.publisher_url,
                    "Publisher"
                )

                # Send publish request
                request = {
                    "action": "publish_article",
                    "article": article_data
                }

                message = create_text_message_object(content=json.dumps(request))
                logger.debug("Sending article to Publisher...")

                result = await self._parse_a2a_response(publisher_client, message)

                if result:
                    logger.debug("Publisher response received: status=%s", result.get('status'))
                    return result

                return self._error_response("No response from Publisher")

        except Exception as e:
            logger.error("Failed to send to Publisher: %s", e, exc_info=True)
            return self._error_response(f"Failed to contact Publisher: {str(e)}")

    async def _integrate_edits(self, original_content: str, review: Dict[str, Any]) -> str:
        """Integrate editorial suggestions into the article using MCP apply_edits tool"""
        suggested_edits = review.get("suggested_edits", [])

        try:
            logger.debug("Calling MCP apply_edits tool...")

            # Direct call to MCP tool (bypass LLM selection for efficiency and reliability)
            if self.mcp_client is None:
                self._init_mcp_client()

            result = await self.mcp_client.call_tool(
                tool_name="apply_edits",
                arguments={
                    "original_content": original_content,
                    "suggested_edits": json.dumps(suggested_edits)
                }
            )

            logger.debug("Edits applied: words=%s", len(str(result).split()))
            return result

        except Exception as e:
            logger.error("MCP apply_edits tool failed: %s", e, exc_info=True)
            # MCP server is required - re-raise the exception
            raise Exception(f"MCP apply_edits tool failed: {e}")

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

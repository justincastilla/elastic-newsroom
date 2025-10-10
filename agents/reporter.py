"""
Reporter Agent

Writes news articles based on story assignments from the News Chief.
Uses Anthropic Claude for AI-powered content generation.
"""

import json
import logging
import os
import asyncio
from typing import Dict, Any, Optional, List
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
from utils import setup_logger, load_env_config, init_anthropic_client, run_agent_server

# Load environment variables
load_env_config()

# Configure logging using centralized utility
logger = setup_logger("REPORTER")


class ReporterAgent:
    """Reporter Agent - Writes news articles based on assignments"""

    def __init__(self, editor_url: Optional[str] = None, researcher_url: Optional[str] = None, archivist_url: Optional[str] = None, publisher_url: Optional[str] = None):
        self.assignments: Dict[str, Dict[str, Any]] = {}
        self.drafts: Dict[str, Dict[str, Any]] = {}
        self.editor_reviews: Dict[str, Dict[str, Any]] = {}
        self.research_data: Dict[str, Dict[str, Any]] = {}
        self.archive_data: Dict[str, Dict[str, Any]] = {}
        self.editor_url = editor_url or "http://localhost:8082"
        self.researcher_url = researcher_url or "http://localhost:8083"
        self.publisher_url = publisher_url or "http://localhost:8084"
        # Get Archivist URL from environment or parameter
        self.archivist_url = archivist_url or os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL")
        self.archivist_api_key = os.getenv("ELASTIC_ARCHIVIST_API_KEY")
        
        # Initialize Anthropic client using centralized utility
        self.anthropic_client = init_anthropic_client(logger)
        if not self.anthropic_client:
            logger.warning("Will use mock article generation")

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

            if action == "accept_assignment":
                return await self._accept_assignment(query_data)
            elif action == "write_article":
                return await self._write_article(query_data)
            elif action == "submit_draft":
                return await self._submit_draft(query_data)
            elif action == "apply_edits":
                return await self._apply_edits(query_data)
            elif action == "publish_article":
                return await self._publish_article(query_data)
            elif action == "get_status":
                return await self._get_status(query_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": ["accept_assignment", "write_article", "submit_draft", "apply_edits", "publish_article", "get_status"]
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
            logger.error("❌ No assignment data provided")
            return {
                "status": "error",
                "message": "No assignment data provided"
            }

        story_id = assignment.get("story_id")
        if not story_id:
            logger.error("❌ Assignment missing story_id")
            return {
                "status": "error",
                "message": "Assignment missing story_id"
            }

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

        logger.info(f"✅ Assignment accepted and stored")
        logger.info(f"   Total assignments: {len(self.assignments)}")

        return {
            "status": "success",
            "message": f"Assignment accepted for story: {assignment.get('topic', story_id)}",
            "story_id": story_id,
            "estimated_completion": "30 minutes",  # Mock estimate
            "reporter_status": "ready_to_write"
        }

    async def _write_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Write an article using Anthropic Claude with Researcher support"""
        logger.info("✍️  Starting article writing...")
        story_id = request.get("story_id")

        if not story_id:
            logger.error("❌ No story_id provided")
            return {
                "status": "error",
                "message": "No story_id provided"
            }

        if story_id not in self.assignments:
            logger.error(f"❌ No assignment found for story_id: {story_id}")
            return {
                "status": "error",
                "message": f"No assignment found for story_id: {story_id}"
            }

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

            logger.info(f"✅ Outline generated")
            logger.info(f"   Research questions identified: {len(research_questions)}")

            # Call both Researcher and Archivist in parallel
            import asyncio
            research_results = None
            archive_results = None

            if research_questions:
                logger.info("🔍 Calling Researcher and Archivist in parallel...")

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

                # Process Archivist response - it's REQUIRED, so fail if it errors
                if isinstance(archive_response, Exception):
                    logger.error(f"❌ CRITICAL: Archivist failed - this is a required component")
                    raise archive_response
                elif archive_response.get("status") == "success":
                    archive_results = archive_response.get("articles", [])
                    self.archive_data[story_id] = archive_results
                    logger.info(f"✅ Received archive data: {len(archive_results)} historical articles")
                else:
                    error_msg = f"Archivist request failed: {archive_response.get('message')}"
                    logger.error(f"❌ CRITICAL: {error_msg}")
                    raise Exception(error_msg)
            else:
                logger.info("ℹ️  No research questions needed for this article")

            # Update status to writing
            self.assignments[story_id]["reporter_status"] = "writing"

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

            logger.info(f"✅ Draft stored successfully")
            logger.info(f"   Word count: {draft['word_count']}")
            logger.info(f"   Total drafts: {len(self.drafts)}")

            # Automatically continue workflow: submit to Editor
            logger.info("📤 Automatically submitting draft to Editor...")
            editor_response = await self._send_to_editor(draft)

            if editor_response.get("status") == "success":
                logger.info(f"✅ Editor review received")

                # Apply edits (which will also publish)
                logger.info("✏️  Applying editorial suggestions...")
                edit_response = await self._apply_edits({"story_id": story_id})

                if edit_response.get("status") == "success":
                    logger.info(f"✅ Full workflow completed - article published!")

                    # Extract headline from article content
                    lines = article_content.strip().split('\n')
                    headline = next((line.strip() for line in lines if line.strip() and not line.strip().startswith('#')), "Untitled Article")

                    return {
                        "status": "success",
                        "message": "Article completed and published",
                        "story_id": story_id,
                        "word_count": draft["word_count"],
                        "preview": article_content[:200] + "..." if len(article_content) > 200 else article_content,
                        "published": True,
                        "publisher_response": edit_response.get("publisher_response"),
                        "article_data": {
                            "headline": headline,
                            "content": article_content,
                            "word_count": draft["word_count"]
                        }
                    }
                else:
                    logger.warning(f"⚠️  Failed to apply edits: {edit_response.get('message')}")
            else:
                logger.warning(f"⚠️  Editor review failed: {editor_response.get('message')}")

            # Fallback: return draft completion if workflow didn't complete
            return {
                "status": "success",
                "message": "Article draft completed",
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

        if self.anthropic_client:
            try:
                message = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = message.content[0].text
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                return json.loads(response_text)
            except Exception as e:
                logger.error(f"Error generating outline: {e}", exc_info=True)
                return {
                    "outline": "Introduction, Background, Current State, Future Outlook",
                    "research_questions": []
                }
        else:
            return {
                "outline": "Introduction, Background, Current State, Future Outlook",
                "research_questions": []
            }

    async def _send_to_researcher(self, story_id: str, assignment: Dict[str, Any], questions: List[str]) -> Dict[str, Any]:
        """Send research questions to Researcher agent via A2A"""
        try:
            async with httpx.AsyncClient(timeout=90.0) as http_client:
                # Discover Researcher agent
                logger.info(f"🔍 Discovering Researcher agent at {self.researcher_url}")
                card_resolver = A2ACardResolver(http_client, self.researcher_url)
                researcher_card = await card_resolver.get_agent_card()
                logger.info(f"✅ Found Researcher: {researcher_card.name} (v{researcher_card.version})")

                # Create A2A client
                logger.info(f"🔧 Creating A2A client...")
                client_config = ClientConfig(httpx_client=http_client, streaming=False)
                client_factory = ClientFactory(client_config)
                researcher_client = client_factory.create(researcher_card)

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

                # Get response
                logger.info(f"⏳ Waiting for Researcher response...")
                async for response in researcher_client.send_message(message):
                    if hasattr(response, 'parts'):
                        part = response.parts[0]
                        text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                        if text_content:
                            result = json.loads(text_content)
                            logger.info(f"📬 Received A2A response from Researcher:")
                            logger.info(f"   Status: {result.get('status')}")
                            logger.info(f"   Research ID: {result.get('research_id')}")
                            logger.info(f"   Questions answered: {result.get('total_questions')}")
                            return result

                logger.warning("⚠️  No response from Researcher")
                return {"status": "error", "message": "No response from Researcher"}

        except Exception as e:
            logger.error(f"Failed to send research request to Researcher: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to contact Researcher: {str(e)}"
            }

    async def _send_to_archivist(self, story_id: str, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Search for historical articles via Archivist agent using A2A protocol"""
        import time

        # Check if Archivist URL is configured
        if not self.archivist_url:
            logger.warning("⚠️  ELASTIC_ARCHIVIST_AGENT_CARD_URL not set - skipping archive search")
            return {
                "status": "skipped",
                "message": "Archivist agent card URL not configured"
            }

        # Build search query from topic and angle
        topic = assignment.get("topic", "")
        angle = assignment.get("angle", "")
        search_query = f"Find articles about {topic} {angle}".strip()

        logger.info(f"🔍 Connecting to Archivist agent at {self.archivist_url}")
        logger.info(f"   Search query: '{search_query}'")

        # Extract base URL and agent ID from the agent card URL
        # Example URL: https://gemini-searchlabs-f15e57.kb.us-central1.gcp.elastic.cloud/api/agent_builder/a2a/elastic-ai-agent
        # We need the base URL + /api/agent_builder/a2a/ + agent_id
        if "/api/agent_builder/a2a/" in self.archivist_url:
            # Extract agent_id from URL (last segment)
            agent_id = self.archivist_url.split("/")[-1]
            # Remove .json extension if present
            if agent_id.endswith(".json"):
                agent_id = agent_id[:-5]
            a2a_endpoint = self.archivist_url.replace(f"/{agent_id}.json", f"/{agent_id}").replace(f"/{agent_id}", f"/{agent_id}")
        else:
            logger.error(f"❌ Invalid Archivist URL format: {self.archivist_url}")
            raise Exception(f"Invalid Archivist URL format. Expected format: https://.../api/agent_builder/a2a/agent-id")

        # Create headers with API key
        headers = {
            "Content-Type": "application/json"
        }

        if self.archivist_api_key:
            headers["Authorization"] = f"ApiKey {self.archivist_api_key}"
            logger.info(f"🔑 Using API key authentication")
            logger.info(f"   API Key (masked): {self.archivist_api_key[:20]}...{self.archivist_api_key[-10:]}")
        else:
            logger.warning("⚠️  ELASTIC_ARCHIVIST_API_KEY not set - request may fail")

        # Retry logic: up to 3 attempts if response is empty
        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            attempt += 1

            try:
                # Generate unique message ID for this request
                message_id = f"msg-{int(time.time() * 1000)}-{story_id[:8]}-{attempt}"

                # Build A2A protocol request
                a2a_request = {
                    "id": message_id,
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "params": {
                        "configuration": {
                            "acceptedOutputModes": ["text/plain", "video/mp4"]
                        },
                        "message": {
                            "kind": "message",
                            "messageId": message_id,
                            "metadata": {},
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": search_query
                                }
                            ],
                            "role": "user"
                        }
                    }
                }

                logger.info(f"📨 Sending A2A request to Archivist (attempt {attempt}/{max_attempts}):")
                logger.info(f"   Story ID: {story_id}")
                logger.info(f"   Message ID: {message_id}")
                logger.info(f"   Search Query: {search_query}")

                # Use 30 second timeout as specified
                logger.info(f"⏱️  Setting timeout to 30 seconds for Archivist request")
                start_time = time.time()

                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    logger.info(f"⏳ Waiting for Archivist response...")
                    logger.info(f"   Request started at: {time.strftime('%H:%M:%S')}")

                    response = await http_client.post(
                        a2a_endpoint,
                        json=a2a_request,
                        headers=headers
                    )

                    elapsed = time.time() - start_time
                    logger.info(f"📥 Received response in {elapsed:.1f} seconds")
                    logger.info(f"   Status Code: {response.status_code}")

                    response.raise_for_status()
                    result = response.json()

                    # Check if response is empty or contains empty result
                    response_text = response.text.strip()
                    if not response_text or response_text == '""' or response_text == "":
                        logger.warning(f"⚠️  Archivist returned empty response (attempt {attempt}/{max_attempts})")

                        if attempt < max_attempts:
                            logger.info(f"🔄 Retrying in 2 seconds...")
                            await asyncio.sleep(2)
                            continue
                        else:
                            logger.error(f"❌ CRITICAL: Archivist returned empty response after {max_attempts} attempts")
                            raise Exception(f"Archivist returned empty response after {max_attempts} attempts")

                    # Extract articles from A2A response
                    articles = []
                    full_response = ""

                    # Parse A2A response structure
                    if "result" in result:
                        result_data = result["result"]

                        # Extract text content from response parts
                        if "parts" in result_data:
                            for part in result_data["parts"]:
                                if part.get("kind") == "text":
                                    text_content = part.get("text", "")
                                    full_response += text_content

                                    # Try to parse as structured data if it looks like JSON
                                    if text_content.strip().startswith("{") or text_content.strip().startswith("["):
                                        try:
                                            parsed = json.loads(text_content)
                                            if isinstance(parsed, list):
                                                articles.extend(parsed)
                                            elif isinstance(parsed, dict) and "articles" in parsed:
                                                articles.extend(parsed["articles"])
                                        except:
                                            pass

                        # Also check for resources in the response
                        if "resources" in result_data:
                            for resource in result_data["resources"]:
                                article = {
                                    "id": resource.get("id", "unknown"),
                                    "content": resource.get("text", ""),
                                    "metadata": resource.get("metadata", {})
                                }
                                articles.append(article)

                    logger.info(f"")
                    logger.info(f"📚 ARCHIVIST SEARCH RESULTS:")
                    logger.info(f"   🔍 Search Query: {search_query}")
                    logger.info(f"   📊 Found {len(articles)} historical articles")
                    logger.info(f"   📝 Response length: {len(full_response)} characters")

                    if articles:
                        logger.info(f"   📰 Article References:")
                        for i, article in enumerate(articles[:10], 1):
                            article_id = article.get('id', 'Unknown')
                            content = article.get('content', '')
                            preview = content[:100] if content else "No content"
                            logger.info(f"      {i}. {article_id}: {preview}...")

                        if len(articles) > 10:
                            logger.info(f"      ... and {len(articles) - 10} more articles")
                    else:
                        logger.info(f"   ℹ️  No historical articles found (but got text response)")
                    logger.info(f"")

                    return {
                        "status": "success",
                        "query": search_query,
                        "response": full_response,
                        "articles": articles,
                        "message_id": message_id,
                        "attempts": attempt
                    }

            except Exception as e:
                elapsed = time.time() - start_time if 'start_time' in locals() else 0
                error_msg = str(e)

                if "Timeout" in error_msg or "timeout" in error_msg:
                    logger.error(f"❌ Archivist request timed out (attempt {attempt}/{max_attempts})")
                    logger.error(f"   Elapsed time: {elapsed:.1f} seconds")

                    if attempt < max_attempts:
                        logger.info(f"🔄 Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        logger.error(f"❌ CRITICAL: Archivist timed out after {max_attempts} attempts")
                        logger.error(f"   Archivist URL: {self.archivist_url}")
                        raise Exception(f"Archivist request timed out after {max_attempts} attempts")
                else:
                    logger.error(f"❌ CRITICAL: Failed to send request to Archivist (attempt {attempt}/{max_attempts}): {e}", exc_info=True)
                    logger.error(f"   Elapsed time: {elapsed:.1f} seconds")

                    if attempt < max_attempts:
                        logger.info(f"🔄 Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        # Re-raise the exception to halt the workflow after all attempts
                        raise Exception(f"Archivist request failed after {max_attempts} attempts: {str(e)}") from e

    async def _send_to_publisher(self, story_id: str) -> Dict[str, Any]:
        """Send finalized article to Publisher agent via A2A"""
        try:
            # Get draft and all related data
            if story_id not in self.drafts:
                return {
                    "status": "error",
                    "message": f"No draft found for story_id: {story_id}"
                }

            draft = self.drafts[story_id]
            assignment = self.assignments.get(story_id, {})
            review = self.editor_reviews.get(story_id, {})
            research = self.research_data.get(story_id, [])
            archive = self.archive_data.get(story_id, {})

            # Build complete article data for Publisher
            article_data = {
                "story_id": story_id,
                "headline": self._extract_headline(draft.get("content", "")),
                "content": draft.get("content"),
                "topic": assignment.get("topic"),
                "angle": assignment.get("angle"),
                "word_count": draft.get("word_count"),
                "target_length": assignment.get("target_length"),
                "priority": assignment.get("priority", "normal"),
                "published_at": datetime.now().isoformat(),
                "created_at": assignment.get("accepted_at"),
                "deadline": assignment.get("deadline"),
                "author": "Reporter Agent",
                "editor": "Editor Agent",
                "research_questions": [r.get("question") for r in research] if research else [],
                "research_data": research,
                "editorial_review": review,
                "archive_references": str(archive) if archive else None,
                "url_slug": draft.get("url_slug") or self._generate_url_slug(assignment.get("topic", story_id)),
                "filepath": draft.get("filepath"),
                "version": 1,
                "revisions_count": draft.get("revisions_applied", 0),
                "agents_involved": ["News Chief", "Reporter", "Researcher", "Archivist", "Editor", "Publisher"],
                "metadata": {
                    "workflow_start": assignment.get("accepted_at"),
                    "draft_completed": draft.get("created_at"),
                    "reviewed_at": review.get("reviewed_at") if review else None,
                    "revised_at": draft.get("revised_at")
                }
            }

            logger.info(f"🔍 Discovering Publisher agent at {self.publisher_url}")

            async with httpx.AsyncClient(timeout=90.0) as http_client:
                # Discover Publisher agent
                card_resolver = A2ACardResolver(http_client, self.publisher_url)
                publisher_card = await card_resolver.get_agent_card()
                logger.info(f"✅ Found Publisher: {publisher_card.name} (v{publisher_card.version})")

                # Create A2A client
                logger.info(f"🔧 Creating A2A client for Publisher...")
                client_config = ClientConfig(httpx_client=http_client, streaming=False)
                client_factory = ClientFactory(client_config)
                publisher_client = client_factory.create(publisher_card)

                # Send publish request
                request = {
                    "action": "publish_article",
                    "article": article_data
                }

                logger.info(f"📨 Sending A2A message to Publisher:")
                logger.info(f"   Story ID: {story_id}")
                logger.info(f"   Headline: {article_data['headline'][:60]}...")

                message = create_text_message_object(content=json.dumps(request))

                # Get response
                logger.info(f"⏳ Waiting for Publisher response...")
                async for response in publisher_client.send_message(message):
                    if hasattr(response, 'parts'):
                        part = response.parts[0]
                        text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                        if text_content:
                            result = json.loads(text_content)
                            logger.info(f"📬 Received A2A response from Publisher:")
                            logger.info(f"   Status: {result.get('status')}")
                            if result.get("status") == "success":
                                logger.info(f"   Published to: {result.get('elasticsearch', {}).get('index')}")
                                logger.info(f"   Tags: {result.get('tags')}")
                                logger.info(f"   Categories: {result.get('categories')}")
                            return result

                logger.warning("⚠️  No response from Publisher")
                return {"status": "error", "message": "No response from Publisher"}

        except Exception as e:
            logger.error(f"Failed to send to Publisher: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to contact Publisher: {str(e)}"
            }

    def _extract_headline(self, content: str) -> str:
        """Extract headline from article content"""
        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("HEADLINE:"):
                return line.replace("HEADLINE:", "").strip()
            elif line.strip() and not line.strip().startswith("#"):
                # First non-empty, non-markdown-header line
                return line.strip()
        return "Untitled Article"

    def _generate_url_slug(self, topic: str) -> str:
        """Generate URL-friendly slug from topic"""
        import re
        slug = topic.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:50]  # Limit to 50 chars

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

        # Use Anthropic if available, otherwise mock
        if self.anthropic_client:
            try:
                message = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return message.content[0].text
            except Exception as e:
                logger.error(f"Anthropic API error: {e}", exc_info=True)
                return self._generate_mock_article(topic, angle, target_length)
        else:
            return self._generate_mock_article(topic, angle, target_length)

    def _generate_mock_article(self, topic: str, angle: str, target_length: int) -> str:
        """Generate a simple mock article when Anthropic API is not available"""
        return f"""HEADLINE: {topic}: A Comprehensive Analysis

{topic} has emerged as a significant development in recent news. {angle if angle else 'This story examines the key aspects and implications of this important topic.'}

Industry experts and analysts have been closely monitoring these developments, noting the potential impact on various stakeholders. The situation continues to evolve, with new information emerging regularly.

Sources familiar with the matter indicate that multiple factors are contributing to the current state of affairs. Observers suggest that the coming weeks will be crucial in determining the long-term implications.

Further updates will be provided as more information becomes available. Stakeholders are advised to monitor the situation closely and stay informed through reliable news sources.

[Article generated with mock content - ANTHROPIC_API_KEY not configured]
[Target length: {target_length} words]"""

    async def _submit_draft(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit completed draft to Editor via A2A"""
        logger.info("📤 Submitting draft to Editor...")
        story_id = request.get("story_id")

        if not story_id:
            logger.error("❌ No story_id provided")
            return {
                "status": "error",
                "message": "No story_id provided"
            }

        if story_id not in self.drafts:
            logger.error(f"❌ No draft found for story_id: {story_id}")
            return {
                "status": "error",
                "message": f"No draft found for story_id: {story_id}"
            }

        draft = self.drafts[story_id]

        # Mark as submitted
        draft["status"] = "submitted"
        draft["submitted_at"] = datetime.now().isoformat()
        draft["submitted_to"] = "editor"

        # Update assignment status
        if story_id in self.assignments:
            self.assignments[story_id]["reporter_status"] = "submitted"

        logger.info(f"📨 Sending draft to Editor via A2A...")
        logger.info(f"   Story ID: {story_id}")
        logger.info(f"   Word count: {draft['word_count']}")

        # Send draft to Editor via A2A
        editor_response = await self._send_to_editor(draft)

        logger.info(f"✅ Draft submitted. Editor status: {editor_response.get('status')}")

        return {
            "status": "success",
            "message": "Draft submitted for editorial review",
            "story_id": story_id,
            "submitted_to": "editor",
            "word_count": draft["word_count"],
            "submitted_at": draft["submitted_at"],
            "editor_response": editor_response
        }

    async def _send_to_editor(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Send draft to Editor agent via A2A"""
        try:
            async with httpx.AsyncClient(timeout=90.0) as http_client:
                # Discover Editor agent
                logger.info(f"🔍 Discovering Editor agent at {self.editor_url}")
                card_resolver = A2ACardResolver(http_client, self.editor_url)
                editor_card = await card_resolver.get_agent_card()
                logger.info(f"✅ Found Editor: {editor_card.name} (v{editor_card.version})")

                # Create A2A client
                logger.info(f"🔧 Creating A2A client...")
                client_config = ClientConfig(httpx_client=http_client, streaming=False)
                client_factory = ClientFactory(client_config)
                editor_client = client_factory.create(editor_card)

                # Send review_draft task to Editor
                request = {
                    "action": "review_draft",
                    "draft": draft
                }
                logger.info(f"📨 Sending A2A message to Editor:")
                logger.info(f"   Action: {request['action']}")
                logger.info(f"   Story ID: {draft.get('story_id')}")

                message = create_text_message_object(content=json.dumps(request))

                # Get response
                logger.info(f"⏳ Waiting for Editor response...")
                async for response in editor_client.send_message(message):
                    if hasattr(response, 'parts'):
                        part = response.parts[0]
                        text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                        if text_content:
                            result = json.loads(text_content)
                            logger.info(f"📬 Received A2A response from Editor:")
                            logger.info(f"   Status: {result.get('status')}")
                            logger.info(f"   Review ID: {result.get('review_id')}")

                            # Store the review
                            story_id = draft.get('story_id')
                            if story_id and result.get('status') == 'success':
                                self.editor_reviews[story_id] = result.get('review', {})
                                logger.info(f"   Approval status: {self.editor_reviews[story_id].get('approval_status')}")

                            return result

                logger.warning("⚠️  No response from Editor")
                return {"status": "error", "message": "No response from Editor"}

        except Exception as e:
            logger.error(f"Failed to send draft to Editor: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to contact Editor: {str(e)}"
            }

    async def _apply_edits(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Apply editorial suggestions to a draft using Anthropic"""
        logger.info("✏️  Applying editorial suggestions...")
        story_id = request.get("story_id")

        if not story_id:
            logger.error("❌ No story_id provided")
            return {
                "status": "error",
                "message": "No story_id provided"
            }

        if story_id not in self.drafts:
            logger.error(f"❌ No draft found for story_id: {story_id}")
            return {
                "status": "error",
                "message": f"No draft found for story_id: {story_id}"
            }

        if story_id not in self.editor_reviews:
            logger.error(f"❌ No editor review found for story_id: {story_id}")
            return {
                "status": "error",
                "message": f"No editor review found for story_id: {story_id}. Submit draft for review first."
            }

        draft = self.drafts[story_id]
        review = self.editor_reviews[story_id]

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

            logger.info(f"✅ Draft updated successfully")
            logger.info(f"   Word count: {old_word_count} → {draft['word_count']}")

            # Automatically send to Publisher after edits are applied
            logger.info("📤 Automatically sending to Publisher...")
            publisher_response = await self._send_to_publisher(story_id)

            response = {
                "status": "success",
                "message": "Editorial suggestions applied successfully",
                "story_id": story_id,
                "old_word_count": old_word_count,
                "new_word_count": draft["word_count"],
                "revisions_applied": draft["revisions_applied"],
                "preview": revised_content[:200] + "..." if len(revised_content) > 200 else revised_content
            }

            # Include publisher response if successful
            if publisher_response.get("status") == "success":
                response["publisher_response"] = publisher_response
                logger.info(f"✅ Article published successfully")
            else:
                response["publisher_error"] = publisher_response.get("message")
                logger.warning(f"⚠️  Publisher failed: {publisher_response.get('message')}")

            return response

        except Exception as e:
            logger.error(f"❌ Error applying edits: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to apply edits: {str(e)}",
                "story_id": story_id
            }

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

        # Use Anthropic if available
        if self.anthropic_client:
            try:
                message = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=3000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return message.content[0].text
            except Exception as e:
                logger.error(f"Anthropic API error during edit integration: {e}", exc_info=True)
                # Fall back to simple replacement if API fails
                return self._apply_simple_edits(original_content, suggested_edits)
        else:
            return self._apply_simple_edits(original_content, suggested_edits)

    def _apply_simple_edits(self, content: str, suggested_edits: List[Dict[str, Any]]) -> str:
        """Apply simple text replacements when Anthropic is not available"""
        revised = content
        for edit in suggested_edits:
            original = edit.get("original", "")
            suggested = edit.get("suggested", "")
            if original and suggested and original in revised:
                revised = revised.replace(original, suggested)
        return revised

    async def _publish_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Publish the final article to markdown file"""
        logger.info("📰 Publishing article...")
        story_id = request.get("story_id")

        if not story_id:
            logger.error("❌ No story_id provided")
            return {
                "status": "error",
                "message": "No story_id provided"
            }

        if story_id not in self.drafts:
            logger.error(f"❌ No draft found for story_id: {story_id}")
            return {
                "status": "error",
                "message": f"No draft found for story_id: {story_id}"
            }

        draft = self.drafts[story_id]
        assignment = draft.get("assignment", {})
        content = draft.get("content", "")

        # Create articles directory if it doesn't exist
        articles_dir = "articles"
        os.makedirs(articles_dir, exist_ok=True)

        # Generate filename from topic and story_id
        topic = assignment.get("topic", "article")
        # Clean topic for filename
        filename = topic.lower().replace(" ", "-").replace(":", "").replace(",", "")
        filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_'))
        filepath = os.path.join(articles_dir, f"{filename}-{story_id}.md")

        # Build markdown content with metadata
        markdown_content = f"""---
title: {assignment.get('topic', 'Untitled')}
story_id: {story_id}
author: Elastic News Reporter Agent
date: {datetime.now().strftime('%Y-%m-%d')}
word_count: {draft.get('word_count')}
status: {draft.get('status')}
priority: {assignment.get('priority', 'normal')}
target_length: {assignment.get('target_length')}
---

{content}

---

**Article Metadata:**
- Story ID: {story_id}
- Created: {assignment.get('created_at', 'N/A')}
- Published: {datetime.now().isoformat()}
- Word Count: {draft.get('word_count')}
- Revisions Applied: {draft.get('revisions_applied', 0)}
- Angle: {assignment.get('angle', 'N/A')}

*Generated by Elastic News - A Multi-Agent AI Newsroom*
*Powered by Anthropic Claude Sonnet 4 and A2A Protocol*
"""

        # Write to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"✅ Article published successfully")
            logger.info(f"   File: {filepath}")
            logger.info(f"   Word count: {draft.get('word_count')}")

            # Update draft status
            draft["status"] = "published"
            draft["published_at"] = datetime.now().isoformat()
            draft["published_path"] = filepath

            # Update assignment status
            if story_id in self.assignments:
                self.assignments[story_id]["reporter_status"] = "published"

            return {
                "status": "success",
                "message": "Article published successfully",
                "story_id": story_id,
                "filepath": filepath,
                "word_count": draft.get("word_count"),
                "published_at": draft["published_at"]
            }

        except Exception as e:
            logger.error(f"❌ Error publishing article: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to publish article: {str(e)}",
                "story_id": story_id
            }

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
                "editor_review": review_info if review_info else None
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
                "reviews": list(self.editor_reviews.values())
            }


class ReporterAgentExecutor(AgentExecutor):
    """AgentExecutor for the Reporter agent following official A2A pattern"""

    def __init__(self):
        self.agent = ReporterAgent()

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
        description="Writes news articles based on story assignments using AI-powered content generation",
        url=f"http://{host}:{port}",
        version="1.0.0",
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/reporter-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True,
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
                id="article.writing.submit_draft",
                name="Submit Draft",
                description="Submits completed article draft for editorial review via A2A",
                tags=["writing", "workflow"],
                examples=[
                    '{"action": "submit_draft", "story_id": "story_123"}',
                    "Submit completed draft"
                ]
            ),
            AgentSkill(
                id="article.writing.apply_edits",
                name="Apply Editorial Suggestions",
                description="Applies editorial feedback and suggested edits to revise the article",
                tags=["editing", "revision", "ai-integration"],
                examples=[
                    '{"action": "apply_edits", "story_id": "story_123"}',
                    "Apply editor's suggestions to article"
                ]
            ),
            AgentSkill(
                id="article.writing.publish_article",
                name="Publish Article",
                description="Publishes the final article to a markdown file in the articles directory",
                tags=["publishing", "output", "workflow"],
                examples=[
                    '{"action": "publish_article", "story_id": "story_123"}',
                    "Publish final article to file"
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

    return server.build()


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

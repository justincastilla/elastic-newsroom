"""
Publisher Agent

Publishes finalized articles to Elasticsearch and handles deployment workflow.
Includes mock CI/CD and CRM notifications, but real Elasticsearch indexing.
"""

import json
import logging
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

import click
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
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
logger = setup_logger("PUBLISHER")

# Singleton instance for maintaining state across requests
_publisher_agent_instance = None

class PublisherAgent(BaseAgent):
    """Publisher Agent - Publishes articles to Elasticsearch and manages deployment"""

    def __init__(self):
        # Initialize base agent with logger
        super().__init__(logger)

        self.published_articles: Dict[str, Dict[str, Any]] = {}
        self.es_client = None
        self.es_index = os.getenv("ELASTIC_ARCHIVIST_INDEX", "news_archive")

        # Initialize Elasticsearch client
        es_endpoint = os.getenv("ELASTICSEARCH_ENDPOINT")
        es_api_key = os.getenv("ELASTICSEARCH_API_KEY")

        if es_endpoint and es_api_key:
            try:
                self.es_client = Elasticsearch(
                    es_endpoint,
                    api_key=es_api_key
                )
                # Test connection
                info = self.es_client.info()
                logger.debug("Connected to Elasticsearch version=%s index=%s", info['version']['number'], self.es_index)
            except Exception as e:
                logger.error("Failed to connect to Elasticsearch: %s", e)
                self.es_client = None
        else:
            logger.warning("Elasticsearch credentials not configured")

        # Initialize Anthropic client using centralized utility (from BaseAgent)
        self._init_anthropic_client()
        if not self.anthropic_client:
            logger.warning("Anthropic client not available - tags will be empty")

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
                logger.info("Received query: %s", format_json_for_log(query))

            # Parse the query to determine the action
            query_data = json.loads(query) if query.startswith('{') else {"action": "status"}
            action = query_data.get("action")

            # Only log non-status actions to reduce log spam
            if action != "get_status":
                logger.info("Action: %s", action)

            if action == "publish_article":
                return await self._publish_article(query_data)
            elif action == "bulk_publish":
                return await self._bulk_publish(query_data)
            elif action == "unpublish_article":
                return await self._unpublish_article(query_data)
            elif action == "get_status":
                return await self._get_status(query_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": ["publish_article", "bulk_publish", "unpublish_article", "get_status"]
                }

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in query: %s", e)
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

    def _sanitize_research_data(self, research_data: list) -> list:
        """Sanitize research_data so it matches the ES mapping.

        The mapping expects research_data.sources to be keyword (simple strings),
        but the Reporter may send rich objects with title/url/published_date.
        This flattens source objects to URL strings before indexing.
        Structured source data is preserved in the top-level research_sources field.
        """
        if not isinstance(research_data, list):
            return research_data

        sanitized = []
        for item in research_data:
            if not isinstance(item, dict):
                sanitized.append(item)
                continue

            item_copy = dict(item)
            sources = item_copy.get("sources")
            if isinstance(sources, list):
                flat_sources = []
                for src in sources:
                    if isinstance(src, dict):
                        flat_sources.append(src.get("url", str(src)))
                    else:
                        flat_sources.append(str(src))
                item_copy["sources"] = flat_sources
            sanitized.append(item_copy)

        return sanitized

    async def _publish_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Publish article to Elasticsearch with CI/CD and CRM workflow"""
        logger.info("Processing article publication")

        article_data = request.get("article")
        if not article_data:
            logger.error("No article data provided")
            return {
                "status": "error",
                "message": "No article data provided"
            }

        story_id = article_data.get("story_id")

        # Publish event: publication started
        await self._publish_event(
            event_type="publication_started",
            story_id=story_id,
            data={
                "headline": article_data.get("headline"),
                "word_count": article_data.get("word_count")
            }
        )

        logger.debug("Publishing story=%s headline=%s words=%s", story_id, article_data.get('headline', 'N/A')[:60], article_data.get('word_count'))

        # Check Elasticsearch connection
        if not self.es_client:
            logger.error("Elasticsearch not available")
            return {
                "status": "error",
                "message": "Elasticsearch not configured or unavailable"
            }

        # Generate tags and categories
        logger.debug("Generating tags and categories")
        tags, categories = await self._generate_tags_and_categories(article_data)
        logger.debug("Tags: %s Categories: %s", tags, categories)

        # Build Elasticsearch document
        logger.debug("Building Elasticsearch document")
        es_document = self._build_es_document(article_data, tags, categories)

        # ALWAYS save to local file first (fallback if Elasticsearch fails)
        file_path = await self._save_article_to_file(article_data, tags, categories)
        logger.info("Article saved to file: %s", file_path)

        # Publish event: file saved
        await self._publish_event(
            event_type="file_saved",
            story_id=story_id,
            data={"file_path": file_path}
        )

        # Index to Elasticsearch - CRITICAL STEP
        es_success = False
        es_response = None
        logger.info("Indexing article to Elasticsearch index=%s", self.es_index)
        try:
            es_response = self.es_client.index(
                index=self.es_index,
                id=story_id,  # Use story_id as document ID
                document=es_document,
                refresh="wait_for"  # Ensure article is immediately searchable
            )
            logger.debug("Article indexed result=%s id=%s", es_response['result'], es_response['_id'])
            es_success = True

            # Publish event: elasticsearch indexed
            await self._publish_event(
                event_type="elasticsearch_indexed",
                story_id=story_id,
                data={
                    "index": self.es_index,
                    "document_id": es_response['_id']
                }
            )

        except Exception as e:
            logger.error("Elasticsearch indexing failed: %s", e, exc_info=True)
            logger.warning("Article saved to local file but not indexed to Elasticsearch")
            # Don't return error - continue with local file publication
            es_success = False

        # CI/CD Deployment via MCP tool
        deployment_result = await self._deploy_to_production(story_id, article_data)

        # CRM Notification via MCP tool
        notification_result = await self._notify_subscribers(story_id, article_data)

        # Store publication record
        publication_record = {
            "story_id": story_id,
            "headline": article_data.get("headline"),
            "published_at": datetime.now().isoformat(),
            "file_path": file_path,
            "es_index": self.es_index if es_success else None,
            "es_document_id": es_response['_id'] if es_success else None,
            "build_number": deployment_result.get("build", {}).get("number"),
            "deployment_url": deployment_result.get("deployment", {}).get("url"),
            "subscribers_notified": notification_result.get("notification", {}).get("subscribers_notified"),
            "tags": tags,
            "categories": categories,
            "elasticsearch_indexed": es_success
        }
        self.published_articles[story_id] = publication_record

        # Publish event: publication completed
        await self._publish_event(
            event_type="publication_completed",
            story_id=story_id,
            data={
                "file_path": file_path,
                "elasticsearch_indexed": es_success
            }
        )

        if es_success:
            logger.info("Publication workflow completed successfully (Elasticsearch + Local File)")
        else:
            logger.info("Publication workflow completed (Local File Only - Elasticsearch indexing failed)")
        logger.debug("Total published articles: %s", len(self.published_articles))

        result = {
            "status": "success",
            "message": f"Article '{article_data.get('headline')}' published successfully",
            "story_id": story_id,
            "published_at": publication_record["published_at"],
            "file_path": file_path,
            "build_number": publication_record["build_number"],
            "deployment_url": publication_record["deployment_url"],
            "subscribers_notified": publication_record["subscribers_notified"],
            "tags": tags,
            "categories": categories
        }

        # Include Elasticsearch info only if successful
        if es_success:
            result["elasticsearch"] = {
                "index": self.es_index,
                "document_id": es_response['_id'],
                "result": es_response['result']
            }
        else:
            result["elasticsearch_warning"] = "Article not indexed to Elasticsearch (saved to local file only)"

        return result

    async def _unpublish_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Unpublish article from Elasticsearch (set status to unpublished)"""
        logger.info("Processing article unpublish request")

        story_id = request.get("story_id")
        if not story_id:
            logger.error("No story_id provided")
            return {
                "status": "error",
                "message": "No story_id provided"
            }

        # Check Elasticsearch connection
        if not self.es_client:
            logger.error("Elasticsearch not available")
            return {
                "status": "error",
                "message": "Elasticsearch not configured or unavailable"
            }

        # Update document status in Elasticsearch
        try:
            logger.debug("Updating article status in Elasticsearch story=%s", story_id)
            response = self.es_client.update(
                index=self.es_index,
                id=story_id,
                doc={
                    "status": "unpublished",
                    "unpublished_at": datetime.now().isoformat()
                }
            )
            logger.debug("Article status updated result=%s", response['result'])

        except Exception as e:
            logger.error("Failed to update Elasticsearch: %s", e, exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to unpublish article: {str(e)}",
                "story_id": story_id
            }

        # Mock CI/CD - Remove from production
        logger.debug("[MOCK CI/CD] Removing from production")
        time.sleep(1)
        logger.debug("[MOCK CI/CD] Article removed from production")

        # Update local record
        if story_id in self.published_articles:
            self.published_articles[story_id]["status"] = "unpublished"
            self.published_articles[story_id]["unpublished_at"] = datetime.now().isoformat()

        return {
            "status": "success",
            "message": f"Article unpublished successfully",
            "story_id": story_id,
            "unpublished_at": datetime.now().isoformat()
        }

    async def _bulk_publish(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk publish multiple articles to Elasticsearch using the bulk API"""
        logger.info("Processing bulk article publication count=%s", len(request.get("articles", [])))

        articles = request.get("articles", [])
        if not articles:
            return {"status": "error", "message": "No articles provided for bulk publish"}

        if not self.es_client:
            return {"status": "error", "message": "Elasticsearch not configured or unavailable"}

        # Build bulk actions
        actions = []
        results = {"succeeded": [], "failed": []}

        for article_data in articles:
            story_id = article_data.get("story_id")
            if not story_id:
                results["failed"].append({"error": "Missing story_id", "article": article_data.get("headline", "unknown")})
                continue

            try:
                tags, categories = await self._generate_tags_and_categories(article_data)
                es_document = self._build_es_document(article_data, tags, categories)

                actions.append({
                    "_index": self.es_index,
                    "_id": story_id,
                    "_source": es_document
                })
            except Exception as e:
                logger.error("Failed to prepare article %s: %s", story_id, e)
                results["failed"].append({"story_id": story_id, "error": str(e)})

        if not actions:
            return {"status": "error", "message": "No valid articles to index", "failed": results["failed"]}

        # Execute bulk indexing
        try:
            success_count, errors = bulk(
                self.es_client,
                actions,
                refresh="wait_for",
                raise_on_error=False
            )

            logger.info("Bulk indexed %s articles", success_count)

            for action in actions:
                story_id = action["_id"]
                results["succeeded"].append(story_id)
                self.published_articles[story_id] = {
                    "story_id": story_id,
                    "headline": action["_source"].get("headline"),
                    "published_at": action["_source"].get("published_at"),
                    "elasticsearch_indexed": True
                }

            if errors:
                for error in errors:
                    logger.error("Bulk index error: %s", error)
                    results["failed"].append(error)

            return {
                "status": "success",
                "message": f"Bulk published {success_count} of {len(articles)} articles",
                "succeeded": len(results["succeeded"]),
                "failed": len(results["failed"]),
                "details": results
            }

        except Exception as e:
            logger.error("Bulk indexing failed: %s", e, exc_info=True)
            return {"status": "error", "message": f"Bulk indexing failed: {str(e)}"}

    async def _generate_tags_and_categories(self, article_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Generate tags and categories from article content using MCP generate_tags tool"""

        headline = article_data.get("headline", "")
        content = article_data.get("content", "")
        topic = article_data.get("topic", "")

        try:
            logger.debug("Calling MCP generate_tags tool")

            # Direct call to MCP tool (bypass LLM selection for efficiency and reliability)
            if self.mcp_client is None:
                self._init_mcp_client()

            result = await self.mcp_client.call_tool(
                tool_name="generate_tags",
                arguments={
                    "headline": headline,
                    "content": content[:500],  # First 500 chars
                    "topic": topic
                }
            )

            # Parse the JSON response
            tag_data = json.loads(result) if isinstance(result, str) else result
            tags = tag_data.get("tags", [])
            categories = tag_data.get("categories", [])

            logger.debug("Tags generated count=%s categories=%s", len(tags), len(categories))
            return tags, categories

        except Exception as e:
            logger.error("MCP generate_tags tool failed: %s", e, exc_info=True)
            # MCP server is required - re-raise the exception
            raise Exception(f"MCP generate_tags tool failed: {e}")

    async def _deploy_to_production(self, story_id: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy article to production via MCP deploy_to_production tool"""
        try:
            logger.info("Deploying to production via CI/CD pipeline")

            # Direct call to MCP tool
            if self.mcp_client is None:
                self._init_mcp_client()

            url_slug = article_data.get('url_slug', story_id)
            build_number = f"#{int(time.time()) % 10000}"

            result = await self.mcp_client.call_tool(
                tool_name="deploy_to_production",
                arguments={
                    "story_id": story_id,
                    "url_slug": url_slug,
                    "build_number": build_number
                }
            )

            # Parse the JSON response
            deployment_data = json.loads(result) if isinstance(result, str) else result

            # Log deployment results
            build_info = deployment_data.get("build", {})
            deploy_info = deployment_data.get("deployment", {})

            logger.debug("Build %s completed duration=%ss", build_info.get('number'), build_info.get('duration_seconds'))
            logger.debug("Deployment to %s completed url=%s", deploy_info.get('environment'), deploy_info.get('url'))

            return deployment_data

        except Exception as e:
            logger.error("Deployment failed: %s", e, exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _notify_subscribers(self, story_id: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notify subscribers via MCP notify_subscribers tool"""
        try:
            logger.info("Notifying subscribers via CRM")

            # Direct call to MCP tool
            if self.mcp_client is None:
                self._init_mcp_client()

            headline = article_data.get('headline', article_data.get('topic', 'Untitled'))
            topic = article_data.get('topic', 'General')

            result = await self.mcp_client.call_tool(
                tool_name="notify_subscribers",
                arguments={
                    "story_id": story_id,
                    "headline": headline,
                    "topic": topic
                }
            )

            # Parse the JSON response
            notification_data = json.loads(result) if isinstance(result, str) else result

            # Log notification results
            notif_info = notification_data.get("notification", {})
            metrics = notif_info.get("estimated_metrics", {})

            logger.debug("Notification sent subscribers=%s template=%s open_rate=%s", notif_info.get('subscribers_notified'), notif_info.get('email_template'), metrics.get('open_rate'))

            return notification_data

        except Exception as e:
            logger.error("Subscriber notification failed: %s", e, exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _save_article_to_file(self, article_data: Dict[str, Any], tags: List[str], categories: List[str]) -> str:
        """Save article to local markdown file"""
        story_id = article_data.get("story_id")
        topic = article_data.get("topic", "article")
        content = article_data.get("content", "")
        headline = article_data.get("headline", "Untitled")
        research_sources = article_data.get("research_sources", [])

        # Create articles directory if it doesn't exist
        articles_dir = "articles"
        os.makedirs(articles_dir, exist_ok=True)

        # Generate filename from topic and story_id
        filename = topic.lower().replace(" ", "-").replace(":", "").replace(",", "")
        filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_'))
        filepath = os.path.join(articles_dir, f"{filename}-{story_id}.md")

        # Build research sources section grouped by domain
        # Always replace any existing Sources section from the LLM with a properly
        # domain-grouped version built from structured research_sources data
        sources_section = ""
        if research_sources:
            # Strip any existing Sources section from content so we can replace it
            import re
            content = re.sub(
                r'\n##\s+Sources\s*\n.*',
                '',
                content,
                flags=re.DOTALL | re.IGNORECASE
            ).rstrip()

            # Group sources by domain
            from urllib.parse import urlparse
            domain_groups = {}
            for src in research_sources:
                url = src.get("url", "")
                title = src.get("title", url)
                if not url:
                    continue
                domain = urlparse(url).netloc.replace("www.", "")
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append({"title": title, "url": url})

            if domain_groups:
                sources_section = "\n\n## Sources\n\n"
                for domain in sorted(domain_groups.keys()):
                    sources_section += f"**{domain}**\n\n"
                    for src in domain_groups[domain]:
                        sources_section += f"- [{src['title']}]({src['url']})\n"
                    sources_section += "\n"

        # Build markdown content with metadata
        markdown_content = f"""---
title: {topic}
story_id: {story_id}
headline: {headline}
author: Elastic News Reporter Agent
date: {datetime.now().strftime('%Y-%m-%d')}
word_count: {article_data.get('word_count')}
tags: {', '.join(tags)}
categories: {', '.join(categories)}
---

{content}
{sources_section}
---

**Article Metadata:**
- Story ID: {story_id}
- Published: {datetime.now().isoformat()}
- Word Count: {article_data.get('word_count')}
- Tags: {', '.join(tags)}
- Categories: {', '.join(categories)}

*Generated by Elastic News - A Multi-Agent AI Newsroom*
*Powered by Anthropic Claude Sonnet 4 and A2A Protocol*
"""

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return filepath

    def _build_es_document(self, article_data: Dict[str, Any], tags: List[str], categories: List[str]) -> Dict[str, Any]:
        """Build Elasticsearch document from article data"""

        # Calculate workflow duration if timestamps available
        workflow_duration_ms = None
        if article_data.get("created_at") and article_data.get("published_at"):
            try:
                created = datetime.fromisoformat(article_data["created_at"].replace("Z", "+00:00"))
                published = datetime.fromisoformat(article_data["published_at"].replace("Z", "+00:00"))
                workflow_duration_ms = int((published - created).total_seconds() * 1000)
            except Exception as e:
                logger.warning("Could not calculate workflow duration: %s", e)

        # Build document
        document = {
            "story_id": article_data.get("story_id"),
            "headline": article_data.get("headline"),
            "content": article_data.get("content"),
            "topic": article_data.get("topic"),
            "angle": article_data.get("angle"),
            "word_count": article_data.get("word_count"),
            "target_length": article_data.get("target_length"),
            "priority": article_data.get("priority", "normal"),
            "status": "published",
            "published_at": article_data.get("published_at") or datetime.now().isoformat(),
            "created_at": article_data.get("created_at"),
            "updated_at": datetime.now().isoformat(),
            "author": article_data.get("author", "Reporter Agent"),
            "editor": article_data.get("editor", "Editor Agent"),
            "tags": tags,
            "categories": categories,
            "research_questions": article_data.get("research_questions", []),
            "research_data": self._sanitize_research_data(article_data.get("research_data", [])),
            "editorial_review": article_data.get("editorial_review"),
            "archive_references": article_data.get("archive_references"),
            "research_sources": article_data.get("research_sources", []),
            "url_slug": article_data.get("url_slug"),
            "filepath": article_data.get("filepath"),
            "version": article_data.get("version", 1),
            "revisions_count": article_data.get("revisions_count", 0),
            "agents_involved": article_data.get("agents_involved", ["News Chief", "Reporter", "Researcher", "Archivist", "Editor", "Publisher"]),
            "workflow_duration_ms": workflow_duration_ms,
            "metadata": article_data.get("metadata", {})
        }

        return document

    async def _get_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get publication status"""
        story_id = request.get("story_id")

        if story_id:
            if story_id not in self.published_articles:
                return {
                    "status": "error",
                    "message": f"No publication record found for story_id: {story_id}"
                }
            return {
                "status": "success",
                "publication": self.published_articles[story_id]
            }
        else:
            return {
                "status": "success",
                "total_published": len(self.published_articles),
                "recent_publications": list(self.published_articles.values())[-10:]  # Last 10
            }


def get_publisher_agent() -> PublisherAgent:
    """Get singleton PublisherAgent instance to maintain state across requests"""
    global _publisher_agent_instance
    if _publisher_agent_instance is None:
        _publisher_agent_instance = PublisherAgent()
    return _publisher_agent_instance


class PublisherAgentExecutor(AgentExecutor):
    """AgentExecutor for the Publisher agent following official A2A pattern"""

    def __init__(self):
        # Use singleton instance to maintain state across requests
        self.agent = get_publisher_agent()

    async def execute(self, context, event_queue) -> None:
        """Execute the agent request"""
        logger.info('Executing Publisher agent')

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
    """Create the Publisher agent card"""
    return AgentCard(
        name="Publisher",
        description="Publishes finalized articles to Elasticsearch, handles CI/CD deployment, and sends CRM notifications. Works through News Chief for workflow coordination.",
        url=f"http://{host}:{port}",
        version="1.0.0",
        protocol_version="0.3.0",  # A2A Protocol version
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/publisher-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,  # Not implemented yet
            state_transition_history=True,
            max_concurrent_tasks=20
        ),
        skills=[
            AgentSkill(
                id="publishing.article.publish",
                name="Publish Article",
                description="Publishes article to Elasticsearch with auto-generated tags/categories, triggers CI/CD deployment, and sends CRM notifications",
                tags=["publishing", "elasticsearch", "deployment"],
                examples=[
                    '{"action": "publish_article", "article": {"story_id": "story_123", "headline": "...", "content": "...", ...}}',
                    "Publish completed article to production"
                ]
            ),
            AgentSkill(
                id="publishing.article.bulk_publish",
                name="Bulk Publish Articles",
                description="Publishes multiple articles to Elasticsearch in a single bulk operation for efficiency",
                tags=["publishing", "elasticsearch", "bulk"],
                examples=[
                    '{"action": "bulk_publish", "articles": [{"story_id": "story_1", ...}, {"story_id": "story_2", ...}]}',
                    "Bulk publish a batch of articles"
                ]
            ),
            AgentSkill(
                id="publishing.article.unpublish",
                name="Unpublish Article",
                description="Removes article from public view by updating status in Elasticsearch",
                tags=["publishing", "removal"],
                examples=[
                    '{"action": "unpublish_article", "story_id": "story_123"}',
                    "Unpublish article from production"
                ]
            ),
            AgentSkill(
                id="publishing.status",
                name="Get Publication Status",
                description="Returns publication status and records",
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


def create_app(host='localhost', port=8084):
    """Factory function to create the A2A application"""
    agent_card = create_agent_card(host, port)

    request_handler = DefaultRequestHandler(
        agent_executor=PublisherAgentExecutor(),
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
@click.option('--port', 'port', default=8084)
@click.option('--reload', 'reload', is_flag=True, default=False, help='Enable hot reload on file changes')
def main(host, port, reload):
    """Starts the Publisher Agent server."""
    run_agent_server(
        agent_name="Publisher",
        host=host,
        port=port,
        create_app_func=lambda: create_app(host, port),
        logger=logger,
        reload=reload,
        reload_module="agents.publisher:app" if reload else None
    )


if __name__ == "__main__":
    main()

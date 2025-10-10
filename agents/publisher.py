"""
Publisher Agent

Publishes finalized articles to Elasticsearch and handles deployment workflow.
Includes mock CI/CD and CRM notifications, but real Elasticsearch indexing.
"""

import json
import logging
import os
import time
from typing import Dict, Any, List
from datetime import datetime

import click
from elasticsearch import Elasticsearch
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
logger = setup_logger("PUBLISHER")


class PublisherAgent:
    """Publisher Agent - Publishes articles to Elasticsearch and manages deployment"""

    def __init__(self):
        self.published_articles: Dict[str, Dict[str, Any]] = {}
        self.es_client = None
        self.anthropic_client = None
        self.es_index = os.getenv("ELASTIC_ARCHIVIST_INDEX", "news_archive")

        # Initialize Elasticsearch client
        es_endpoint = os.getenv("ELASTICSEARCH_ENDPOINT")
        es_api_key = os.getenv("ELASTIC_SEARCH_API_KEY")

        if es_endpoint and es_api_key:
            try:
                self.es_client = Elasticsearch(
                    es_endpoint,
                    api_key=es_api_key
                )
                # Test connection
                info = self.es_client.info()
                logger.info(f"✅ Connected to Elasticsearch")
                logger.info(f"   Version: {info['version']['number']}")
                logger.info(f"   Index: {self.es_index}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
                self.es_client = None
        else:
            logger.warning("⚠️  Elasticsearch credentials not configured")

        # Initialize Anthropic client using centralized utility
        self.anthropic_client = init_anthropic_client(logger)
        if self.anthropic_client:
            logger.info("(for tag generation)")
        else:
            logger.warning("⚠️  Tags will be empty")

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

            if action == "publish_article":
                return await self._publish_article(query_data)
            elif action == "unpublish_article":
                return await self._unpublish_article(query_data)
            elif action == "get_status":
                return await self._get_status(query_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": ["publish_article", "unpublish_article", "get_status"]
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

    async def _publish_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Publish article to Elasticsearch with CI/CD and CRM workflow"""
        logger.info("📰 Processing article publication...")

        article_data = request.get("article")
        if not article_data:
            logger.error("❌ No article data provided")
            return {
                "status": "error",
                "message": "No article data provided"
            }

        story_id = article_data.get("story_id")
        logger.info(f"📋 Publication details:")
        logger.info(f"   Story ID: {story_id}")
        logger.info(f"   Headline: {article_data.get('headline', 'N/A')[:60]}...")
        logger.info(f"   Word Count: {article_data.get('word_count')}")

        # Check Elasticsearch connection
        if not self.es_client:
            logger.error("❌ Elasticsearch not available")
            return {
                "status": "error",
                "message": "Elasticsearch not configured or unavailable"
            }

        # Generate tags and categories
        logger.info("🏷️  Generating tags and categories...")
        tags, categories = await self._generate_tags_and_categories(article_data)
        logger.info(f"   Tags: {tags}")
        logger.info(f"   Categories: {categories}")

        # Build Elasticsearch document
        logger.info("📦 Building Elasticsearch document...")
        es_document = self._build_es_document(article_data, tags, categories)

        # Mock CI/CD - Step 1: Build
        logger.info("🔨 [MOCK CI/CD] Starting build pipeline...")
        time.sleep(2)  # Simulate build time
        build_number = f"#{int(time.time()) % 10000}"
        logger.info(f"✅ [MOCK CI/CD] Build {build_number} completed successfully")

        # ALWAYS save to local file first (fallback if Elasticsearch fails)
        logger.info(f"💾 Saving article to local file...")
        file_path = await self._save_article_to_file(article_data, tags, categories)
        logger.info(f"✅ Article saved to: {file_path}")

        # Index to Elasticsearch - CRITICAL STEP
        es_success = False
        es_response = None
        logger.info(f"📊 Indexing article to Elasticsearch ({self.es_index})...")
        try:
            es_response = self.es_client.index(
                index=self.es_index,
                id=story_id,  # Use story_id as document ID
                document=es_document
            )
            logger.info(f"✅ Article indexed to Elasticsearch")
            logger.info(f"   Index: {es_response['_index']}")
            logger.info(f"   ID: {es_response['_id']}")
            logger.info(f"   Result: {es_response['result']}")
            es_success = True

        except Exception as e:
            logger.error(f"❌ Elasticsearch indexing failed: {e}", exc_info=True)
            logger.warning(f"⚠️  Article saved to local file but NOT indexed to Elasticsearch")
            # Don't return error - continue with local file publication
            es_success = False

        # Mock CI/CD - Step 2: Deploy
        logger.info("🚀 [MOCK CI/CD] Deploying to production...")
        time.sleep(1.5)  # Simulate deployment time
        logger.info("✅ [MOCK CI/CD] Deployment completed successfully")
        logger.info("   Environment: production")
        logger.info("   URL: https://newsroom.example.com/articles/" + article_data.get('url_slug', story_id))

        # Mock CRM - Notify subscribers
        logger.info("📧 [MOCK CRM] Notifying subscribers...")
        time.sleep(1)  # Simulate CRM processing
        subscriber_count = 1247  # Mock subscriber count
        logger.info(f"✅ [MOCK CRM] Notification sent to {subscriber_count} subscribers")
        logger.info("   Email template: new_article_published")
        logger.info("   Open rate estimate: 42%")

        # Store publication record
        publication_record = {
            "story_id": story_id,
            "headline": article_data.get("headline"),
            "published_at": datetime.now().isoformat(),
            "file_path": file_path,
            "es_index": self.es_index if es_success else None,
            "es_document_id": es_response['_id'] if es_success else None,
            "build_number": build_number,
            "deployment_url": f"https://newsroom.example.com/articles/{article_data.get('url_slug', story_id)}",
            "subscribers_notified": subscriber_count,
            "tags": tags,
            "categories": categories,
            "elasticsearch_indexed": es_success
        }
        self.published_articles[story_id] = publication_record

        if es_success:
            logger.info(f"✅ Publication workflow completed successfully (Elasticsearch + Local File)")
        else:
            logger.info(f"✅ Publication workflow completed (Local File Only - Elasticsearch indexing failed)")
        logger.info(f"   Total published articles: {len(self.published_articles)}")

        result = {
            "status": "success",
            "message": f"Article '{article_data.get('headline')}' published successfully",
            "story_id": story_id,
            "published_at": publication_record["published_at"],
            "file_path": file_path,
            "build_number": build_number,
            "deployment_url": publication_record["deployment_url"],
            "subscribers_notified": subscriber_count,
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
        logger.info("📤 Processing article unpublish request...")

        story_id = request.get("story_id")
        if not story_id:
            logger.error("❌ No story_id provided")
            return {
                "status": "error",
                "message": "No story_id provided"
            }

        logger.info(f"   Story ID: {story_id}")

        # Check Elasticsearch connection
        if not self.es_client:
            logger.error("❌ Elasticsearch not available")
            return {
                "status": "error",
                "message": "Elasticsearch not configured or unavailable"
            }

        # Update document status in Elasticsearch
        try:
            logger.info(f"📊 Updating article status in Elasticsearch...")
            response = self.es_client.update(
                index=self.es_index,
                id=story_id,
                doc={
                    "status": "unpublished",
                    "unpublished_at": datetime.now().isoformat()
                }
            )
            logger.info(f"✅ Article status updated in Elasticsearch")
            logger.info(f"   Result: {response['result']}")

        except Exception as e:
            logger.error(f"❌ Failed to update Elasticsearch: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to unpublish article: {str(e)}",
                "story_id": story_id
            }

        # Mock CI/CD - Remove from production
        logger.info("🔄 [MOCK CI/CD] Removing from production...")
        time.sleep(1)
        logger.info("✅ [MOCK CI/CD] Article removed from production")

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

    async def _generate_tags_and_categories(self, article_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Generate tags and categories from article content using Anthropic"""

        if not self.anthropic_client:
            logger.warning("⚠️  Anthropic not available, returning empty tags/categories")
            return [], []

        headline = article_data.get("headline", "")
        content = article_data.get("content", "")
        topic = article_data.get("topic", "")

        # Build prompt for tag generation
        prompt = f"""Analyze this news article and generate relevant tags and categories.

Headline: {headline}
Topic: {topic}
Content Preview: {content[:500]}...

Generate:
1. Tags: 5-7 specific keywords that describe the article (lowercase, hyphenated if multi-word)
2. Categories: 2-3 broad categories (e.g., "technology", "business", "science", "politics", "sports")

Return your response as a JSON object:
{{
  "tags": ["tag1", "tag2", "tag3", ...],
  "categories": ["category1", "category2", ...]
}}

Return ONLY the JSON, no additional text."""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text

            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)
            tags = result.get("tags", [])
            categories = result.get("categories", [])

            return tags, categories

        except Exception as e:
            logger.error(f"❌ Failed to generate tags/categories: {e}")
            return [], []

    async def _save_article_to_file(self, article_data: Dict[str, Any], tags: List[str], categories: List[str]) -> str:
        """Save article to local markdown file"""
        story_id = article_data.get("story_id")
        topic = article_data.get("topic", "article")
        content = article_data.get("content", "")
        headline = article_data.get("headline", "Untitled")

        # Create articles directory if it doesn't exist
        articles_dir = "articles"
        os.makedirs(articles_dir, exist_ok=True)

        # Generate filename from topic and story_id
        filename = topic.lower().replace(" ", "-").replace(":", "").replace(",", "")
        filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_'))
        filepath = os.path.join(articles_dir, f"{filename}-{story_id}.md")

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
                logger.warning(f"Could not calculate workflow duration: {e}")

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
            "research_data": article_data.get("research_data", []),
            "editorial_review": article_data.get("editorial_review"),
            "archive_references": article_data.get("archive_references"),
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


class PublisherAgentExecutor(AgentExecutor):
    """AgentExecutor for the Publisher agent following official A2A pattern"""

    def __init__(self):
        self.agent = PublisherAgent()

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
        description="Publishes finalized articles to Elasticsearch, handles CI/CD deployment, and sends CRM notifications",
        url=f"http://{host}:{port}",
        version="1.0.0",
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/publisher-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=True,
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

    return server.build()


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

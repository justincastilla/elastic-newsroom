"""
Editor Agent

Reviews article drafts for grammar, tone, consistency, and length.
Provides detailed editorial feedback and suggested edits.
"""

import json
import logging
import os
import re
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
from utils import setup_logger, load_env_config, init_anthropic_client, extract_json_from_llm_response, run_agent_server
from agents.base_agent import BaseAgent

# Load environment variables
load_env_config()

# Configure logging using centralized utility
logger = setup_logger("EDITOR")

# Singleton instance for maintaining state across requests
_editor_agent_instance = None

class EditorAgent(BaseAgent):
    """Editor Agent - Reviews drafts and provides editorial feedback"""

    def __init__(self):
        # Initialize base agent with logger
        super().__init__(logger)

        self.reviews: Dict[str, Dict[str, Any]] = {}
        self.drafts_under_review: Dict[str, Dict[str, Any]] = {}

        # Initialize Anthropic client using centralized utility (from BaseAgent)
        self._init_anthropic_client()

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

            if action == "review_draft":
                return await self._review_draft(query_data)
            elif action == "get_review":
                return await self._get_review(query_data)
            elif action == "get_status":
                return await self._get_status(query_data)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "available_actions": ["review_draft", "get_review", "get_status"]
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

    async def _review_draft(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Review a draft from the Reporter"""
        logger.info("📝 Processing draft review request...")
        draft = request.get("draft", {})

        # Validate draft
        if not draft:
            logger.error("❌ No draft data provided")
            return {
                "status": "error",
                "message": "No draft data provided"
            }

        story_id = draft.get("story_id")
        if not story_id:
            logger.error("❌ Draft missing story_id")
            return {
                "status": "error",
                "message": "Draft missing story_id"
            }

        content = draft.get("content")
        if not content:
            logger.error("❌ Draft missing content")
            return {
                "status": "error",
                "message": "Draft missing content"
            }

        logger.info(f"📋 Draft details:")
        logger.info(f"   Story ID: {story_id}")
        logger.info(f"   Word Count: {draft.get('word_count')}")
        logger.info(f"   Target Length: {draft.get('assignment', {}).get('target_length')}")

        # Store draft under review
        self.drafts_under_review[story_id] = {
            **draft,
            "received_at": datetime.now().isoformat(),
            "review_status": "reviewing"
        }

        # Publish event: review started
        await self._publish_event(
            event_type="review_started",
            story_id=story_id,
            data={
                "word_count": draft.get("word_count"),
                "target_length": draft.get("assignment", {}).get("target_length")
            }
        )

        # Perform review
        try:
            logger.info("🤖 Calling Anthropic API to review article...")
            review_result = await self._perform_review(draft)
            logger.info(f"✅ Review completed")

            # Store review
            review_id = f"review_{story_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            review_record = {
                "review_id": review_id,
                "story_id": story_id,
                "reviewed_at": datetime.now().isoformat(),
                "original_word_count": draft.get("word_count"),
                "target_length": draft.get("assignment", {}).get("target_length"),
                "review": review_result,
                "status": "completed"
            }
            self.reviews[review_id] = review_record

            # Update draft status
            self.drafts_under_review[story_id]["review_status"] = "completed"
            self.drafts_under_review[story_id]["review_id"] = review_id

            # Publish event: review completed
            await self._publish_event(
                event_type="review_completed",
                story_id=story_id,
                data={
                    "approval_status": review_result.get("approval_status"),
                    "suggested_edits_count": len(review_result.get("suggested_edits", []))
                }
            )

            logger.info(f"✅ Review stored successfully")
            logger.info(f"   Review ID: {review_id}")
            logger.info(f"   Total reviews: {len(self.reviews)}")

            return {
                "status": "success",
                "message": "Draft review completed",
                "review_id": review_id,
                "story_id": story_id,
                "review": review_result,
                "original_draft": content[:200] + "..." if len(content) > 200 else content
            }

        except Exception as e:
            logger.error(f"❌ Error performing review: {e}", exc_info=True)
            self.drafts_under_review[story_id]["review_status"] = "error"
            return {
                "status": "error",
                "message": f"Failed to review draft: {str(e)}",
                "story_id": story_id
            }

    async def _perform_review(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Perform editorial review using Anthropic Claude"""
        content = draft.get("content", "")
        assignment = draft.get("assignment", {})
        target_length = assignment.get("target_length", 1000)
        current_word_count = draft.get("word_count", len(content.split()))

        # Build review prompt
        prompt = f"""You are a professional editor for Elastic News, a technology news publication.

Please review the following article draft and provide detailed editorial feedback.

ARTICLE DRAFT:
{content}

ASSIGNMENT DETAILS:
- Target Length: {target_length} words
- Current Word Count: {current_word_count} words
- Topic: {assignment.get('topic', 'N/A')}
- Angle: {assignment.get('angle', 'N/A')}

REVIEW CRITERIA:
1. Grammar & Spelling: Check for grammatical errors, typos, and spelling mistakes
2. Professional Tone: Ensure the tone is professional, objective, and appropriate for a tech news publication
3. Consistency: Check for consistent terminology, voice, and style throughout
4. Length: The article should be within 50 words of the target length ({target_length - 50} to {target_length + 50} words)

Please provide your review in the following JSON format:
{{
  "overall_assessment": "brief overall assessment (1-2 sentences)",
  "grammar_issues": [
    {{"issue": "description of grammar issue", "location": "quote from article", "suggestion": "corrected version"}}
  ],
  "tone_issues": [
    {{"issue": "description of tone issue", "location": "quote from article", "suggestion": "improved version"}}
  ],
  "consistency_issues": [
    {{"issue": "description of consistency issue", "location": "quote from article", "suggestion": "consistent version"}}
  ],
  "length_assessment": {{
    "current_length": {current_word_count},
    "target_length": {target_length},
    "difference": {current_word_count - target_length},
    "meets_requirement": {"true" if abs(current_word_count - target_length) <= 50 else "false"},
    "recommendation": "specific recommendation about length adjustment"
  }},
  "suggested_edits": [
    {{"type": "grammar|tone|consistency|length", "original": "original text", "suggested": "suggested replacement", "reason": "why this change is needed"}}
  ],
  "approval_status": "approved|needs_minor_revisions|needs_major_revisions",
  "editor_notes": "additional notes or recommendations for the reporter"
}}

Provide only the JSON response, no additional text."""

        # Use Anthropic if available, otherwise mock
        if self.anthropic_client:
            try:
                message = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,  # Increased from 3000 to handle longer JSON responses
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Parse the JSON response using centralized utility
                review_text = message.content[0].text
                review_data = extract_json_from_llm_response(review_text, logger)
                
                if review_data:
                    return review_data
                else:
                    # If JSON extraction failed, return mock review
                    logger.warning("Failed to extract JSON from LLM response, returning mock review")
                    return self._generate_mock_review(current_word_count, target_length)

            except Exception as e:
                logger.error(f"Anthropic API error: {e}", exc_info=True)
                return self._generate_mock_review(current_word_count, target_length)
        else:
            return self._generate_mock_review(current_word_count, target_length)

    def _generate_mock_review(self, current_word_count: int, target_length: int) -> Dict[str, Any]:
        """Generate a simple mock review when Anthropic API is not available"""
        difference = current_word_count - target_length
        meets_requirement = abs(difference) <= 50

        return {
            "overall_assessment": "Article is well-structured but requires some minor revisions for publication.",
            "grammar_issues": [
                {
                    "issue": "Missing comma in compound sentence",
                    "location": "[Mock location - API key not configured]",
                    "suggestion": "[Mock suggestion - API key not configured]"
                }
            ],
            "tone_issues": [],
            "consistency_issues": [],
            "length_assessment": {
                "current_length": current_word_count,
                "target_length": target_length,
                "difference": difference,
                "meets_requirement": meets_requirement,
                "recommendation": f"Article is {'within acceptable range' if meets_requirement else f'{abs(difference)} words too {"long" if difference > 0 else "short"} - please adjust'}"
            },
            "suggested_edits": [
                {
                    "type": "grammar",
                    "original": "[Mock - ANTHROPIC_API_KEY not configured]",
                    "suggested": "[Mock suggestion]",
                    "reason": "This is a mock review. Configure ANTHROPIC_API_KEY for real reviews."
                }
            ],
            "approval_status": "needs_minor_revisions" if not meets_requirement else "approved",
            "editor_notes": "Mock review generated. Please configure ANTHROPIC_API_KEY for actual editorial review."
        }

    async def _get_review(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific review by review_id or story_id"""
        review_id = request.get("review_id")
        story_id = request.get("story_id")

        if review_id:
            if review_id not in self.reviews:
                return {
                    "status": "error",
                    "message": f"Review {review_id} not found"
                }
            return {
                "status": "success",
                "review": self.reviews[review_id]
            }
        elif story_id:
            # Find review by story_id
            matching_reviews = [r for r in self.reviews.values() if r["story_id"] == story_id]
            if not matching_reviews:
                return {
                    "status": "error",
                    "message": f"No review found for story_id: {story_id}"
                }
            return {
                "status": "success",
                "reviews": matching_reviews
            }
        else:
            return {
                "status": "error",
                "message": "Either review_id or story_id must be provided"
            }

    async def _get_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get current status of all reviews"""
        return {
            "status": "success",
            "total_reviews": len(self.reviews),
            "drafts_under_review": len(self.drafts_under_review),
            "reviews": list(self.reviews.values()),
            "drafts": list(self.drafts_under_review.values())
        }


def get_editor_agent() -> EditorAgent:
    """Get singleton EditorAgent instance to maintain state across requests"""
    global _editor_agent_instance
    if _editor_agent_instance is None:
        _editor_agent_instance = EditorAgent()
    return _editor_agent_instance


class EditorAgentExecutor(AgentExecutor):
    """AgentExecutor for the Editor agent following official A2A pattern"""

    def __init__(self):
        # Use singleton instance to maintain state across requests
        self.agent = get_editor_agent()

    async def execute(self, context, event_queue) -> None:
        """Execute the agent request"""
        logger.info('Executing Editor agent')

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
    """Create the Editor agent card"""
    return AgentCard(
        name="Editor",
        description="Reviews article drafts for grammar, tone, consistency, and length. Works through News Chief for workflow coordination.",
        url=f"http://{host}:{port}",
        version="1.0.0",
        protocol_version="0.3.0",  # A2A Protocol version
        preferred_transport="JSONRPC",
        documentation_url="https://github.com/elastic/elastic-news/blob/main/docs/editor-agent.md",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,  # Not implemented yet
            state_transition_history=True,
            max_concurrent_tasks=20
        ),
        skills=[
            AgentSkill(
                id="editorial.review.draft_review",
                name="Review Draft",
                description="Reviews article drafts for grammar, professional tone, consistency, and appropriate length",
                tags=["editing", "review", "quality-control"],
                examples=[
                    '{"action": "review_draft", "draft": {"story_id": "story_123", "content": "...", "word_count": 950, "assignment": {"target_length": 1000}}}',
                    "Review draft for publication readiness"
                ]
            ),
            AgentSkill(
                id="editorial.review.get_review",
                name="Get Review",
                description="Retrieves a specific review by review_id or story_id",
                tags=["review", "retrieval"],
                examples=[
                    '{"action": "get_review", "review_id": "review_story_123_20250107_120000"}',
                    '{"action": "get_review", "story_id": "story_123"}'
                ]
            ),
            AgentSkill(
                id="editorial.review.status",
                name="Get Status",
                description="Returns current status of all reviews and drafts under review",
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


def create_app(host='localhost', port=8082):
    """Factory function to create the A2A application"""
    # Create agent card using the single source of truth
    agent_card = create_agent_card(host, port)

    # Set up the request handler
    request_handler = DefaultRequestHandler(
        agent_executor=EditorAgentExecutor(),
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
@click.option('--port', 'port', default=8082)
@click.option('--reload', 'reload', is_flag=True, default=False, help='Enable hot reload on file changes')
def main(host, port, reload):
    """Starts the Editor Agent server."""
    run_agent_server(
        agent_name="Editor",
        host=host,
        port=port,
        create_app_func=lambda: create_app(host, port),
        logger=logger,
        reload=reload,
        reload_module="agents.editor:app" if reload else None
    )


if __name__ == "__main__":
    main()

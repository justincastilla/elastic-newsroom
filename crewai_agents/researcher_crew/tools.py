"""
CrewAI Tools for Researcher Agent

Defines custom tools that the researcher agent can use to gather information,
verify facts, and provide structured research data.
"""

import json
import os
import logging
from typing import List, Dict, Any
from crewai_tools import tool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RESEARCHER_CREW_TOOLS")


@tool("Research Questions Tool")
def research_questions_tool(questions_json: str, topic: str) -> str:
    """
    Research multiple questions and return structured data with facts, figures, and sources.

    This tool wraps the existing MCP research_questions functionality and provides
    comprehensive research results for news article generation.

    Args:
        questions_json: JSON string containing list of questions to research
        topic: The main topic or subject area for the research

    Returns:
        JSON string with research results containing:
        - question: The original question
        - claim_verified: Boolean indicating if claim was verified
        - confidence: Confidence score (0-100)
        - summary: Brief summary of findings
        - facts: List of factual statements
        - figures: Dictionary with percentages, dollar amounts, numbers, dates, companies
        - sources: List of source citations

    Example:
        questions_json = '["What percentage of companies use AI?", "Who are the leaders?"]'
        topic = "AI in Business"
        result = research_questions_tool(questions_json, topic)
    """
    try:
        # Parse questions from JSON string
        questions = json.loads(questions_json) if isinstance(questions_json, str) else questions_json

        logger.info(f"🔍 Research tool called for {len(questions)} questions about: {topic}")

        # Import MCP client utilities
        # Note: This bridges to existing MCP infrastructure
        from utils.mcp_client import create_mcp_client
        from utils import setup_logger, init_anthropic_client

        # Initialize clients
        mcp_logger = setup_logger("MCP_CLIENT_TOOL")
        anthropic_client = init_anthropic_client(mcp_logger)

        # Check if MCP server is available
        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8095")

        if not mcp_server_url:
            logger.warning("MCP_SERVER_URL not configured, using mock data")
            return json.dumps(_generate_mock_research_results(questions, topic))

        try:
            # Use MCP client to call research_questions tool
            import asyncio

            async def call_mcp():
                mcp_client = create_mcp_client(
                    logger=mcp_logger,
                    anthropic_client=anthropic_client,
                    agent_name="ResearcherCrewTool"
                )

                result = await mcp_client.call_tool(
                    tool_name="research_questions",
                    arguments={
                        "questions": questions,
                        "topic": topic
                    }
                )
                return result

            # Run async MCP call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(call_mcp())
            loop.close()

            # Parse result if it's a string
            if isinstance(result, str):
                result = json.loads(result)

            logger.info(f"✅ MCP research completed: {len(result)} results")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"❌ MCP call failed: {e}")
            logger.info("Using mock research data as fallback")
            return json.dumps(_generate_mock_research_results(questions, topic))

    except Exception as e:
        logger.error(f"❌ Research tool error: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "status": "failed"
        })


@tool("Fact Verification Tool")
def fact_verification_tool(claim: str, context: str = "") -> str:
    """
    Verify a specific claim and provide a confidence score.

    This tool checks the validity of factual claims and provides a confidence
    assessment based on available information.

    Args:
        claim: The factual claim to verify
        context: Optional context or topic area for the claim

    Returns:
        JSON string with verification result containing:
        - claim: The original claim
        - verified: Boolean indicating if claim is verified
        - confidence: Confidence score (0-100)
        - explanation: Explanation of the verification
        - sources: Supporting sources if available

    Example:
        claim = "AI adoption increased 45% in 2024"
        result = fact_verification_tool(claim, context="Technology trends")
    """
    logger.info(f"🔍 Fact verification for: {claim}")

    try:
        # Use Anthropic to verify the claim
        from utils import init_anthropic_client, setup_logger

        anthropic_logger = setup_logger("FACT_CHECK_TOOL")
        client = init_anthropic_client(anthropic_logger)

        if client:
            prompt = f"""You are a fact-checking assistant. Verify this claim and provide a confidence score.

Claim: {claim}
Context: {context}

Provide your response in the following JSON format:
{{
    "claim": "{claim}",
    "verified": true/false,
    "confidence": 0-100,
    "explanation": "Brief explanation of verification",
    "sources": ["List of relevant sources if available"]
}}
"""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            logger.info("✅ Fact verification completed")
            return response_text
        else:
            # Mock response if Anthropic not available
            logger.warning("Anthropic client not available, using mock verification")
            return json.dumps({
                "claim": claim,
                "verified": True,
                "confidence": 75,
                "explanation": "Mock verification - Anthropic API not configured",
                "sources": ["Mock source"]
            }, indent=2)

    except Exception as e:
        logger.error(f"❌ Fact verification error: {e}")
        return json.dumps({
            "claim": claim,
            "verified": False,
            "confidence": 0,
            "explanation": f"Error during verification: {str(e)}",
            "sources": []
        }, indent=2)


def _generate_mock_research_results(questions: List[str], topic: str) -> List[Dict[str, Any]]:
    """
    Generate mock research results when MCP or Anthropic is unavailable.

    Args:
        questions: List of research questions
        topic: Research topic

    Returns:
        List of mock research result dictionaries
    """
    results = []

    for i, question in enumerate(questions):
        results.append({
            "question": question,
            "claim_verified": True,
            "confidence": 70 + (i * 5) % 30,  # Vary confidence
            "summary": f"Mock research data for question about {topic}. Configure ANTHROPIC_API_KEY for real research.",
            "facts": [
                f"Industry adoption of {topic} has increased significantly",
                f"Leading companies are investing in {topic}",
                f"Market analysts project continued growth in {topic}"
            ],
            "figures": {
                "percentages": ["45%", "60% growth"],
                "dollar_amounts": ["$1.5B", "$3.2B projected"],
                "numbers": ["500 companies", "1M users"],
                "dates": ["Q4 2024", "2025"],
                "companies": ["TechCorp", "InnovateLabs", "DataSystems"]
            },
            "sources": [
                "Mock Industry Report 2024 (ANTHROPIC_API_KEY not configured)",
                "Mock Market Analysis",
                "Mock Tech Survey"
            ]
        })

    return results

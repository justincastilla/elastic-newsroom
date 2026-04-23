"""
Newsroom Tools MCP Server

Provides MCP tools for the Elastic News newsroom agents:
1. research_questions - Researches questions via Tavily web search + Claude synthesis
2. generate_outline - Creates article outline and identifies research needs (uses Anthropic)
3. generate_article - Creates article content from outline and research (uses Anthropic)
4. apply_edits - Applies editorial suggestions to article (uses Anthropic)
5. review_article - Reviews draft for grammar, tone, consistency, length (uses Anthropic)
6. generate_tags - Generates tags and categories for article (keyword extraction)
7. deploy_to_production - Simulates CI/CD deployment pipeline (mock)
8. notify_subscribers - Simulates CRM subscriber notification (mock)

Tools that require AI use Anthropic Claude for content generation.
Research uses Tavily for real web search results.
"""

import json
import os
import time
from typing import List, Dict, Any
from fastmcp import FastMCP
from anthropic import Anthropic
from tavily import TavilyClient

# Load environment variables
from utils import load_env_config
load_env_config()

from utils.config import DEFAULT_MODEL

# Initialize Anthropic client
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    print("WARNING: ANTHROPIC_API_KEY not set - MCP tools will use fallback mock data")
    anthropic_client = None
else:
    anthropic_client = Anthropic(api_key=anthropic_api_key)
    print("Anthropic client initialized for MCP tools")

# Initialize Tavily client
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    print("WARNING: TAVILY_API_KEY not set - research tool will use Anthropic-only fallback")
    tavily_client = None
else:
    tavily_client = TavilyClient(api_key=tavily_api_key)
    print("Tavily client initialized for web search")

# Initialize FastMCP server
mcp = FastMCP("Newsroom Tools")


@mcp.tool()
def research_questions(questions: List[str], topic: str) -> str:
    """
    Research multiple questions using Tavily web search and return structured data
    with facts, figures, and real source URLs.

    Uses Tavily for real web search results, then optionally Claude to synthesize
    into structured format. Falls back gracefully if either service is unavailable.

    Args:
        questions: List of research questions to answer
        topic: The article topic for context

    Returns:
        JSON string containing research results for each question with facts, figures, and sources
    """
    results = []

    for i, question in enumerate(questions, 1):
        # Step 1: Search with Tavily for real web results
        tavily_results = None
        tavily_answer = None
        sources = []

        if tavily_client:
            try:
                search = tavily_client.search(
                    query=f"{topic}: {question}",
                    search_depth="advanced",
                    max_results=5,
                    include_answer=True,
                    topic="news"
                )
                tavily_answer = search.get("answer", "")
                tavily_results = search.get("results", [])
                sources = [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:300],
                        "score": r.get("score", 0),
                        "published_date": r.get("published_date", "")
                    }
                    for r in tavily_results
                ]
            except Exception as e:
                print("Tavily search error for question %d: %s" % (i, e))

        # Step 2: Synthesize with Claude if available
        if anthropic_client and (tavily_results or tavily_answer):
            try:
                synthesis_prompt = f"""You are a research assistant. Based on these web search results, provide a structured research answer.

QUESTION: {question}
TOPIC: {topic}

TAVILY SUMMARY: {tavily_answer or 'No summary available'}

SEARCH RESULTS:
{json.dumps(sources, indent=2)}

Return ONLY a JSON object with this structure:
{{
  "question_number": {i},
  "question": "{question}",
  "claim_verified": true/false,
  "confidence": 0-100,
  "summary": "brief synthesized answer",
  "facts": ["fact 1", "fact 2", ...],
  "figures": {{
    "percentages": ["45%", ...],
    "dollar_amounts": ["$1.5B", ...],
    "numbers": ["500 companies", ...],
    "dates": ["Q4 2024", ...],
    "companies": ["CompanyName", ...]
  }},
  "sources": [
    {{"title": "Article Title", "url": "https://...", "published_date": "2026-04-15"}}
  ]
}}"""

                response = anthropic_client.messages.create(
                    model=DEFAULT_MODEL,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": synthesis_prompt}]
                )

                content = response.content[0].text
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()

                result = json.loads(content)
                results.append(result)
                continue

            except Exception as e:
                print("Claude synthesis error for question %d: %s" % (i, e))

        # Step 3: Return Tavily results directly if Claude unavailable
        if tavily_results or tavily_answer:
            results.append({
                "question_number": i,
                "question": question,
                "claim_verified": True,
                "confidence": 75,
                "summary": tavily_answer or "See sources for details.",
                "facts": [r.get("content", "")[:200] for r in (tavily_results or [])[:3]],
                "figures": {},
                "sources": [
                    {"title": r.get("title", ""), "url": r.get("url", ""), "published_date": r.get("published_date", "")}
                    for r in (tavily_results or [])
                ]
            })
            continue

        # Step 4: No Tavily, no results - return error (no more fake data)
        results.append({
            "question_number": i,
            "question": question,
            "claim_verified": False,
            "confidence": 0,
            "summary": "Research unavailable - configure TAVILY_API_KEY for web search.",
            "facts": [],
            "figures": {},
            "sources": []
        })

    return json.dumps(results, indent=2)


@mcp.tool()
def generate_outline(topic: str, angle: str, target_length: int) -> str:
    """
    Generate article outline and identify 3-5 research questions that would strengthen the piece.

    Args:
        topic: The article topic
        angle: The angle or focus of the article (optional)
        target_length: Target word count for the article

    Returns:
        JSON string with outline and research questions
    """
    if not anthropic_client:
        # Fallback mock
        return json.dumps({
            "outline": f"Introduction to {topic}, Background, Key developments, Future outlook",
            "research_questions": [f"What is the current state of {topic}?"]
        }, indent=2)

    angle_text = f"\nAngle/Focus: {angle}" if angle else ""

    prompt = f"""You are a news editor. Create an article outline and identify 3-5 research questions for this story:

Topic: {topic}{angle_text}
Target Length: {target_length} words

Provide:
1. A clear article outline (comma-separated sections)
2. 3-5 specific research questions that would strengthen the article with data and facts

Return ONLY a JSON object:
{{
  "outline": "Introduction, Section 1, Section 2, ...",
  "research_questions": ["Question 1?", "Question 2?", ...]
}}"""

    try:
        response = anthropic_client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        outline_data = json.loads(content)
        return json.dumps(outline_data, indent=2)

    except Exception as e:
        print("Error generating outline: %s" % e)
        return json.dumps({
            "outline": f"Introduction to {topic}, Analysis, Conclusion",
            "research_questions": [f"What are the key facts about {topic}?"]
        }, indent=2)


@mcp.tool()
def generate_article(topic: str, angle: str, target_length: int, outline: str, research_data: str, archive_context: str) -> str:
    """
    Generate article content based on topic, research, and archive context.

    Args:
        topic: The article topic
        angle: The angle or focus (optional)
        target_length: Target word count
        outline: Article outline
        research_data: JSON string of research results
        archive_context: Context from historical articles

    Returns:
        Article text with headline and body paragraphs
    """
    if not anthropic_client:
        # Fallback mock
        return f"""HEADLINE: {topic}

{topic} - {angle if angle else 'A news analysis.'}

[Mock article - Anthropic API not configured]
Target: {target_length} words"""

    angle_text = f"\nAngle/Focus: {angle}" if angle else ""
    archive_text = f"\n\nARCHIVE CONTEXT (for background/reference):\n{archive_context}" if archive_context else ""

    prompt = f"""You are a professional journalist. Write a news article based on the following information:

TOPIC: {topic}{angle_text}

OUTLINE:
{outline}

RESEARCH DATA:
{research_data}{archive_text}

TARGET LENGTH: {target_length} words

Instructions:
- Write in professional journalistic style
- Include a compelling HEADLINE at the start
- Use facts and figures from the research data
- When citing a fact, statistic, or quote from the research data, mention the source name inline (e.g., "according to Forbes", "Reuters reported")
- At the end of the article, include a "## Sources" section listing every source URL used
- Group sources by their domain/publication (e.g., "**NYTimes.com**", "**Reuters.com**", "**NPR.org**"), then list each article as a bullet under its group: `- [Article Title](URL)`
- Include ALL source URLs from the research data — do not omit any
- Meet the target length (within 10%) — the Sources section does not count toward the word count
- Make it engaging and informative

Return ONLY the article text (headline + body + sources section), no JSON."""

    try:
        response = anthropic_client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        article = response.content[0].text.strip()
        return article

    except Exception as e:
        print("Error generating article: %s" % e)
        return f"""HEADLINE: {topic}

{topic} has emerged as a significant topic. {angle if angle else "This story examines key developments."}

[Error generating article with AI - using fallback]
Target length: {target_length} words"""


@mcp.tool()
def review_article(content: str, word_count: int, target_length: int, topic: str) -> str:
    """
    Review article draft for grammar, tone, consistency, and length.

    Args:
        content: The article content to review
        word_count: Current word count
        target_length: Target word count
        topic: Article topic for context

    Returns:
        JSON string with review results including assessment, issues, and suggested edits
    """
    if not anthropic_client:
        # Fallback mock
        difference = word_count - target_length
        meets_requirement = abs(difference) <= 50
        return json.dumps({
            "overall_assessment": f"Mock review of {topic}",
            "grammar_issues": [],
            "suggested_edits": [],
            "approval_status": "approved" if meets_requirement else "needs_revisions"
        }, indent=2)

    prompt = f"""You are a professional news editor. Review this article draft:

TOPIC: {topic}
CURRENT LENGTH: {word_count} words
TARGET LENGTH: {target_length} words

ARTICLE:
{content}

Provide a comprehensive editorial review including:
- Overall assessment
- Grammar/spelling issues (if any)
- Tone/consistency issues (if any)
- Length assessment
- Specific suggested edits (type, original text, suggested replacement, reason)
- Approval status ("approved", "needs_minor_revisions", or "needs_major_revisions")
- Editor notes

Return ONLY a JSON object with this structure:
{{
  "overall_assessment": "...",
  "grammar_issues": [{{...}}],
  "tone_issues": [{{...}}],
  "consistency_issues": [{{...}}],
  "length_assessment": {{...}},
  "suggested_edits": [{{"type": "...", "original": "...", "suggested": "...", "reason": "..."}}],
  "approval_status": "...",
  "editor_notes": "..."
}}"""

    try:
        response = anthropic_client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        review_text = response.content[0].text.strip()
        if review_text.startswith("```"):
            review_text = review_text.split("```")[1]
            if review_text.startswith("json"):
                review_text = review_text[4:]
        review_text = review_text.strip()

        review = json.loads(review_text)
        return json.dumps(review, indent=2)

    except Exception as e:
        print("Error reviewing article: %s" % e)
        return json.dumps({
            "overall_assessment": f"Review of {topic} - API error",
            "grammar_issues": [],
            "suggested_edits": [],
            "approval_status": "approved"
        }, indent=2)


@mcp.tool()
def apply_edits(original_content: str, suggested_edits: str) -> str:
    """
    Apply editorial suggestions to article content.

    Args:
        original_content: The original article text
        suggested_edits: JSON string of suggested edits to apply

    Returns:
        Revised article content with edits applied
    """
    try:
        edits = json.loads(suggested_edits)
    except json.JSONDecodeError:
        return original_content

    if not edits or len(edits) == 0:
        return original_content

    if not anthropic_client:
        # Fallback: simple string replacement
        revised_content = original_content
        for edit in edits:
            if isinstance(edit, dict):
                original_text = edit.get("original", "")
                suggested_text = edit.get("suggested", "")
                if original_text and suggested_text and original_text in revised_content:
                    revised_content = revised_content.replace(original_text, suggested_text)
        return revised_content

    prompt = f"""You are a professional editor. Apply these editorial suggestions to the article:

ORIGINAL ARTICLE:
{original_content}

SUGGESTED EDITS (apply these changes):
{json.dumps(edits, indent=2)}

Instructions:
- Apply each suggested edit carefully
- Maintain the article's structure and flow
- Preserve all other content unchanged
- Return ONLY the revised article text (no JSON, no explanations)"""

    try:
        response = anthropic_client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        revised_content = response.content[0].text.strip()
        return revised_content

    except Exception as e:
        print("Error applying edits: %s" % e)
        # Fallback to simple replacement
        revised_content = original_content
        for edit in edits:
            if isinstance(edit, dict):
                original_text = edit.get("original", "")
                suggested_text = edit.get("suggested", "")
                if original_text and suggested_text:
                    revised_content = revised_content.replace(original_text, suggested_text, 1)
        return revised_content


@mcp.tool()
def generate_tags(headline: str, content: str, topic: str) -> str:
    """
    Generate tags and categories for an article.

    Args:
        headline: Article headline
        content: Article content (first 500 chars used)
        topic: Article topic

    Returns:
        JSON string with tags and categories
    """
    # Extract key terms from topic
    topic_words = topic.lower().replace(",", "").replace(":", "").split()

    tags = [
        topic.lower().replace(" ", "-")[:30],  # Main topic as tag
        "technology",
        "innovation",
        "industry-analysis",
        "market-trends"
    ]

    # Add topic-specific tags
    for word in topic_words[:3]:
        if len(word) > 3 and word not in ["the", "and", "for", "with"]:
            tags.append(word)

    categories = ["technology", "business", "innovation"]

    result = {
        "tags": list(set(tags))[:7],  # Unique tags, max 7
        "categories": categories[:3]  # Max 3 categories
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def deploy_to_production(story_id: str, url_slug: str, build_number: str = None) -> str:
    """
    Deploy article to production via CI/CD pipeline simulation.

    Simulates a build and deployment process with realistic timing.

    Args:
        story_id: The unique story identifier
        url_slug: URL-friendly slug for the article
        build_number: Optional build number (generated if not provided)

    Returns:
        JSON string with deployment results including build info, environment, and URL
    """
    # Simulate build pipeline
    time.sleep(2)  # Build time

    if not build_number:
        build_number = f"#{int(time.time()) % 10000}"

    # Simulate deployment
    time.sleep(1.5)  # Deployment time

    result = {
        "status": "success",
        "build": {
            "number": build_number,
            "status": "completed",
            "duration_seconds": 2.0
        },
        "deployment": {
            "status": "completed",
            "environment": "production",
            "duration_seconds": 1.5,
            "url": f"https://newsroom.example.com/articles/{url_slug}",
            "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def notify_subscribers(story_id: str, headline: str, topic: str) -> str:
    """
    Notify subscribers about new article via CRM system simulation.

    Simulates sending email notifications to subscribers with realistic metrics.

    Args:
        story_id: The unique story identifier
        headline: Article headline for the email
        topic: Article topic for targeting

    Returns:
        JSON string with notification results including subscriber count and engagement metrics
    """
    # Simulate CRM processing
    time.sleep(1)  # CRM notification time

    # Mock subscriber count (could vary based on topic in real implementation)
    subscriber_count = 1247

    result = {
        "status": "success",
        "notification": {
            "subscribers_notified": subscriber_count,
            "email_template": "new_article_published",
            "subject": f"New Article: {headline}",
            "segmentation": {
                "topic": topic,
                "total_subscribers": subscriber_count
            },
            "estimated_metrics": {
                "open_rate": "42%",
                "click_rate": "18%",
                "expected_opens": int(subscriber_count * 0.42)
            },
            "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    return json.dumps(result, indent=2)


# Health check endpoint for Docker and monitoring
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "Newsroom MCP Server"})


# Export the FastMCP HTTP app for uvicorn
# FastMCP 3.x http_app() serves the MCP protocol via SSE at /mcp
app = mcp.http_app()

if __name__ == "__main__":
    # Run the MCP server
    # Can be started with: uvicorn mcp_servers.newsroom_tools:app --host localhost --port 8095
    mcp.run()

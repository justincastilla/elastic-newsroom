"""
CrewAI Task Definitions for Researcher Crew

Defines the research tasks that agents can perform.
Tasks specify what needs to be done, expected outputs, and context.
"""

from crewai import Task, Agent
from typing import List, Dict, Any, Optional


def create_research_task(
    agent: Agent,
    questions: List[str],
    topic: str,
    story_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Task:
    """
    Creates a research task that answers multiple questions about a topic.

    This task maps to the current ResearcherAgent._research_questions() action,
    providing comprehensive research results for news article generation.

    Args:
        agent: The researcher agent who will perform this task
        questions: List of research questions to answer
        topic: The main topic or subject area
        story_id: Unique identifier for the story being researched
        context: Optional additional context for the research

    Returns:
        CrewAI Task configured for research execution

    Expected Output:
        JSON array with research results for each question containing:
        - question: The original question
        - claim_verified: Boolean verification status
        - confidence: Confidence score (0-100)
        - summary: Brief summary of findings
        - facts: List of factual statements
        - figures: Dictionary with statistics, dates, companies, etc.
        - sources: List of source citations
    """
    if context is None:
        context = {}

    # Format questions for the task description
    questions_formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

    task_description = f"""
Research the following questions about {topic}:

{questions_formatted}

For each question, you must:
1. Investigate the question thoroughly using available tools
2. Verify any claims or statements
3. Gather specific facts, statistics, figures, and data points
4. Provide confidence scores for your findings
5. Cite credible sources
6. Structure your results in the required JSON format

Context:
- Story ID: {story_id}
- Topic: {topic}
- Number of questions: {len(questions)}

Use the research_questions_tool to gather information efficiently.
"""

    expected_output = """
A JSON array containing research results for each question with this structure:
[
  {
    "question": "The original question",
    "claim_verified": true/false,
    "confidence": 0-100,
    "summary": "Brief summary of findings",
    "facts": ["List of factual statements"],
    "figures": {
      "percentages": ["45%", "60% growth"],
      "dollar_amounts": ["$1.5B", "$3.2B"],
      "numbers": ["500 companies", "1M users"],
      "dates": ["Q4 2024", "2025"],
      "companies": ["Company A", "Company B"]
    },
    "sources": ["Source 1", "Source 2", "Source 3"]
  }
]
"""

    return Task(
        description=task_description,
        agent=agent,
        expected_output=expected_output,
        context_data={
            "story_id": story_id,
            "topic": topic,
            "questions": questions,
            **context
        }
    )


def create_fact_check_task(
    agent: Agent,
    claims: List[str],
    topic: str,
    story_id: str
) -> Task:
    """
    Creates a fact-checking task to verify specific claims.

    This is an optional specialized task for enhanced fact verification.

    Args:
        agent: The fact-checker agent who will perform this task
        claims: List of claims to verify
        topic: The main topic or subject area
        story_id: Unique identifier for the story

    Returns:
        CrewAI Task configured for fact-checking execution
    """
    claims_formatted = "\n".join([f"{i+1}. {c}" for i, c in enumerate(claims)])

    task_description = f"""
Verify the following claims related to {topic}:

{claims_formatted}

For each claim:
1. Assess the accuracy and credibility
2. Provide a confidence score (0-100)
3. Explain your verification reasoning
4. Cite supporting sources if available

Use the fact_verification_tool for each claim.
"""

    expected_output = """
A JSON array containing verification results for each claim:
[
  {
    "claim": "The original claim",
    "verified": true/false,
    "confidence": 0-100,
    "explanation": "Reasoning for the verification",
    "sources": ["Supporting source 1", "Supporting source 2"]
  }
]
"""

    return Task(
        description=task_description,
        agent=agent,
        expected_output=expected_output,
        context_data={
            "story_id": story_id,
            "topic": topic,
            "claims": claims
        }
    )


def create_simple_research_task(
    agent: Agent,
    query: str,
    story_id: str
) -> Task:
    """
    Creates a simple, general research task for ad-hoc queries.

    Args:
        agent: The researcher agent who will perform this task
        query: The research query or question
        story_id: Unique identifier for the story

    Returns:
        CrewAI Task configured for general research
    """
    return Task(
        description=f"""
Research the following query: {query}

Provide comprehensive information including:
- Key facts and findings
- Relevant statistics and figures
- Source citations
- Confidence in the information

Format your response as structured JSON.
""",
        agent=agent,
        expected_output="JSON object with research findings, facts, figures, and sources",
        context_data={
            "story_id": story_id,
            "query": query
        }
    )

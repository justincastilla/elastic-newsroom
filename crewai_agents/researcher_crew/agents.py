"""
CrewAI Agent Definitions for Researcher Crew

Defines the specialized AI agents used in the research crew.
Each agent has a specific role, goal, and set of capabilities.
"""

from crewai import Agent
from langchain_anthropic import ChatAnthropic
from typing import List, Optional
import os


def create_researcher_agent(tools: List, llm: Optional[ChatAnthropic] = None) -> Agent:
    """
    Creates a researcher agent specialized in fact-checking, data gathering,
    and providing structured research results.

    This agent maps to the functionality of the original A2A ResearcherAgent,
    providing factual information, background context, and supporting figures
    for news articles.

    Args:
        tools: List of CrewAI tools available to this agent
        llm: Optional ChatAnthropic LLM instance (creates default if not provided)

    Returns:
        CrewAI Agent configured for research tasks

    Agent Capabilities:
    - Research multiple questions simultaneously
    - Verify factual claims with confidence scores
    - Gather statistics, figures, and data points
    - Provide source citations
    - Structure research results in JSON format
    """
    # Create LLM if not provided
    if llm is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "This is required for CrewAI agents to function."
            )

        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0.7,
            max_tokens=4000
        )

    return Agent(
        role="Research Specialist",
        goal="Gather accurate, factual information and provide structured research data with sources for news articles",
        backstory="""You are an expert research specialist with access to comprehensive
        information sources. You excel at fact-checking, finding relevant statistics,
        and providing well-sourced research results. You always verify claims, provide
        confidence scores, and cite your sources. Your research is thorough, accurate,
        and presented in a structured format that journalists can easily use.""",
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False,  # Single-agent crew, no delegation needed
        max_iter=10,  # Allow up to 10 iterations to complete research
        memory=True,  # Enable memory for context retention
    )


def create_fact_checker_agent(tools: List, llm: Optional[ChatAnthropic] = None) -> Agent:
    """
    Creates a fact-checking agent specialized in verifying claims and assessing credibility.

    This is an optional specialized agent that can be added to the crew for
    enhanced fact-checking capabilities.

    Args:
        tools: List of CrewAI tools available to this agent
        llm: Optional ChatAnthropic LLM instance

    Returns:
        CrewAI Agent configured for fact-checking tasks
    """
    if llm is None:
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3,  # Lower temperature for more focused fact-checking
            max_tokens=2000
        )

    return Agent(
        role="Fact Verification Specialist",
        goal="Verify factual claims with high accuracy and provide confidence assessments",
        backstory="""You are a meticulous fact-checker with expertise in verifying
        claims across multiple domains. You assess the credibility of information,
        cross-reference sources, and provide confidence scores based on available
        evidence. You are thorough, skeptical, and committed to accuracy.""",
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=True,
    )

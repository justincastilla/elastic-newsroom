"""
Newsroom Agents

This module contains all the specialized agents for the newsroom system.
"""

from .news_chief import NewsChiefAgent, NewsChiefAgentExecutor, create_agent_card as create_news_chief_card
from .reporter import ReporterAgent, ReporterAgentExecutor, create_agent_card as create_reporter_card
from .researcher import ResearcherAgent, ResearcherAgentExecutor, create_agent_card as create_researcher_card
from .editor import EditorAgent, EditorAgentExecutor, create_agent_card as create_editor_card
from .publisher import PublisherAgent, PublisherAgentExecutor, create_agent_card as create_publisher_card

__all__ = [
    # News Chief
    "NewsChiefAgent",
    "NewsChiefAgentExecutor",
    "create_news_chief_card",

    # Reporter
    "ReporterAgent",
    "ReporterAgentExecutor",
    "create_reporter_card",

    # Researcher
    "ResearcherAgent",
    "ResearcherAgentExecutor",
    "create_researcher_card",

    # Editor
    "EditorAgent",
    "EditorAgentExecutor",
    "create_editor_card",

    # Publisher
    "PublisherAgent",
    "PublisherAgentExecutor",
    "create_publisher_card"
]


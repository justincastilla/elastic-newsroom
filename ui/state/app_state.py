"""
Application State Management

Global state for the Elastic News UI
"""

import mesop as me
from typing import Optional, Dict, Any
from dataclasses import field


@me.stateclass
class AppState:
    """Global application state"""

    # News Chief client configuration
    news_chief_url: str = "http://localhost:8080"

    # Current story being worked on
    current_story_id: str = ""

    # Workflow status tracking
    workflow_status: str = "pending"  # pending, assigned, writing, researching, editing, publishing, completed, error

    # Article content (when available)
    article_headline: str = ""
    article_content: str = ""
    article_word_count: int = 0

    # Loading states
    is_loading: bool = False
    loading_message: str = ""

    # Error handling
    error_message: str = ""


@me.stateclass
class AssignmentFormState:
    """State for the story assignment form"""

    topic: str = ""
    angle: str = ""
    target_length: int = 1000

    # Form validation
    validation_errors: Dict[str, str] = field(default_factory=dict)


@me.stateclass
class ArticleViewState:
    """State for the article viewer page"""

    # Which metadata sections are expanded
    research_expanded: bool = False
    review_expanded: bool = False
    metadata_expanded: bool = False

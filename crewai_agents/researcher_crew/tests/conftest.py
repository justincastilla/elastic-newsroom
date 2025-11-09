"""
Pytest Configuration for Researcher Crew Tests

Provides fixtures and configuration for testing the CrewAI researcher.
"""

import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("MCP_SERVER_URL", "http://localhost:8095")
    monkeypatch.setenv("EVENT_HUB_URL", "http://localhost:8090")
    monkeypatch.setenv("EVENT_HUB_ENABLED", "false")  # Disable for tests


@pytest.fixture
def sample_research_questions():
    """Sample research questions for testing"""
    return [
        "What percentage of news organizations use AI?",
        "Who are the leading companies in AI journalism?",
        "What are the main challenges in AI adoption?"
    ]


@pytest.fixture
def sample_research_result():
    """Sample research result for testing"""
    return {
        "question": "What is AI?",
        "claim_verified": True,
        "confidence": 85,
        "summary": "AI is artificial intelligence, enabling machines to learn and make decisions.",
        "facts": [
            "AI enables machines to learn from data",
            "Machine learning is a subset of AI",
            "AI is used in various industries"
        ],
        "figures": {
            "percentages": ["45% of companies use AI"],
            "dollar_amounts": ["$1.5B AI market"],
            "numbers": ["500 AI companies"],
            "dates": ["2024 adoption surge"],
            "companies": ["Google", "Microsoft", "OpenAI"]
        },
        "sources": [
            "AI Industry Report 2024",
            "Tech Trends Analysis",
            "Market Research Study"
        ]
    }


@pytest.fixture
def sample_a2a_request():
    """Sample A2A request for testing"""
    return {
        "input": {
            "action": "research_questions",
            "story_id": "story_123",
            "topic": "Artificial Intelligence",
            "questions": [
                "What is AI?",
                "Who invented it?"
            ]
        },
        "task_id": "task_456"
    }

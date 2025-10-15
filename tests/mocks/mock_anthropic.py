"""
Mock Anthropic client for testing without API calls.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MockTextContent:
    """Mock text content from Anthropic response."""
    text: str
    type: str = "text"


@dataclass
class MockMessage:
    """Mock Anthropic message response."""
    content: List[MockTextContent]
    model: str
    role: str = "assistant"
    stop_reason: str = "end_turn"

    def __init__(self, text: str, model: str = "claude-sonnet-4-20250514"):
        self.content = [MockTextContent(text=text)]
        self.model = model


class MockMessages:
    """Mock messages API."""

    def create(self, model: str, max_tokens: int, messages: List[Dict[str, str]]) -> MockMessage:
        """Create a mock message response based on the prompt."""
        user_message = messages[0]["content"] if messages else ""

        # Generate appropriate response based on prompt content
        if "outline" in user_message.lower() and "research questions" in user_message.lower():
            # Outline and research questions
            response_text = """{
  "outline": "Introduction: Overview of the topic, Background: Historical context and current state, Key Developments: Recent advances and trends, Future Outlook: Predictions and implications",
  "research_questions": [
    "What percentage of enterprises are adopting multi-agent AI systems?",
    "What are the key benefits reported by early adopters?",
    "Who are the leading companies in this space?",
    "What are the main technical challenges?",
    "What is the projected market growth?"
  ]
}"""

        elif "news article" in user_message.lower() or "write a" in user_message.lower():
            # Article generation
            topic = "Multi-Agent AI Systems"
            if "Topic:" in user_message:
                # Extract topic from prompt
                lines = user_message.split('\n')
                for line in lines:
                    if line.startswith('Topic:'):
                        topic = line.split('Topic:')[1].strip()
                        break

            response_text = f"""HEADLINE: {topic} Transform Enterprise Operations

{topic} are revolutionizing how organizations approach complex problem-solving and automation. By enabling specialized AI agents to collaborate seamlessly, companies are achieving unprecedented levels of efficiency and innovation.

Industry analysts report that early adopters are seeing significant improvements in productivity and decision-making quality. The technology builds on the Agent2Agent (A2A) protocol, which standardizes how autonomous agents communicate and coordinate their activities.

Leading technology companies have already deployed multi-agent systems for tasks ranging from customer service to research and development. The systems excel at breaking down complex problems into manageable subtasks, with each agent specializing in a specific domain.

Experts predict continued growth in this sector, with enterprise adoption expected to accelerate over the next several years. However, challenges remain around integration, security, and ensuring effective coordination between diverse agent types.

As the technology matures, organizations that successfully implement multi-agent AI systems are positioning themselves for significant competitive advantages in their respective markets."""

        elif "revising your article" in user_message.lower() or "editorial feedback" in user_message.lower():
            # Editorial revisions
            response_text = """HEADLINE: Multi-Agent AI Systems Transform Enterprise Operations

Multi-agent AI systems are revolutionizing how organizations approach complex problem-solving and automation. By enabling specialized AI agents to collaborate seamlessly, companies are achieving unprecedented levels of efficiency and innovation.

According to recent industry analysis, early adopters report significant improvements in productivity and decision-making quality. The technology builds on the Agent2Agent (A2A) protocol, which standardizes how autonomous agents communicate and coordinate their activities.

Leading technology companies have deployed multi-agent systems for tasks ranging from customer service to research and development. These systems excel at breaking down complex problems into manageable subtasks, with each agent specializing in a specific domain.

Industry experts predict continued growth in this sector, with enterprise adoption expected to accelerate substantially over the next several years. However, challenges remain around system integration, security considerations, and ensuring effective coordination between diverse agent types.

Organizations that successfully implement multi-agent AI systems are positioning themselves for significant competitive advantages in their respective markets."""

        else:
            # Generic response
            response_text = f"Mock response for: {user_message[:100]}..."

        return MockMessage(text=response_text, model=model)


class MockAnthropicClient:
    """
    Mock Anthropic client for testing.

    This client simulates Anthropic API responses without making actual API calls.
    It generates appropriate responses based on the prompt content.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize mock client (api_key is ignored)."""
        self.messages = MockMessages()
        self.api_key = api_key or "mock-api-key"

    @property
    def Messages(self):
        """Provide Messages API (for compatibility)."""
        return self.messages


def mock_anthropic_response(text: str) -> MockMessage:
    """
    Create a mock Anthropic response with custom text.

    Useful for testing specific response scenarios.
    """
    return MockMessage(text=text)


# Example usage in tests:
# from tests.mocks import MockAnthropicClient
#
# def test_with_mock_anthropic():
#     mock_client = MockAnthropicClient()
#     response = mock_client.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=1000,
#         messages=[{"role": "user", "content": "Write an article about AI"}]
#     )
#     assert response.content[0].text is not None

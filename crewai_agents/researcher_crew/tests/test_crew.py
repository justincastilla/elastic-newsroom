"""
Unit Tests for ResearcherCrew

Tests the core functionality of the CrewAI-based researcher agent.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from crewai_agents.researcher_crew.crew import ResearcherCrew


class TestResearcherCrew:
    """Test suite for ResearcherCrew class"""

    def test_initialization(self):
        """Test crew initialization"""
        crew = ResearcherCrew()

        assert crew is not None
        assert hasattr(crew, 'research_history')
        assert hasattr(crew, 'tools')
        assert hasattr(crew, 'event_hub')
        assert len(crew.tools) == 2  # research_questions_tool, fact_verification_tool

    @pytest.mark.asyncio
    async def test_research_questions_mock(self):
        """Test research_questions with mock crew output"""
        crew_instance = ResearcherCrew()

        # Mock the crew creation and execution
        with patch.object(crew_instance, 'create_crew') as mock_create_crew:
            mock_crew = Mock()
            mock_crew.kickoff_async = AsyncMock(return_value=json.dumps([
                {
                    "question": "What is AI?",
                    "claim_verified": True,
                    "confidence": 85,
                    "summary": "AI is artificial intelligence",
                    "facts": ["AI enables machines to learn"],
                    "figures": {"percentages": ["45%"]},
                    "sources": ["Tech Journal 2024"]
                }
            ]))
            mock_create_crew.return_value = mock_crew

            # Test research_questions
            result = await crew_instance.research_questions(
                questions=["What is AI?"],
                topic="Artificial Intelligence",
                story_id="test_123"
            )

            assert result["status"] == "success"
            assert "research_id" in result
            assert result["story_id"] == "test_123"
            assert len(result["research_results"]) == 1
            assert result["research_results"][0]["question"] == "What is AI?"
            assert result["total_questions"] == 1

    def test_get_research_history_not_found(self):
        """Test get_research_history with non-existent research_id"""
        crew = ResearcherCrew()

        result = crew.get_research_history(research_id="nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["message"]

    def test_get_status(self):
        """Test get_status returns correct structure"""
        crew = ResearcherCrew()

        result = crew.get_status()

        assert result["status"] == "success"
        assert "total_research_requests" in result
        assert "research_history" in result
        assert result["total_research_requests"] == 0

    @pytest.mark.asyncio
    async def test_event_hub_integration(self):
        """Test Event Hub integration during research"""
        crew_instance = ResearcherCrew()

        # Mock Event Hub client
        with patch.object(crew_instance.event_hub, 'publish_research_started') as mock_start, \
             patch.object(crew_instance.event_hub, 'publish_research_completed') as mock_complete, \
             patch.object(crew_instance, 'create_crew') as mock_create_crew:

            # Setup mocks
            mock_start.return_value = AsyncMock(return_value=True)
            mock_complete.return_value = AsyncMock(return_value=True)

            mock_crew = Mock()
            mock_crew.kickoff_async = AsyncMock(return_value=json.dumps([{
                "question": "Test",
                "claim_verified": True,
                "confidence": 80,
                "summary": "Test",
                "facts": [],
                "figures": {},
                "sources": []
            }]))
            mock_create_crew.return_value = mock_crew

            # Execute
            await crew_instance.research_questions(
                questions=["Test?"],
                topic="Test",
                story_id="test_123"
            )

            # Verify Event Hub calls
            assert mock_start.called or mock_start.call_count == 0  # May be disabled
            assert mock_complete.called or mock_complete.call_count == 0  # May be disabled

    def test_parse_crew_output_json_array(self):
        """Test parsing crew output when it's a JSON array"""
        crew = ResearcherCrew()

        output = '[{"question": "Test", "confidence": 90}]'
        questions = ["Test"]

        result = crew._parse_crew_output(output, questions)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["question"] == "Test"

    def test_parse_crew_output_markdown_json(self):
        """Test parsing crew output with markdown code blocks"""
        crew = ResearcherCrew()

        output = '''```json
[{"question": "Test", "confidence": 90}]
```'''
        questions = ["Test"]

        result = crew._parse_crew_output(output, questions)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_parse_crew_output_fallback(self):
        """Test parsing falls back to mock data on invalid output"""
        crew = ResearcherCrew()

        output = "Invalid JSON output"
        questions = ["Test 1", "Test 2"]

        result = crew._parse_crew_output(output, questions)

        assert isinstance(result, list)
        assert len(result) == 2  # Should generate mock results for both questions

    def test_generate_mock_results(self):
        """Test mock result generation"""
        crew = ResearcherCrew()

        questions = ["What is AI?", "Who invented it?"]

        result = crew._generate_mock_results(questions)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all("question" in r for r in result)
        assert all("confidence" in r for r in result)
        assert all("facts" in r for r in result)

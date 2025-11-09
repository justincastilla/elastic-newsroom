# Tests for CrewAI Researcher Agent

This directory contains unit tests and integration tests for the CrewAI-based researcher agent.

## Test Structure

```
tests/
├── __init__.py             # Package initialization
├── conftest.py             # Pytest configuration and fixtures
├── test_crew.py            # Tests for ResearcherCrew class
├── test_main.py            # Tests for FastAPI server
├── test_shared_utilities.py # Tests for shared utilities
└── README.md               # This file
```

## Running Tests

### All Tests
```bash
# From project root
pytest crewai_agents/researcher_crew/tests/ -v

# With coverage
pytest crewai_agents/researcher_crew/tests/ --cov=crewai_agents.researcher_crew --cov-report=html
```

### Specific Test Files
```bash
# Test crew only
pytest crewai_agents/researcher_crew/tests/test_crew.py -v

# Test FastAPI endpoints only
pytest crewai_agents/researcher_crew/tests/test_main.py -v

# Test shared utilities only
pytest crewai_agents/researcher_crew/tests/test_shared_utilities.py -v
```

### Specific Tests
```bash
# Test a specific function
pytest crewai_agents/researcher_crew/tests/test_crew.py::TestResearcherCrew::test_initialization -v

# Test with markers
pytest -m asyncio -v  # Run only async tests
```

## Test Coverage

### `test_crew.py` - ResearcherCrew Tests
- Crew initialization
- Research questions execution (mocked)
- Event Hub integration
- Crew output parsing (JSON array, markdown, fallback)
- Mock result generation
- Research history retrieval
- Status reporting

### `test_main.py` - FastAPI Server Tests
- Health check endpoint
- A2A agent card endpoint
- Status endpoint
- Research endpoint (with mocking)
- History endpoint
- A2A protocol bridge (/a2a/tasks)
- CORS middleware
- Error handling (missing fields, unknown actions)

### `test_shared_utilities.py` - Shared Utilities Tests
- EventHubClient initialization and configuration
- Event publishing (mocked)
- Enable/disable functionality
- A2A request parsing
- A2A response formatting
- A2A agent card creation
- A2A request validation

## Test Fixtures

Defined in `conftest.py`:
- `mock_env_vars` - Mock environment variables
- `sample_research_questions` - Sample questions for testing
- `sample_research_result` - Sample research result
- `sample_a2a_request` - Sample A2A request

## Mocking Strategy

### External Dependencies
- **Anthropic API**: Mocked in all tests (no real API calls)
- **MCP Server**: Mocked tool calls
- **Event Hub**: Mocked HTTP requests
- **CrewAI crew execution**: Mocked `kickoff_async()` method

### Why Mocking?
- Fast execution (no network calls)
- No external service dependencies
- Deterministic results
- No API costs

## Example Test Run

```bash
$ pytest crewai_agents/researcher_crew/tests/ -v

===== test session starts =====
collected 25 items

test_crew.py::TestResearcherCrew::test_initialization PASSED          [  4%]
test_crew.py::TestResearcherCrew::test_research_questions_mock PASSED [  8%]
test_crew.py::TestResearcherCrew::test_get_research_history_not_found PASSED [ 12%]
test_crew.py::TestResearcherCrew::test_get_status PASSED               [ 16%]
test_crew.py::TestResearcherCrew::test_event_hub_integration PASSED    [ 20%]
test_crew.py::TestResearcherCrew::test_parse_crew_output_json_array PASSED [ 24%]
test_crew.py::TestResearcherCrew::test_parse_crew_output_markdown_json PASSED [ 28%]
test_crew.py::TestResearcherCrew::test_parse_crew_output_fallback PASSED [ 32%]
test_crew.py::TestResearcherCrew::test_generate_mock_results PASSED    [ 36%]
test_main.py::TestFastAPIEndpoints::test_health_check PASSED           [ 40%]
test_main.py::TestFastAPIEndpoints::test_agent_card PASSED             [ 44%]
test_main.py::TestFastAPIEndpoints::test_status_endpoint PASSED        [ 48%]
test_main.py::TestFastAPIEndpoints::test_research_endpoint_mock PASSED [ 52%]
test_main.py::TestFastAPIEndpoints::test_history_endpoint_missing_params PASSED [ 56%]
test_main.py::TestFastAPIEndpoints::test_research_endpoint_missing_fields PASSED [ 60%]
test_main.py::TestA2AProtocolBridge::test_a2a_tasks_research_questions PASSED [ 64%]
test_main.py::TestA2AProtocolBridge::test_a2a_tasks_get_status PASSED  [ 68%]
test_main.py::TestA2AProtocolBridge::test_a2a_tasks_unknown_action PASSED [ 72%]
test_main.py::TestA2AProtocolBridge::test_a2a_tasks_missing_input PASSED [ 76%]
test_main.py::TestCORSMiddleware::test_cors_headers_present PASSED     [ 80%]
test_shared_utilities.py::TestEventHubClient::test_initialization PASSED [ 84%]
test_shared_utilities.py::TestEventHubClient::test_disabled_client PASSED [ 88%]
test_shared_utilities.py::TestA2ABridge::test_parse_a2a_request_dict_input PASSED [ 92%]
test_shared_utilities.py::TestA2ABridge::test_format_a2a_response PASSED [ 96%]
test_shared_utilities.py::TestA2ABridge::test_validate_a2a_request_valid PASSED [100%]

===== 25 passed in 2.34s =====
```

## Notes

- Tests are self-contained within the researcher_crew folder
- No dependencies on other agent tests
- All external services are mocked
- Tests run quickly (<5 seconds total)
- Coverage focuses on core functionality, not edge cases
- Integration tests with real services can be run separately

## Future Improvements

- Add integration tests with real MCP server
- Add end-to-end tests with Docker compose
- Add performance tests for crew execution time
- Add stress tests for concurrent research requests

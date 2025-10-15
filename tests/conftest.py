"""
Pytest configuration and fixtures for Elastic News tests.

This file provides shared fixtures and configuration for all tests.
"""

import pytest
import httpx
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver
from unittest.mock import patch

# Add project root and tests directory to path for imports
project_root = Path(__file__).parent.parent
tests_dir = Path(__file__).parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

# Import mocks using relative import
from mocks import MockAnthropicClient, MockElasticsearchClient


# Agent URLs
AGENT_URLS = {
    'news_chief': 'http://localhost:8080',
    'reporter': 'http://localhost:8081',
    'editor': 'http://localhost:8082',
    'researcher': 'http://localhost:8083',
    'publisher': 'http://localhost:8084'
}


@pytest.fixture(scope="session")
def use_mock_services() -> bool:
    """
    Determine whether to use mock services or real services.

    Set USE_REAL_SERVICES=true environment variable to use actual API calls.
    By default, tests use mocks for speed and reliability.
    """
    return os.getenv("USE_REAL_SERVICES", "false").lower() != "true"


@pytest.fixture(scope="session")
def agent_urls() -> Dict[str, str]:
    """Provide agent URLs for all tests."""
    return AGENT_URLS


@pytest.fixture(scope="session", autouse=True)
def mock_anthropic_globally(use_mock_services):
    """
    Mock Anthropic client globally for all tests.

    This prevents tests from making actual API calls unless USE_REAL_SERVICES=true.
    """
    if use_mock_services:
        with patch('anthropic.Anthropic', MockAnthropicClient):
            with patch('utils.init_anthropic_client') as mock_init:
                # Make init_anthropic_client return our mock
                mock_init.return_value = MockAnthropicClient()
                yield
    else:
        # Use real services
        yield


@pytest.fixture(scope="session", autouse=True)
def mock_elasticsearch_globally(use_mock_services):
    """
    Mock Elasticsearch client globally for all tests.

    This prevents tests from requiring an actual ES instance.
    """
    if use_mock_services:
        with patch('elasticsearch.Elasticsearch', MockElasticsearchClient):
            yield
    else:
        # Use real services
        yield


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def http_client():
    """Provide a shared HTTP client for the test session."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        yield client


@pytest.fixture(scope="session")
async def a2a_clients(http_client, agent_urls):
    """Initialize A2A clients for all agents."""
    clients = {}
    client_config = ClientConfig(httpx_client=http_client, streaming=False)
    client_factory = ClientFactory(client_config)

    for agent_name, agent_url in agent_urls.items():
        try:
            card_resolver = A2ACardResolver(http_client, agent_url)
            agent_card = await card_resolver.get_agent_card()
            clients[agent_name] = client_factory.create(agent_card)
        except Exception as e:
            pytest.fail(f"Failed to initialize {agent_name} client: {e}")

    return clients


@pytest.fixture(scope="function")
def sample_story() -> Dict[str, Any]:
    """Provide a sample story for testing."""
    return {
        "topic": "Multi-Agent AI Systems in Enterprise Applications",
        "angle": "How A2A protocol enables seamless agent collaboration",
        "target_length": 1000,
        "priority": "high"
    }


@pytest.fixture(scope="session")
async def check_agents_health(http_client, agent_urls):
    """Check that all agents are running before tests start."""
    unhealthy_agents = []

    for agent_name, agent_url in agent_urls.items():
        try:
            card_resolver = A2ACardResolver(http_client, agent_url)
            await card_resolver.get_agent_card()
        except Exception as e:
            unhealthy_agents.append((agent_name, agent_url, str(e)))

    if unhealthy_agents:
        error_msg = "The following agents are not responding:\n"
        for name, url, error in unhealthy_agents:
            error_msg += f"  - {name} ({url}): {error}\n"
        error_msg += "\nPlease start all agents with: ./scripts/start_newsroom.sh"
        pytest.exit(error_msg, returncode=1)

    return True


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "workflow: marks tests that run full workflow")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their names."""
    for item in items:
        # Mark workflow tests as slow
        if "workflow" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.integration)

        # Mark unit tests
        if "test_utils" in item.nodeid:
            item.add_marker(pytest.mark.unit)

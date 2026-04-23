"""
Configuration and credential validation tests.

Validates that all API keys and endpoints in .env are correctly configured
and can successfully authenticate. These tests make real network calls —
they are NOT mocked.

Usage:
    pytest tests/test_validate_config.py -v
    pytest tests/test_validate_config.py -v -k anthropic   # just Anthropic
    pytest tests/test_validate_config.py -v -k elastic      # just Elasticsearch
    pytest tests/test_validate_config.py -v -k tavily       # just Tavily
    pytest tests/test_validate_config.py -v -k archivist    # just Archivist
"""

import os
import sys
import json
import pytest
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load .env from project root (don't override existing env vars)
load_dotenv(project_root / ".env", override=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env(name: str) -> str:
    """Get an env var or skip the test if it's not set."""
    val = os.getenv(name, "").strip()
    if not val or val.startswith("your_") or val.startswith("<your_"):
        pytest.skip(f"{name} not configured in .env")
    return val


# ---------------------------------------------------------------------------
# 1. Anthropic API
# ---------------------------------------------------------------------------

class TestAnthropicAPI:
    """Validate Anthropic API key and model access."""

    def test_api_key_format(self):
        """Check that ANTHROPIC_API_KEY looks like a valid key."""
        key = _env("ANTHROPIC_API_KEY")
        assert key.startswith("sk-ant-"), (
            f"ANTHROPIC_API_KEY should start with 'sk-ant-', got '{key[:10]}...'"
        )

    def test_api_key_authenticates(self):
        """Make a minimal API call to verify the key works and has credits."""
        key = _env("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Reply with OK"}],
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            return  # Success

        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        error_type = body.get("error", {}).get("type", "")
        error_msg = body.get("error", {}).get("message", response.text)

        if response.status_code == 401:
            pytest.fail(f"ANTHROPIC_API_KEY is invalid (401 Unauthorized): {error_msg}")
        elif response.status_code == 400 and "credit balance" in error_msg.lower():
            pytest.fail(f"Anthropic account has insufficient credits: {error_msg}")
        elif response.status_code == 400 and "model" in error_msg.lower():
            pytest.fail(f"Model '{model}' not available: {error_msg}")
        else:
            pytest.fail(
                f"Anthropic API returned {response.status_code} ({error_type}): {error_msg}"
            )


# ---------------------------------------------------------------------------
# 2. Tavily Search API
# ---------------------------------------------------------------------------

class TestTavilyAPI:
    """Validate Tavily API key."""

    def test_api_key_format(self):
        """Check that TAVILY_API_KEY looks like a valid key."""
        key = _env("TAVILY_API_KEY")
        assert key.startswith("tvly-"), (
            f"TAVILY_API_KEY should start with 'tvly-', got '{key[:10]}...'"
        )

    def test_api_key_authenticates(self):
        """Make a minimal search to verify the key works."""
        key = _env("TAVILY_API_KEY")

        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": key,
                "query": "test",
                "max_results": 1,
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            return  # Success

        if response.status_code == 401 or response.status_code == 403:
            pytest.fail(f"TAVILY_API_KEY is invalid ({response.status_code}): {response.text[:200]}")
        else:
            pytest.fail(f"Tavily API returned {response.status_code}: {response.text[:200]}")


# ---------------------------------------------------------------------------
# 3. Elasticsearch
# ---------------------------------------------------------------------------

class TestElasticsearch:
    """Validate Elasticsearch endpoint and API key."""

    def test_endpoint_format(self):
        """Check that ELASTICSEARCH_ENDPOINT looks like a valid URL."""
        endpoint = _env("ELASTICSEARCH_ENDPOINT")
        assert endpoint.startswith("http"), (
            f"ELASTICSEARCH_ENDPOINT should start with http(s)://, got '{endpoint[:30]}'"
        )

    def test_api_key_authenticates(self):
        """Verify Elasticsearch credentials by hitting the cluster info endpoint."""
        endpoint = _env("ELASTICSEARCH_ENDPOINT").rstrip("/")
        api_key = _env("ELASTICSEARCH_API_KEY")

        response = httpx.get(
            endpoint,
            headers={
                "Authorization": f"ApiKey {api_key}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )

        if response.status_code == 200:
            info = response.json()
            cluster = info.get("cluster_name", "unknown")
            version = info.get("version", {}).get("number", "unknown")
            print(f"\n  Elasticsearch cluster: {cluster}, version: {version}")
            return

        if response.status_code == 401:
            pytest.fail(
                "ELASTICSEARCH_API_KEY is invalid (401 Unauthorized). "
                "Regenerate the key in Kibana > Stack Management > API Keys."
            )
        else:
            pytest.fail(f"Elasticsearch returned {response.status_code}: {response.text[:200]}")

    def test_index_exists(self):
        """Check that the news_archive index exists."""
        endpoint = _env("ELASTICSEARCH_ENDPOINT").rstrip("/")
        api_key = _env("ELASTICSEARCH_API_KEY")
        index = os.getenv("ELASTIC_ARCHIVIST_INDEX", "news_archive")

        response = httpx.head(
            f"{endpoint}/{index}",
            headers={
                "Authorization": f"ApiKey {api_key}",
            },
            timeout=15.0,
        )

        if response.status_code == 200:
            return  # Index exists
        elif response.status_code == 404:
            pytest.fail(
                f"Index '{index}' does not exist. "
                f"Create it with: python scripts/create_elasticsearch_index.py"
            )
        elif response.status_code == 401:
            pytest.skip("Skipping index check — Elasticsearch auth failed (see test_api_key_authenticates)")
        else:
            pytest.fail(f"Index check returned {response.status_code}: {response.text[:200]}")


# ---------------------------------------------------------------------------
# 4. Elastic Archivist (A2A Agent)
# ---------------------------------------------------------------------------

class TestArchivist:
    """Validate Archivist agent URL and API key."""

    def _get_archivist_url(self) -> str:
        """Get whichever Archivist URL is configured."""
        agent_url = os.getenv("ELASTIC_ARCHIVIST_AGENT_URL", "").strip()
        card_url = os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL", "").strip()

        url = agent_url or card_url
        if not url or url.startswith("your_") or url.startswith("<your_") or url.startswith("https://your-kb"):
            pytest.skip("Archivist URL not configured in .env")
        return url

    def _get_base_url(self, url: str) -> str:
        """Extract base Kibana URL from agent or card URL."""
        if "/api/agent_builder/" in url:
            return url.split("/api/agent_builder/")[0]
        elif "/.well-known/" in url:
            return url.split("/.well-known/")[0]
        else:
            pytest.fail(f"Unrecognized Archivist URL format: {url}")

    def _get_agent_id(self, url: str) -> str:
        """Extract agent ID from URL, or return default."""
        if "/api/agent_builder/a2a/" in url:
            return url.split("/api/agent_builder/a2a/")[-1].replace(".json", "")
        return "elastic-ai-agent"

    def test_url_configured(self):
        """Check that at least one Archivist URL is set."""
        self._get_archivist_url()  # Skips if not configured

    def test_api_key_set(self):
        """Check that the Archivist API key is set."""
        _env("ELASTIC_ARCHIVIST_API_KEY")

    def test_agent_card_reachable(self):
        """Fetch the agent card to verify the URL and auth work."""
        url = self._get_archivist_url()
        api_key = _env("ELASTIC_ARCHIVIST_API_KEY")
        base_url = self._get_base_url(url)
        agent_id = self._get_agent_id(url)

        card_endpoint = f"{base_url}/api/agent_builder/a2a/{agent_id}.json"

        response = httpx.get(
            card_endpoint,
            headers={
                "Authorization": f"ApiKey {api_key}",
                "kbn-xsrf": "kibana",
            },
            timeout=15.0,
        )

        if response.status_code == 200:
            try:
                card = response.json()
                agent_name = card.get("name", "unknown")
                print(f"\n  Archivist agent card: {agent_name}")
                print(f"  Agent ID: {agent_id}")
                print(f"  Endpoint: {card_endpoint}")
            except Exception:
                pass  # Card fetched but couldn't parse — still a pass
            return

        if response.status_code == 401:
            pytest.fail(
                "ELASTIC_ARCHIVIST_API_KEY is invalid (401 Unauthorized). "
                "Check your Kibana API key."
            )
        elif response.status_code == 404:
            pytest.fail(
                f"Agent '{agent_id}' not found at {base_url}. "
                "Verify the agent exists in Elastic Agent Builder."
            )
        else:
            pytest.fail(
                f"Agent card request returned {response.status_code}: {response.text[:200]}"
            )

    def test_a2a_endpoint_responds(self):
        """Send a minimal A2A message to verify the endpoint accepts requests."""
        url = self._get_archivist_url()
        api_key = _env("ELASTIC_ARCHIVIST_API_KEY")
        base_url = self._get_base_url(url)
        agent_id = self._get_agent_id(url)

        a2a_endpoint = f"{base_url}/api/agent_builder/a2a/{agent_id}"

        # Send a minimal A2A JSONRPC request
        a2a_request = {
            "id": "validate-config-test",
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "configuration": {
                    "acceptedOutputModes": ["text/plain"]
                },
                "message": {
                    "kind": "message",
                    "messageId": "validate-config-test",
                    "metadata": {},
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Hello, are you available?"
                        }
                    ],
                    "role": "user"
                }
            }
        }

        response = httpx.post(
            a2a_endpoint,
            json=a2a_request,
            headers={
                "Authorization": f"ApiKey {api_key}",
                "Content-Type": "application/json",
                "kbn-xsrf": "kibana",
            },
            timeout=60.0,
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print(f"\n  A2A endpoint responded successfully")
                return
            elif "error" in result:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                pytest.fail(f"A2A endpoint returned error: {error_msg}")
            else:
                # Got 200 with some response — good enough for validation
                return

        if response.status_code == 401:
            pytest.fail("ELASTIC_ARCHIVIST_API_KEY failed A2A auth (401)")
        elif response.status_code == 404:
            pytest.fail(f"A2A endpoint not found: {a2a_endpoint}")
        else:
            pytest.fail(
                f"A2A endpoint returned {response.status_code}: {response.text[:200]}"
            )


# ---------------------------------------------------------------------------
# 5. MCP Server (local — only if agents are running)
# ---------------------------------------------------------------------------

class TestMCPServer:
    """Validate MCP Server health (requires agents to be running)."""

    def test_health_endpoint(self):
        """Check MCP server health endpoint."""
        mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8095").rstrip("/")

        try:
            response = httpx.get(f"{mcp_url}/health", timeout=5.0)
        except httpx.ConnectError:
            pytest.skip(
                f"MCP server not running at {mcp_url}. "
                "Start agents with: make start"
            )

        if response.status_code == 200:
            return
        else:
            pytest.fail(f"MCP health returned {response.status_code}: {response.text[:200]}")


# ---------------------------------------------------------------------------
# 6. Summary (always runs last)
# ---------------------------------------------------------------------------

class TestConfigSummary:
    """Print a summary of which services are configured."""

    def test_print_summary(self):
        """Print configuration summary (always passes)."""
        services = {
            "Anthropic API": os.getenv("ANTHROPIC_API_KEY", ""),
            "Tavily Search": os.getenv("TAVILY_API_KEY", ""),
            "Elasticsearch": os.getenv("ELASTICSEARCH_ENDPOINT", ""),
            "ES API Key": os.getenv("ELASTICSEARCH_API_KEY", ""),
            "Archivist URL": os.getenv("ELASTIC_ARCHIVIST_AGENT_URL", "") or os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL", ""),
            "Archivist Key": os.getenv("ELASTIC_ARCHIVIST_API_KEY", ""),
        }

        print("\n" + "=" * 60)
        print("  CONFIGURATION SUMMARY")
        print("=" * 60)

        for name, val in services.items():
            if val and not val.startswith("your_") and not val.startswith("<your_"):
                status = "SET"
                # Mask the value
                if "key" in name.lower() or "api" in name.lower():
                    display = val[:8] + "..." + val[-4:] if len(val) > 16 else "***"
                else:
                    display = val[:40] + "..." if len(val) > 40 else val
            else:
                status = "NOT SET"
                display = ""

            print(f"  {name:20s}  [{status:7s}]  {display}")

        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        index = os.getenv("ELASTIC_ARCHIVIST_INDEX", "news_archive")
        print(f"\n  Model: {model}")
        print(f"  Index: {index}")
        print("=" * 60)

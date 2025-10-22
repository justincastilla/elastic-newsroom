#!/usr/bin/env python3
"""
Direct Archivist Test Script

This script sends a simple query to the Archivist agent and displays the raw response.
Useful for debugging Archivist integration issues.

Usage:
    python test_archivist_direct.py
    python test_archivist_direct.py "Your custom query here"
"""

import os
import sys
import json
import time
import httpx
import asyncio
from utils.env_loader import load_env_config

# Load environment variables
load_env_config()


def create_a2a_message(query: str, story_id: str = "test_direct"):
    """Create an A2A JSONRPC message"""
    timestamp_ms = int(time.time() * 1000)
    message_id = f"msg-{timestamp_ms}-{story_id}"

    return {
        "id": message_id,
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "configuration": {
                "acceptedOutputModes": ["text/plain", "video/mp4"]
            },
            "message": {
                "kind": "message",
                "messageId": message_id,
                "metadata": {},
                "parts": [
                    {
                        "kind": "text",
                        "text": query
                    }
                ],
                "role": "user"
            }
        }
    }


async def test_archivist(query: str):
    """Test the Archivist with a direct query"""

    # Get configuration from environment
    agent_card_url = os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL")
    api_key = os.getenv("ELASTIC_ARCHIVIST_API_KEY")

    if not agent_card_url:
        print("❌ Error: ELASTIC_ARCHIVIST_AGENT_CARD_URL not configured")
        print("   Please set this in your .env file")
        return

    if not api_key:
        print("❌ Error: ELASTIC_ARCHIVIST_API_KEY not configured")
        print("   Please set this in your .env file")
        return

    # Parse URL to get endpoint
    # Example URL: https://gemini-searchlabs-f15e57.kb.us-central1.gcp.elastic.cloud/api/agent_builder/a2a/elastic-ai-agent.json
    # Endpoint:    https://gemini-searchlabs-f15e57.kb.us-central1.gcp.elastic.cloud/api/agent_builder/a2a/elastic-ai-agent

    if "/api/agent_builder/a2a/" not in agent_card_url:
        print("❌ Error: Invalid ELASTIC_ARCHIVIST_AGENT_CARD_URL format")
        print("   Expected format: https://<kb-url>/api/agent_builder/a2a/<agent-id>.json")
        return

    # Extract agent ID from the URL (remove .json if present)
    agent_id = agent_card_url.split("/")[-1]
    if agent_id.endswith(".json"):
        agent_id = agent_id[:-5]

    # Build the endpoint URL (without .json)
    base_url = agent_card_url.split("/api/agent_builder/")[0]
    endpoint = f"{base_url}/api/agent_builder/a2a/{agent_id}"

    print(f"   Parsed from: {agent_card_url}")
    print(f"   Using endpoint: {endpoint}")

    print("=" * 80)
    print("🔍 ARCHIVIST DIRECT TEST")
    print("=" * 80)
    print(f"\n📋 Configuration:")
    print(f"   Agent Card URL: {agent_card_url}")
    print(f"   Endpoint: {endpoint}")
    print(f"   Agent ID: {agent_id}")
    print(f"   API Key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
    print(f"\n📨 Query: {query}")
    print("\n" + "=" * 80)

    # Create message
    message = create_a2a_message(query)

    print(f"\n📤 REQUEST (JSONRPC 2.0):")
    print("-" * 80)
    print(json.dumps(message, indent=2))
    print("-" * 80)

    # Create headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {api_key}",
        "kbn-xsrf": "kibana"
    }

    print(f"\n🔑 REQUEST HEADERS:")
    print("-" * 80)
    headers_display = headers.copy()
    headers_display["Authorization"] = f"ApiKey {'*' * (len(api_key) - 4)}{api_key[-4:]}"
    print(json.dumps(headers_display, indent=2))
    print("-" * 80)

    # Make request
    print(f"\n⏳ Sending request (timeout: 60s)...")
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                json=message,
                headers=headers
            )

        elapsed_time = time.time() - start_time

        print(f"\n✅ Response received in {elapsed_time:.2f}s")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content Length: {len(response.text)} bytes")

        print(f"\n📥 RAW RESPONSE:")
        print("=" * 80)
        print(response.text)
        print("=" * 80)

        # Try to parse as JSON
        if response.status_code == 200:
            try:
                result = response.json()

                print(f"\n📊 PARSED RESPONSE:")
                print("-" * 80)
                print(json.dumps(result, indent=2))
                print("-" * 80)

                # Extract text content
                if "result" in result:
                    a2a_result = result.get("result", {})
                    message_obj = a2a_result.get("message", {})
                    parts = message_obj.get("parts", [])

                    print(f"\n💬 EXTRACTED TEXT CONTENT:")
                    print("-" * 80)

                    if not parts:
                        print("⚠️  No parts found in response")

                    for i, part in enumerate(parts, 1):
                        if part.get("kind") == "text":
                            text = part.get("text", "")
                            if text:
                                print(f"Part {i}: {len(text)} characters")
                                print(text)
                            else:
                                print(f"Part {i}: EMPTY")
                        else:
                            print(f"Part {i}: {part.get('kind', 'unknown')} (not text)")

                    print("-" * 80)

                elif "error" in result:
                    print(f"\n❌ ERROR RESPONSE:")
                    print("-" * 80)
                    print(json.dumps(result["error"], indent=2))
                    print("-" * 80)

            except json.JSONDecodeError as e:
                print(f"\n❌ Failed to parse JSON response: {e}")

    except httpx.TimeoutException:
        elapsed_time = time.time() - start_time
        print(f"\n⏰ Request timed out after {elapsed_time:.2f}s")
        print("   The Archivist agent did not respond within 60 seconds")

    except httpx.HTTPError as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ HTTP Error after {elapsed_time:.2f}s:")
        print(f"   {type(e).__name__}: {e}")

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ Unexpected error after {elapsed_time:.2f}s:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)


def main():
    """Main entry point"""
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Find articles about artificial intelligence"

    # Check if --retry flag is present
    max_attempts = 10  # Default max attempts
    retry_enabled = False

    if "--retry" in sys.argv:
        retry_enabled = True
        sys.argv.remove("--retry")

        # Check for custom max attempts
        for i, arg in enumerate(sys.argv):
            if arg.startswith("--max-attempts="):
                try:
                    max_attempts = int(arg.split("=")[1])
                    sys.argv.pop(i)
                except ValueError:
                    print("⚠️  Invalid --max-attempts value, using default: 10")
                break

    if retry_enabled:
        print(f"\n🔄 RETRY MODE ENABLED")
        print(f"   Will retry up to {max_attempts} times until text content is found")
        print(f"   Query: {query}")
        print("=" * 80 + "\n")

        for attempt in range(1, max_attempts + 1):
            print(f"\n{'='*80}")
            print(f"ATTEMPT {attempt}/{max_attempts}")
            print(f"{'='*80}\n")

            # Run the test
            result = asyncio.run(test_archivist_with_result(query))

            # Check if we got text content
            if result and result.get("has_content"):
                print(f"\n{'='*80}")
                print(f"✅ SUCCESS! Got text content on attempt {attempt}/{max_attempts}")
                print(f"   Content length: {result.get('content_length', 0)} characters")
                print(f"{'='*80}\n")
                break
            else:
                if attempt < max_attempts:
                    print(f"\n⚠️  Attempt {attempt} returned empty content - retrying...")
                    print(f"   Waiting 2 seconds before next attempt...")
                    time.sleep(2)
                else:
                    print(f"\n❌ All {max_attempts} attempts returned empty content")
                    print(f"   The Archivist may not have relevant data for this query")
    else:
        # Run the test once
        asyncio.run(test_archivist(query))


async def test_archivist_with_result(query: str) -> dict:
    """Test the Archivist and return result status"""

    # Get configuration from environment
    agent_card_url = os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL")
    api_key = os.getenv("ELASTIC_ARCHIVIST_API_KEY")

    if not agent_card_url or not api_key:
        return {"has_content": False, "content_length": 0, "error": "Configuration missing"}

    # Parse URL to get endpoint
    if "/api/agent_builder/a2a/" not in agent_card_url:
        return {"has_content": False, "content_length": 0, "error": "Invalid URL format"}

    agent_id = agent_card_url.split("/")[-1]
    if agent_id.endswith(".json"):
        agent_id = agent_id[:-5]

    base_url = agent_card_url.split("/api/agent_builder/")[0]
    endpoint = f"{base_url}/api/agent_builder/a2a/{agent_id}"

    # Create message
    message = create_a2a_message(query)

    # Create headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {api_key}",
        "kbn-xsrf": "kibana"
    }

    # Make request
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                json=message,
                headers=headers
            )

        if response.status_code == 200:
            result = response.json()

            # Extract text content
            if "result" in result:
                a2a_result = result.get("result", {})
                message_obj = a2a_result.get("message", {})
                parts = message_obj.get("parts", [])

                full_text = ""
                for part in parts:
                    if part.get("kind") == "text":
                        text = part.get("text", "")
                        if text:
                            full_text += text

                has_content = len(full_text) > 0
                return {
                    "has_content": has_content,
                    "content_length": len(full_text),
                    "text": full_text[:200] if full_text else ""
                }

        return {"has_content": False, "content_length": 0}

    except Exception as e:
        return {"has_content": False, "content_length": 0, "error": str(e)}


if __name__ == "__main__":
    main()

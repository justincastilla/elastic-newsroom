#!/usr/bin/env python3
"""
Standalone test for Archivist agent connectivity

Tests the Archivist agent connection, authentication, and response.
"""

import asyncio
import httpx
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Archivist configuration
ARCHIVIST_URL = os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL")
ARCHIVIST_API_KEY = os.getenv("ELASTIC_ARCHIVIST_API_KEY")

print("=" * 80)
print("🔍 ARCHIVIST AGENT CONNECTIVITY TEST")
print("=" * 80)
print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Validate configuration
print("📋 Configuration Check:")
print(f"   Archivist URL: {ARCHIVIST_URL}")
print(f"   API Key configured: {'Yes' if ARCHIVIST_API_KEY else 'No'}")
if ARCHIVIST_API_KEY:
    print(f"   API Key (masked): {ARCHIVIST_API_KEY[:20]}...{ARCHIVIST_API_KEY[-10:]}")
print()

if not ARCHIVIST_URL:
    print("❌ ERROR: ELASTIC_ARCHIVIST_AGENT_CARD_URL not set in .env")
    sys.exit(1)

if not ARCHIVIST_API_KEY:
    print("⚠️  WARNING: ELASTIC_ARCHIVIST_API_KEY not set - request may fail")
print()


async def test_agent_card():
    """Test 1: Fetch agent card"""
    print("TEST 1: Fetching Agent Card")
    print("-" * 80)

    headers = {}
    if ARCHIVIST_API_KEY:
        headers["Authorization"] = f"ApiKey {ARCHIVIST_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"⏱️  Timeout: 30 seconds")
            print(f"🌐 GET {ARCHIVIST_URL}")

            start_time = asyncio.get_event_loop().time()
            response = await client.get(ARCHIVIST_URL, headers=headers)
            elapsed = asyncio.get_event_loop().time() - start_time

            print(f"✅ Response received in {elapsed:.2f} seconds")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Size: {len(response.content)} bytes")

            response.raise_for_status()

            agent_card = response.json()
            print(f"   Agent Name: {agent_card.get('name', 'Unknown')}")
            print(f"   Agent Version: {agent_card.get('version', 'Unknown')}")
            print(f"   Protocol Version: {agent_card.get('protocol_version', 'Unknown')}")

            if 'skills' in agent_card:
                print(f"   Skills: {len(agent_card['skills'])} available")
                for skill in agent_card['skills']:
                    print(f"      - id: {skill.get('id', 'Unknown')}")
                    print(f"        name: {skill.get('name', 'Unknown')}")
                    if 'input_modes' in skill:
                        print(f"        input_modes: {skill.get('input_modes')}")

            # Save agent card for inspection
            with open('archivist_agent_card.json', 'w') as f:
                json.dump(agent_card, f, indent=2)
            print(f"   📄 Agent card saved to: archivist_agent_card.json")

            print()
            return agent_card

    except httpx.TimeoutException as e:
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"❌ TIMEOUT after {elapsed:.2f} seconds")
        print(f"   Error: {e}")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_a2a_message(agent_card):
    """Test 2: Send A2A message"""
    if not agent_card:
        print("⏭️  Skipping A2A message test (no agent card)")
        return

    print("TEST 2: Sending A2A Message")
    print("-" * 80)

    try:
        from a2a.types import AgentCard
        from a2a.client import ClientConfig, ClientFactory, create_text_message_object

        headers = {}
        if ARCHIVIST_API_KEY:
            headers["Authorization"] = f"ApiKey {ARCHIVIST_API_KEY}"

        # Create A2A client
        async with httpx.AsyncClient(timeout=120.0, headers=headers) as http_client:
            print(f"⏱️  Timeout: 120 seconds")

            archivist_card = AgentCard(**agent_card)
            client_config = ClientConfig(httpx_client=http_client, streaming=False)
            client_factory = ClientFactory(client_config)
            archivist_client = client_factory.create(archivist_card)

            # Test search query - try plain text format (as in reporter.py line 482)
            search_query = "artificial intelligence healthcare"
            print(f"🔍 Search Query (plain text): '{search_query}'")

            # Create A2A message using the SDK utility (same pattern as reporter.py)
            message = create_text_message_object(content=search_query)

            print(f"📤 Sending A2A message...")
            start_time = asyncio.get_event_loop().time()

            response_count = 0
            async for response in archivist_client.send_message(message):
                elapsed = asyncio.get_event_loop().time() - start_time
                response_count += 1
                print(f"📥 Received response chunk #{response_count} (at {elapsed:.2f}s)")

                # Debug: Show response structure
                print(f"   Response type: {type(response)}")
                print(f"   Has parts: {hasattr(response, 'parts')}")
                if hasattr(response, 'parts'):
                    print(f"   Parts count: {len(response.parts)}")
                    print(f"   Parts: {response.parts}")

                if hasattr(response, 'parts') and len(response.parts) > 0:
                    part = response.parts[0]
                    print(f"   Part type: {type(part)}")

                    # Inspect the Part root
                    if hasattr(part, 'root'):
                        print(f"   Part.root type: {type(part.root)}")
                        print(f"   Part.root: {part.root}")
                        if hasattr(part.root, 'metadata') and part.root.metadata:
                            print(f"   Part.root.metadata: {part.root.metadata}")

                    # Check response metadata
                    if hasattr(response, 'metadata') and response.metadata:
                        print(f"   Response metadata: {response.metadata}")

                    text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None

                    if text_content:
                        print(f"   Content length: {len(text_content)} characters")
                        print(f"   Preview: {text_content[:200]}...")

                        # Try to parse as JSON
                        try:
                            result = json.loads(text_content)
                            if isinstance(result, dict):
                                print(f"   ✅ Valid JSON response")
                                if 'articles' in result:
                                    print(f"   📚 Found {len(result['articles'])} articles")
                        except json.JSONDecodeError:
                            print(f"   ℹ️  Response is text (not JSON)")

                        print(f"✅ A2A message test successful!")
                        return True
                    else:
                        print(f"   ⚠️  Part has no text content")
                        # Try to access part content directly
                        if hasattr(part, 'text'):
                            print(f"   Direct text: {part.text}")
                        if hasattr(part, 'content'):
                            print(f"   Direct content: {part.content}")

            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"⚠️  No response content (received {response_count} chunks in {elapsed:.2f}s)")
            return False

    except asyncio.TimeoutError:
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"❌ TIMEOUT after {elapsed:.2f} seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_elastic_converse_api():
    """Test 3: Elastic Conversational API (agent_builder/converse)"""
    print("TEST 3: Elastic Conversational API")
    print("-" * 80)

    try:
        # Build converse endpoint URL
        # Base URL: https://gemini-searchlabs-f15e57.kb.us-central1.gcp.elastic.cloud/api/agent_builder/a2a/archive-agent.json
        # Converse URL: https://gemini-searchlabs-f15e57.kb.us-central1.gcp.elastic.cloud/api/agent_builder/converse
        base_url = ARCHIVIST_URL.replace("/agent_builder/a2a/archive-agent.json", "")
        converse_url = f"{base_url}/agent_builder/converse"

        print(f"🌐 Converse URL: {converse_url}")

        headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "true"  # Required by Kibana API
        }
        if ARCHIVIST_API_KEY:
            headers["Authorization"] = f"ApiKey {ARCHIVIST_API_KEY}"

        # Use Elastic conversational format
        converse_request = {
            "input": "Do we have any articles about artificial intelligence in healthcare?",
            "agent_id": "archive-agent"
        }

        print(f"📝 Converse Request:")
        print(json.dumps(converse_request, indent=2))

        async with httpx.AsyncClient(timeout=120.0) as client:
            print(f"📤 Sending converse request...")
            start_time = asyncio.get_event_loop().time()

            response = await client.post(
                converse_url,
                json=converse_request,
                headers=headers
            )

            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"✅ Response received in {elapsed:.2f} seconds")
            print(f"   Status Code: {response.status_code}")

            if response.status_code != 200:
                print(f"   ❌ Error Response:")
                print(f"   {response.text}")
                return False

            result = response.json()
            print(f"📥 Converse Response:")
            print(json.dumps(result, indent=2)[:2000])  # Limit output

            # Check if we got actual content
            if isinstance(result, dict):
                # Look for common response fields
                if 'response' in result or 'message' in result or 'output' in result:
                    print(f"\n✅ Got response content!")
                    return True

            return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""

    # Test 1: Agent Card
    agent_card = await test_agent_card()

    # Test 2: A2A Message (via SDK)
    if agent_card:
        await test_a2a_message(agent_card)

    # Test 3: Elastic Conversational API
    print()
    await test_elastic_converse_api()

    print()
    print("=" * 80)
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

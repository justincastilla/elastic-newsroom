#!/usr/bin/env python3
"""
Test Archivist Agent Integration

Tests the Elastic Agent Builder Converse API integration used by the Reporter
to search for historical articles.
"""

import asyncio
import httpx
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Archivist configuration
ARCHIVIST_URL = os.getenv("ELASTIC_ARCHIVIST_AGENT_CARD_URL")
ARCHIVIST_API_KEY = os.getenv("ELASTIC_ARCHIVIST_API_KEY")


async def test_archivist_converse_api():
    """
    Test the Archivist integration using the Elastic Agent Builder Converse API.

    This test replicates the exact flow used in reporter.py _send_to_archivist()
    """
    print("=" * 80)
    print("🔍 ARCHIVIST AGENT - CONVERSE API TEST")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Validate configuration
    print("📋 Configuration Check:")
    print(f"   Archivist URL: {ARCHIVIST_URL}")
    print(f"   API Key configured: {'Yes' if ARCHIVIST_API_KEY else 'No'}")
    if ARCHIVIST_API_KEY:
        print(f"   API Key (masked): {ARCHIVIST_API_KEY[:20]}...{ARCHIVIST_API_KEY[-10:]}")
    print()

    if not ARCHIVIST_URL:
        print("❌ ERROR: ELASTIC_ARCHIVIST_AGENT_CARD_URL not set in .env")
        print("   Set this in your .env file to the agent card URL")
        return False

    if not ARCHIVIST_API_KEY:
        print("❌ ERROR: ELASTIC_ARCHIVIST_API_KEY not set in .env")
        print("   Set this in your .env file to authenticate with the Archivist")
        return False

    # Test query - same format as reporter.py
    topic = "AI Agents Transform Modern Newsrooms"
    angle = "How A2A protocol enables multi-agent collaboration in journalism"
    search_query = f"Find articles about {topic} {angle}".strip()

    print("🔍 Test Search Query:")
    print(f"   Topic: {topic}")
    print(f"   Angle: {angle}")
    print(f"   Combined Query: '{search_query}'")
    print()

    # Extract base URL and agent_id from agent card URL
    # This matches the logic in reporter.py lines 439-456
    if "/api/agent_builder/a2a/" not in ARCHIVIST_URL:
        print(f"❌ ERROR: Invalid Archivist URL format")
        print(f"   Expected format: https://.../api/agent_builder/a2a/agent-id.json")
        print(f"   Got: {ARCHIVIST_URL}")
        return False

    # Extract agent_id
    agent_id = ARCHIVIST_URL.split("/")[-1]
    if agent_id.endswith(".json"):
        agent_id = agent_id[:-5]

    # Build converse API endpoint (per Elastic docs: POST /api/agent_builder/converse)
    base_url = ARCHIVIST_URL.split("/api/agent_builder/")[0]
    converse_endpoint = f"{base_url}/api/agent_builder/converse"

    print("📡 API Details:")
    print(f"   Base URL: {base_url}")
    print(f"   Agent ID: {agent_id}")
    print(f"   Converse Endpoint: {converse_endpoint}")
    print()

    # Create headers (per Elastic docs: requires kbn-xsrf header)
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
        "Authorization": f"ApiKey {ARCHIVIST_API_KEY}"
    }

    # Build request (per Elastic docs format)
    converse_request = {
        "input": search_query,
        "agent_id": agent_id
    }

    print("📨 Sending Request:")
    print(f"   Timeout: 120 seconds")
    print(f"   Request Body:")
    print(json.dumps(converse_request, indent=4))
    print()

    try:
        start_time = time.time()

        async with httpx.AsyncClient(timeout=120.0) as http_client:
            print("⏳ Waiting for Archivist response...")

            response = await http_client.post(
                converse_endpoint,
                json=converse_request,
                headers=headers
            )

            elapsed = time.time() - start_time

            print(f"\n📥 Response Received:")
            print(f"   Elapsed Time: {elapsed:.1f} seconds")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Size: {len(response.text)} characters")
            print()

            # Check status code
            if response.status_code != 200:
                print(f"❌ ERROR: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                response.raise_for_status()
                return False

            # Parse response
            result = response.json()

            print("📄 Response Structure:")
            print(f"   Keys: {list(result.keys())}")
            print()

            # Extract text response from Elastic Conversational API
            # Response structure: {"conversation_id": "...", "steps": [...], "response": {...}}
            conversation_id = result.get("conversation_id", "")

            # The response is in the steps array, particularly in tool_call results
            full_response = ""
            articles = []

            steps = result.get("steps", [])
            for step in steps:
                if step.get("type") == "tool_call" and "results" in step:
                    # Extract results from the tool call
                    for tool_result in step.get("results", []):
                        if tool_result.get("type") == "resource":
                            data = tool_result.get("data", {})
                            content = data.get("content", {})

                            # Extract highlights or full text
                            highlights = content.get("highlights", [])
                            if highlights:
                                full_response += "\n".join(highlights) + "\n\n"

                            # Store article reference
                            reference = data.get("reference", {})
                            if reference:
                                articles.append({
                                    "id": reference.get("id", "unknown"),
                                    "index": reference.get("index", "unknown"),
                                    "content": "\n".join(highlights) if highlights else ""
                                })

            # Also check the response field for final answer
            response_field = result.get("response", {})
            if isinstance(response_field, dict):
                response_text = response_field.get("text", response_field.get("message", response_field.get("content", "")))
                if response_text:
                    full_response += response_text
            elif isinstance(response_field, str) and response_field:
                full_response += response_field

            if not full_response.strip():
                print("⚠️  WARNING: No response text found in any expected field")
                print("   Full Response Structure:")
                print(json.dumps(result, indent=4)[:2000])
                print()
                return False

            # Display results (same format as reporter.py)
            print("=" * 80)
            print("📚 ARCHIVIST SEARCH RESULTS:")
            print("=" * 80)
            print(f"   🔍 Search Query: {search_query}")
            print(f"   💬 Conversation ID: {conversation_id}")
            print(f"   📊 Found {len(articles)} historical articles")
            print(f"   📝 Response Length: {len(full_response)} characters")
            print()

            if articles:
                print("   📰 Article References:")
                for i, article in enumerate(articles, 1):
                    article_id = article.get('id', 'Unknown')
                    article_index = article.get('index', 'Unknown')
                    content = article.get('content', '')
                    preview = content[:100] if content else "No content"
                    print(f"      {i}. {article_id} (index: {article_index})")
                    print(f"         Preview: {preview}...")
                print()
            print("   Response Preview:")
            print("   " + "-" * 76)

            # Show first 500 characters
            preview = full_response[:500]
            for line in preview.split('\n'):
                print(f"   {line}")

            if len(full_response) > 500:
                print(f"   ... (truncated, showing 500 of {len(full_response)} chars)")

            print("   " + "-" * 76)
            print()

            # Save full response to file for inspection
            output_file = "archivist_test_response.txt"
            with open(output_file, 'w') as f:
                f.write(f"Archivist Test Response\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"Query: {search_query}\n")
                f.write(f"Conversation ID: {conversation_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(full_response)

            print(f"💾 Full response saved to: {output_file}")
            print()

            # Test success
            print("=" * 80)
            print("✅ ARCHIVIST TEST PASSED")
            print("=" * 80)
            print(f"   Successfully received {len(full_response)} characters")
            print(f"   Elapsed time: {elapsed:.1f} seconds")
            print(f"   The Archivist integration is working correctly!")
            print()

            return True

    except httpx.TimeoutException as e:
        elapsed = time.time() - start_time
        print(f"\n❌ TIMEOUT ERROR after {elapsed:.1f} seconds")
        print(f"   The Archivist took too long to respond (> 120 seconds)")
        print(f"   Error: {e}")
        print()
        return False

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP ERROR: {e}")
        print(f"   Status Code: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        print()
        return False

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def main():
    """Run the Archivist test"""
    success = await test_archivist_converse_api()

    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    if not success:
        print("⚠️  Test failed. Please check the error messages above.")
        print()
        print("Common issues:")
        print("   1. ELASTIC_ARCHIVIST_AGENT_CARD_URL not set in .env")
        print("   2. ELASTIC_ARCHIVIST_API_KEY not set or invalid in .env")
        print("   3. Network connectivity issues")
        print("   4. Archivist agent is down or unavailable")
        print()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Quick test script to verify CrewAI Researcher A2A protocol communication.

Tests both the JSON-RPC endpoint and the native REST endpoint.
"""

import asyncio
import json
import httpx

RESEARCHER_URL = "http://localhost:8083"


async def test_agent_card():
    """Test 1: Agent card discovery"""
    print("🔍 Test 1: Agent Card Discovery")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RESEARCHER_URL}/.well-known/agent-card.json")
            if response.status_code == 200:
                card = response.json()
                print(f"✅ Agent card retrieved: {card['name']} v{card['version']}")
                print(f"   Implementation: {card['implementation']}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_jsonrpc_endpoint():
    """Test 2: A2A JSON-RPC protocol (how Reporter calls it)"""
    print("\n🔍 Test 2: A2A JSON-RPC Protocol (Root Endpoint)")

    # Construct A2A JSON-RPC request
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": "test-123",
        "method": "tasks/send",
        "params": {
            "input": {
                "parts": [{
                    "text": json.dumps({
                        "action": "research_questions",
                        "story_id": "test_story_001",
                        "topic": "AI Testing",
                        "questions": [
                            "What is the current state of AI testing?",
                            "What are common AI testing frameworks?"
                        ]
                    })
                }]
            }
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"📤 Sending JSON-RPC request to {RESEARCHER_URL}/")
            response = await client.post(
                RESEARCHER_URL + "/",
                json=jsonrpc_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ JSON-RPC response received")
                print(f"   Response ID: {result.get('id')}")

                # Extract result text
                if "result" in result and "parts" in result["result"]:
                    result_text = result["result"]["parts"][0]["text"]
                    result_data = json.loads(result_text)
                    print(f"   Status: {result_data.get('status')}")
                    print(f"   Research ID: {result_data.get('research_id')}")
                    print(f"   Results: {result_data.get('total_questions')} questions answered")
                    return True
                else:
                    print(f"⚠️  Unexpected response format: {result}")
                    return False
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_native_endpoint():
    """Test 3: Native CrewAI REST endpoint"""
    print("\n🔍 Test 3: Native CrewAI REST Endpoint")

    request_data = {
        "story_id": "test_story_002",
        "topic": "Python Testing",
        "questions": [
            "What are the best Python testing frameworks?",
            "How to write effective unit tests?"
        ]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"📤 Sending REST request to {RESEARCHER_URL}/research")
            response = await client.post(
                f"{RESEARCHER_URL}/research",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ REST response received")
                print(f"   Status: {result.get('status')}")
                print(f"   Research ID: {result.get('research_id')}")
                print(f"   Results: {result.get('total_questions')} questions answered")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def test_health():
    """Test 4: Health check"""
    print("\n🔍 Test 4: Health Check")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RESEARCHER_URL}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Health check passed: {health}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def main():
    """Run all tests"""
    print("=" * 70)
    print("CrewAI Researcher - A2A Protocol Test Suite")
    print("=" * 70)

    results = []

    # Run tests
    results.append(await test_health())
    results.append(await test_agent_card())
    results.append(await test_jsonrpc_endpoint())
    results.append(await test_native_endpoint())

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! CrewAI Researcher is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

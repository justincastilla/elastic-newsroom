#!/usr/bin/env python
"""
Simple test script to verify Event Hub receives events during a full workflow.
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_event_hub_workflow():
    """Test that Event Hub receives events from a complete workflow"""

    print("=" * 80)
    print("Testing Event Hub with Full Agent Workflow")
    print("=" * 80)

    # Step 1: Check Event Hub is running
    print("\n1. Checking Event Hub status...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get("http://localhost:8090/")
            status = response.json()
            print(f"   ✅ Event Hub is running")
            print(f"   Events stored: {status['events_stored']}")
            print(f"   WebSocket connections: {status['connections']}")
        except Exception as e:
            print(f"   ❌ Event Hub not available: {e}")
            return

    # Step 2: Clear any existing events
    print("\n2. Clearing existing events...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Get current event count
            response = await client.get("http://localhost:8090/events")
            current_events = response.json()["events"]
            print(f"   Found {len(current_events)} existing events")
        except Exception as e:
            print(f"   ❌ Error getting events: {e}")
            return

    # Step 3: Assign a story to trigger workflow
    print("\n3. Assigning a story to News Chief...")
    story_id = f"story_event_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    assignment = {
        "action": "assign_story",
        "story": {
            "story_id": story_id,
            "topic": "Event Hub Integration Test",
            "angle": "Testing real-time event publishing across all agents",
            "target_length": 500,
            "priority": "high"
        }
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            response = await client.post(
                "http://localhost:8080",
                json={
                    "id": "test-001",
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "user",
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": json.dumps(assignment)
                                }
                            ]
                        },
                        "configuration": {
                            "blocking": True
                        }
                    }
                }
            )
            print(f"   ✅ Story assigned successfully (Story ID: {story_id})")
        except Exception as e:
            print(f"   ❌ Error assigning story: {e}")
            return

    # Step 4: Wait for workflow to complete
    print("\n4. Waiting for workflow to complete...")
    await asyncio.sleep(90)  # Give workflow time to complete

    # Step 5: Query Event Hub for events from this story
    print("\n5. Querying Event Hub for workflow events...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"http://localhost:8090/events?story_id={story_id}"
            )
            data = response.json()
            events = data["events"]

            print(f"\n   📊 Event Hub received {len(events)} events for story {story_id}")
            print("\n   Event Timeline:")
            print("   " + "-" * 76)

            for i, event in enumerate(events, 1):
                agent = event.get("agent", "Unknown")
                event_type = event.get("event_type", "unknown")
                timestamp = event.get("timestamp", "")
                data_summary = event.get("data", {})

                print(f"   {i:2}. [{timestamp}] {agent:15} → {event_type}")

                # Show relevant data for each event
                if "word_count" in data_summary:
                    print(f"       Word Count: {data_summary['word_count']}")
                if "question_count" in data_summary:
                    print(f"       Questions: {data_summary['question_count']}")
                if "approval_status" in data_summary:
                    print(f"       Status: {data_summary['approval_status']}")
                if "elasticsearch_indexed" in data_summary:
                    print(f"       ES Indexed: {data_summary['elasticsearch_indexed']}")

            print("   " + "-" * 76)

            # Verify expected events
            print("\n6. Verifying expected events are present...")
            expected_events = [
                ("NewsChiefAgent", "story_assigned"),
                ("ReporterAgent", "assignment_accepted"),
                ("ReporterAgent", "outline_generated"),
                ("ReporterAgent", "research_requested"),
                ("ResearcherAgent", "research_started"),
                ("ResearcherAgent", "research_completed"),
                ("ReporterAgent", "article_drafted"),
                ("EditorAgent", "review_started"),
                ("EditorAgent", "review_completed"),
                ("ReporterAgent", "edits_applied"),
                ("PublisherAgent", "publication_started"),
                ("PublisherAgent", "file_saved"),
                ("PublisherAgent", "publication_completed"),
            ]

            found_events = set()
            for event in events:
                agent = event.get("agent", "")
                event_type = event.get("event_type", "")
                found_events.add((agent, event_type))

            missing_events = []
            for expected in expected_events:
                if expected in found_events:
                    print(f"   ✅ {expected[0]:20} {expected[1]}")
                else:
                    print(f"   ❌ {expected[0]:20} {expected[1]} (MISSING)")
                    missing_events.append(expected)

            print("\n" + "=" * 80)
            if len(events) > 0 and len(missing_events) == 0:
                print("✅ SUCCESS: Event Hub integration working correctly!")
                print(f"   All {len(expected_events)} expected events received")
            elif len(events) > 0:
                print(f"⚠️  PARTIAL SUCCESS: Received {len(events)} events")
                print(f"   Missing {len(missing_events)} expected events")
            else:
                print("❌ FAILURE: No events received from workflow")
            print("=" * 80)

        except Exception as e:
            print(f"   ❌ Error querying events: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_event_hub_workflow())

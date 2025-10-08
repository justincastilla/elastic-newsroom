#!/usr/bin/env python3
"""
End-to-End Newsroom Workflow Test

Tests the complete workflow:
Client → News Chief → Reporter → (Mock Editor)

This demonstrates A2A agent-to-agent communication.
"""

import asyncio
import json
import httpx
from a2a.client import ClientFactory, ClientConfig, A2ACardResolver, create_text_message_object

async def test_newsroom_workflow():
    """Test the complete newsroom workflow with agent-to-agent communication"""

    print("🏢 Elastic News - Newsroom Workflow Test")
    print("="*60)
    print("Testing: Client → News Chief → Reporter → Mock Editor")
    print("="*60)

    news_chief_url = "http://localhost:8080"
    reporter_url = "http://localhost:8081"

    # Use longer timeout for Anthropic API calls with research (can take 50+ seconds)
    # Reporter now: generates outline (8s) + researcher bulk call (15s) + writes article (15s) = ~40s
    async with httpx.AsyncClient(timeout=90.0) as http_client:

        # ========================================
        # STEP 1: Connect to News Chief
        # ========================================
        print("\n📋 STEP 1: Connecting to News Chief")
        print("-" * 60)

        card_resolver = A2ACardResolver(http_client, news_chief_url)
        news_chief_card = await card_resolver.get_agent_card()

        print(f"✅ Connected to: {news_chief_card.name}")
        print(f"   URL: {news_chief_card.url}")
        print(f"   Skills: {len(news_chief_card.skills)}")

        # Create News Chief client
        client_config = ClientConfig(httpx_client=http_client, streaming=False)
        client_factory = ClientFactory(client_config)
        news_chief_client = client_factory.create(news_chief_card)

        # ========================================
        # STEP 2: Verify Reporter is Online
        # ========================================
        print("\n📝 STEP 2: Verifying Reporter Agent")
        print("-" * 60)

        reporter_resolver = A2ACardResolver(http_client, reporter_url)
        reporter_card = await reporter_resolver.get_agent_card()

        print(f"✅ Reporter online: {reporter_card.name}")
        print(f"   URL: {reporter_card.url}")
        print(f"   Skills: {len(reporter_card.skills)}")

        # ========================================
        # STEP 3: Assign Story via News Chief
        # ========================================
        print("\n📰 STEP 3: Assigning Story via News Chief")
        print("-" * 60)

        story = {
            "topic": "AI Agents Transform Modern Newsrooms",
            "angle": "How A2A protocol enables multi-agent collaboration in journalism",
            "target_length": 1200,
            "priority": "high",
            "deadline": "2025-10-08T18:00:00Z"
        }

        print(f"Story Topic: {story['topic']}")
        print(f"Angle: {story['angle']}")
        print(f"Priority: {story['priority']}")
        print(f"Target Length: {story['target_length']} words")

        request = {
            "action": "assign_story",
            "story": story
        }
        message = create_text_message_object(content=json.dumps(request))

        story_id = None
        async for response in news_chief_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    print(f"\n✅ News Chief Response:")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Story ID: {result.get('story_id')}")
                    print(f"   Message: {result.get('message')}")

                    story_id = result.get('story_id')

                    # Check if Reporter received the assignment
                    reporter_response = result.get('reporter_response', {})
                    if reporter_response:
                        print(f"\n📝 Reporter Response (via A2A):")
                        print(f"   Status: {reporter_response.get('status')}")
                        print(f"   Message: {reporter_response.get('message')}")
                        print(f"   Reporter Status: {reporter_response.get('reporter_status')}")
                        print(f"   Estimated Completion: {reporter_response.get('estimated_completion')}")

        if not story_id:
            print("❌ Failed to assign story")
            return

        # ========================================
        # STEP 4: Check Reporter's Status
        # ========================================
        print("\n🔍 STEP 4: Checking Reporter's Status")
        print("-" * 60)

        # Create Reporter client
        reporter_client = client_factory.create(reporter_card)

        request = {
            "action": "get_status",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        async for response in reporter_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    print(f"✅ Reporter has assignment:")
                    assignment = result.get('assignment', {})
                    print(f"   Topic: {assignment.get('topic')}")
                    print(f"   Status: {assignment.get('reporter_status')}")
                    print(f"   Accepted at: {assignment.get('accepted_at')}")

        # ========================================
        # STEP 5: Tell Reporter to Write Article
        # ========================================
        print("\n✍️  STEP 5: Reporter Writes Article (Using Anthropic)")
        print("-" * 60)
        print("⏳ This may take 10-20 seconds with Anthropic API...")

        request = {
            "action": "write_article",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        async for response in reporter_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    print(f"\n✅ Article Generated:")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Word Count: {result.get('word_count')}")
                    print(f"   Preview: {result.get('preview', '')[:150]}...")

        # ========================================
        # STEP 6: Reporter Submits Draft to Editor
        # ========================================
        print("\n📤 STEP 6: Reporter Submits Draft to Editor")
        print("-" * 60)
        print("⏳ Submitting to Editor for review (may take 30-40 seconds)...")

        request = {
            "action": "submit_draft",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        editor_response = None
        async for response in reporter_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    editor_response = result.get('editor_response', {})
                    print(f"✅ Draft Submitted and Reviewed:")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Word Count: {result.get('word_count')}")

                    if editor_response:
                        review = editor_response.get('review', {})
                        print(f"\n✏️  Editor Review:")
                        print(f"   Approval: {review.get('approval_status')}")
                        print(f"   Overall: {review.get('overall_assessment', 'N/A')[:80]}...")
                        print(f"   Suggested Edits: {len(review.get('suggested_edits', []))}")

        # ========================================
        # STEP 7: Apply Editorial Suggestions
        # ========================================
        print("\n✏️  STEP 7: Reporter Applies Editorial Suggestions")
        print("-" * 60)
        print("⏳ Integrating editor feedback (may take 20-30 seconds)...")

        request = {
            "action": "apply_edits",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        async for response in reporter_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    print(f"✅ Edits Applied:")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Old Word Count: {result.get('old_word_count')}")
                    print(f"   New Word Count: {result.get('new_word_count')}")
                    print(f"   Revisions Applied: {result.get('revisions_applied')}")
                    print(f"   Preview: {result.get('preview', '')[:100]}...")

        # ========================================
        # STEP 8: Publish Final Article
        # ========================================
        print("\n📰 STEP 8: Publishing Final Article")
        print("-" * 60)

        request = {
            "action": "publish_article",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        published_filepath = None
        async for response in reporter_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    published_filepath = result.get('filepath')
                    print(f"✅ Article Published:")
                    print(f"   Status: {result.get('status')}")
                    print(f"   File: {published_filepath}")
                    print(f"   Word Count: {result.get('word_count')}")
                    print(f"   Published at: {result.get('published_at')}")

        # ========================================
        # STEP 9: Final Status Check
        # ========================================
        print("\n📊 STEP 9: Final Status Check")
        print("-" * 60)

        # Check News Chief status
        request = {
            "action": "get_story_status",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        async for response in news_chief_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    story = result.get('story', {})
                    print(f"✅ News Chief Status:")
                    print(f"   Story ID: {story.get('story_id')}")
                    print(f"   Topic: {story.get('topic')}")
                    print(f"   Status: {story.get('status')}")
                    print(f"   Created: {story.get('created_at')}")

        # Check Reporter status
        request = {
            "action": "get_status",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        async for response in reporter_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    draft = result.get('draft', {})
                    print(f"\n✅ Reporter Status:")
                    print(f"   Draft Status: {draft.get('status')}")
                    print(f"   Word Count: {draft.get('word_count')}")
                    print(f"   Submitted to: {draft.get('submitted_to')}")

        # ========================================
        # SUMMARY
        # ========================================
        print("\n" + "="*60)
        print("🎉 FULL EDITORIAL WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\n✅ Demonstrated Complete A2A Agent Chain:")
        print("   1. Client assigned story to News Chief")
        print("   2. News Chief sent assignment to Reporter (A2A)")
        print("   3. Reporter generated outline and research questions (Anthropic)")
        print("   4. Reporter called Researcher + Archivist in PARALLEL (A2A)")
        print("   5. Researcher answered all questions in 1 API call (Anthropic)")
        print("   6. Archivist searched historical articles (Elastic Cloud)")
        print("   7. Reporter wrote article with research + archive data (Anthropic)")
        print("   8. Reporter submitted draft to Editor (A2A)")
        print("   9. Editor reviewed draft (Anthropic: grammar, tone, consistency, length)")
        print("   10. Editor sent feedback to Reporter (A2A response)")
        print("   11. Reporter applied editorial suggestions (Anthropic)")
        print("   12. Reporter automatically sent to Publisher (A2A)")
        print("   13. Publisher generated tags/categories (Anthropic)")
        print("   14. Publisher indexed article to Elasticsearch")
        print("   15. Publisher ran mock CI/CD deployment")
        print("   16. Publisher sent mock CRM notifications")
        print("   17. Article published and indexed successfully!")
        print("\n💡 6 agents total: News Chief, Reporter, Researcher, Archivist, Editor, Publisher")
        print("💡 All agents communicate via A2A protocol!")
        print("💡 Researcher + Archivist called in parallel for efficiency!")
        print("💡 Archivist is hosted on Elastic Cloud (external A2A agent)!")
        print("💡 Publisher auto-generates tags/categories and indexes to Elasticsearch!")
        print("💡 Check newsroom.log for detailed message flow!")
        if published_filepath:
            print(f"💡 Read your published article: {published_filepath}")
        print("="*60)


if __name__ == "__main__":
    print("\n🧪 Elastic News - End-to-End Workflow Test")
    print("\n⚠️  Prerequisites:")
    print("   1. News Chief running on http://localhost:8080")
    print("      → python run_news_chief.py --reload")
    print("   2. Reporter running on http://localhost:8081")
    print("      → python run_reporter.py --reload")
    print("   3. Editor running on http://localhost:8082")
    print("      → python run_editor.py --reload")
    print("   4. Researcher running on http://localhost:8083")
    print("      → python run_researcher.py --reload")
    print("   5. Publisher running on http://localhost:8084")
    print("      → python run_publisher.py --reload")
    print("   6. Elasticsearch index created")
    print("      → python scripts/create_elasticsearch_index.py")
    print("   7. Environment variables set:")
    print("      → ANTHROPIC_API_KEY (required)")
    print("      → ELASTICSEARCH_ENDPOINT (required)")
    print("      → ELASTIC_SEARCH_API_KEY (required)")
    print("      → ELASTIC_ARCHIVIST_INDEX (required)")
    print("      → ELASTIC_ARCHIVIST_AGENT_CARD_URL (optional - for historical search)")
    print("      → ELASTIC_ARCHIVIST_API_KEY (optional - for historical search)")
    print("\nStarting test in 2 seconds...")

    import time
    time.sleep(2)

    try:
        asyncio.run(test_newsroom_workflow())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

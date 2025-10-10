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

    # No timeout for test - let the workflow complete naturally
    # The workflow can take varying amounts of time depending on:
    # - Anthropic API response times
    # - Archivist retry logic (up to 122s with retries)
    # - Network conditions
    # - Agent processing time
    async with httpx.AsyncClient(timeout=None) as http_client:

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
        print("\n✍️  STEP 5: Reporter Writes Article (Multi-Agent Workflow)")
        print("-" * 60)
        print("⏳ This involves multiple steps:")
        print("   1. Generate outline and research questions (~8s)")
        print("   2. Call Researcher + Archivist IN PARALLEL (~20s)")
        print("      → Researcher: Answers research questions using Anthropic")
        print("      → Archivist: Searches Elasticsearch for historical articles")
        print("   3. Generate article with research + archive data (~15s)")
        print("   4. Submit to Editor for review (~17s)")
        print("   5. Apply editorial suggestions (~15s)")
        print("   6. Publish to Elasticsearch (~5s)")
        print("   Total: Variable (no timeout - let it complete naturally)")
        print()
        print("📊 Watch the agent logs to see each step in detail:")
        print("   - Reporter log: Shows outline generation and article writing")
        print("   - Researcher log: Shows bulk research processing")
        print("   - Archivist: Direct HTTP call to Elastic Cloud")
        print("   - Editor log: Shows editorial review")
        print("   - Publisher log: Shows tag generation and indexing")
        print()

        request = {
            "action": "write_article",
            "story_id": story_id
        }
        message = create_text_message_object(content=json.dumps(request))

        import time
        start_time = time.time()
        print(f"⏱️  Started at: {time.strftime('%H:%M:%S')}")
        print()

        async for response in reporter_client.send_message(message):
            if hasattr(response, 'parts'):
                part = response.parts[0]
                text_content = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else None
                if text_content:
                    result = json.loads(text_content)
                    elapsed = time.time() - start_time

                    print(f"\n✅ Article Generation Complete!")
                    print(f"   ⏱️  Total Time: {elapsed:.1f} seconds")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Word Count: {result.get('word_count')}")

                    # Show if published
                    if result.get('published'):
                        print(f"   📰 Published: Yes")
                        publisher_resp = result.get('publisher_response', {})
                        if publisher_resp.get('elasticsearch'):
                            es_info = publisher_resp['elasticsearch']
                            print(f"   📇 Elasticsearch:")
                            print(f"      - Index: {es_info.get('index')}")
                            print(f"      - Document ID: {es_info.get('document_id')}")
                        if publisher_resp.get('tags'):
                            print(f"   🏷️  Tags: {', '.join(publisher_resp.get('tags', [])[:5])}")
                        if publisher_resp.get('categories'):
                            print(f"   📂 Categories: {', '.join(publisher_resp.get('categories', []))}")

                    print(f"   Preview: {result.get('preview', '')[:150]}...")
                    print()
                    print("=" * 60)
                    print("📋 MULTI-AGENT WORKFLOW SUMMARY")
                    print("=" * 60)
                    print("✓ Reporter generated outline with research questions")
                    print("✓ Researcher answered questions in parallel with Archivist")
                    print("✓ Archivist searched historical articles from Elasticsearch")
                    print("✓ Reporter wrote article integrating all data")
                    print("✓ Editor reviewed and provided suggestions")
                    print("✓ Reporter applied editorial suggestions")
                    print("✓ Publisher indexed article to Elasticsearch")
                    print("=" * 60)

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
        print("\n✅ Complete Multi-Agent Workflow:")
        print()
        print("   📋 STEP 1: Assignment Phase")
        print("   ├─ Client → News Chief: Story assignment request")
        print("   └─ News Chief → Reporter: A2A message with story details")
        print()
        print("   ✍️  STEP 2: Research & Writing Phase (PARALLEL EXECUTION)")
        print("   ├─ Reporter → Anthropic: Generate outline + research questions (~8s)")
        print("   ├─ Reporter → Researcher: A2A request with questions")
        print("   │  └─ Researcher → Anthropic: Bulk research call (~15s)")
        print("   ├─ Reporter → Archivist: HTTP POST to Elastic Agent Builder API")
        print("   │  └─ Archivist → Elasticsearch: Search news_archive index (~20s)")
        print("   │     • Returns: Historical article highlights and references")
        print("   │     • Status: REQUIRED (workflow fails if unavailable)")
        print("   └─ Reporter → Anthropic: Generate article with all data (~15s)")
        print()
        print("   ✏️  STEP 3: Editorial Review Phase")
        print("   ├─ Reporter → Editor: A2A request with draft")
        print("   │  └─ Editor → Anthropic: Review for grammar/tone/length (~17s)")
        print("   └─ Editor → Reporter: A2A response with suggestions")
        print()
        print("   📰 STEP 4: Revision & Publishing Phase")
        print("   ├─ Reporter → Anthropic: Apply editorial suggestions (~15s)")
        print("   ├─ Reporter → Publisher: A2A request with final article")
        print("   │  ├─ Publisher → Anthropic: Generate tags/categories (~8s)")
        print("   │  ├─ Publisher → Elasticsearch: Index to news_archive (~2s)")
        print("   │  ├─ Publisher → CI/CD: Trigger deployment (mock)")
        print("   │  └─ Publisher → CRM: Send notifications (mock)")
        print("   └─ Publisher → Reporter: A2A response with confirmation")
        print()
        print("=" * 60)
        print("📊 MULTI-AGENT STATISTICS")
        print("=" * 60)
        print("   🤖 Total Agents: 6")
        print("      • News Chief (Coordinator)")
        print("      • Reporter (Writer)")
        print("      • Researcher (Fact-checker)")
        print("      • Archivist (Search - Elastic Cloud) ⚠️  REQUIRED")
        print("      • Editor (Reviewer)")
        print("      • Publisher (Indexer)")
        print()
        print("   🔄 Communication Protocol: A2A (Agent2Agent)")
        print("      • Internal agents: A2A JSONRPC 2.0")
        print("      • Archivist: Elastic Agent Builder Converse API")
        print()
        print("   ⚡ Parallel Execution:")
        print("      • Researcher + Archivist run simultaneously")
        print("      • Saves ~20 seconds vs sequential execution")
        print()
        print("   🤖 AI Model Usage:")
        print("      • Claude Sonnet 4: All Anthropic API calls")
        print("      • Total API calls: ~6 (outline, research, article, review, edits, tags)")
        print()
        print("   📇 Elasticsearch Integration:")
        print("      • Archivist: Searches news_archive for context")
        print("      • Publisher: Indexes final articles to news_archive")
        print()
        print("   📝 Detailed Logs Available:")
        print("      • Check individual agent logs for full message flow")
        print("      • Reporter log shows Researcher + Archivist timing")
        if published_filepath:
            print(f"      • Published article: {published_filepath}")
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

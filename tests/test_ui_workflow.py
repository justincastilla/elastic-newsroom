"""
Test UI to Agent Workflow

Tests the complete workflow from UI submission to article completion,
mimicking how the UI interacts with the News Chief agent.
"""

import asyncio
import json
import httpx
from datetime import datetime


class UIWorkflowTester:
    """Test the UI workflow end-to-end"""

    def __init__(self, news_chief_url: str = "http://localhost:8080"):
        self.news_chief_url = news_chief_url

    async def send_jsonrpc_request(self, action_payload: dict) -> dict:
        """Send a JSON-RPC 2.0 request to News Chief (mimics UI behavior)"""
        message_id = f"test_{datetime.now().timestamp()}"

        rpc_request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"text": json.dumps(action_payload)}],
                }
            },
            "id": 1,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.news_chief_url}/",
                json=rpc_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            rpc_response = response.json()

            # Extract result from JSON-RPC response
            if "result" in rpc_response:
                result_message = rpc_response["result"]
                if "parts" in result_message and len(result_message["parts"]) > 0:
                    text_content = result_message["parts"][0].get("text", "{}")
                    return json.loads(text_content)

            raise Exception(f"Unexpected response format: {rpc_response}")

    async def assign_story(self, topic: str, angle: str, target_length: int) -> dict:
        """Assign a story to News Chief (mimics UI form submission)"""
        print(f"\n{'='*60}")
        print(f"📝 ASSIGNING STORY")
        print(f"{'='*60}")
        print(f"Topic: {topic}")
        print(f"Angle: {angle}")
        print(f"Target Length: {target_length} words")

        payload = {
            "action": "assign_story",
            "story": {
                "topic": topic,
                "angle": angle,
                "target_length": target_length,
                "deadline": "",
                "priority": "normal",
            }
        }

        result = await self.send_jsonrpc_request(payload)

        if result.get("status") == "success":
            story_id = result.get("story_id")
            print(f"\n✅ Story assigned successfully!")
            print(f"   Story ID: {story_id}")
            print(f"   Status: {result['assignment']['status']}")
            return result
        else:
            print(f"\n❌ Story assignment failed: {result.get('message')}")
            raise Exception(f"Story assignment failed: {result.get('message')}")

    async def get_story_status(self, story_id: str) -> dict:
        """Get story status from News Chief (mimics UI polling)"""
        payload = {
            "action": "get_story_status",
            "story_id": story_id
        }

        result = await self.send_jsonrpc_request(payload)

        if result.get("status") == "success":
            return result.get("story", {})
        else:
            raise Exception(f"Failed to get status: {result.get('message')}")

    async def poll_until_complete(self, story_id: str, max_polls: int = 60, poll_interval: int = 2) -> dict:
        """Poll for story completion (mimics UI behavior)"""
        print(f"\n{'='*60}")
        print(f"⏳ POLLING FOR COMPLETION")
        print(f"{'='*60}")
        print(f"Story ID: {story_id}")
        print(f"Max polls: {max_polls} (timeout: {max_polls * poll_interval}s)")

        status_map = {
            "pending": "📋 Waiting to start...",
            "assigned": "📝 Assignment sent to Reporter...",
            "writing": "✍️ Reporter is writing the article...",
            "researching": "🔍 Researcher gathering information...",
            "editing": "✏️ Editor reviewing the article...",
            "publishing": "📤 Publisher preparing to publish...",
            "completed": "✅ Article complete!",
            "published": "✅ Article published!",
            "error": "❌ Error in workflow"
        }

        poll_count = 0
        last_status = None

        while poll_count < max_polls:
            story = await self.get_story_status(story_id)
            current_status = story.get("status", "unknown")

            # Only print if status changed
            if current_status != last_status:
                message = status_map.get(current_status, f"Working... ({current_status})")
                print(f"\n[Poll #{poll_count + 1}] {message}")
                last_status = current_status

            # Check if workflow is complete
            if current_status in ["completed", "published"]:
                print(f"\n{'='*60}")
                print(f"🎉 WORKFLOW COMPLETE!")
                print(f"{'='*60}")
                print(f"Final Status: {current_status}")
                print(f"Total polls: {poll_count + 1}")
                print(f"Time elapsed: ~{(poll_count + 1) * poll_interval}s")
                return story

            # Check for errors
            if current_status == "error":
                print(f"\n❌ Workflow encountered an error")
                return story

            await asyncio.sleep(poll_interval)
            poll_count += 1

        print(f"\n⏱️ Polling timeout after {max_polls * poll_interval}s")
        print(f"Last known status: {last_status}")
        return story

    async def run_full_workflow(self, topic: str, angle: str, target_length: int = 800) -> dict:
        """Run the complete UI workflow end-to-end"""
        print(f"\n{'#'*60}")
        print(f"# UI WORKFLOW TEST")
        print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}")

        try:
            # Step 1: Assign story
            assignment_result = await self.assign_story(topic, angle, target_length)
            story_id = assignment_result.get("story_id")

            if not story_id:
                raise Exception("No story_id returned from assignment")

            # Step 2: Poll for completion
            final_story = await self.poll_until_complete(story_id)

            # Step 3: Verify article file was created
            print(f"\n{'='*60}")
            print(f"📄 VERIFYING ARTICLE FILE")
            print(f"{'='*60}")

            import os
            import glob

            # Look for article file matching the story_id
            article_pattern = f"articles/*{story_id}*.md"
            matching_files = glob.glob(article_pattern)

            article_exists = len(matching_files) > 0

            if article_exists:
                article_path = matching_files[0]
                file_size = os.path.getsize(article_path)
                print(f"✅ Article file found: {article_path}")
                print(f"   File size: {file_size} bytes")

                # Read first few lines to verify content
                with open(article_path, 'r') as f:
                    first_lines = [f.readline() for _ in range(5)]
                    print(f"   First line: {first_lines[0].strip()}")
            else:
                print(f"❌ Article file NOT found")
                print(f"   Pattern searched: {article_pattern}")
                print(f"   Files in articles/: {os.listdir('articles') if os.path.exists('articles') else 'directory does not exist'}")

            # Step 4: Summary
            print(f"\n{'='*60}")
            print(f"📊 TEST SUMMARY")
            print(f"{'='*60}")
            print(f"Story ID: {story_id}")
            print(f"Topic: {topic}")
            print(f"Final Status: {final_story.get('status')}")
            print(f"Created: {final_story.get('created_at')}")
            print(f"Updated: {final_story.get('updated_at')}")
            print(f"Article File: {'✅ Created' if article_exists else '❌ NOT Created'}")

            # Test only passes if status is completed AND article file exists
            if final_story.get('status') == 'completed' and article_exists:
                print(f"\n✅ TEST PASSED: Workflow completed and article published!")
                return {"status": "success", "story": final_story, "article_path": article_path if article_exists else None}
            elif not article_exists:
                print(f"\n❌ TEST FAILED: Article file was not created")
                return {"status": "failed", "reason": "Article file not created", "story": final_story}
            else:
                print(f"\n⚠️  TEST INCOMPLETE: Final status is '{final_story.get('status')}'")
                return {"status": "incomplete", "story": final_story}

        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ TEST FAILED")
            print(f"{'='*60}")
            print(f"Error: {str(e)}")
            return {"status": "error", "error": str(e)}


async def main():
    """Run the UI workflow test"""
    tester = UIWorkflowTester()

    # Test story assignment
    result = await tester.run_full_workflow(
        topic="Sustainable Data Centers",
        angle="Environmental impact and green computing initiatives in cloud infrastructure",
        target_length=800
    )

    # Exit with appropriate code
    if result.get("status") == "success":
        print(f"\n{'='*60}")
        print(f"🎉 All tests passed!")
        print(f"{'='*60}\n")
        exit(0)
    else:
        print(f"\n{'='*60}")
        print(f"❌ Tests failed or incomplete")
        print(f"{'='*60}\n")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())

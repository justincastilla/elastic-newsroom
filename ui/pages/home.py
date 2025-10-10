"""
Home Page - Story Assignment Form

This page allows users to assign new stories to the News Chief agent.
"""

import mesop as me
import asyncio
import logging
from state.app_state import AppState, AssignmentFormState
from services.news_chief_client import NewsChiefClient

logger = logging.getLogger(__name__)


@me.page(path="/", title="Elastic News - Assign Story")
def home_page():
    """Main page with story assignment form"""
    app_state = me.state(AppState)
    form_state = me.state(AssignmentFormState)

    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            min_height="100vh",
            background="#f5f5f5",
            padding=me.Padding.all(20),
        )
    ):
        # Header
        with me.box(
            style=me.Style(
                background="white",
                padding=me.Padding.all(20),
                border_radius=8,
                margin=me.Margin(bottom=20),
                box_shadow="0 2px 4px rgba(0,0,0,0.1)",
            )
        ):
            me.text(
                "Elastic News - Newsroom",
                style=me.Style(font_size=32, font_weight=700, color="#1a1a1a"),
            )
            me.text(
                "Assign a new story to the News Chief",
                style=me.Style(font_size=16, color="#666", margin=me.Margin(top=8)),
            )

        # Success message (story complete)
        if app_state.current_story_id and not app_state.is_loading and not app_state.error_message:
            with me.box(
                style=me.Style(
                    background="#e8f5e9",
                    border="1px solid #4caf50",
                    padding=me.Padding.all(16),
                    border_radius=8,
                    margin=me.Margin(bottom=20),
                )
            ):
                me.text(
                    "✅ Story Complete!",
                    style=me.Style(font_weight=700, color="#2e7d32", margin=me.Margin(bottom=8)),
                )
                me.text(
                    f"Your article is ready. Story ID: {app_state.current_story_id}",
                    style=me.Style(color="#2e7d32", margin=me.Margin(bottom=12)),
                )
                me.button(
                    "View Article →",
                    on_click=view_article,
                    type="flat",
                    style=me.Style(
                        background="#4caf50",
                        color="white",
                        padding=me.Padding(top=8, bottom=8, left=16, right=16),
                        border_radius=4,
                    ),
                )

        # Error message
        if app_state.error_message:
            with me.box(
                style=me.Style(
                    background="#fee",
                    border="1px solid #fcc",
                    padding=me.Padding.all(16),
                    border_radius=8,
                    margin=me.Margin(bottom=20),
                )
            ):
                me.text(
                    "❌ Error",
                    style=me.Style(font_weight=700, color="#c00", margin=me.Margin(bottom=8)),
                )
                me.text(app_state.error_message, style=me.Style(color="#c00"))
                me.button("Dismiss", on_click=clear_error)

        # Assignment Form
        with me.box(
            style=me.Style(
                background="white",
                padding=me.Padding.all(24),
                border_radius=8,
                box_shadow="0 2px 4px rgba(0,0,0,0.1)",
                max_width=800,
            )
        ):
            me.text(
                "Story Details",
                style=me.Style(font_size=24, font_weight=600, margin=me.Margin(bottom=20)),
            )

            # Topic
            me.text("Topic *", style=me.Style(font_weight=600, margin=me.Margin(bottom=4)))
            me.input(
                value=form_state.topic,
                placeholder="e.g., AI in Healthcare, Quantum Computing Breakthrough",
                on_blur=on_topic_change,
                style=me.Style(width="100%", margin=me.Margin(bottom=16)),
                disabled=app_state.is_loading,
            )

            # Angle
            me.text(
                "Editorial Angle *", style=me.Style(font_weight=600, margin=me.Margin(bottom=4))
            )
            me.textarea(
                value=form_state.angle,
                placeholder="e.g., Focus on enterprise adoption and ROI, Interview with leading researchers",
                on_blur=on_angle_change,
                rows=3,
                style=me.Style(width="100%", margin=me.Margin(bottom=16)),
                disabled=app_state.is_loading,
            )

            # Target Length
            me.text(
                "Target Length (words) *",
                style=me.Style(font_weight=600, margin=me.Margin(bottom=4)),
            )
            me.input(
                value=str(form_state.target_length),
                type="number",
                placeholder="1000",
                on_blur=on_length_change,
                style=me.Style(width=200, margin=me.Margin(bottom=16)),
                disabled=app_state.is_loading,
            )


            # Submit button or loading state
            if app_state.is_loading:
                with me.box(
                    style=me.Style(
                        display="flex",
                        align_items="center",
                        gap=12,
                        padding=me.Padding.all(16),
                        background="#e3f2fd",
                        border_radius=8,
                    )
                ):
                    me.progress_spinner()
                    me.text(
                        app_state.loading_message or "Processing...",
                        style=me.Style(color="#1976d2", font_weight=500),
                    )
            else:
                me.button(
                    "Assign Story to News Chief",
                    on_click=submit_story,
                    type="flat",
                    style=me.Style(
                        background="#1976d2",
                        color="white",
                        padding=me.Padding(top=12, bottom=12, left=24, right=24),
                        border_radius=4,
                        font_weight=600,
                    ),
                )

            # Helper text
            me.text(
                "* Required fields",
                style=me.Style(
                    font_size=12, color="#999", margin=me.Margin(top=16), font_style="italic"
                ),
            )


# Event Handlers


def on_topic_change(e: me.InputBlurEvent):
    """Update topic in state"""
    form_state = me.state(AssignmentFormState)
    form_state.topic = e.value


def on_angle_change(e: me.InputBlurEvent):
    """Update angle in state"""
    form_state = me.state(AssignmentFormState)
    form_state.angle = e.value


def on_length_change(e: me.InputBlurEvent):
    """Update target length in state"""
    form_state = me.state(AssignmentFormState)
    try:
        form_state.target_length = int(e.value) if e.value else 1000
    except ValueError:
        form_state.target_length = 1000


def clear_error(e: me.ClickEvent):
    """Clear error message"""
    app_state = me.state(AppState)
    app_state.error_message = ""


def view_article(e: me.ClickEvent):
    """Navigate to article page"""
    app_state = me.state(AppState)
    if app_state.current_story_id:
        logger.info(f"🔄 Navigating to article: {app_state.current_story_id}")
        me.navigate("/article")


def submit_story(e: me.ClickEvent):
    """Submit story assignment to News Chief"""
    app_state = me.state(AppState)
    form_state = me.state(AssignmentFormState)

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("📝 New Story Assignment Request")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Validate form
    if not form_state.topic or not form_state.angle:
        logger.warning("❌ Validation failed: Missing required fields")
        app_state.error_message = "Topic and Angle are required fields"
        return

    logger.info(f"📋 Topic: {form_state.topic}")
    logger.info(f"📐 Angle: {form_state.angle[:100]}...")
    logger.info(f"📏 Target Length: {form_state.target_length} words")

    # Clear any previous errors
    app_state.error_message = ""
    app_state.is_loading = True
    app_state.loading_message = "Submitting story assignment..."

    logger.info("🚀 Initiating story assignment...")

    # Submit the story synchronously first to get story_id
    import threading
    import queue

    result_queue = queue.Queue()

    def submit_and_get_id():
        """Submit story and get ID before navigating"""
        try:
            result = asyncio.run(_submit_story_only(form_state, app_state))
            result_queue.put(result)
        except Exception as e:
            result_queue.put({"error": str(e)})

    # Submit in thread and wait for story_id
    thread = threading.Thread(target=submit_and_get_id)
    thread.start()
    thread.join(timeout=5)  # Wait up to 5 seconds for story_id

    if not result_queue.empty():
        result = result_queue.get()
        if "error" in result:
            app_state.error_message = f"Failed to submit story: {result['error']}"
            app_state.is_loading = False
            return
        elif "story_id" in result:
            # Navigate to status page (no background polling needed)
            # User will manually refresh to see updates
            me.navigate("/status")
        else:
            app_state.error_message = "Invalid response from News Chief"
            app_state.is_loading = False
    else:
        app_state.error_message = "Story submission timed out"
        app_state.is_loading = False


async def _submit_story_only(form_state: AssignmentFormState, app_state: AppState) -> dict:
    """Submit story and return story_id"""
    client = NewsChiefClient(base_url=app_state.news_chief_url)

    try:
        logger.info("📤 Sending assignment to News Chief...")

        result = await client.assign_story(
            topic=form_state.topic,
            angle=form_state.angle,
            target_length=form_state.target_length,
            deadline="",
            priority="normal",
        )

        story_id = result.get("story_id")
        if not story_id:
            logger.error("❌ No story_id returned from News Chief")
            return {"error": "No story_id returned from News Chief"}

        logger.info(f"✅ Story assigned: {story_id}")
        app_state.current_story_id = story_id
        app_state.workflow_status = "assigned"

        return {"story_id": story_id}

    except Exception as ex:
        logger.error(f"❌ Story assignment failed: {str(ex)}", exc_info=True)
        return {"error": str(ex)}
    finally:
        await client.close()


async def _poll_status_sync(story_id: str, app_state: AppState):
    """Poll for status updates in background (DEPRECATED - not used anymore)"""
    # This function is no longer used - we do manual refresh only
    pass


async def _submit_and_poll_sync(form_state: AssignmentFormState, app_state: AppState):
    """Async function to submit story and poll for completion (runs in thread)"""
    client = NewsChiefClient(base_url=app_state.news_chief_url)

    try:
        # Submit story
        logger.info("📤 Sending assignment to News Chief...")

        result = await client.assign_story(
            topic=form_state.topic,
            angle=form_state.angle,
            target_length=form_state.target_length,
            deadline="",
            priority="normal",
        )

        # Extract story_id from result
        story_id = result.get("story_id")
        if not story_id:
            logger.error("❌ No story_id returned from News Chief")
            raise Exception("No story_id returned from News Chief")

        logger.info(f"✅ Story assigned: {story_id}")
        app_state.current_story_id = story_id
        app_state.workflow_status = "assigned"

        # Poll for status updates and show progress
        logger.info(f"⏳ Polling for workflow progress...")

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

        max_polls = 60  # Poll for up to 2 minutes (60 * 2 seconds)
        poll_count = 0

        while poll_count < max_polls:
            # Get current status
            status_response = await client.get_story_status(story_id)

            if status_response.get("status") == "success":
                story = status_response.get("story", {})
                story_status = story.get("status", "pending")

                # Update workflow status
                app_state.workflow_status = story_status

                # Update loading message based on status
                message = status_map.get(story_status, f"Working on it... ({story_status})")
                app_state.loading_message = message
                logger.info(f"📊 Status update: {story_status} - {message}")

                # Check if workflow is complete
                if story_status in ["completed", "published"]:
                    logger.info(f"🎉 Workflow complete!")
                    # Extract article data if available
                    if "article_data" in story:
                        article_data = story["article_data"]
                        app_state.article_headline = article_data.get("headline", "")
                        app_state.article_content = article_data.get("content", "")
                        app_state.article_word_count = article_data.get("word_count", 0)
                    app_state.is_loading = False
                    app_state.loading_message = ""
                    return

                # Check for errors
                if story_status == "error":
                    logger.error(f"❌ Workflow encountered an error")
                    app_state.workflow_status = "error"
                    app_state.error_message = "Workflow encountered an error. Check logs for details."
                    app_state.is_loading = False
                    app_state.loading_message = ""
                    return

            # Wait before next poll
            await asyncio.sleep(2)
            poll_count += 1

        # Timeout - but the workflow might still be running
        logger.warning(f"⏱️ Polling timeout - workflow may still be in progress")
        app_state.loading_message = "⏱️ Taking longer than expected... Check back soon!"
        await asyncio.sleep(3)
        app_state.is_loading = False
        app_state.loading_message = ""
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    except TimeoutError:
        logger.error(f"⏱️ Workflow timeout after 5 minutes")
        logger.error(f"📝 Story ID: {app_state.current_story_id or 'unknown'}")
        app_state.error_message = (
            f"Story workflow timed out after 5 minutes. "
            f"Story ID: {app_state.current_story_id or 'unknown'}"
        )
        app_state.is_loading = False
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    except Exception as ex:
        logger.error(f"❌ Story assignment failed: {str(ex)}", exc_info=True)
        app_state.error_message = f"Failed to assign story: {str(ex)}"
        app_state.is_loading = False
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    finally:
        await client.close()

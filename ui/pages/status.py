"""
Status Page - Shows workflow progress

This page displays real-time status updates for an article in progress.
"""

import mesop as me
import logging
from state.app_state import AppState
from services.news_chief_client import NewsChiefClient

logger = logging.getLogger(__name__)


@me.page(path="/status", title="Elastic News - Article Status")
def status_page():
    """Status page showing workflow progress"""
    app_state = me.state(AppState)

    # If no story is being tracked, redirect to home
    if not app_state.current_story_id:
        me.navigate("/")
        return

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
                "Elastic News - Article Status",
                style=me.Style(font_size=32, font_weight=700, color="#1a1a1a"),
            )
            me.text(
                f"Story ID: {app_state.current_story_id}",
                style=me.Style(font_size=14, color="#666", margin=me.Margin(top=8), font_family="monospace"),
            )

        # Status Card
        with me.box(
            style=me.Style(
                background="white",
                padding=me.Padding.all(24),
                border_radius=8,
                box_shadow="0 2px 4px rgba(0,0,0,0.1)",
                max_width=800,
            )
        ):
            # Check current status
            status_info = _get_status_display(app_state.workflow_status)

            with me.box(
                style=me.Style(
                    display="flex",
                    align_items="center",
                    gap=16,
                    padding=me.Padding.all(16),
                    background="#e3f2fd",
                    border_radius=8,
                    margin=me.Margin(bottom=20),
                )
            ):
                # Show spinner if not complete
                if app_state.workflow_status not in ["completed", "published", "error"]:
                    me.progress_spinner()

                with me.box(style=me.Style(flex=1)):
                    me.text(
                        status_info["icon"] + " " + status_info["title"],
                        style=me.Style(font_size=20, font_weight=600, color=status_info["color"]),
                    )
                    me.text(
                        status_info["message"],
                        style=me.Style(font_size=14, color="#666", margin=me.Margin(top=4)),
                    )

            # Progress steps
            me.text(
                "Workflow Progress",
                style=me.Style(font_size=18, font_weight=600, margin=me.Margin(bottom=16)),
            )

            _render_progress_steps(app_state.workflow_status)

            # Action buttons
            with me.box(
                style=me.Style(
                    display="flex",
                    gap=12,
                    margin=me.Margin(top=24),
                )
            ):
                if app_state.workflow_status in ["completed", "published"]:
                    me.button(
                        "View Article →",
                        on_click=view_article,
                        type="flat",
                        style=me.Style(
                            background="#4caf50",
                            color="white",
                            padding=me.Padding(top=10, bottom=10, left=20, right=20),
                            border_radius=4,
                        ),
                    )
                    me.button(
                        "← Assign New Story",
                        on_click=go_home,
                        type="flat",
                        style=me.Style(
                            background="#1976d2",
                            color="white",
                            padding=me.Padding(top=10, bottom=10, left=20, right=20),
                            border_radius=4,
                        ),
                    )
                else:
                    # Auto-refresh button
                    me.button(
                        "🔄 Refresh Status",
                        on_click=refresh_status,
                        type="flat",
                        style=me.Style(
                            background="#1976d2",
                            color="white",
                            padding=me.Padding(top=10, bottom=10, left=20, right=20),
                            border_radius=4,
                        ),
                    )
                    me.text(
                        "💡 Click 'Refresh Status' to check for updates. The workflow continues in the background.",
                        style=me.Style(
                            font_size=12,
                            color="#666",
                            margin=me.Margin(top=8),
                            font_style="italic",
                        ),
                    )


def _get_status_display(status: str) -> dict:
    """Get display info for a status"""
    status_map = {
        "pending": {
            "icon": "⏳",
            "title": "Pending",
            "message": "Story assignment in queue...",
            "color": "#666",
        },
        "assigned": {
            "icon": "📝",
            "title": "Assigned",
            "message": "Story has been assigned to Reporter...",
            "color": "#1976d2",
        },
        "writing": {
            "icon": "✍️",
            "title": "Writing",
            "message": "Reporter is writing the article...",
            "color": "#1976d2",
        },
        "researching": {
            "icon": "🔍",
            "title": "Researching",
            "message": "Researcher is gathering information...",
            "color": "#1976d2",
        },
        "editing": {
            "icon": "✏️",
            "title": "Editing",
            "message": "Editor is reviewing the article...",
            "color": "#1976d2",
        },
        "publishing": {
            "icon": "📤",
            "title": "Publishing",
            "message": "Publisher is preparing to publish...",
            "color": "#1976d2",
        },
        "completed": {
            "icon": "✅",
            "title": "Complete",
            "message": "Article has been successfully published!",
            "color": "#4caf50",
        },
        "published": {
            "icon": "✅",
            "title": "Published",
            "message": "Article has been successfully published!",
            "color": "#4caf50",
        },
        "error": {
            "icon": "❌",
            "title": "Error",
            "message": "An error occurred during the workflow",
            "color": "#c00",
        },
    }

    return status_map.get(status, {
        "icon": "❓",
        "title": "Unknown",
        "message": f"Status: {status}",
        "color": "#666",
    })


def _render_progress_steps(current_status: str):
    """Render workflow progress steps"""
    steps = [
        ("assigned", "📝 Assigned"),
        ("writing", "✍️ Writing"),
        ("editing", "✏️ Editing"),
        ("publishing", "📤 Publishing"),
        ("completed", "✅ Complete"),
    ]

    step_order = {step[0]: idx for idx, step in enumerate(steps)}
    current_idx = step_order.get(current_status, -1)

    for idx, (step_status, step_label) in enumerate(steps):
        is_complete = idx <= current_idx
        is_current = step_status == current_status

        with me.box(
            style=me.Style(
                display="flex",
                align_items="center",
                gap=12,
                padding=me.Padding(top=8, bottom=8),
            )
        ):
            # Status indicator
            with me.box(
                style=me.Style(
                    width=32,
                    height=32,
                    border_radius=16,
                    background="#4caf50" if is_complete else "#e0e0e0",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                )
            ):
                me.text(
                    "✓" if is_complete and not is_current else str(idx + 1),
                    style=me.Style(
                        color="white" if is_complete else "#999",
                        font_weight=600,
                    ),
                )

            # Step label
            me.text(
                step_label,
                style=me.Style(
                    color="#1a1a1a" if is_complete else "#999",
                    font_weight=600 if is_current else 400,
                ),
            )


def refresh_status(e: me.ClickEvent):
    """Refresh status from News Chief"""
    app_state = me.state(AppState)

    logger.info(f"🔄 Refreshing status for story: {app_state.current_story_id}")

    # Create client and fetch status
    import asyncio

    async def fetch_status():
        client = NewsChiefClient(base_url=app_state.news_chief_url)
        try:
            result = await client.get_story_status(app_state.current_story_id)
            logger.info(f"📊 Status refresh result: {result.get('status')}")

            if result.get("status") == "success":
                story = result.get("story", {})
                app_state.workflow_status = story.get("status", "pending")

                logger.info(f"   Workflow status: {app_state.workflow_status}")
                logger.info(f"   Story has article_data: {'article_data' in story}")

                # Extract article data if available
                if "article_data" in story:
                    article_data = story["article_data"]
                    app_state.article_headline = article_data.get("headline", "")
                    app_state.article_content = article_data.get("content", "")
                    app_state.article_word_count = article_data.get("word_count", 0)
                    logger.info(f"   ✅ Extracted article data:")
                    logger.info(f"      Headline: {app_state.article_headline[:50]}...")
                    logger.info(f"      Content length: {len(app_state.article_content)} chars")
                    logger.info(f"      Word count: {app_state.article_word_count}")
                else:
                    logger.warning(f"   ⚠️  No article_data in story response")
                    logger.warning(f"   Story keys: {list(story.keys())}")

                logger.info(f"✅ Status updated: {app_state.workflow_status}")
        except Exception as ex:
            logger.error(f"❌ Failed to fetch status: {ex}")
        finally:
            await client.close()

    asyncio.run(fetch_status())


def view_article(e: me.ClickEvent):
    """Navigate to article viewer"""
    app_state = me.state(AppState)
    logger.info(f"🔄 Navigating to article: {app_state.current_story_id}")
    me.navigate("/article")


def go_home(e: me.ClickEvent):
    """Go back to home page"""
    logger.info("🏠 Navigating to home")
    me.navigate("/")

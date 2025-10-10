"""
Article Page - Display Completed Article

This page shows the completed article with all metadata in expandable sections.
"""

import mesop as me
import json
import logging
from typing import Any, Dict
from state.app_state import AppState, ArticleViewState

logger = logging.getLogger(__name__)


@me.page(path="/article", title="Elastic News - Article")
def article_page():
    """Article viewer page with expandable metadata"""
    app_state = me.state(AppState)
    view_state = me.state(ArticleViewState)

    # Get story_id from app state (should be set when navigating here)
    story_id = app_state.current_story_id

    logger.info(f"📄 Loading article page for story: {story_id}")

    # Check if this is the current story and has content
    has_article = (app_state.current_story_id == story_id and app_state.article_content)

    if has_article:
        logger.info(f"✅ Article loaded: '{app_state.article_headline}' ({app_state.article_word_count} words)")
    else:
        logger.warning(f"⚠️  Article not found for story: {story_id}")

    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            min_height="100vh",
            background="#f5f5f5",
            padding=me.Padding.all(20),
        )
    ):
        # Header with navigation
        with me.box(
            style=me.Style(
                background="white",
                padding=me.Padding.all(20),
                border_radius=8,
                margin=me.Margin(bottom=20),
                box_shadow="0 2px 4px rgba(0,0,0,0.1)",
                display="flex",
                justify_content="space-between",
                align_items="center",
            )
        ):
            with me.box():
                me.text(
                    "Elastic News - Article",
                    style=me.Style(font_size=32, font_weight=700, color="#1a1a1a"),
                )
                me.text(
                    f"Story ID: {story_id}",
                    style=me.Style(font_size=14, color="#666", margin=me.Margin(top=4)),
                )

            me.button(
                "← New Story",
                on_click=go_home,
                type="flat",
                style=me.Style(
                    background="#1976d2",
                    color="white",
                    padding=me.Padding(top=8, bottom=8, left=16, right=16),
                    border_radius=4,
                ),
            )

        # Article content or loading/error state
        if not has_article:
            with me.box(
                style=me.Style(
                    background="white",
                    padding=me.Padding.all(40),
                    border_radius=8,
                    box_shadow="0 2px 4px rgba(0,0,0,0.1)",
                    text_align="center",
                )
            ):
                me.text("❌ Article not found", style=me.Style(font_size=24, color="#999"))
                me.text(
                    f"Story ID {story_id} was not found",
                    style=me.Style(margin=me.Margin(top=8), color="#666"),
                )
        else:
            # Primary Section: Headline, Content, Word Count
            with me.box(
                style=me.Style(
                    background="white",
                    padding=me.Padding.all(32),
                    border_radius=8,
                    box_shadow="0 2px 4px rgba(0,0,0,0.1)",
                    margin=me.Margin(bottom=20),
                )
            ):
                # Headline
                me.text(
                    app_state.article_headline,
                    style=me.Style(
                        font_size=36,
                        font_weight=700,
                        line_height="1.2",
                        margin=me.Margin(bottom=16),
                        color="#1a1a1a",
                    ),
                )

                # Word count badge
                me.text(
                    f"📊 {app_state.article_word_count} words",
                    style=me.Style(
                        font_size=14,
                        color="#666",
                        background="#f0f0f0",
                        padding=me.Padding(top=4, bottom=4, left=12, right=12),
                        border_radius=12,
                        display="inline-block",
                        margin=me.Margin(bottom=24),
                    ),
                )

                # Article content
                me.markdown(
                    app_state.article_content,
                    style=me.Style(
                        font_size=18,
                        line_height="1.6",
                        color="#333",
                    ),
                )


def _render_metadata_sections(story_data: Dict[str, Any], view_state: ArticleViewState):
    """Render expandable metadata sections"""

    # Extract metadata
    research_data = _extract_research_data(story_data)
    editorial_review = _extract_editorial_review(story_data)
    tags = _extract_tags(story_data)
    timestamp = _extract_timestamp(story_data)
    es_doc_id = _extract_es_doc_id(story_data)

    # Metadata header
    with me.box(
        style=me.Style(
            background="white",
            padding=me.Padding.all(24),
            border_radius=8,
            box_shadow="0 2px 4px rgba(0,0,0,0.1)",
            margin=me.Margin(bottom=20),
        )
    ):
        me.text(
            "Article Metadata",
            style=me.Style(font_size=24, font_weight=600, margin=me.Margin(bottom=16)),
        )

        # Quick metadata (always visible)
        with me.box(style=me.Style(margin=me.Margin(bottom=16))):
            if tags:
                me.text("Tags:", style=me.Style(font_weight=600, margin=me.Margin(bottom=4)))
                with me.box(style=me.Style(display="flex", gap=8, flex_wrap="wrap")):
                    for tag in tags:
                        me.text(
                            tag,
                            style=me.Style(
                                background="#e3f2fd",
                                color="#1976d2",
                                padding=me.Padding(top=4, bottom=4, left=12, right=12),
                                border_radius=12,
                                font_size=14,
                            ),
                        )

            if timestamp:
                me.text(
                    f"📅 Published: {timestamp}",
                    style=me.Style(color="#666", margin=me.Margin(top=8)),
                )

            if es_doc_id:
                me.text(
                    f"🔗 Elasticsearch ID: {es_doc_id}",
                    style=me.Style(color="#666", font_family="monospace", font_size=12),
                )

    # Research Data (Expandable)
    if research_data:
        _render_expandable_section(
            title="📚 Research Data & Sources",
            content=research_data,
            is_expanded=view_state.research_expanded,
            toggle_fn=toggle_research,
        )

    # Editorial Review (Expandable)
    if editorial_review:
        _render_expandable_section(
            title="✏️ Editorial Review",
            content=editorial_review,
            is_expanded=view_state.review_expanded,
            toggle_fn=toggle_review,
        )


def _render_expandable_section(title: str, content: Any, is_expanded: bool, toggle_fn):
    """Render an expandable section"""
    with me.box(
        style=me.Style(
            background="white",
            border_radius=8,
            box_shadow="0 2px 4px rgba(0,0,0,0.1)",
            margin=me.Margin(bottom=16),
        )
    ):
        # Header (clickable)
        with me.box(
            on_click=toggle_fn,
            style=me.Style(
                padding=me.Padding.all(16),
                cursor="pointer",
                display="flex",
                justify_content="space-between",
                align_items="center",
                background="#fafafa" if is_expanded else "white",
                border_radius=8,
            ),
        ):
            me.text(title, style=me.Style(font_weight=600, font_size=16))
            me.text(
                "▼" if is_expanded else "▶",
                style=me.Style(color="#666", font_size=14),
            )

        # Content (shown when expanded)
        if is_expanded:
            with me.box(
                style=me.Style(
                    padding=me.Padding.all(16),
                    border_top="1px solid #eee",
                )
            ):
                # Format content based on type
                if isinstance(content, dict):
                    me.text(
                        json.dumps(content, indent=2),
                        style=me.Style(
                            font_family="monospace",
                            font_size=14,
                            white_space="pre-wrap",
                            background="#f5f5f5",
                            padding=me.Padding.all(12),
                            border_radius=4,
                        ),
                    )
                elif isinstance(content, str):
                    me.markdown(content)
                else:
                    me.text(str(content))


# Helper functions to extract data from story response


def _extract_article_content(story_data: Dict[str, Any]) -> str:
    """Extract article content from story data"""
    return story_data.get("article", {}).get("content", story_data.get("content", "No content available"))


def _extract_headline(story_data: Dict[str, Any]) -> str:
    """Extract headline from story data"""
    return story_data.get("article", {}).get("headline", story_data.get("headline", "Untitled Article"))


def _extract_word_count(story_data: Dict[str, Any]) -> int:
    """Extract word count from story data"""
    return story_data.get("article", {}).get("word_count", story_data.get("word_count", 0))


def _extract_research_data(story_data: Dict[str, Any]) -> Any:
    """Extract research data from story data"""
    return story_data.get("research_data") or story_data.get("article", {}).get("research_data")


def _extract_editorial_review(story_data: Dict[str, Any]) -> Any:
    """Extract editorial review from story data"""
    return story_data.get("editorial_review") or story_data.get("article", {}).get("editorial_review")


def _extract_tags(story_data: Dict[str, Any]) -> list:
    """Extract tags from story data"""
    tags = story_data.get("tags") or story_data.get("article", {}).get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    return tags if tags else []


def _extract_timestamp(story_data: Dict[str, Any]) -> str:
    """Extract publication timestamp from story data"""
    return story_data.get("published_at") or story_data.get("article", {}).get("published_at", "")


def _extract_es_doc_id(story_data: Dict[str, Any]) -> str:
    """Extract Elasticsearch document ID from story data"""
    return story_data.get("elasticsearch_id") or story_data.get("article", {}).get("elasticsearch_id", "")


# Event Handlers


def go_home(e: me.ClickEvent):
    """Navigate back to home page"""
    logger.info("🏠 Navigating back to home page")
    me.navigate("/")


def toggle_research(e: me.ClickEvent):
    """Toggle research data section"""
    view_state = me.state(ArticleViewState)
    view_state.research_expanded = not view_state.research_expanded
    logger.debug(f"📚 Research section {'expanded' if view_state.research_expanded else 'collapsed'}")


def toggle_review(e: me.ClickEvent):
    """Toggle editorial review section"""
    view_state = me.state(ArticleViewState)
    view_state.review_expanded = not view_state.review_expanded
    logger.debug(f"✏️ Review section {'expanded' if view_state.review_expanded else 'collapsed'}")

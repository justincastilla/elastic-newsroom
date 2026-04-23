"""
Mock Tavily client for testing without API calls.

Provides realistic search results for testing the research pipeline.
"""

from typing import List, Optional, Sequence


class MockTavilyClient:
    """
    Mock Tavily client for testing.

    Returns realistic-looking search results without making actual API calls.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize mock client (api_key is ignored)."""
        self.api_key = api_key or "tvly-mock-key"

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        topic: str = "general",
        time_range: Optional[str] = None,
        include_domains: Optional[Sequence[str]] = None,
        exclude_domains: Optional[Sequence[str]] = None,
        **kwargs
    ) -> dict:
        """
        Mock search that returns realistic results based on the query.
        """
        # Generate mock results based on the query
        results = []
        for i in range(min(max_results, 5)):
            results.append({
                "title": f"Research Finding {i+1}: {query[:50]}",
                "url": f"https://example.com/article-{i+1}",
                "content": f"According to recent analysis, {query[:30]} shows significant developments. "
                           f"Industry experts report that this area has seen {20 + i*10}% growth in adoption. "
                           f"Leading organizations are investing heavily in this space.",
                "score": round(0.95 - (i * 0.1), 2),
                "published_date": f"2026-04-{15-i:02d}"
            })

        response = {
            "results": results,
            "response_time": 1.2,
            "query": query
        }

        if include_answer:
            response["answer"] = (
                f"Based on current research, {query[:40]} represents a significant area of development. "
                f"Key findings include widespread adoption across industries, measurable efficiency gains, "
                f"and projected continued growth through 2027."
            )

        return response

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

"""
Article API - Minimal FastAPI backend for serving articles to the UI

This is a lightweight API separate from the agent architecture.
It queries Elasticsearch directly to serve published articles to the React UI.
"""

import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from pydantic import BaseModel
import uvicorn

from utils import setup_logger, load_env_config

# Load environment variables
load_env_config()

# Configure logging
logger = setup_logger("ARTICLE_API")

# Initialize FastAPI app
app = FastAPI(
    title="Elastic News Article API",
    description="Lightweight API for serving published articles from Elasticsearch",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Elasticsearch client
es_client = None
es_index = os.getenv("ELASTIC_ARCHIVIST_INDEX", "news_archive")

try:
    es_endpoint = os.getenv("ELASTICSEARCH_ENDPOINT")
    es_api_key = os.getenv("ELASTICSEARCH_API_KEY")

    if es_endpoint and es_api_key:
        es_client = Elasticsearch(
            es_endpoint,
            api_key=es_api_key
        )
        # Test connection
        info = es_client.info()
        logger.info("Connected to Elasticsearch - Version: %s, Index: %s", info['version']['number'], es_index)
    else:
        logger.warning("Elasticsearch credentials not configured")
except Exception as e:
    logger.error("Failed to connect to Elasticsearch: %s", e)
    es_client = None


class ArticleResponse(BaseModel):
    """Article response model"""
    story_id: str
    headline: str
    content: str
    topic: Optional[str] = None
    angle: Optional[str] = None
    word_count: Optional[int] = None
    target_length: Optional[int] = None
    published_at: Optional[str] = None
    tags: Optional[list] = []
    categories: Optional[list] = []
    agents_involved: Optional[list] = []
    research_sources: Optional[list] = []


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "elasticsearch_connected": es_client is not None,
        "index": es_index
    }


@app.get("/article/{story_id}", response_model=ArticleResponse)
async def get_article(story_id: str):
    """
    Fetch a published article from Elasticsearch by story_id

    Args:
        story_id: The unique story identifier

    Returns:
        ArticleResponse with article data

    Raises:
        HTTPException: If Elasticsearch is unavailable or article not found
    """
    logger.info("Fetching article: %s", story_id)

    if not es_client:
        logger.error("Elasticsearch not available")
        raise HTTPException(
            status_code=503,
            detail="Elasticsearch is not configured or unavailable"
        )

    try:
        # Query Elasticsearch for the article
        response = es_client.get(
            index=es_index,
            id=story_id
        )

        if not response['found']:
            logger.warning("Article not found: %s", story_id)
            raise HTTPException(
                status_code=404,
                detail=f"Article with story_id '{story_id}' not found"
            )

        # Extract article data from Elasticsearch response
        article_data = response.get('_source', {})

        if not article_data:
            logger.warning("Article data is empty for %s", story_id)
            raise HTTPException(
                status_code=404,
                detail=f"Article with story_id '{story_id}' has no data"
            )

        headline = article_data.get('headline') or 'Untitled'
        content = article_data.get('content') or 'No content available'

        # If headline is still "Untitled", try to extract from content
        if headline == 'Untitled' and content and content != 'No content available':
            import re
            lines = content.split('\n')
            # Priority 1: "HEADLINE: ..." prefix
            headline_line = next((l.strip() for l in lines if l.strip().startswith('HEADLINE:')), None)
            if headline_line:
                headline = headline_line.replace('HEADLINE:', '').strip()
            else:
                # Priority 2: First markdown heading (# or ##)
                heading_line = next((l.strip() for l in lines if re.match(r'^#{1,2}\s+.+', l.strip())), None)
                if heading_line:
                    headline = re.sub(r'^#+\s+', '', heading_line)

        logger.info("Article retrieved: %s", headline[:60] if headline else 'N/A')

        # Return article in expected format
        return ArticleResponse(
            story_id=article_data.get('story_id', story_id),
            headline=headline,
            content=content,
            topic=article_data.get('topic'),
            angle=article_data.get('angle'),
            word_count=article_data.get('word_count'),
            target_length=article_data.get('target_length'),
            published_at=article_data.get('published_at'),
            tags=article_data.get('tags') or [],
            categories=article_data.get('categories') or [],
            agents_involved=article_data.get('agents_involved') or [],
            research_sources=article_data.get('research_sources') or []
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching article: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving article: {str(e)}"
        )


@app.get("/articles/recent")
async def get_recent_articles(limit: int = 10):
    """
    Fetch recent published articles from Elasticsearch

    Args:
        limit: Maximum number of articles to return (default: 10)

    Returns:
        List of recent articles with metadata
    """
    logger.info("Fetching %d recent articles", limit)

    if not es_client:
        logger.error("Elasticsearch not available")
        raise HTTPException(
            status_code=503,
            detail="Elasticsearch is not configured or unavailable"
        )

    try:
        # Query for recent articles (ES Python client 9.x keyword args)
        response = es_client.search(
            index=es_index,
            query={"match_all": {}},
            sort=[{"published_at": {"order": "desc"}}],
            size=limit,
            source=["story_id", "headline", "topic", "word_count", "published_at", "tags", "categories"]
        )

        articles = [hit['_source'] for hit in response['hits']['hits']]

        logger.info("Retrieved %d recent articles", len(articles))

        return {
            "total": response['hits']['total']['value'],
            "articles": articles
        }

    except Exception as e:
        logger.error("Error fetching recent articles: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recent articles: {str(e)}"
        )


@app.get("/articles/search")
async def search_articles(
    q: str = Query(..., description="Search query text"),
    mode: str = Query("keyword", description="Search mode: 'keyword', 'semantic', or 'hybrid'"),
    limit: int = Query(10, description="Maximum number of results"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    Search articles using keyword, semantic, or hybrid search.

    - **keyword**: Traditional full-text search across headline, content, and topic
    - **semantic**: Natural language search using the semantic_text field (requires inference configured on ES cluster)
    - **hybrid**: Combines keyword and semantic results using RRF (Reciprocal Rank Fusion)

    Args:
        q: Search query text
        mode: Search mode (keyword, semantic, or hybrid)
        limit: Maximum results to return (default: 10)
        tag: Optional tag filter
        category: Optional category filter

    Returns:
        Search results with relevance scores
    """
    logger.info("Searching articles: q='%s', mode=%s, limit=%d", q, mode, limit)

    if not es_client:
        raise HTTPException(status_code=503, detail="Elasticsearch is not configured or unavailable")

    try:
        # Build optional filters
        filter_clauses = [{"term": {"status": "published"}}]
        if tag:
            filter_clauses.append({"term": {"tags": tag}})
        if category:
            filter_clauses.append({"term": {"categories": category}})

        if mode == "semantic":
            # Semantic search using semantic_text field
            search_query = {
                "bool": {
                    "must": [
                        {"semantic": {"field": "content_semantic", "query": q}}
                    ],
                    "filter": filter_clauses
                }
            }
        elif mode == "hybrid":
            # Hybrid search: combine keyword + semantic with sub_searches and RRF
            response = es_client.search(
                index=es_index,
                sub_searches=[
                    {
                        "query": {
                            "multi_match": {
                                "query": q,
                                "fields": ["headline^3", "content", "topic^2"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    },
                    {
                        "query": {
                            "semantic": {"field": "content_semantic", "query": q}
                        }
                    }
                ],
                rank={"rrf": {"window_size": 50, "rank_constant": 20}},
                size=limit,
                source=["story_id", "headline", "topic", "word_count", "published_at", "tags", "categories", "content"]
            )

            articles = []
            for hit in response['hits']['hits']:
                article = hit['_source']
                article['_score'] = hit.get('_score')
                articles.append(article)

            return {
                "total": response['hits']['total']['value'],
                "mode": "hybrid",
                "query": q,
                "articles": articles
            }
        else:
            # Default: keyword search with multi_match
            search_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": q,
                                "fields": ["headline^3", "content", "topic^2", "tags^1.5"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": filter_clauses
                }
            }

        # Execute search (keyword or semantic mode)
        response = es_client.search(
            index=es_index,
            query=search_query,
            size=limit,
            source=["story_id", "headline", "topic", "word_count", "published_at", "tags", "categories", "content"],
            highlight={
                "fields": {
                    "content": {"fragment_size": 200, "number_of_fragments": 2},
                    "headline": {}
                }
            }
        )

        articles = []
        for hit in response['hits']['hits']:
            article = hit['_source']
            article['_score'] = hit.get('_score')
            # Include highlight snippets if available
            if 'highlight' in hit:
                article['highlights'] = hit['highlight']
            articles.append(article)

        logger.info("Search returned %d results for '%s' (mode=%s)", len(articles), q, mode)

        return {
            "total": response['hits']['total']['value'],
            "mode": mode,
            "query": q,
            "articles": articles
        }

    except Exception as e:
        logger.error("Error searching articles: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching articles: {str(e)}"
        )


def main():
    """Start the Article API server"""
    logger.info("Starting Article API server - Port: 8085, CORS: http://localhost:3000, http://localhost:3001")

    uvicorn.run(
        app,
        host="localhost",
        port=8085,
        log_level="info"
    )


if __name__ == "__main__":
    main()

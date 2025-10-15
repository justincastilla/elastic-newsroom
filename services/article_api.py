"""
Article API - Minimal FastAPI backend for serving articles to the UI

This is a lightweight API separate from the agent architecture.
It queries Elasticsearch directly to serve published articles to the React UI.
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
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
    es_api_key = os.getenv("ELASTIC_SEARCH_API_KEY")

    if es_endpoint and es_api_key:
        es_client = Elasticsearch(
            es_endpoint,
            api_key=es_api_key
        )
        # Test connection
        info = es_client.info()
        logger.info(f"✅ Connected to Elasticsearch")
        logger.info(f"   Version: {info['version']['number']}")
        logger.info(f"   Index: {es_index}")
    else:
        logger.warning("⚠️  Elasticsearch credentials not configured")
except Exception as e:
    logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
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
    logger.info(f"📄 Fetching article: {story_id}")

    if not es_client:
        logger.error("❌ Elasticsearch not available")
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
            logger.warning(f"⚠️  Article not found: {story_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Article with story_id '{story_id}' not found"
            )

        # Extract article data from Elasticsearch response
        article_data = response.get('_source', {})

        if not article_data:
            logger.warning(f"⚠️  Article data is empty for {story_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Article with story_id '{story_id}' has no data"
            )

        headline = article_data.get('headline') or 'Untitled'
        content = article_data.get('content') or 'No content available'

        logger.info(f"✅ Article retrieved: {headline[:60] if headline else 'N/A'}")

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
            agents_involved=article_data.get('agents_involved') or []
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching article: {e}", exc_info=True)
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
    logger.info(f"📋 Fetching {limit} recent articles")

    if not es_client:
        logger.error("❌ Elasticsearch not available")
        raise HTTPException(
            status_code=503,
            detail="Elasticsearch is not configured or unavailable"
        )

    try:
        # Query for recent articles
        response = es_client.search(
            index=es_index,
            body={
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"published_at": {"order": "desc"}}
                ],
                "size": limit,
                "_source": [
                    "story_id", "headline", "topic", "word_count",
                    "published_at", "tags", "categories"
                ]
            }
        )

        articles = [hit['_source'] for hit in response['hits']['hits']]

        logger.info(f"✅ Retrieved {len(articles)} recent articles")

        return {
            "total": response['hits']['total']['value'],
            "articles": articles
        }

    except Exception as e:
        logger.error(f"❌ Error fetching recent articles: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving recent articles: {str(e)}"
        )


def main():
    """Start the Article API server"""
    logger.info("🚀 Starting Article API server...")
    logger.info("   Port: 8085")
    logger.info("   CORS: http://localhost:3000, http://localhost:3001")

    uvicorn.run(
        app,
        host="localhost",
        port=8085,
        log_level="info"
    )


if __name__ == "__main__":
    main()

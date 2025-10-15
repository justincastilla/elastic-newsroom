#!/usr/bin/env python3
"""
Test Event Hub Service

Tests the Event Hub API and WebSocket functionality.
"""

import asyncio
import httpx
import pytest
from datetime import datetime


EVENT_HUB_URL = "http://localhost:8090"


@pytest.mark.integration
async def test_event_hub_health():
    """Test Event Hub health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{EVENT_HUB_URL}/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "Elastic News Event Hub"
        assert data["status"] == "healthy"
        assert "websocket_endpoint" in data


@pytest.mark.integration
async def test_publish_event():
    """Test publishing an event to Event Hub"""
    event = {
        "agent": "TestAgent",
        "event_type": "test_event",
        "story_id": "test_123",
        "data": {
            "message": "Test event from pytest"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EVENT_HUB_URL}/events",
            json=event
        )
        assert response.status_code == 200

        result = response.json()
        assert result["status"] == "ok"
        assert "event_id" in result


@pytest.mark.integration
async def test_query_events():
    """Test querying events from Event Hub"""
    # First publish an event
    event = {
        "agent": "TestAgent",
        "event_type": "query_test",
        "story_id": "query_test_123",
        "data": {"test": "data"}
    }

    async with httpx.AsyncClient() as client:
        # Publish
        await client.post(f"{EVENT_HUB_URL}/events", json=event)

        # Query all events
        response = await client.get(f"{EVENT_HUB_URL}/events?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "total" in data
        assert data["total"] > 0

        # Query by story_id
        response = await client.get(
            f"{EVENT_HUB_URL}/events?story_id=query_test_123"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1
        assert any(e["story_id"] == "query_test_123" for e in data["events"])


@pytest.mark.integration
async def test_story_timeline():
    """Test getting story timeline"""
    story_id = f"timeline_test_{int(datetime.now().timestamp())}"

    # Publish multiple events for the same story
    events = [
        {"agent": "NewsChiefAgent", "event_type": "story_assigned", "story_id": story_id},
        {"agent": "ReporterAgent", "event_type": "assignment_accepted", "story_id": story_id},
        {"agent": "ReporterAgent", "event_type": "article_drafted", "story_id": story_id},
    ]

    async with httpx.AsyncClient() as client:
        # Publish events
        for event in events:
            await client.post(f"{EVENT_HUB_URL}/events", json=event)

        # Get timeline
        response = await client.get(f"{EVENT_HUB_URL}/events/story/{story_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["story_id"] == story_id
        assert data["total_events"] >= 3
        assert len(data["timeline"]) >= 3


@pytest.mark.integration
async def test_statistics():
    """Test Event Hub statistics endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{EVENT_HUB_URL}/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_events" in data
        assert "websocket_connections" in data
        assert "events_by_agent" in data
        assert "events_by_type" in data


if __name__ == "__main__":
    print("Event Hub Integration Tests")
    print("=" * 60)
    print(f"Make sure Event Hub is running at {EVENT_HUB_URL}")
    print("Run with: pytest tests/test_event_hub.py -v")
    print("=" * 60)

"""
Event Hub Server

Centralized event broadcasting service for Elastic News multi-agent system.
Receives events from agents and broadcasts them to connected UI clients via Server-Sent Events (SSE).

Features:
- SSE endpoint for real-time client updates
- Event buffering for clients that reconnect
- Story-specific event filtering
- Health check endpoint

Architecture:
- Agents POST events to /events
- UI clients connect to /stream for real-time updates
- Events are broadcast to all connected clients
- Optional story_id filtering for targeted updates
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque

import click
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, JSONResponse
from starlette.routing import Route
from starlette.requests import Request
import uvicorn

from utils import setup_logger, load_env_config

# Load environment variables
load_env_config()

# Configure logging
logger = setup_logger("EVENT_HUB")

# Event storage (in-memory queue with max size)
MAX_EVENT_HISTORY = 1000
event_history: deque = deque(maxlen=MAX_EVENT_HISTORY)

# Connected SSE clients
connected_clients: List[asyncio.Queue] = []


class ServerSentEvent:
    """Server-Sent Event formatter"""

    def __init__(
        self,
        data: str,
        event: Optional[str] = None,
        id: Optional[int] = None,
        retry: Optional[int] = None
    ):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry

    def encode(self) -> str:
        """Encode event in SSE format"""
        message = f"data: {self.data}\n"
        if self.event:
            message = f"event: {self.event}\n{message}"
        if self.id is not None:
            message = f"id: {self.id}\n{message}"
        if self.retry is not None:
            message = f"retry: {self.retry}\n{message}"
        message += "\n"
        return message


async def event_stream(request: Request):
    """
    SSE endpoint for clients to receive real-time events.

    Query parameters:
    - story_id: Optional filter to only receive events for a specific story
    - since: Optional timestamp (ISO format) to receive events since that time
    """
    # Create queue for this client
    queue: asyncio.Queue = asyncio.Queue()
    connected_clients.append(queue)

    # Get optional filters from query params
    story_id = request.query_params.get('story_id')
    since_param = request.query_params.get('since')

    logger.info(f"📡 New SSE client connected (story_id: {story_id or 'all'}, total clients: {len(connected_clients)})")

    # Send historical events if 'since' parameter provided
    if since_param:
        try:
            since_time = datetime.fromisoformat(since_param)
            historical_events = [
                event for event in event_history
                if datetime.fromisoformat(event['timestamp']) > since_time
            ]
            if story_id:
                historical_events = [e for e in historical_events if e.get('story_id') == story_id]

            logger.info(f"📜 Sending {len(historical_events)} historical events to client")
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid 'since' parameter: {e}")
            historical_events = []
    else:
        historical_events = []

    async def event_generator():
        try:
            # Send connection established event
            yield ServerSentEvent(
                data=json.dumps({
                    "type": "connected",
                    "message": "Event Hub connected",
                    "timestamp": datetime.now().isoformat(),
                    "total_clients": len(connected_clients)
                }),
                event="connection"
            ).encode()

            # Send historical events
            for event in historical_events:
                yield ServerSentEvent(
                    data=json.dumps(event),
                    event="historical"
                ).encode()

            # Send heartbeat every 15 seconds to keep connection alive
            last_heartbeat = datetime.now()

            while True:
                # Check for new events (with timeout for heartbeat)
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)

                    # Apply story_id filter if specified
                    if story_id and event.get('story_id') != story_id:
                        continue

                    # Send event to client
                    yield ServerSentEvent(
                        data=json.dumps(event),
                        event=event.get('event_type', 'agent_event')
                    ).encode()

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    now = datetime.now()
                    if (now - last_heartbeat).seconds >= 15:
                        yield ServerSentEvent(
                            data=json.dumps({
                                "type": "heartbeat",
                                "timestamp": now.isoformat()
                            }),
                            event="heartbeat"
                        ).encode()
                        last_heartbeat = now

        except asyncio.CancelledError:
            logger.info(f"📡 SSE client disconnected (total clients: {len(connected_clients) - 1})")
        finally:
            # Remove client from connected list
            if queue in connected_clients:
                connected_clients.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


async def receive_event(request: Request):
    """
    Receive events from agents and broadcast to connected clients.

    Expected JSON payload:
    {
        "agent": "NewsChiefAgent",
        "event_type": "story_assigned",
        "story_id": "story_123",
        "data": {...},
        "timestamp": "2025-01-14T12:00:00"
    }
    """
    try:
        event = await request.json()

        # Validate required fields
        if 'event_type' not in event:
            return JSONResponse(
                {"status": "error", "message": "Missing 'event_type' field"},
                status_code=400
            )

        # Add to event history
        event_history.append(event)

        # Log event (reduced verbosity for common events)
        event_type = event.get('event_type')
        story_id = event.get('story_id', 'N/A')
        agent = event.get('agent', 'Unknown')

        if event_type not in ['heartbeat', 'status_update']:
            logger.info(f"📨 Event received: {event_type} from {agent} (story: {story_id})")

        # Broadcast to all connected clients
        if connected_clients:
            # Create list of tasks to send to all clients
            for client_queue in connected_clients[:]:  # Copy list to avoid modification during iteration
                try:
                    client_queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning("Client queue full, skipping event")

        return JSONResponse({
            "status": "success",
            "message": "Event received and broadcasted",
            "clients_notified": len(connected_clients)
        })

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in event: {e}")
        return JSONResponse(
            {"status": "error", "message": f"Invalid JSON: {str(e)}"},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )


async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "Event Hub",
        "connected_clients": len(connected_clients),
        "event_history_size": len(event_history),
        "uptime": "N/A",  # Could track this if needed
        "timestamp": datetime.now().isoformat()
    })


async def get_events(request: Request):
    """
    Get recent events (HTTP polling fallback).

    Query parameters:
    - story_id: Optional filter by story ID
    - since: Optional ISO timestamp to get events since that time
    - limit: Max number of events to return (default: 50, max: 500)
    """
    story_id = request.query_params.get('story_id')
    since_param = request.query_params.get('since')
    limit = min(int(request.query_params.get('limit', 50)), 500)

    # Filter events
    events = list(event_history)

    if since_param:
        try:
            since_time = datetime.fromisoformat(since_param)
            events = [e for e in events if datetime.fromisoformat(e['timestamp']) > since_time]
        except (ValueError, KeyError):
            pass

    if story_id:
        events = [e for e in events if e.get('story_id') == story_id]

    # Apply limit
    events = events[-limit:]

    return JSONResponse({
        "status": "success",
        "events": events,
        "count": len(events),
        "total_history": len(event_history)
    })


async def clear_history(request: Request):
    """Clear event history (admin endpoint)"""
    event_history.clear()
    logger.info("🧹 Event history cleared")
    return JSONResponse({
        "status": "success",
        "message": "Event history cleared"
    })


def create_app():
    """Create the Starlette application"""

    routes = [
        Route("/stream", event_stream, methods=["GET"]),
        Route("/events", receive_event, methods=["POST"]),
        Route("/events", get_events, methods=["GET"]),
        Route("/health", health_check, methods=["GET"]),
        Route("/clear", clear_history, methods=["POST"]),
    ]

    app = Starlette(debug=True, routes=routes)

    # Add CORS middleware for React UI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=8090)
@click.option('--reload', 'reload', is_flag=True, default=False, help='Enable hot reload on file changes')
def main(host, port, reload):
    """Starts the Event Hub server."""
    logger.info(f"🚀 Starting Event Hub on {host}:{port}")
    logger.info(f"📡 SSE endpoint: http://{host}:{port}/stream")
    logger.info(f"📨 Event receiver: http://{host}:{port}/events")

    uvicorn.run(
        "event_hub:app" if reload else app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

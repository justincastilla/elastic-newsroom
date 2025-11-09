"""
FastAPI HTTP Server for CrewAI Researcher

Exposes the CrewAI-based researcher agent via HTTP endpoints,
providing both native CrewAI endpoints and A2A protocol compatibility.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import click

from crewai_agents.researcher_crew.crew import ResearcherCrew

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RESEARCHER_CREW_API")

# Initialize FastAPI app
app = FastAPI(
    title="CrewAI Researcher Agent",
    description="Research agent powered by CrewAI framework with A2A protocol compatibility",
    version="1.0.0"
)

# Add CORS middleware for React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize researcher crew (singleton)
researcher_crew = ResearcherCrew()


# ===== Pydantic Models =====

class ResearchRequest(BaseModel):
    """Request model for native CrewAI research endpoint."""
    story_id: str = Field(..., description="Unique identifier for the story")
    topic: str = Field(..., description="Main topic or subject area")
    questions: List[str] = Field(..., description="List of research questions")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional additional context")


class ResearchResponse(BaseModel):
    """Response model for research requests."""
    status: str
    message: str
    research_id: Optional[str] = None
    story_id: Optional[str] = None
    research_results: Optional[List[Dict[str, Any]]] = None
    total_questions: Optional[int] = None


class HistoryRequest(BaseModel):
    """Request model for research history retrieval."""
    research_id: Optional[str] = None
    story_id: Optional[str] = None


class A2ATaskRequest(BaseModel):
    """Request model for A2A protocol compatibility."""
    input: Dict[str, Any]
    task_id: Optional[str] = None


# ===== A2A Protocol Compatibility =====

@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    """
    A2A agent card endpoint for compatibility with A2A protocol.

    This allows existing A2A agents to discover and communicate with
    the CrewAI researcher using the standard A2A protocol.
    """
    return {
        "name": "Researcher (CrewAI)",
        "description": "Research agent powered by CrewAI - provides factual information, background context, and supporting data with structured figures for news articles",
        "url": f"http://localhost:8083",
        "version": "2.0.0",
        "protocol_version": "0.3.0",
        "implementation": "crewai",
        "preferred_transport": "HTTP",
        "documentation_url": "https://github.com/elastic/elastic-news/blob/main/crewai_agents/researcher_crew/README.md",
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
            "max_concurrent_tasks": 30
        },
        "skills": [
            {
                "id": "research.questions.bulk_research",
                "name": "Research Questions",
                "description": "Researches multiple questions and returns structured data with facts, figures, and sources",
                "tags": ["research", "fact-checking", "data"],
                "examples": [
                    '{"action": "research_questions", "story_id": "story_123", "topic": "AI in Journalism", "questions": ["What percentage of news orgs use AI?", "Who are the leading companies?"]}',
                    "Research multiple questions about a topic"
                ]
            },
            {
                "id": "research.history.get_history",
                "name": "Get Research History",
                "description": "Retrieves past research by research_id or story_id",
                "tags": ["history", "retrieval"],
                "examples": [
                    '{"action": "get_history", "research_id": "research_story_123_20250107_120000"}',
                    '{"action": "get_history", "story_id": "story_123"}'
                ]
            },
            {
                "id": "research.status",
                "name": "Get Status",
                "description": "Returns current status and history of all research requests",
                "tags": ["status", "reporting"],
                "examples": ['{"action": "get_status"}']
            }
        ],
        "default_input_modes": ["application/json"],
        "default_output_modes": ["application/json"],
        "provider": {
            "organization": "Elastic News",
            "url": "https://newsroom.example.com"
        }
    }


@app.post("/a2a/tasks")
async def a2a_task_handler(request: A2ATaskRequest):
    """
    A2A protocol handler - bridges A2A requests to CrewAI.

    This endpoint maintains backward compatibility with existing A2A agents
    (like the Reporter) that call the researcher using A2A JSONRPC protocol.

    Supported actions:
    - research_questions: Research multiple questions
    - get_history: Retrieve research history
    - get_status: Get current status
    """
    try:
        logger.info(f"📨 A2A task request received")

        # Parse A2A input
        input_data = request.input
        action = input_data.get("action")

        logger.info(f"🎯 A2A action: {action}")

        if action == "research_questions":
            # Extract parameters
            story_id = input_data.get("story_id")
            topic = input_data.get("topic", "")
            questions = input_data.get("questions", [])

            if not story_id or not questions:
                raise HTTPException(
                    status_code=400,
                    detail="Missing required fields: story_id or questions"
                )

            # Call CrewAI crew
            result = await researcher_crew.research_questions(
                questions=questions,
                topic=topic,
                story_id=story_id
            )

            # Format as A2A response
            return _format_a2a_response(result)

        elif action == "get_history":
            research_id = input_data.get("research_id")
            story_id = input_data.get("story_id")

            result = researcher_crew.get_research_history(
                research_id=research_id,
                story_id=story_id
            )

            return _format_a2a_response(result)

        elif action == "get_status":
            result = researcher_crew.get_status()
            return _format_a2a_response(result)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action: {action}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ A2A task handler error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _format_a2a_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format CrewAI result as A2A JSONRPC response.

    Args:
        result: Result dictionary from CrewAI crew

    Returns:
        A2A-formatted response
    """
    return {
        "jsonrpc": "2.0",
        "result": {
            "parts": [{
                "text": json.dumps(result, indent=2)
            }]
        }
    }


# ===== Native CrewAI Endpoints =====

@app.post("/research", response_model=ResearchResponse)
async def research_questions(request: ResearchRequest):
    """
    Native CrewAI endpoint for research requests.

    This endpoint provides direct access to the CrewAI researcher without
    A2A protocol overhead. Ideal for new integrations.

    Request:
        - story_id: Unique identifier for the story
        - topic: Main topic or subject area
        - questions: List of research questions
        - context: Optional additional context

    Response:
        - status: "success" or "error"
        - message: Status message
        - research_id: Unique ID for this research
        - story_id: Story identifier
        - research_results: Array of research results
        - total_questions: Number of questions answered
    """
    try:
        logger.info(f"🔍 Research request received for story: {request.story_id}")
        logger.info(f"   Topic: {request.topic}")
        logger.info(f"   Questions: {len(request.questions)}")

        result = await researcher_crew.research_questions(
            questions=request.questions,
            topic=request.topic,
            story_id=request.story_id,
            context=request.context
        )

        return ResearchResponse(**result)

    except Exception as e:
        logger.error(f"❌ Research endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/history")
async def get_history(request: HistoryRequest):
    """
    Retrieve research history by research_id or story_id.

    Request:
        - research_id: Specific research ID (optional)
        - story_id: Story ID to find all related research (optional)

    At least one of research_id or story_id must be provided.
    """
    try:
        result = researcher_crew.get_research_history(
            research_id=request.research_id,
            story_id=request.story_id
        )
        return result

    except Exception as e:
        logger.error(f"❌ History endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """
    Get current status of all research requests.

    Returns:
        - status: "success"
        - total_research_requests: Number of research requests
        - research_history: List of all research records
    """
    try:
        result = researcher_crew.get_status()
        return result

    except Exception as e:
        logger.error(f"❌ Status endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker and monitoring.

    Returns:
        - status: "healthy"
        - service: Service name
        - timestamp: Current timestamp
    """
    return {
        "status": "healthy",
        "service": "CrewAI Researcher",
        "implementation": "crewai",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# ===== Server Startup =====

@click.command()
@click.option('--host', 'host', default='localhost', help='Host to bind to')
@click.option('--port', 'port', default=8083, help='Port to bind to')
@click.option('--reload', 'reload', is_flag=True, default=False, help='Enable hot reload')
def main(host: str, port: int, reload: bool):
    """
    Start the CrewAI Researcher FastAPI server.

    This server exposes the CrewAI-based researcher agent via HTTP,
    providing both native CrewAI endpoints and A2A protocol compatibility.
    """
    logger.info(f"🚀 Starting CrewAI Researcher on {host}:{port}")
    logger.info(f"📡 A2A agent card: http://{host}:{port}/.well-known/agent-card.json")
    logger.info(f"🔬 Research endpoint: http://{host}:{port}/research")
    logger.info(f"🔄 A2A compatibility: http://{host}:{port}/a2a/tasks")
    logger.info(f"❤️  Health check: http://{host}:{port}/health")

    uvicorn.run(
        "crewai_agents.researcher_crew.main:app" if reload else app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

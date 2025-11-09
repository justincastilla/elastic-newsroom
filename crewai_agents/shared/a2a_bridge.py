"""
A2A Protocol Bridge Utilities

Utilities for bridging A2A JSONRPC protocol to CrewAI HTTP/JSON.
Allows existing A2A agents (like Reporter) to call CrewAI agents seamlessly.

The main bridge implementation is in the FastAPI server (main.py),
but this module provides reusable utilities for A2A protocol handling.
"""

import json
from typing import Dict, Any, Optional


def parse_a2a_request(a2a_message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert A2A JSONRPC request to CrewAI-friendly format.

    Extracts the action and parameters from an A2A message and returns
    them in a simple dictionary format that CrewAI agents can process.

    Args:
        a2a_message: A2A JSONRPC message with input field

    Returns:
        Dictionary with action and params:
        {
            "action": "research_questions",
            "params": {...}
        }

    Example:
        a2a_msg = {
            "input": {
                "action": "research_questions",
                "story_id": "story_123",
                "questions": [...]
            }
        }
        parsed = parse_a2a_request(a2a_msg)
        # Returns: {"action": "research_questions", "params": {...}}
    """
    input_data = a2a_message.get("input", {})

    # If input is a string, parse it as JSON
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)
        except json.JSONDecodeError:
            # Return as-is if not valid JSON
            pass

    return {
        "action": input_data.get("action"),
        "params": input_data
    }


def format_a2a_response(crewai_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert CrewAI result to A2A JSONRPC response format.

    Wraps a CrewAI agent's response in the A2A JSONRPC envelope that
    A2A clients expect to receive.

    Args:
        crewai_result: Result dictionary from CrewAI crew execution

    Returns:
        A2A JSONRPC response:
        {
            "jsonrpc": "2.0",
            "result": {
                "parts": [{"text": "..."}]
            }
        }

    Example:
        crew_result = {
            "status": "success",
            "research_results": [...]
        }
        a2a_response = format_a2a_response(crew_result)
    """
    return {
        "jsonrpc": "2.0",
        "result": {
            "parts": [{
                "text": json.dumps(crewai_result, indent=2)
            }]
        }
    }


def create_a2a_agent_card(
    name: str,
    description: str,
    url: str,
    version: str,
    skills: list,
    implementation: str = "crewai"
) -> Dict[str, Any]:
    """
    Create an A2A agent card for a CrewAI agent.

    Generates a standard A2A agent card that allows A2A clients to
    discover and communicate with CrewAI agents.

    Args:
        name: Agent name (e.g., "Researcher (CrewAI)")
        description: Agent description
        url: Agent URL (e.g., "http://localhost:8083")
        version: Agent version (e.g., "2.0.0")
        skills: List of agent skills (A2A skill dictionaries)
        implementation: Implementation type (default: "crewai")

    Returns:
        A2A agent card dictionary

    Example:
        card = create_a2a_agent_card(
            name="Researcher (CrewAI)",
            description="Research agent powered by CrewAI",
            url="http://localhost:8083",
            version="2.0.0",
            skills=[...]
        )
    """
    return {
        "name": name,
        "description": description,
        "url": url,
        "version": version,
        "protocol_version": "0.3.0",
        "implementation": implementation,
        "preferred_transport": "HTTP",
        "capabilities": {
            "streaming": False,
            "push_notifications": False,
            "state_transition_history": True,
            "max_concurrent_tasks": 30
        },
        "skills": skills,
        "default_input_modes": ["application/json"],
        "default_output_modes": ["application/json"]
    }


def validate_a2a_request(request: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate an A2A request has required fields.

    Args:
        request: A2A request dictionary

    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, "error message")

    Example:
        valid, error = validate_a2a_request(request)
        if not valid:
            raise HTTPException(status_code=400, detail=error)
    """
    if "input" not in request:
        return False, "Missing 'input' field in A2A request"

    input_data = request["input"]
    if isinstance(input_data, dict) and "action" not in input_data:
        return False, "Missing 'action' field in A2A request input"

    return True, None

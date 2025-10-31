"""
Simple HTTP/REST wrapper for Newsroom MCP Tools

Provides simple REST endpoints for MCP tool discovery and execution.
This imports the actual tool implementations and wraps them in REST endpoints.
"""

import json
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Import the MCP module to access the underlying tool functions
import mcp_servers.newsroom_tools as newsroom_tools

# Import logging utilities
from utils import setup_logger

# Setup logger for MCP server
logger = setup_logger("MCP_SERVER", log_file="logs/MCP_Server.log")

app = FastAPI(title="Newsroom MCP HTTP Server")


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolListResponse(BaseModel):
    tools: List[Dict[str, Any]]


class ToolCallResponse(BaseModel):
    content: List[Dict[str, str]]


def get_tool_function(tool):
    """
    Extract the underlying function from a FastMCP tool decorator.

    FastMCP wraps functions in a FunctionTool object with a 'fn' attribute.
    This helper unwraps it to get the actual callable function.

    Args:
        tool: The tool object (either a FunctionTool wrapper or raw function)

    Returns:
        The underlying callable function
    """
    return tool.fn if hasattr(tool, 'fn') else tool


# Tool registry with metadata
# Access the underlying function from FastMCP's FunctionTool wrapper
TOOLS = {
    "research_questions": {
        "function": get_tool_function(newsroom_tools.research_questions),
        "name": "research_questions",
        "description": "Research multiple questions and return structured data with facts, figures, and sources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of research questions to answer"
                },
                "topic": {
                    "type": "string",
                    "description": "The article topic for context"
                }
            },
            "required": ["questions", "topic"]
        }
    },
    "generate_outline": {
        "function": get_tool_function(newsroom_tools.generate_outline),
        "name": "generate_outline",
        "description": "Generate article outline and identify 3-5 research questions that would strengthen the piece.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The article topic"},
                "angle": {"type": "string", "description": "The angle or focus of the article (optional)"},
                "target_length": {"type": "integer", "description": "Target word count for the article"}
            },
            "required": ["topic", "target_length"]
        }
    },
    "generate_article": {
        "function": get_tool_function(newsroom_tools.generate_article),
        "name": "generate_article",
        "description": "Generate article content based on topic, research, and archive context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "angle": {"type": "string"},
                "target_length": {"type": "integer"},
                "outline": {"type": "string"},
                "research_data": {"type": "string"},
                "archive_context": {"type": "string"}
            },
            "required": ["topic", "target_length", "outline", "research_data", "archive_context"]
        }
    },
    "review_article": {
        "function": get_tool_function(newsroom_tools.review_article),
        "name": "review_article",
        "description": "Review article draft for grammar, tone, consistency, and length.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "word_count": {"type": "integer"},
                "target_length": {"type": "integer"},
                "topic": {"type": "string"}
            },
            "required": ["content", "word_count", "target_length", "topic"]
        }
    },
    "apply_edits": {
        "function": get_tool_function(newsroom_tools.apply_edits),
        "name": "apply_edits",
        "description": "Apply editorial suggestions to article content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "original_content": {"type": "string"},
                "suggested_edits": {"type": "string"}
            },
            "required": ["original_content", "suggested_edits"]
        }
    },
    "generate_tags": {
        "function": get_tool_function(newsroom_tools.generate_tags),
        "name": "generate_tags",
        "description": "Generate tags and categories for an article.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "headline": {"type": "string"},
                "content": {"type": "string"},
                "topic": {"type": "string"}
            },
            "required": ["headline", "content", "topic"]
        }
    },
    "deploy_to_production": {
        "function": get_tool_function(newsroom_tools.deploy_to_production),
        "name": "deploy_to_production",
        "description": "Deploy article to production via CI/CD pipeline simulation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "story_id": {"type": "string"},
                "url_slug": {"type": "string"},
                "build_number": {"type": "string"}
            },
            "required": ["story_id", "url_slug"]
        }
    },
    "notify_subscribers": {
        "function": get_tool_function(newsroom_tools.notify_subscribers),
        "name": "notify_subscribers",
        "description": "Notify subscribers about new article via CRM system simulation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "story_id": {"type": "string"},
                "headline": {"type": "string"},
                "topic": {"type": "string"}
            },
            "required": ["story_id", "headline", "topic"]
        }
    }
}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Newsroom MCP HTTP Server", "tools_count": len(TOOLS)}


@app.get("/health")
async def health():
    """Dedicated health check endpoint for Docker and monitoring"""
    return {"status": "healthy", "service": "Newsroom MCP HTTP Server"}


@app.post("/mcp/v1/tools/list", response_model=ToolListResponse)
async def list_tools():
    """List all available MCP tools"""
    tools = [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["inputSchema"]
        }
        for tool in TOOLS.values()
    ]
    return {"tools": tools}


@app.post("/mcp/v1/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest, http_request: Request):
    """Call an MCP tool with the provided arguments"""
    tool_name = request.name
    arguments = request.arguments

    # Get calling agent from header
    calling_agent = http_request.headers.get("X-Calling-Agent", "UNKNOWN")

    # Log the tool call with custom format [AGENT → MCP]
    logger.info(f"[{calling_agent} → MCP] Calling tool: {tool_name}")

    if tool_name not in TOOLS:
        logger.error(f"[{calling_agent} → MCP] ❌ Tool not found: {tool_name}")
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    tool = TOOLS[tool_name]
    tool_function = tool["function"]

    try:
        # Call the tool function with unpacked arguments
        result = tool_function(**arguments)

        logger.info(f"[{calling_agent} → MCP] ✅ Tool {tool_name} completed")

        # Return in MCP format
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }
    except TypeError as e:
        # Log the actual arguments that caused the error
        logger.error(f"[{calling_agent} → MCP] ❌ TypeError in tool '{tool_name}': {str(e)}")
        logger.error(f"[{calling_agent} → MCP]    Arguments received: {json.dumps(arguments, indent=2)}")
        logger.error(f"[{calling_agent} → MCP]    Tool schema: {json.dumps(tool['inputSchema'], indent=2)}")

        raise HTTPException(
            status_code=400,
            detail=f"Invalid arguments for tool '{tool_name}': {str(e)}. Arguments: {json.dumps(arguments)}"
        )
    except Exception as e:
        logger.error(f"[{calling_agent} → MCP] ❌ Exception in tool '{tool_name}': {str(e)}")
        logger.error(f"[{calling_agent} → MCP]    Arguments received: {json.dumps(arguments, indent=2)}")

        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8095)

"""
MCP Client for Elastic News Agents

Uses FastMCP's built-in Client for direct communication with the MCP server.
Supports both in-process (direct FastMCP instance) and remote (SSE URL) connections.
Includes optional LLM-based tool selection via Anthropic.
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from anthropic import Anthropic
from fastmcp import Client as FastMCPClient
from utils.config import DEFAULT_MODEL


class MCPClient:
    """
    Client for interacting with MCP servers via FastMCP's built-in Client.

    The MCP client provides two modes of operation:
    1. Direct tool calling via call_tool() - works without Anthropic client
    2. LLM-based tool selection via select_and_call_tool() - requires Anthropic client
    """

    def __init__(self, mcp_transport, anthropic_client: Optional[Anthropic] = None, logger=None, agent_name: Optional[str] = None):
        """
        Initialize MCP client.

        Args:
            mcp_transport: FastMCP server instance or SSE URL string (e.g., "http://localhost:8095/mcp")
            anthropic_client: Optional Anthropic client for LLM-based tool selection.
            logger: Optional logger instance
            agent_name: Optional name of the agent using this client (for logging)
        """
        self.mcp_transport = mcp_transport
        self.anthropic_client = anthropic_client
        self.logger = logger
        self.agent_name = agent_name or "UNKNOWN"

        # Tool cache
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tools_cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=2)

    async def list_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        List available MCP tools with caching.

        Args:
            force_refresh: Force refresh cache even if not expired

        Returns:
            List of tool definitions
        """
        # Check cache
        if not force_refresh and self._tools_cache and self._tools_cache_time:
            if datetime.now() - self._tools_cache_time < self._cache_duration:
                if self.logger:
                    self.logger.info("Using cached MCP tools (%d tools)", len(self._tools_cache))
                return self._tools_cache

        if self.logger:
            self.logger.info("Fetching tools from MCP server...")

        try:
            client = FastMCPClient(self.mcp_transport)
            async with client:
                tools = await client.list_tools()

                # Convert to dict format for compatibility
                tools_list = [
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                    }
                    for tool in tools
                ]

                # Update cache
                self._tools_cache = tools_list
                self._tools_cache_time = datetime.now()

                if self.logger:
                    tool_list_str = ", ".join([f"{tool['name']}: {tool['description'][:80]}" for tool in tools_list])
                    self.logger.info("Discovered %d MCP tools: %s", len(tools_list), tool_list_str)

                return tools_list

        except Exception as e:
            if self.logger:
                self.logger.error("Failed to list MCP tools: %s", e)
            raise Exception(
                f"Runtime error: MCP server error - {e}. "
                f"The MCP server is REQUIRED for all agent operations."
            )

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool directly using FastMCP Client.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Tool result (text content)
        """
        if self.logger:
            self.logger.info("[%s -> MCP] Calling tool: %s", self.agent_name, tool_name)

        try:
            client = FastMCPClient(self.mcp_transport)
            async with client:
                result = await client.call_tool(tool_name, arguments)

                if result.is_error:
                    error_msg = result.content[0].text if result.content else "Unknown error"
                    raise Exception(f"Tool returned error: {error_msg}")

                # Extract text from the result
                tool_result = result.content[0].text if result.content else ""

                if self.logger:
                    self.logger.info("[%s -> MCP] Tool %s completed - Result length: %d characters", self.agent_name, tool_name, len(str(tool_result)))

                return tool_result

        except Exception as e:
            if self.logger:
                self.logger.error("[%s -> MCP] Tool call failed: %s", self.agent_name, e)
            raise Exception(
                f"Runtime error: MCP tool '{tool_name}' failed - {e}. "
                f"The MCP server is REQUIRED for all agent operations."
            )

    async def select_and_call_tool(self, task_description: str, context: Dict[str, Any]) -> Any:
        """
        Use LLM to select appropriate tool and call it.

        Requires an Anthropic client for LLM-based tool selection.

        Args:
            task_description: Description of what needs to be done
            context: Context information for tool selection

        Returns:
            Tool result

        Raises:
            Exception: If Anthropic client is not available
        """
        if not self.anthropic_client:
            raise Exception(
                "Anthropic client required for LLM-based tool selection. "
                "Use call_tool() directly if you don't have an Anthropic client."
            )

        # Get available tools
        tools = await self.list_tools()

        if not tools:
            raise Exception("No MCP tools available")

        # Build tool selection prompt
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tools
        ])

        prompt = f"""You are helping select the right MCP tool to accomplish a task.

**Task Description:**
{task_description}

**Context:**
{json.dumps(context, indent=2)}

**Available Tools:**
{tools_description}

Select the most appropriate tool and provide the arguments needed to call it.
Respond with a JSON object containing:
{{
  "tool_name": "name of the selected tool",
  "arguments": {{
    "arg1": "value1",
    "arg2": "value2"
  }},
  "reasoning": "why you selected this tool"
}}

Provide ONLY the JSON object, no additional text."""

        if self.logger:
            self.logger.info("Using LLM to select MCP tool for task: %s", task_description[:100])

        try:
            message = self.anthropic_client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Strip markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            selection = json.loads(response_text)

            tool_name = selection.get("tool_name")
            arguments = selection.get("arguments", {})
            reasoning = selection.get("reasoning", "")

            if self.logger:
                self.logger.info("LLM selected tool: %s - Reasoning: %s", tool_name, reasoning)

            result = await self.call_tool(tool_name, arguments)
            return result

        except Exception as e:
            if self.logger:
                self.logger.error("Tool selection failed: %s", e)
            raise Exception(f"Failed to select and call tool: {e}")


def create_mcp_client(logger=None, anthropic_client: Optional[Anthropic] = None, agent_name: Optional[str] = None) -> MCPClient:
    """
    Create MCP client with configuration from environment.

    Uses the MCP_SERVER_URL env var to connect via SSE transport,
    or falls back to in-process connection if a FastMCP instance is provided.

    Args:
        logger: Optional logger instance
        anthropic_client: Optional Anthropic client for tool selection
        agent_name: Optional name of the agent using this client (for logging)

    Returns:
        MCPClient instance
    """
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8095")

    # FastMCP Client expects the SSE endpoint path
    # The FastMCP http_app() serves at /mcp by default
    transport = f"{mcp_server_url}/mcp"

    return MCPClient(
        mcp_transport=transport,
        anthropic_client=anthropic_client,
        logger=logger,
        agent_name=agent_name
    )

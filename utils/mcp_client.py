"""
MCP Client for Elastic News Agents

Provides a client for agents to interact with MCP (Model Context Protocol) servers.
Includes tool discovery, caching, and LLM-based tool selection.
"""

import json
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import httpx
from anthropic import Anthropic


class MCPClient:
    """
    Client for interacting with MCP servers.

    The MCP client provides two modes of operation:
    1. Direct tool calling via call_tool() - works without Anthropic client
    2. LLM-based tool selection via select_and_call_tool() - requires Anthropic client

    This design allows the MCP client to be used in environments where LLM access
    is not available or desired, while still supporting intelligent tool selection
    when an LLM is available.
    """

    def __init__(self, mcp_server_url: str, anthropic_client: Optional[Anthropic] = None, logger=None, agent_name: Optional[str] = None):
        """
        Initialize MCP client.

        Args:
            mcp_server_url: URL of the MCP server (e.g., http://localhost:8095)
            anthropic_client: Optional Anthropic client for LLM-based tool selection.
                             If not provided, select_and_call_tool() will raise an exception,
                             but call_tool() will still work.
            logger: Optional logger instance
            agent_name: Optional name of the agent using this client (for logging)
        """
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.anthropic_client = anthropic_client
        self.logger = logger
        self.agent_name = agent_name or "UNKNOWN"

        # Tool cache
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._tools_cache_time: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=2)  # Cache for 2 minutes

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
                    self.logger.info(f"🔧 Using cached MCP tools ({len(self._tools_cache)} tools)")
                return self._tools_cache

        # Fetch tools from MCP server
        if self.logger:
            self.logger.info(f"🔄 Fetching tools from MCP server: {self.mcp_server_url}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.mcp_server_url}/mcp/v1/tools/list",
                    json={}
                )
                response.raise_for_status()

                result = response.json()
                tools = result.get("tools", [])

                # Update cache
                self._tools_cache = tools
                self._tools_cache_time = datetime.now()

                if self.logger:
                    self.logger.info(f"✅ Discovered {len(tools)} MCP tools")
                    for tool in tools:
                        self.logger.info(f"   - {tool.get('name')}: {tool.get('description', '')[:80]}")

                return tools

        except httpx.ConnectError as e:
            if self.logger:
                self.logger.error(f"❌ Cannot connect to MCP server at {self.mcp_server_url}")
            raise Exception(
                f"Configuration error: MCP server not running at {self.mcp_server_url}. "
                f"The MCP server is REQUIRED for all agent operations. "
                f"Start it with: python -m mcp_servers.newsroom_http_server"
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to list MCP tools: {e}")
            raise Exception(
                f"Runtime error: MCP server error at {self.mcp_server_url} - {e}. "
                f"The MCP server is REQUIRED for all agent operations."
            )

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool directly.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Tool result
        """
        if self.logger:
            self.logger.info(f"🔧 Calling MCP tool: {tool_name}")
            self.logger.info(f"   Arguments: {json.dumps(arguments, indent=2)[:200]}...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.mcp_server_url}/mcp/v1/tools/call",
                    json={
                        "name": tool_name,
                        "arguments": arguments
                    },
                    headers={
                        "X-Calling-Agent": self.agent_name
                    }
                )
                response.raise_for_status()

                result = response.json()
                tool_result = result.get("content", [{}])[0].get("text", "")

                if self.logger:
                    self.logger.info(f"✅ MCP tool {tool_name} completed")
                    self.logger.info(f"   Result length: {len(str(tool_result))} characters")

                return tool_result

        except httpx.ConnectError as e:
            if self.logger:
                self.logger.error(f"❌ Cannot connect to MCP server at {self.mcp_server_url}")
            raise Exception(
                f"Configuration error: MCP server not running at {self.mcp_server_url}. "
                f"The MCP server is REQUIRED for all agent operations. "
                f"Start it with: python -m mcp_servers.newsroom_http_server"
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ MCP tool call failed: {e}")
                # Try to get the actual error response
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    self.logger.error(f"   Server response: {e.response.text}")
            raise Exception(
                f"Runtime error: MCP tool '{tool_name}' failed - {e}. "
                f"The MCP server is REQUIRED for all agent operations."
            )

    async def select_and_call_tool(self, task_description: str, context: Dict[str, Any]) -> Any:
        """
        Use LLM to select appropriate tool and call it.

        This method requires an Anthropic client for LLM-based tool selection.
        If you don't have an Anthropic client, use call_tool() directly instead.

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
            f"- {tool.get('name')}: {tool.get('description', 'No description')}"
            for tool in tools
        ])

        # Build tool schemas for LLM
        tool_schemas = []
        for tool in tools:
            schema = {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            }
            tool_schemas.append(schema)

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
            self.logger.info(f"🤔 Using LLM to select MCP tool for task: {task_description[:100]}...")

        try:
            # Call Anthropic to select tool
            message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text

            # Strip markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse selection
            selection = json.loads(response_text)

            tool_name = selection.get("tool_name")
            arguments = selection.get("arguments", {})
            reasoning = selection.get("reasoning", "")

            if self.logger:
                self.logger.info(f"✅ LLM selected tool: {tool_name}")
                self.logger.info(f"   Reasoning: {reasoning}")

            # Call the selected tool
            result = await self.call_tool(tool_name, arguments)

            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Tool selection failed: {e}")
            raise Exception(f"Failed to select and call tool: {e}")


def create_mcp_client(logger=None, anthropic_client: Optional[Anthropic] = None, agent_name: Optional[str] = None) -> MCPClient:
    """
    Create MCP client with configuration from environment.

    Args:
        logger: Optional logger instance
        anthropic_client: Optional Anthropic client for tool selection
        agent_name: Optional name of the agent using this client (for logging)

    Returns:
        MCPClient instance
    """
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8095")

    return MCPClient(
        mcp_server_url=mcp_server_url,
        anthropic_client=anthropic_client,
        logger=logger,
        agent_name=agent_name
    )

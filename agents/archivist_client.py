"""
Archivist Client Module

The Archivist is an agent created in Elastic Cloud using Agent Builder and exposed
via the A2A (Agent-to-Agent) protocol. It searches historical news articles stored
in the 'news_archive' Elasticsearch index.

For more information about creating A2A-enabled agents in Elastic and finding your
agent card URL, see: https://www.elastic.co/docs/solutions/search/agent-builder/a2a-server

Provides two methods for calling the Elastic Archivist:
1. converse() - Uses the /converse endpoint (simpler, recommended)
2. send_task() - Uses the A2A JSONRPC protocol (/a2a endpoint)

Helper Functions:
- extract_response_text() - Robust text extraction with logging for unexpected formats
- prepare_search_query() - Consistent query formatting for both endpoints
"""

import json
import time
import httpx
import asyncio
from typing import Dict, Any, Optional
from utils import setup_logger, truncate_text

logger = setup_logger("ARCHIVIST_CLIENT")


# Query configuration
ARCHIVE_INDEX = "news_archive"
NO_RESULTS_MESSAGE = "No results found"


def extract_response_text(response_data: Any) -> str:
    """
    Extract text from Archivist response with robust error handling.

    Handles various response formats:
    - String: returned as-is
    - Dict with 'text' field: extracts text value
    - Dict with 'message' field: extracts message value (Elastic Agent Builder format)
    - Dict without 'text' or 'message': logs warning and serializes to JSON
    - List: attempts to extract text from items, otherwise serializes
    - Other types: converts to string with warning

    Args:
        response_data: Response data from Archivist (any type)

    Returns:
        Extracted text string, or JSON serialization for unexpected formats
    """
    if isinstance(response_data, str):
        return response_data

    elif isinstance(response_data, dict):
        # If response is a dict, try to extract text from expected fields
        if "text" in response_data:
            return response_data["text"]
        elif "message" in response_data:
            return response_data["message"]
        else:
            # Log warning about unexpected structure before falling back to JSON serialization
            logger.warning("Unexpected response dict structure. Expected 'text' field not found. Response keys: %s. Full response (truncated): %s. Falling back to JSON serialization.", list(response_data.keys()), truncate_text(str(response_data), max_length=200))
            return json.dumps(response_data, indent=2)

    elif isinstance(response_data, list):
        # Handle list responses (might be multiple parts)
        logger.warning("Response is a list with %d items. Attempting to extract text from parts.", len(response_data))
        text_parts = []
        for item in response_data:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
        return "\n".join(text_parts) if text_parts else json.dumps(response_data)

    else:
        # Fallback: convert to string
        logger.warning("Unexpected response type: %s. Converting to string.", type(response_data).__name__)
        return str(response_data) if response_data else ""


def resolve_agent_url(agent_url: Optional[str] = None, card_url: Optional[str] = None) -> str:
    """
    Resolve the base Kibana URL and agent ID from either an agent URL or card URL.

    Supports multiple URL formats:
    - Agent URL: https://host/api/agent_builder/a2a/{agentId}
    - Card URL:  https://host/api/agent_builder/a2a/{agentId}.json
    - Card URL:  https://host/.well-known/a2a/agent-card.json

    For /.well-known/ card URLs, the agent ID defaults to "elastic-ai-agent"
    since it can't be derived from the URL.

    Args:
        agent_url: Direct A2A endpoint URL (preferred)
        card_url: Agent card URL (fallback)

    Returns:
        Tuple-style dict with 'base_url' and 'agent_id'

    Raises:
        Exception: If neither URL is provided or URL format is unrecognized
    """
    url = agent_url or card_url
    if not url:
        raise Exception(
            "No Archivist URL configured. "
            "Set ELASTIC_ARCHIVIST_AGENT_URL or ELASTIC_ARCHIVIST_AGENT_CARD_URL."
        )

    # Format: https://host/api/agent_builder/a2a/{agentId}[.json]
    if "/api/agent_builder/a2a/" in url:
        base_url = url.split("/api/agent_builder/")[0]
        agent_id = url.split("/api/agent_builder/a2a/")[-1].replace(".json", "")
        logger.debug("Resolved agent URL: base=%s, agent_id=%s", base_url, agent_id)
        return {"base_url": base_url, "agent_id": agent_id}

    # Format: https://host/.well-known/a2a/agent-card.json
    if "/.well-known/" in url:
        base_url = url.split("/.well-known/")[0]
        logger.debug("Resolved .well-known card URL: base=%s (using default agent_id)", base_url)
        return {"base_url": base_url, "agent_id": "elastic-ai-agent"}

    # Format: https://host/api/agent_builder/converse (legacy direct endpoint)
    if "/api/agent_builder/" in url:
        base_url = url.split("/api/agent_builder/")[0]
        logger.debug("Resolved legacy agent_builder URL: base=%s", base_url)
        return {"base_url": base_url, "agent_id": "elastic-ai-agent"}

    raise Exception(
        f"Unrecognized Archivist URL format: {url}. "
        "Expected /api/agent_builder/a2a/{{agentId}} or /.well-known/a2a/agent-card.json"
    )


def prepare_search_query(query: str, index: str = ARCHIVE_INDEX, format_type: str = "summary") -> str:
    """
    Prepare a search query for the Archivist with consistent formatting.

    Args:
        query: The search topic/query
        index: The Elasticsearch index to search (default: news_archive)
        format_type: Type of response format:
            - "summary": Return results as a summary (for /converse endpoint)
            - "string": Return results as a single string (for A2A JSONRPC)

    Returns:
        Formatted query string ready to send to Archivist
    """
    if format_type == "summary":
        return (
            f"Search the '{index}' index for articles about: {query}. "
            f"Return relevant results as a summary. "
            f"If no results found, say '{NO_RESULTS_MESSAGE}'."
        )
    elif format_type == "string":
        return (
            f"Run a search in the '{index}' index about this topic: {query}. "
            f"Return the results as a single string. "
            f"If there are no results, then simply return the phrase '{NO_RESULTS_MESSAGE}'."
        )
    else:
        raise ValueError(f"Unknown format_type: {format_type}. Use 'summary' or 'string'.")


async def converse(
    query: str,
    story_id: str,
    agent_url: Optional[str] = None,
    card_url: Optional[str] = None,
    api_key: str = None,
    max_retries: int = 10,
    agent_id: str = None
) -> Dict[str, Any]:
    """
    Call the Archivist agent via /converse endpoint with retry logic.

    This is the simpler, recommended method for calling the Archivist.

    Args:
        query: Search query to send to Archivist
        story_id: Story ID for tracking
        agent_url: Direct A2A endpoint URL (preferred)
        card_url: Agent card URL (fallback if agent_url not set)
        api_key: Elastic Archivist API key
        max_retries: Maximum number of retry attempts (default: 10)
        agent_id: Agent ID to chat with (overrides ID derived from URL)

    Returns:
        Dict with status, query, response, and conversation_id

    Raises:
        Exception: If all retries fail or configuration is invalid
    """

    # Validate API key
    if not api_key:
        raise Exception("api_key is required")

    # Resolve the base URL and agent ID from whichever URL is available
    resolved = resolve_agent_url(agent_url=agent_url, card_url=card_url)
    base_url = resolved["base_url"]
    if agent_id is None:
        agent_id = resolved["agent_id"]
    endpoint = f"{base_url}/api/agent_builder/converse"

    logger.debug("Archivist Client - Using /converse endpoint. Endpoint: %s, Query: %s, Story ID: %s, Agent ID: %s", endpoint, query, story_id, agent_id)

    # Prepare the search query using helper function
    prepared_query = prepare_search_query(query, format_type="summary")

    # Build /converse request (simpler format)
    converse_request = {
        "input": prepared_query,
        "agent_id": agent_id
    }

    # Create headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {api_key}",
        "kbn-xsrf": "kibana"
    }

    # Log request details
    logger.debug("ARCHIVIST /converse REQUEST - Endpoint: %s, Payload: %s", endpoint, json.dumps(converse_request, indent=2))

    # Retry loop
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Attempt %d/%d (timeout: 60s)", attempt, max_retries)
            start_time = time.time()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    json=converse_request,
                    headers=headers
                )

            elapsed = time.time() - start_time
            response_text = response.text
            logger.info("Archivist response received (Attempt %d) - Status: %d, Length: %d characters, Preview: %s", attempt, response.status_code, len(response_text), truncate_text(response_text, max_length=100))

            # Check status
            response.raise_for_status()

            # Parse JSON
            if response.status_code == 200:
                result = response.json()

                # Extract response from /converse endpoint
                # The response field might be a string or nested in a different structure
                response_data = result.get("response", "")
                conversation_id = result.get("conversation_id", "")

                # Handle different response types with explicit error handling
                # Expected format: string or dict with 'text' field
                # Fallback behavior: JSON serialization with warning for debugging
                response_text = extract_response_text(response_data)

                # Check if we got content
                if response_text and len(response_text.strip()) > 0:
                    logger.info("Success on attempt %d - %d characters, Conversation ID: %s", attempt, len(response_text), conversation_id)
                    return {
                        "status": "success",
                        "query": query,
                        "response": response_text,
                        "conversation_id": conversation_id,
                        "articles": []  # Could parse this from response if needed
                    }
                else:
                    logger.warning("Empty response on attempt %d - Response data type: %s, Response data: %s", attempt, type(response_data), response_data)
                    if attempt < max_retries:
                        logger.info("Waiting 2 seconds before retry...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise Exception("Empty response after %d attempts" % max_retries)

        except httpx.TimeoutException as e:
            logger.warning("Timeout on attempt %d: %s", attempt, e)
            if attempt < max_retries:
                logger.info("Retrying...")
                await asyncio.sleep(2)
                continue
            else:
                raise Exception("Timeout after %d attempts" % max_retries)

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error on attempt %d: %d", attempt, e.response.status_code)
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception("HTTP error after %d attempts: %s" % (max_retries, e))

        except Exception as e:
            logger.error("Error on attempt %d: %s: %s", attempt, type(e).__name__, e)
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception("Failed after %d attempts: %s" % (max_retries, e))

    raise Exception(f"Failed after {max_retries} attempts")


async def send_task(
    query: str,
    story_id: str,
    agent_url: Optional[str] = None,
    card_url: Optional[str] = None,
    api_key: str = None,
    max_retries: int = 10
) -> Dict[str, Any]:
    """
    Call the Archivist agent via A2A JSONRPC protocol with retry logic.

    This is the original A2A JSONRPC method (more complex but standards-compliant).

    Args:
        query: Search query to send to Archivist
        story_id: Story ID for message tracking
        agent_url: Direct A2A endpoint URL (preferred)
        card_url: Agent card URL (fallback if agent_url not set)
        api_key: Elastic Archivist API key
        max_retries: Maximum number of retry attempts (default: 10)

    Returns:
        Dict with status, query, response, message_id, and articles

    Raises:
        Exception: If all retries fail or configuration is invalid
    """

    # Validate API key
    if not api_key:
        raise Exception("api_key is required")

    # Resolve the A2A endpoint from whichever URL is available
    resolved = resolve_agent_url(agent_url=agent_url, card_url=card_url)
    endpoint = f"{resolved['base_url']}/api/agent_builder/a2a/{resolved['agent_id']}"
    logger.debug("Archivist Client - Using A2A JSONRPC /a2a endpoint. Endpoint: %s, Query: %s, Story ID: %s", endpoint, query, story_id)

    # Generate unique message ID
    timestamp_ms = int(time.time() * 1000)
    message_id = f"msg-{timestamp_ms}-{story_id.replace('_', '')[:8]}"

    # Prepare the search query using helper function
    prepared_query = prepare_search_query(query, format_type="string")

    # Build A2A JSONRPC request
    a2a_request = {
        "id": message_id,
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "configuration": {
                "acceptedOutputModes": ["text/plain", "video/mp4"]
            },
            "message": {
                "kind": "message",
                "messageId": message_id,
                "metadata": {},
                "parts": [
                    {
                        "kind": "text",
                        "text": prepared_query
                    }
                ],
                "role": "user"
            }
        }
    }

    # Create headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {api_key}",
        "kbn-xsrf": "kibana"
    }

    # Log request details
    logger.debug("ARCHIVIST A2A JSONRPC REQUEST - Message ID: %s, Endpoint: %s, Payload: %s", message_id, endpoint, json.dumps(a2a_request, indent=2))

    # Retry loop
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Attempt %d/%d (timeout: 60s)", attempt, max_retries)
            start_time = time.time()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    json=a2a_request,
                    headers=headers
                )

            elapsed = time.time() - start_time
            response_text = response.text
            logger.info("Archivist response received (Attempt %d) - Status: %d, Length: %d characters, Preview: %s", attempt, response.status_code, len(response_text), truncate_text(response_text, max_length=100))

            # Check status
            response.raise_for_status()

            # Parse JSON
            if response.status_code == 200:
                result = response.json()

                # Extract text content from A2A JSONRPC response
                if "result" in result:
                    a2a_result = result.get("result", {})
                    # Parts are directly in the result object
                    parts = a2a_result.get("parts", [])

                    full_text = ""
                    for part in parts:
                        if part.get("kind") == "text":
                            text = part.get("text", "")
                            if text:
                                full_text += text

                    # Check if we got content
                    if full_text and len(full_text) > 0:
                        logger.info("Success on attempt %d - %d characters", attempt, len(full_text))
                        return {
                            "status": "success",
                            "query": query,
                            "response": full_text,
                            "message_id": message_id,
                            "articles": []  # Could parse this from response if needed
                        }
                    else:
                        logger.warning("Empty content on attempt %d", attempt)
                        if attempt < max_retries:
                            logger.info("Waiting 2 seconds before retry...")
                            await asyncio.sleep(2)
                            continue
                        else:
                            raise Exception("Empty content after %d attempts" % max_retries)

                elif "error" in result:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error("A2A error: %s", error_msg)
                    if attempt < max_retries:
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise Exception("A2A error after %d attempts: %s" % (max_retries, error_msg))

        except httpx.TimeoutException as e:
            logger.warning("Timeout on attempt %d: %s", attempt, e)
            if attempt < max_retries:
                logger.info("Retrying...")
                await asyncio.sleep(2)
                continue
            else:
                raise Exception("Timeout after %d attempts" % max_retries)

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error on attempt %d: %d", attempt, e.response.status_code)
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception("HTTP error after %d attempts: %s" % (max_retries, e))

        except Exception as e:
            logger.error("Error on attempt %d: %s: %s", attempt, type(e).__name__, e)
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception("Failed after %d attempts: %s" % (max_retries, e))

    raise Exception(f"Failed after {max_retries} attempts")


# Legacy alias for backward compatibility
async def call_archivist(
    query: str,
    story_id: str,
    agent_card_url: Optional[str] = None,
    agent_url: Optional[str] = None,
    api_key: str = None,
    max_retries: int = 10,
    agent_id: str = None
) -> Dict[str, Any]:
    """
    Legacy method that calls converse(). Kept for backward compatibility.

    New code should use converse() or send_task() directly.
    """
    return await converse(
        query=query,
        story_id=story_id,
        agent_url=agent_url,
        card_url=agent_card_url,
        api_key=api_key,
        max_retries=max_retries,
        agent_id=agent_id
    )

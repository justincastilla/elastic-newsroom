"""
Archivist Client Module

Provides two methods for calling the Elastic Archivist:
1. converse() - Uses the /converse endpoint (simpler, recommended)
2. send_task() - Uses the A2A JSONRPC protocol (/a2a endpoint)
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
    api_key: str = None,
    max_retries: int = 10,
    agent_id: str = "elastic-ai-agent"
) -> Dict[str, Any]:
    """
    Call the Archivist agent via /converse endpoint with retry logic.

    This is the simpler, recommended method for calling the Archivist.

    Args:
        query: Search query to send to Archivist
        story_id: Story ID for tracking
        agent_url: Base KB URL (e.g., https://...kb.../api/agent_builder/a2a/elastic-ai-agent)
        api_key: Elastic Archivist API key
        max_retries: Maximum number of retry attempts (default: 10)
        agent_id: Agent ID to chat with (default: "elastic-ai-agent")

    Returns:
        Dict with status, query, response, and conversation_id

    Raises:
        Exception: If all retries fail or configuration is invalid
    """

    # Validate API key
    if not api_key:
        raise Exception("api_key is required")

    # Parse the base URL from agent_url
    # agent_url format: https://...kb.../api/agent_builder/a2a/elastic-ai-agent
    # We need: https://...kb.../api/agent_builder/converse
    if agent_url and "/api/agent_builder/" in agent_url:
        base_url = agent_url.split("/api/agent_builder/")[0]
        endpoint = f"{base_url}/api/agent_builder/converse"
    else:
        raise Exception("Invalid agent_url - must contain /api/agent_builder/")

    logger.info(f"🔍 Archivist Client - Using /converse endpoint")
    logger.info(f"   Endpoint: {endpoint}")
    logger.info(f"   Query: {query}")
    logger.info(f"   Story ID: {story_id}")
    logger.info(f"   Agent ID: {agent_id}")

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
    logger.info(f"")
    logger.info(f"=" * 80)
    logger.info(f"📨 ARCHIVIST /converse REQUEST")
    logger.info(f"=" * 80)
    logger.info(f"Endpoint: {endpoint}")
    logger.info(f"")
    logger.info(f"JSON Payload:")
    logger.info(json.dumps(converse_request, indent=2))
    logger.info(f"=" * 80)
    logger.info(f"")

    # Retry loop
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔄 Attempt {attempt}/{max_retries} (timeout: 60s)")
            start_time = time.time()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    json=converse_request,
                    headers=headers
                )

            elapsed = time.time() - start_time
            logger.info(f"📥 Response received in {elapsed:.2f}s")
            logger.info(f"   Status Code: {response.status_code}")

            # Log raw response (truncated)
            response_text = response.text
            logger.info(f"📥 Archivist response received (Attempt {attempt})")
            logger.info(f"   Status: {response.status_code}")
            logger.info(f"   Length: {len(response_text)} characters")
            logger.info(f"   Preview: {truncate_text(response_text, max_length=100)}")

            # Check status
            response.raise_for_status()

            # Parse JSON
            if response.status_code == 200:
                result = response.json()

                # Extract response from /converse endpoint
                # The response field might be a string or nested in a different structure
                response_data = result.get("response", "")
                conversation_id = result.get("conversation_id", "")

                # Handle different response types
                response_text = ""
                if isinstance(response_data, str):
                    response_text = response_data
                elif isinstance(response_data, dict):
                    # If response is a dict, try to extract text from it
                    # It might be in a 'text' field or we need to serialize it
                    response_text = response_data.get("text", json.dumps(response_data))
                else:
                    # Fallback: convert to string
                    response_text = str(response_data) if response_data else ""

                # Check if we got content
                if response_text and len(response_text.strip()) > 0:
                    logger.info(f"✅ Success on attempt {attempt} - {len(response_text)} characters")
                    logger.info(f"   Conversation ID: {conversation_id}")
                    return {
                        "status": "success",
                        "query": query,
                        "response": response_text,
                        "conversation_id": conversation_id,
                        "articles": []  # Could parse this from response if needed
                    }
                else:
                    logger.warning(f"⚠️  Empty response on attempt {attempt}")
                    logger.warning(f"   Response data type: {type(response_data)}")
                    logger.warning(f"   Response data: {response_data}")
                    if attempt < max_retries:
                        logger.info(f"   Waiting 2 seconds before retry...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise Exception(f"Empty response after {max_retries} attempts")

        except httpx.TimeoutException as e:
            logger.warning(f"⏰ Timeout on attempt {attempt}: {e}")
            if attempt < max_retries:
                logger.info(f"   Retrying...")
                await asyncio.sleep(2)
                continue
            else:
                raise Exception(f"Timeout after {max_retries} attempts")

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error on attempt {attempt}: {e.response.status_code}")
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception(f"HTTP error after {max_retries} attempts: {e}")

        except Exception as e:
            logger.error(f"❌ Error on attempt {attempt}: {type(e).__name__}: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception(f"Failed after {max_retries} attempts: {e}")

    raise Exception(f"Failed after {max_retries} attempts")


async def send_task(
    query: str,
    story_id: str,
    agent_url: Optional[str] = None,
    api_key: str = None,
    max_retries: int = 10
) -> Dict[str, Any]:
    """
    Call the Archivist agent via A2A JSONRPC protocol with retry logic.

    This is the original A2A JSONRPC method (more complex but standards-compliant).

    Args:
        query: Search query to send to Archivist
        story_id: Story ID for message tracking
        agent_url: Direct A2A endpoint URL (e.g., https://.../a2a/agent-id)
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

    endpoint = agent_url
    logger.info(f"🔍 Archivist Client - Using A2A JSONRPC /a2a endpoint")
    logger.info(f"   Endpoint: {endpoint}")
    logger.info(f"   Query: {query}")
    logger.info(f"   Story ID: {story_id}")

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
    logger.info(f"")
    logger.info(f"=" * 80)
    logger.info(f"📨 ARCHIVIST A2A JSONRPC REQUEST")
    logger.info(f"=" * 80)
    logger.info(f"Message ID: {message_id}")
    logger.info(f"Endpoint: {endpoint}")
    logger.info(f"")
    logger.info(f"JSON Payload:")
    logger.info(json.dumps(a2a_request, indent=2))
    logger.info(f"=" * 80)
    logger.info(f"")

    # Retry loop
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔄 Attempt {attempt}/{max_retries} (timeout: 60s)")
            start_time = time.time()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    json=a2a_request,
                    headers=headers
                )

            elapsed = time.time() - start_time
            logger.info(f"📥 Response received in {elapsed:.2f}s")
            logger.info(f"   Status Code: {response.status_code}")

            # Log raw response (truncated)
            response_text = response.text
            logger.info(f"📥 Archivist response received (Attempt {attempt})")
            logger.info(f"   Status: {response.status_code}")
            logger.info(f"   Length: {len(response_text)} characters")
            logger.info(f"   Preview: {truncate_text(response_text, max_length=100)}")

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
                        logger.info(f"✅ Success on attempt {attempt} - {len(full_text)} characters")
                        return {
                            "status": "success",
                            "query": query,
                            "response": full_text,
                            "message_id": message_id,
                            "articles": []  # Could parse this from response if needed
                        }
                    else:
                        logger.warning(f"⚠️  Empty content on attempt {attempt}")
                        if attempt < max_retries:
                            logger.info(f"   Waiting 2 seconds before retry...")
                            await asyncio.sleep(2)
                            continue
                        else:
                            raise Exception(f"Empty content after {max_retries} attempts")

                elif "error" in result:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error(f"❌ A2A error: {error_msg}")
                    if attempt < max_retries:
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise Exception(f"A2A error after {max_retries} attempts: {error_msg}")

        except httpx.TimeoutException as e:
            logger.warning(f"⏰ Timeout on attempt {attempt}: {e}")
            if attempt < max_retries:
                logger.info(f"   Retrying...")
                await asyncio.sleep(2)
                continue
            else:
                raise Exception(f"Timeout after {max_retries} attempts")

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error on attempt {attempt}: {e.response.status_code}")
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception(f"HTTP error after {max_retries} attempts: {e}")

        except Exception as e:
            logger.error(f"❌ Error on attempt {attempt}: {type(e).__name__}: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception(f"Failed after {max_retries} attempts: {e}")

    raise Exception(f"Failed after {max_retries} attempts")


# Legacy alias for backward compatibility
async def call_archivist(
    query: str,
    story_id: str,
    agent_card_url: Optional[str] = None,
    agent_url: Optional[str] = None,
    api_key: str = None,
    max_retries: int = 10,
    agent_id: str = "elastic-ai-agent"
) -> Dict[str, Any]:
    """
    Legacy method that calls converse(). Kept for backward compatibility.

    New code should use converse() or send_task() directly.
    """
    return await converse(
        query=query,
        story_id=story_id,
        agent_url=agent_url,
        api_key=api_key,
        max_retries=max_retries,
        agent_id=agent_id
    )

"""
Archivist Client Module

Simple client for calling the Elastic Archivist via A2A JSONRPC protocol.
This module contains the working logic extracted from test_archivist_direct.py.
"""

import os
import json
import time
import httpx
import asyncio
from typing import Dict, Any, Optional
from utils import setup_logger

logger = setup_logger("ARCHIVIST_CLIENT")


async def call_archivist(
    query: str,
    story_id: str,
    agent_card_url: Optional[str] = None,
    agent_url: Optional[str] = None,
    api_key: str = None,
    max_retries: int = 10
) -> Dict[str, Any]:
    """
    Call the Archivist agent via A2A JSONRPC protocol with retry logic.

    This is the proven working implementation from test_archivist_direct.py.

    Args:
        query: Search query to send to Archivist
        story_id: Story ID for message tracking
        agent_card_url: Full URL to Archivist agent card (deprecated, for backward compatibility)
        agent_url: Direct A2A endpoint URL (preferred, e.g., https://.../a2a/agent-id)
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
    logger.info(f"🔍 Archivist Client - Using direct agent URL")

    endpoint = agent_url

    logger.info(f"   Endpoint: {endpoint}")
    logger.info(f"   Query: {query}")
    logger.info(f"   Story ID: {story_id}")

    # Generate unique message ID
    timestamp_ms = int(time.time() * 1000)
    message_id = f"msg-{timestamp_ms}-{story_id.replace('_', '')[:8]}"

    prepared_query = f"Run a search in the 'news_archive' index about this topic: {query}'. Return the results as a single string. If there are no results. then simply return the phrase 'No results found'."

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
    logger.info(f"📨 ARCHIVIST REQUEST")
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

            # Log raw response
            response_text = response.text
            logger.info(f"")
            logger.info(f"=" * 80)
            logger.info(f"📥 RAW RESPONSE (Attempt {attempt})")
            logger.info(f"=" * 80)
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Length: {len(response_text)} characters")
            logger.info(f"")
            logger.info(response_text if response_text else "(EMPTY)")
            logger.info(f"=" * 80)
            logger.info(f"")

            # Check status
            response.raise_for_status()

            # Parse JSON
            if response.status_code == 200:
                result = response.json()

                # Extract text content from A2A response
                if "result" in result:
                    a2a_result = result.get("result", {})
                    # Parts are directly in the result object, not nested in message
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

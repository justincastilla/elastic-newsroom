"""
Anthropic client initialization utilities for Elastic News

Provides centralized functions for initializing Anthropic clients with proper
error handling and logging.
"""

import os
import logging
from typing import Optional
from anthropic import Anthropic


def init_anthropic_client(logger: Optional[logging.Logger] = None) -> Optional[Anthropic]:
    """
    Initialize Anthropic client if API key is available.
    
    Args:
        logger: Optional logger for status messages. If not provided, uses root logger.
        
    Returns:
        Anthropic client instance if API key is available, None otherwise.
        
    Example:
        >>> from utils import init_anthropic_client, setup_logger
        >>> logger = setup_logger("MY_AGENT")
        >>> client = init_anthropic_client(logger)
        >>> if client:
        ...     # Use the client
        ...     pass
        >>> else:
        ...     # Handle the case where client is not available
        ...     pass
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        client = Anthropic(api_key=api_key)
        logger.info("✅ Anthropic client initialized")
        return client
    else:
        logger.warning("⚠️  ANTHROPIC_API_KEY not set - Anthropic features will be unavailable")
        return None

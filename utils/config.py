"""
Centralized configuration for Elastic News

Single source of truth for model strings, defaults, and shared constants.
"""

import os

# AI Model configuration
# Override via ANTHROPIC_MODEL environment variable
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

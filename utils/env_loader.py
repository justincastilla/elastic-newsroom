"""
Environment variable loading utilities for Elastic News

Provides centralized functions for loading environment variables from .env files
with fallback support.
"""

import os
from dotenv import load_dotenv, dotenv_values


def load_env_config():
    """
    Load environment variables from .env file into os.environ.
    
    This function tries multiple approaches to ensure environment variables are loaded:
    1. First tries load_dotenv() which loads into os.environ
    2. Falls back to dotenv_values() and manually sets missing values
    
    This is useful for ensuring all agents have access to required configuration
    regardless of how the environment is set up.
    
    Example:
        >>> from utils import load_env_config
        >>> load_env_config()
        >>> api_key = os.getenv("ANTHROPIC_API_KEY")
    """
    # First try load_dotenv() which loads into os.environ
    load_dotenv()
    
    # Also get values directly as a backup
    env_config = dotenv_values('.env')
    if env_config:
        # If dotenv_values found config, ensure it's in os.environ
        for key, value in env_config.items():
            if value and not os.getenv(key):
                os.environ[key] = value

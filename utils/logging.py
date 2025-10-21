"""
Centralized logging configuration for Elastic News

This module provides a single source of truth for logging configuration
across all agents and UI components.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional, Any


# ANSI color codes for terminal output
class AgentColors:
    """Color codes for different agents in terminal output"""
    RESET = '\033[0m'

    # Agent-specific colors
    NEWS_CHIEF = '\033[95m'      # Magenta
    REPORTER = '\033[96m'        # Cyan (powder blue)
    EDITOR = '\033[93m'          # Yellow
    RESEARCHER = '\033[92m'      # Green
    PUBLISHER = '\033[95m\033[1m'  # Bright Magenta (pink)
    ARCHIVIST_CLIENT = '\033[94m'  # Blue
    EVENT_HUB = '\033[97m'       # White
    ARTICLE_API = '\033[91m'     # Red
    MCP_SERVER = '\033[30m\033[102m'  # Black text on bright green background
    UI = '\033[90m'              # Gray

    # Fallback for unknown agents
    DEFAULT = '\033[37m'         # Light gray


# Map agent names to colors
AGENT_COLOR_MAP = {
    'NEWS_CHIEF': AgentColors.NEWS_CHIEF,
    'REPORTER': AgentColors.REPORTER,
    'EDITOR': AgentColors.EDITOR,
    'RESEARCHER': AgentColors.RESEARCHER,
    'PUBLISHER': AgentColors.PUBLISHER,
    'ARCHIVIST_CLIENT': AgentColors.ARCHIVIST_CLIENT,
    'EVENT_HUB': AgentColors.EVENT_HUB,
    'ARTICLE_API': AgentColors.ARTICLE_API,
    'MCP_SERVER': AgentColors.MCP_SERVER,
    'UI': AgentColors.UI,
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to agent names in console output"""

    def __init__(self, fmt, datefmt=None, agent_name=None):
        super().__init__(fmt, datefmt)
        self.agent_name = agent_name
        self.color = AGENT_COLOR_MAP.get(agent_name, AgentColors.DEFAULT)

    def format(self, record):
        # Format the message normally
        result = super().format(record)

        # Add color to the agent name in brackets
        if self.agent_name:
            colored_name = f"{self.color}[{self.agent_name}]{AgentColors.RESET}"
            result = result.replace(f"[{self.agent_name}]", colored_name)

        return result


def setup_logger(
    name: str,
    log_file: str = "logs/newsroom.log",
    level: int = logging.INFO,
    console: bool = True,
    console_colors: bool = False
) -> logging.Logger:
    """
    Set up a logger for an agent or component.

    Args:
        name: Name of the logger (e.g., "NEWS_CHIEF", "REPORTER", "UI")
        log_file: Path to log file (default: "logs/newsroom.log")
        level: Logging level (default: logging.INFO)
        console: Whether to also log to console (default: True)
        console_colors: Whether to use colors in console output (default: False)
                       Set to True only when running agents directly for debugging.
                       Set to False when running via start_newsroom.sh (avoids ANSI codes in log files)

    Returns:
        Configured logger instance

    Example:
        >>> from utils import setup_logger
        >>> logger = setup_logger("NEWS_CHIEF")  # Plain console output
        >>> logger.info("Story assigned successfully")
        >>>
        >>> # For debugging with colors
        >>> logger = setup_logger("NEWS_CHIEF", console_colors=True)
    """
    # Create logger with the specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    # File formatter (no colors)
    file_formatter = logging.Formatter(
        f'[{name}] %(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console formatter - use colored or plain depending on console_colors flag
    if console_colors:
        console_formatter = ColoredFormatter(
            f'[{name}] %(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            agent_name=name
        )
    else:
        # Plain formatter (no colors) - same as file formatter
        console_formatter = logging.Formatter(
            f'[{name}] %(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # File handler
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Console handler (enabled by default)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    # Don't propagate to root logger (avoids duplicate logs)
    logger.propagate = False

    return logger


def setup_ui_logger(
    name: str = "UI",
    log_file: str = "logs/UI.log",
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Set up a logger specifically for UI components.

    Args:
        name: Name of the logger (default: "UI")
        log_file: Path to log file (default: "logs/UI.log")
        level: Logging level (default: logging.INFO)
        console: Whether to also log to console (default: True for UI)

    Returns:
        Configured logger instance

    Example:
        >>> from utils import setup_ui_logger
        >>> logger = setup_ui_logger()
        >>> logger.info("Form submitted")
    """
    return setup_logger(name, log_file, level, console)


def format_json_for_log(data: Any, max_length: int = 200, indent: int = 2) -> str:
    """
    Format JSON data for logging with pretty printing and truncation.

    Args:
        data: Data to format (dict, list, or JSON string)
        max_length: Maximum length before truncation (default: 200)
        indent: JSON indentation spaces (default: 2)

    Returns:
        Formatted JSON string, truncated if needed

    Example:
        >>> logger.info(f"Received: {format_json_for_log(query_data)}")
    """
    try:
        # Convert to dict if it's a JSON string
        if isinstance(data, str):
            data = json.loads(data)

        # Pretty print with indentation
        formatted = json.dumps(data, indent=indent)

        # Truncate if too long
        if len(formatted) > max_length:
            return formatted[:max_length] + "..."

        return formatted
    except (json.JSONDecodeError, TypeError):
        # If not JSON, just truncate the string representation
        data_str = str(data)
        if len(data_str) > max_length:
            return data_str[:max_length] + "..."
        return data_str


def truncate_text(text: str, max_length: int = 40) -> str:
    """
    Truncate long text for logging.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 40)

    Returns:
        Truncated text with ellipsis if needed

    Example:
        >>> logger.info(f"Response: {truncate_text(long_response)}")
    """
    if not text:
        return ""

    text_str = str(text)
    if len(text_str) > max_length:
        return text_str[:max_length] + "..."
    return text_str

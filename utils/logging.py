"""
Centralized logging configuration for Elastic News

Provides two output modes:
- Console: Colored, human-readable format for development
- JSON: Structured JSON lines for production/Docker (LOG_FORMAT=json)
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Any


# ANSI color codes for terminal output
class AgentColors:
    """Color codes for different agents in terminal output"""
    RESET = '\033[0m'

    NEWS_CHIEF = '\033[95m'          # Magenta
    REPORTER = '\033[96m'            # Cyan
    EDITOR = '\033[93m'              # Yellow
    RESEARCHER = '\033[92m'          # Green
    PUBLISHER = '\033[95m\033[1m'    # Bright Magenta
    ARCHIVIST_CLIENT = '\033[94m'    # Blue
    EVENT_HUB = '\033[97m'           # White
    ARTICLE_API = '\033[91m'         # Red
    MCP_SERVER = '\033[30m\033[102m' # Black on green
    UI = '\033[90m'                  # Gray
    DEFAULT = '\033[37m'             # Light gray


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
    """Formatter that adds ANSI colors to agent names in console output."""

    def __init__(self, fmt, datefmt=None, agent_name=None):
        super().__init__(fmt, datefmt)
        self.agent_name = agent_name
        self.color = AGENT_COLOR_MAP.get(agent_name, AgentColors.DEFAULT)

    def format(self, record):
        result = super().format(record)
        if self.agent_name:
            colored_name = f"{self.color}[{self.agent_name}]{AgentColors.RESET}"
            result = result.replace(f"[{self.agent_name}]", colored_name)
        return result


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production environments.

    Each log line is a single JSON object with consistent fields,
    making logs parseable by ELK, Datadog, CloudWatch, etc.
    """

    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, '%Y-%m-%dT%H:%M:%S'),
            "level": record.levelname,
            "agent": self.agent_name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)


def setup_logger(
    name: str,
    log_file: str = "logs/newsroom.log",
    level: int = logging.INFO,
    console: bool = True,
    console_colors: bool = False
) -> logging.Logger:
    """
    Set up a logger for an agent or component.

    Output format is controlled by the LOG_FORMAT environment variable:
    - LOG_FORMAT=json  -> structured JSON lines (for production/Docker)
    - LOG_FORMAT=text  -> plain text (default)

    Args:
        name: Logger name (e.g., "NEWS_CHIEF", "REPORTER")
        log_file: Path to log file
        level: Logging level (default: INFO)
        console: Whether to also log to console
        console_colors: Whether to use ANSI colors in console output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    log_format_env = os.getenv("LOG_FORMAT", "text").lower()
    use_json = log_format_env == "json"

    # File handler — always plain text (JSON in file is hard to read during debugging)
    file_formatter = logging.Formatter(
        f'[{name}] %(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Console handler
    if console:
        if use_json:
            console_formatter = JSONFormatter(agent_name=name)
        elif console_colors:
            console_formatter = ColoredFormatter(
                f'[{name}] %(asctime)s %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                agent_name=name
            )
        else:
            console_formatter = logging.Formatter(
                f'[{name}] %(asctime)s %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    logger.propagate = False
    return logger


def setup_ui_logger(
    name: str = "UI",
    log_file: str = "logs/UI.log",
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """Set up a logger for UI components."""
    return setup_logger(name, log_file, level, console)


def format_json_for_log(data: Any, max_length: int = 200, indent: int = 2) -> str:
    """
    Format JSON data for logging with truncation.

    Args:
        data: Data to format (dict, list, or JSON string)
        max_length: Maximum length before truncation
        indent: JSON indentation spaces

    Returns:
        Formatted JSON string, truncated if needed
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
        formatted = json.dumps(data, indent=indent)
        if len(formatted) > max_length:
            return formatted[:max_length] + "..."
        return formatted
    except (json.JSONDecodeError, TypeError):
        data_str = str(data)
        if len(data_str) > max_length:
            return data_str[:max_length] + "..."
        return data_str


def truncate_text(text: str, max_length: int = 40) -> str:
    """Truncate long text for logging."""
    if not text:
        return ""
    text_str = str(text)
    if len(text_str) > max_length:
        return text_str[:max_length] + "..."
    return text_str

"""
Centralized logging configuration for Elastic News

This module provides a single source of truth for logging configuration
across all agents and UI components.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: str = "newsroom.log",
    level: int = logging.INFO,
    console: bool = False
) -> logging.Logger:
    """
    Set up a logger for an agent or component.

    Args:
        name: Name of the logger (e.g., "NEWS_CHIEF", "REPORTER", "UI")
        log_file: Path to log file (default: "newsroom.log")
        level: Logging level (default: logging.INFO)
        console: Whether to also log to console (default: False)

    Returns:
        Configured logger instance

    Example:
        >>> from utils import setup_logger
        >>> logger = setup_logger("NEWS_CHIEF")
        >>> logger.info("Story assigned successfully")
    """
    # Create logger with the specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        f'%(asctime)s [{name}] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Optional console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
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

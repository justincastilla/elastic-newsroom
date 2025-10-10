"""
Elastic News UI - Main Entry Point

Web interface for the Elastic News newsroom system.
Provides a user-friendly interface to assign stories and view completed articles.

Run this with: mesop main.py --port=3000
"""

import logging
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import setup_ui_logger

# Configure logging using centralized utility
logger = setup_ui_logger(name="UI", log_file="logs/UI.log", console=True)

# Set logging level for third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("mesop").setLevel(logging.INFO)
logging.getLogger("flask.app").setLevel(logging.CRITICAL)  # Suppress Flask 404 errors
logging.getLogger("werkzeug").setLevel(logging.WARNING)  # Suppress werkzeug verbose logs

# Import pages to register routes
# These pages will be auto-discovered by Mesop
from pages import home, article, status  # noqa: F401

logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
logger.info("🌐 Elastic News UI")
logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
logger.info("📝 Assignment Form: http://localhost:3000/")
logger.info("📄 Article Viewer: http://localhost:3000/article/{story_id}")
logger.info("📡 News Chief: http://localhost:8080")
logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

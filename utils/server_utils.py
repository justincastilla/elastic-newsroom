"""
Agent server startup utilities for Elastic News

Provides centralized functions for starting agent servers with uvicorn,
handling both development (hot reload) and production modes.
"""

import logging
import uvicorn
from typing import Callable, Optional


def run_agent_server(
    agent_name: str,
    host: str,
    port: int,
    create_app_func: Callable,
    logger: logging.Logger,
    reload: bool = False,
    reload_module: Optional[str] = None
):
    """
    Start an agent server using uvicorn with proper configuration.
    
    This function handles the common pattern of starting agent servers with
    optional hot reload for development.
    
    Args:
        agent_name: Human-readable name of the agent (e.g., "Reporter", "Editor")
        host: Host address to bind to
        port: Port number to bind to
        create_app_func: Function that creates the app instance (called if reload=False)
        logger: Logger instance for status messages
        reload: Enable hot reload for development
        reload_module: Module path for hot reload (e.g., "agents.reporter:app")
        
    Example:
        >>> from utils import run_agent_server, setup_logger
        >>> logger = setup_logger("REPORTER")
        >>> def create_my_app(host, port):
        ...     # Create and return app instance
        ...     pass
        >>> run_agent_server(
        ...     agent_name="Reporter",
        ...     host="localhost",
        ...     port=8081,
        ...     create_app_func=lambda: create_my_app("localhost", 8081),
        ...     logger=logger,
        ...     reload=True,
        ...     reload_module="agents.reporter:app"
        ... )
    """
    try:
        logger.info(f'Starting {agent_name} Agent server on {host}:{port}')
        
        # Get emoji based on agent name
        emoji_map = {
            "Reporter": "📝",
            "Editor": "✏️",
            "Researcher": "🔬",
            "Publisher": "📰",
            "News Chief": "👔"
        }
        emoji = emoji_map.get(agent_name, "🤖")
        
        print(f"{emoji} {agent_name} Agent is running on http://{host}:{port}")
        print(f"📋 Agent Card available at: http://{host}:{port}/.well-known/agent-card.json")
        
        if reload:
            print(f"🔄 Hot reload enabled - watching for file changes")
            
            if reload_module is None:
                raise ValueError("reload_module must be provided when reload=True")
            
            uvicorn.run(
                reload_module,
                host=host,
                port=port,
                reload=True,
                reload_dirs=["./agents"]
            )
        else:
            app_instance = create_app_func()
            uvicorn.run(app_instance, host=host, port=port)
            
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        print(f"❌ Error starting server: {e}")
        raise

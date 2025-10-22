#!/usr/bin/env python3
"""
Docker Entrypoint Script for Elastic News

Starts all agents and services in the correct order within a Docker container.
Ensures MCP server starts first (required dependency), then other services.
"""

import subprocess
import time
import sys
import signal
import os
from typing import List, Dict

# Agent configurations: name, port, module
AGENTS = [
    {"name": "MCP Server", "port": 8095, "module": "mcp_servers.newsroom_http_server:app"},
    {"name": "Event Hub", "port": 8090, "module": "services.event_hub:app"},
    {"name": "Article API", "port": 8085, "module": "services.article_api:app"},
    {"name": "News Chief", "port": 8080, "module": "agents.news_chief:app"},
    {"name": "Reporter", "port": 8081, "module": "agents.reporter:app"},
    {"name": "Editor", "port": 8082, "module": "agents.editor:app"},
    {"name": "Researcher", "port": 8083, "module": "agents.researcher:app"},
    {"name": "Publisher", "port": 8084, "module": "agents.publisher:app"},
]

# Global list to track running processes
processes: List[subprocess.Popen] = []


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🛑 Shutdown signal received. Stopping all agents...")
    for proc in processes:
        try:
            proc.terminate()
        except Exception as e:
            print(f"Error terminating process: {e}")

    # Wait for processes to terminate
    time.sleep(2)

    # Force kill if still running
    for proc in processes:
        try:
            if proc.poll() is None:
                proc.kill()
        except Exception as e:
            print(f"Error killing process: {e}")

    print("✅ All agents stopped")
    sys.exit(0)


def start_agent(name: str, port: int, module: str) -> subprocess.Popen:
    """Start a single agent using uvicorn"""
    print(f"🚀 Starting {name} on port {port}...")

    cmd = [
        "uvicorn",
        module,
        "--host", "0.0.0.0",  # Bind to all interfaces for Docker
        "--port", str(port),
    ]

    log_file = f"logs/{name.replace(' ', '_')}.log"

    try:
        with open(log_file, "w") as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if sys.platform != 'win32' else None
            )

        # Give it a moment to start
        time.sleep(1)

        # Check if process is still running
        if proc.poll() is None:
            print(f"   ✅ {name} started (PID: {proc.pid})")
            print(f"      URL: http://0.0.0.0:{port}")
            print(f"      Logs: {log_file}")
            return proc
        else:
            print(f"   ❌ {name} failed to start")
            print(f"      Check logs: {log_file}")
            return None

    except Exception as e:
        print(f"   ❌ Failed to start {name}: {e}")
        return None


def wait_for_mcp_server(max_retries: int = 30, retry_delay: int = 2) -> bool:
    """Wait for MCP server to be healthy before starting other agents"""
    import httpx

    print("\n⏳ Waiting for MCP server to be healthy...")

    for attempt in range(1, max_retries + 1):
        try:
            response = httpx.get("http://localhost:8095/health", timeout=5.0)
            if response.status_code == 200:
                print(f"✅ MCP server is healthy (attempt {attempt}/{max_retries})")
                return True
        except Exception as e:
            if attempt < max_retries:
                print(f"   ⏳ MCP server not ready yet (attempt {attempt}/{max_retries}), retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"   ❌ MCP server failed to become healthy: {e}")

    return False


def main():
    """Main entrypoint function"""
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 80)
    print("🏢 Elastic News - Docker Container Starting")
    print("=" * 80)
    print()

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Start MCP server first (REQUIRED dependency)
    mcp_config = AGENTS[0]  # MCP Server is first in list
    mcp_proc = start_agent(
        name=mcp_config["name"],
        port=mcp_config["port"],
        module=mcp_config["module"]
    )

    if not mcp_proc:
        print("\n❌ CRITICAL: MCP server failed to start - cannot continue")
        print("   The MCP server is REQUIRED for all agent operations")
        sys.exit(1)

    processes.append(mcp_proc)

    # Wait for MCP server to be healthy
    if not wait_for_mcp_server():
        print("\n❌ CRITICAL: MCP server is not healthy - cannot continue")
        signal_handler(None, None)
        sys.exit(1)

    print()

    # Start remaining agents
    for agent_config in AGENTS[1:]:  # Skip MCP server (already started)
        proc = start_agent(
            name=agent_config["name"],
            port=agent_config["port"],
            module=agent_config["module"]
        )

        if proc:
            processes.append(proc)
        else:
            print(f"⚠️  Warning: {agent_config['name']} failed to start")

        print()

    print("=" * 80)
    print("✅ Elastic News - All Services Started")
    print("=" * 80)
    print()
    print("📊 Service Endpoints:")
    print("   MCP Server:  http://0.0.0.0:8095 (Tool Provider - REQUIRED)")
    print("   Event Hub:   http://0.0.0.0:8090 (Real-time Events)")
    print("   Article API: http://0.0.0.0:8085 (Article Data)")
    print("   News Chief:  http://0.0.0.0:8080 (Coordinator)")
    print("   Reporter:    http://0.0.0.0:8081 (Article Writer)")
    print("   Editor:      http://0.0.0.0:8082 (Content Reviewer)")
    print("   Researcher:  http://0.0.0.0:8083 (Fact Gatherer)")
    print("   Publisher:   http://0.0.0.0:8084 (Article Publisher)")
    print()
    print("📁 Logs: /app/logs/")
    print("📄 Articles: /app/articles/")
    print()
    print("🌐 Access the UI at: http://localhost:3001 (when UI container is running)")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 80)
    print()

    # Wait for all processes
    try:
        while True:
            # Check if any process has died
            for proc in processes:
                if proc.poll() is not None:
                    print(f"⚠️  Warning: A process has terminated unexpectedly")
                    # Don't exit - let other processes continue

            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

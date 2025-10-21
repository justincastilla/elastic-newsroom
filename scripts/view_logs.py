#!/usr/bin/env python3
"""
Colorized Log Viewer for Elastic News Agents

Watches all agent log files and displays them in real-time with color-coded output.
Each agent has its own color for easy identification.
"""

import sys
import time
import os
from pathlib import Path
from threading import Thread
from queue import Queue, Empty
from datetime import datetime

# ANSI color codes matching agent colors from utils/logging.py
COLORS = {
    'MCP_Server': '\033[30m\033[102m',  # Black text on bright green background
    'Event_Hub': '\033[97m',            # White
    'Article_API': '\033[91m',          # Red
    'News_Chief': '\033[95m',           # Magenta
    'Reporter': '\033[96m',             # Cyan (powder blue)
    'Editor': '\033[93m',               # Yellow
    'Researcher': '\033[92m',           # Green
    'Publisher': '\033[95m\033[1m',     # Bright Magenta (pink)
    'ARCHIVIST_CLIENT': '\033[94m',     # Blue
}

RESET = '\033[0m'
BOLD = '\033[1m'

# Global queue for log messages
log_queue = Queue()

def tail_file(filepath, agent_name, color):
    """Tail a log file and put lines into the queue with color"""
    try:
        with open(filepath, 'r') as f:
            # Go to end of file
            f.seek(0, 2)

            while True:
                line = f.readline()
                if line:
                    # Lines already contain agent names from the logger, so just add color
                    colored_line = f"{color}{line.rstrip()}{RESET}"
                    log_queue.put((datetime.now(), colored_line))
                else:
                    time.sleep(0.1)
    except FileNotFoundError:
        log_queue.put((datetime.now(), f"{COLORS.get('News_Chief', '')}[{agent_name:15s}]{RESET} Log file not found: {filepath}"))
    except Exception as e:
        log_queue.put((datetime.now(), f"{COLORS.get('News_Chief', '')}[{agent_name:15s}]{RESET} Error reading log: {e}"))

def main():
    """Main function to start log viewers"""
    # Get log directory
    log_dir = Path(__file__).parent.parent / 'logs'

    if not log_dir.exists():
        print(f"❌ Log directory not found: {log_dir}")
        print("   Run './scripts/start_newsroom.sh' first to start the agents")
        sys.exit(1)

    # Agent log files to watch
    agents = {
        'MCP_Server': 'MCP_Server.log',
        'Event_Hub': 'Event_Hub.log',
        'Article_API': 'Article_API.log',
        'News_Chief': 'News_Chief.log',
        'Reporter': 'Reporter.log',
        'Editor': 'Editor.log',
        'Researcher': 'Researcher.log',
        'Publisher': 'Publisher.log',
    }

    print(f"{BOLD}🔍 Elastic News - Live Agent Logs{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"Log Directory: {log_dir}")
    print(f"Press Ctrl+C to stop")
    print(f"{BOLD}{'=' * 80}{RESET}")
    print()

    # Start a thread for each log file
    threads = []
    for agent_name, log_file in agents.items():
        filepath = log_dir / log_file
        color = COLORS.get(agent_name, RESET)

        thread = Thread(target=tail_file, args=(filepath, agent_name, color), daemon=True)
        thread.start()
        threads.append(thread)

    # Display log messages from queue
    try:
        while True:
            try:
                timestamp, line = log_queue.get(timeout=0.5)
                print(line, flush=True)
            except Empty:
                pass
    except KeyboardInterrupt:
        print(f"\n\n{BOLD}Stopped viewing logs{RESET}")
        sys.exit(0)

if __name__ == '__main__':
    main()

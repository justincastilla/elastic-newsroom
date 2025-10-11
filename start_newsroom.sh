#!/bin/bash
################################################################################
# Elastic News - Start All Agents
#
# Self-contained script that starts all newsroom agents in the background.
# Each agent runs on its designated port with uvicorn.
#
# Usage:
#   ./start_newsroom.sh           # Start all agents
#   ./start_newsroom.sh --reload  # Start with hot reload enabled
#   ./start_newsroom.sh --stop    # Stop all running agents
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="logs"
PID_FILE=".newsroom_pids"

# Agent configurations: name:port:module
AGENTS=(
    "News Chief:8080:agents.news_chief:app"
    "Reporter:8081:agents.reporter:app"
    "Editor:8082:agents.editor:app"
    "Researcher:8083:agents.researcher:app"
    "Publisher:8084:agents.publisher:app"
)

# Parse command line arguments
RELOAD_FLAG=""
START_UI=false

for arg in "$@"; do
    if [ "$arg" == "--reload" ]; then
        RELOAD_FLAG="--reload"
        echo -e "${BLUE}🔄 Hot reload enabled${NC}"
    elif [ "$arg" == "--with-ui" ]; then
        START_UI=true
        echo -e "${BLUE}🌐 UI will be started on port 3000${NC}"
    fi
done

if [ "$1" == "--stop" ]; then
    echo -e "${YELLOW}🛑 Stopping all newsroom agents...${NC}"
    echo ""

    # Stop using PID file first
    if [ -f "$PID_FILE" ]; then
        while IFS= read -r line; do
            NAME=$(echo "$line" | cut -d: -f1)
            PID=$(echo "$line" | cut -d: -f2)

            if ps -p "$PID" > /dev/null 2>&1; then
                echo -e "${YELLOW}   Stopping $NAME (PID: $PID)...${NC}"
                kill "$PID" 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm "$PID_FILE"
    fi

    # Also kill any processes still bound to the ports (including UI port 3000)
    echo -e "${YELLOW}   Checking for processes on ports 8080-8084, 3000...${NC}"
    for port in 8080 8081 8082 8083 8084 3000; do
        PID=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$PID" ]; then
            echo -e "${YELLOW}   Killing process on port $port (PID: $PID)...${NC}"
            kill -9 "$PID" 2>/dev/null || true
        fi
    done

    echo ""
    echo -e "${GREEN}✅ All agents stopped${NC}"
    exit 0
fi

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if any ports are already in use
echo -e "${BLUE}🔍 Checking for port conflicts...${NC}"
PORTS_IN_USE=""
for port in 8080 8081 8082 8083 8084; do
    if lsof -ti:$port > /dev/null 2>&1; then
        PORTS_IN_USE="$PORTS_IN_USE $port"
    fi
done

if [ -n "$PORTS_IN_USE" ]; then
    echo -e "${RED}❌ Error: Ports already in use:$PORTS_IN_USE${NC}"
    echo -e "${YELLOW}   Run './start_newsroom.sh --stop' to stop existing agents${NC}"
    exit 1
fi

# Clean up old PID file
rm -f "$PID_FILE"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🏢 Elastic News - Starting Newsroom Agents${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to start an agent
start_agent() {
    local NAME=$1
    local PORT=$2
    local MODULE=$3
    local LOG_FILE="$LOG_DIR/${NAME// /_}.log"

    echo -e "${YELLOW}🚀 Starting $NAME on port $PORT...${NC}"

    # Start uvicorn directly with the module
    if [ -n "$RELOAD_FLAG" ]; then
        uvicorn "$MODULE" --host localhost --port "$PORT" $RELOAD_FLAG > "$LOG_FILE" 2>&1 &
    else
        uvicorn "$MODULE" --host localhost --port "$PORT" > "$LOG_FILE" 2>&1 &
    fi

    local PID=$!

    # Save PID to file
    echo "$NAME:$PID" >> "$PID_FILE"

    # Give it a moment to start
    sleep 0.5

    # Check if process is still running
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ $NAME started (PID: $PID)${NC}"
        echo -e "${BLUE}      Logs: $LOG_FILE${NC}"
        echo -e "${BLUE}      URL: http://localhost:$PORT${NC}"
    else
        echo -e "${RED}   ❌ $NAME failed to start${NC}"
        echo -e "${RED}      Check logs: $LOG_FILE${NC}"
        return 1
    fi

    echo ""
}

# Start all agents
FAILED=0
for agent in "${AGENTS[@]}"; do
    IFS=':' read -r NAME PORT MODULE <<< "$agent"

    if ! start_agent "$NAME" "$PORT" "$MODULE"; then
        FAILED=1
    fi
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All agents started successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Agent Endpoints:${NC}"
    echo -e "${BLUE}   News Chief:  http://localhost:8080${NC}"
    echo -e "${BLUE}   Reporter:    http://localhost:8081${NC}"
    echo -e "${BLUE}   Editor:      http://localhost:8082${NC}"
    echo -e "${BLUE}   Researcher:  http://localhost:8083${NC}"
    echo -e "${BLUE}   Publisher:   http://localhost:8084${NC}"
    echo ""
    echo -e "${BLUE}📁 Logs directory: $LOG_DIR/${NC}"
    echo ""

    # Start UI if requested
    if [ "$START_UI" = true ]; then
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}🌐 Starting React UI on port 3001...${NC}"

        # Check if React UI exists
        if [ ! -f "react-ui/package.json" ]; then
            echo -e "${RED}   ❌ React UI not found in react-ui/ directory${NC}"
        else
            cd react-ui
            # Start React UI in background
            npm start > "../$LOG_DIR/UI.log" 2>&1 &
            UI_PID=$!
            echo "UI:$UI_PID" >> "../$PID_FILE"
            cd ..

            sleep 2

            if ps -p $UI_PID > /dev/null 2>&1; then
                echo -e "${GREEN}   ✅ React UI started (PID: $UI_PID)${NC}"
                echo -e "${BLUE}      Logs: $LOG_DIR/UI.log${NC}"
                echo -e "${BLUE}      URL: http://localhost:3001${NC}"
                echo ""
                echo -e "${BLUE}📝 React UI will open automatically at http://localhost:3001${NC}"
            else
                echo -e "${RED}   ❌ UI failed to start${NC}"
                echo -e "${RED}      Check logs: $LOG_DIR/UI.log${NC}"
            fi
        fi
        echo ""
    fi

    echo -e "${BLUE}💡 Commands:${NC}"
    echo -e "${BLUE}   View all logs:        tail -f $LOG_DIR/*.log${NC}"
    echo -e "${BLUE}   View specific agent:  tail -f $LOG_DIR/News_Chief.log${NC}"
    echo -e "${BLUE}   Stop all agents:      ./start_newsroom.sh --stop${NC}"
    echo -e "${BLUE}   Test workflow:        python tests/test_newsroom_workflow.py${NC}"
    if [ "$START_UI" = true ]; then
        echo -e "${BLUE}   Open UI:              open http://localhost:3000${NC}"
    fi
    echo ""
else
    echo -e "${RED}⚠️  Some agents failed to start${NC}"
    echo -e "${RED}   Check the log files in $LOG_DIR/ for details${NC}"
    echo ""
    echo -e "${YELLOW}🛑 Stopping successfully started agents...${NC}"
    ./start_newsroom.sh --stop
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🎉 Newsroom is ready!${NC}"
echo ""

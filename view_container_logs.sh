#!/bin/bash

# View logs from inside the containers (where they're actually written)

echo "======================================================================"
echo "Container Internal Logs Viewer"
echo "======================================================================"
echo ""
echo "The agents write logs to /app/logs/*.log inside containers"
echo "Docker compose logs won't show these - we need to read them directly"
echo ""

if [ "$1" == "follow" ] || [ "$1" == "-f" ]; then
    echo "📊 Following all logs (Ctrl+C to stop)..."
    echo "----------------------------------------------------------------------"
    docker compose exec newsroom-agents tail -f /app/logs/*.log
else
    echo "1. MCP Server Logs (last 30 lines)"
    echo "----------------------------------------------------------------------"
    docker compose exec newsroom-agents tail -30 /app/logs/MCP_Server.log 2>/dev/null || echo "❌ Log file not found"
    echo ""

    echo "2. Event Hub Logs (last 30 lines)"
    echo "----------------------------------------------------------------------"
    docker compose exec newsroom-agents tail -30 /app/logs/Event_Hub.log 2>/dev/null || echo "❌ Log file not found"
    echo ""

    echo "3. News Chief Logs (last 30 lines)"
    echo "----------------------------------------------------------------------"
    docker compose exec newsroom-agents tail -30 /app/logs/News_Chief.log 2>/dev/null || echo "❌ Log file not found"
    echo ""

    echo "4. Reporter Logs (last 30 lines)"
    echo "----------------------------------------------------------------------"
    docker compose exec newsroom-agents tail -30 /app/logs/Reporter.log 2>/dev/null || echo "❌ Log file not found"
    echo ""

    echo "5. Editor Logs (last 30 lines)"
    echo "----------------------------------------------------------------------"
    docker compose exec newsroom-agents tail -30 /app/logs/Editor.log 2>/dev/null || echo "❌ Log file not found"
    echo ""

    echo "6. Publisher Logs (last 30 lines)"
    echo "----------------------------------------------------------------------"
    docker compose exec newsroom-agents tail -30 /app/logs/Publisher.log 2>/dev/null || echo "❌ Log file not found"
    echo ""

    echo "7. CrewAI Researcher Logs"
    echo "----------------------------------------------------------------------"
    docker compose logs --tail=30 researcher-crew
    echo ""

    echo "======================================================================"
    echo "To follow logs in real-time, run: $0 follow"
    echo "======================================================================"
fi

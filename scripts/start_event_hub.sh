#!/bin/bash
#
# Start Event Hub Service
#
# Usage:
#   ./start_event_hub.sh           # Start normally
#   ./start_event_hub.sh --reload  # Start with hot reload
#   ./start_event_hub.sh --stop    # Stop running instance
#

set -e

HOST="localhost"
PORT=8090
RELOAD=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        --reload)
            RELOAD="--reload"
            shift
            ;;
        --stop)
            echo "🛑 Stopping Event Hub..."
            pkill -f "uvicorn event_hub.app:app" || echo "No Event Hub process found"
            exit 0
            ;;
        *)
            ;;
    esac
done

echo "=================================="
echo "🔔 Starting Event Hub Service"
echo "=================================="
echo "Host: $HOST"
echo "Port: $PORT"
echo "WebSocket: ws://$HOST:$PORT/ws"
echo "API: http://$HOST:$PORT"
if [ -n "$RELOAD" ]; then
    echo "Mode: Development (hot reload)"
else
    echo "Mode: Production"
fi
echo "=================================="
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Event Hub
python -m event_hub.app --host "$HOST" --port "$PORT" $RELOAD

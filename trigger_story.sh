#!/bin/bash

# Simple script to trigger a story assignment and watch the logs

STORY_TOPIC="${1:-AI in Healthcare}"

echo "======================================================================"
echo "Triggering Story Assignment: $STORY_TOPIC"
echo "======================================================================"
echo ""

# Assign story
echo "📰 Assigning story to News Chief..."
RESPONSE=$(curl -s -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": \"test-$(date +%s)\",
    \"method\": \"tasks/send\",
    \"params\": {
      \"input\": {
        \"parts\": [{
          \"text\": \"{\\\"action\\\": \\\"assign_story\\\", \\\"topic\\\": \\\"$STORY_TOPIC\\\", \\\"target_length\\\": 500}\"
        }]
      }
    }
  }")

echo "Response from News Chief:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract story_id from response if possible
STORY_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('result', {}).get('parts', [{}])[0].get('text', ''))" 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('story_id', 'unknown'))" 2>/dev/null)

if [ "$STORY_ID" != "unknown" ] && [ ! -z "$STORY_ID" ]; then
    echo "✅ Story assigned: $STORY_ID"
    echo ""
    echo "📊 Watching logs for story progression..."
    echo "   (Press Ctrl+C to stop)"
    echo ""

    # Watch all container logs
    docker compose logs -f --tail=20 newsroom-agents researcher-crew
else
    echo "⚠️  Could not extract story_id from response"
    echo ""
    echo "📊 Showing recent logs from all containers..."
    docker compose logs --tail=50 newsroom-agents researcher-crew
fi

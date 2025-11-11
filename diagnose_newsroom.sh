#!/bin/bash

echo "======================================================================"
echo "Elastic Newsroom Diagnostic Tool"
echo "======================================================================"
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

echo "1. Docker Container Status"
echo "----------------------------------------------------------------------"
docker compose ps
echo ""

echo "2. Container Health Status"
echo "----------------------------------------------------------------------"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
echo ""

echo "3. Newsroom Agents Container Logs (last 50 lines)"
echo "----------------------------------------------------------------------"
docker compose logs --tail=50 newsroom-agents
echo ""

echo "4. Researcher Crew Container Logs (last 50 lines)"
echo "----------------------------------------------------------------------"
docker compose logs --tail=50 researcher-crew
echo ""

echo "5. Test Agent Health Endpoints"
echo "----------------------------------------------------------------------"
echo "Testing MCP Server (8095)..."
curl -s -f http://localhost:8095/health && echo " ✅" || echo " ❌"

echo "Testing Event Hub (8090)..."
curl -s -f http://localhost:8090/health && echo " ✅" || echo " ❌"

echo "Testing News Chief (8080)..."
curl -s -f http://localhost:8080/.well-known/agent-card.json > /dev/null && echo " ✅" || echo " ❌"

echo "Testing Reporter (8081)..."
curl -s -f http://localhost:8081/.well-known/agent-card.json > /dev/null && echo " ✅" || echo " ❌"

echo "Testing Editor (8082)..."
curl -s -f http://localhost:8082/.well-known/agent-card.json > /dev/null && echo " ✅" || echo " ❌"

echo "Testing Researcher (8083)..."
curl -s -f http://localhost:8083/.well-known/agent-card.json > /dev/null && echo " ✅" || echo " ❌"

echo "Testing Publisher (8084)..."
curl -s -f http://localhost:8084/.well-known/agent-card.json > /dev/null && echo " ✅" || echo " ❌"
echo ""

echo "6. Environment Variables in newsroom-agents"
echo "----------------------------------------------------------------------"
docker compose exec newsroom-agents printenv | grep -E "ANTHROPIC|MCP_SERVER|EVENT_HUB" | sort
echo ""

echo "7. Environment Variables in researcher-crew"
echo "----------------------------------------------------------------------"
docker compose exec researcher-crew printenv | grep -E "ANTHROPIC|MCP_SERVER|EVENT_HUB" | sort
echo ""

echo "8. Process List in newsroom-agents"
echo "----------------------------------------------------------------------"
docker compose exec newsroom-agents ps aux
echo ""

echo "9. Process List in researcher-crew"
echo "----------------------------------------------------------------------"
docker compose exec researcher-crew ps aux
echo ""

echo "10. Check if agents are listening on expected ports"
echo "----------------------------------------------------------------------"
docker compose exec newsroom-agents netstat -tlnp 2>/dev/null || docker compose exec newsroom-agents ss -tlnp
echo ""

echo "======================================================================"
echo "Diagnostic Complete"
echo "======================================================================"

# Migration Guide: A2A Researcher → CrewAI Researcher

This guide provides step-by-step instructions for migrating from the A2A-based Researcher agent to the CrewAI-based Researcher agent in the Elastic Newsroom.

## Migration Overview

**From**: A2A Researcher (`agents/researcher.py`)
**To**: CrewAI Researcher (`crewai_agents/researcher_crew/`)
**Timeline**: Immediate (drop-in replacement)
**Downtime**: None (both can run in parallel during migration)

## Pre-Migration Checklist

- [ ] Verify Docker and docker-compose installed
- [ ] Verify ANTHROPIC_API_KEY in `.env` file
- [ ] Verify MCP Server is configured and running
- [ ] Verify Event Hub is configured
- [ ] Back up current `.env` file
- [ ] Note current system performance metrics

## Migration Steps

### Step 1: Verify Prerequisites

```bash
# Check Docker version
docker --version  # Should be >= 20.10

# Check docker-compose version
docker-compose --version  # Should be >= 1.29

# Verify .env file exists
ls -la .env

# Verify ANTHROPIC_API_KEY is set
grep ANTHROPIC_API_KEY .env
```

### Step 2: Build CrewAI Researcher Image

```bash
# Build the researcher-crew service
docker-compose build researcher-crew

# Verify build succeeded
docker images | grep researcher-crew
```

**Expected Output:**
```
elastic-news-researcher-crew   latest   abc123...   2 minutes ago   500MB
```

### Step 3: Start CrewAI Researcher (Parallel with A2A)

```bash
# Start researcher-crew service only
docker-compose up -d researcher-crew

# Verify container is running
docker-compose ps researcher-crew
```

**Expected Output:**
```
Name                          State     Ports
elastic-news-researcher-crew  Up (healthy)  0.0.0.0:8083->8083/tcp
```

### Step 4: Verify Health Check

```bash
# Check health endpoint
curl http://localhost:8083/health

# Expected response:
{
  "status": "healthy",
  "service": "CrewAI Researcher",
  "implementation": "crewai",
  "version": "1.0.0",
  "timestamp": "2025-11-09T..."
}
```

### Step 5: Verify A2A Protocol Compatibility

```bash
# Test A2A agent card
curl http://localhost:8083/.well-known/agent-card.json

# Verify response contains:
# - "name": "Researcher (CrewAI)"
# - "protocol_version": "0.3.0"
# - "skills": [...]

# Test A2A task endpoint
curl -X POST http://localhost:8083/a2a/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "get_status"
    }
  }'

# Verify JSONRPC response format
```

### Step 6: Test Full Workflow

```bash
# Test research endpoint directly
curl -X POST http://localhost:8083/research \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "migration_test",
    "topic": "CrewAI Migration Test",
    "questions": ["What is CrewAI?"]
  }'

# Verify response has:
# - "status": "success"
# - "research_results": [...]
# - "research_id": "research_migration_test_..."
```

### Step 7: Monitor Event Hub Integration

```bash
# Subscribe to Event Hub events
curl -N http://localhost:8090/stream

# In another terminal, trigger research
curl -X POST http://localhost:8083/research \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "event_test",
    "topic": "Event Hub Test",
    "questions": ["Test question?"]
  }'

# Verify events received:
# - research_started
# - research_completed
```

### Step 8: Verify Reporter Integration

```bash
# Ensure Reporter agent is running
docker-compose ps newsroom-agents

# Trigger full newsroom workflow
python tests/test_newsroom_workflow.py

# Verify:
# - News Chief assigns story
# - Reporter calls Researcher (CrewAI)
# - Research completes successfully
# - Article is generated
# - No errors in logs
```

### Step 9: Monitor Performance

```bash
# Check container resource usage
docker stats elastic-news-researcher-crew

# Expected:
# - CPU: 5-15% (idle), 50-80% (during research)
# - Memory: 200-300 MB
# - Network I/O: varies

# Check response times
time curl http://localhost:8083/health
# Should be < 100ms

time curl -X POST http://localhost:8083/research \
  -H "Content-Type: application/json" \
  -d '{"story_id": "perf_test", "topic": "Test", "questions": ["Test?"]}'
# Should be 10-30 seconds
```

### Step 10: View Logs

```bash
# View researcher logs
docker-compose logs -f researcher-crew

# Verify:
# - ✅ ChatAnthropic LLM initialized
# - ✅ Loaded 2 research tools
# - ✅ Event Hub client initialized
# - 🚀 Starting CrewAI Researcher on 0.0.0.0:8083
# - No errors or warnings
```

### Step 11: Finalize Migration (Remove A2A Researcher)

The A2A researcher has already been removed from the `newsroom-agents` container in `docker-compose.yml`. Verify this:

```bash
# Check docker-compose.yml
grep -A 5 "Port 8083" docker-compose.yml

# Should show:
# # 8083 - Researcher (moved to separate researcher-crew service)

# Verify researcher-crew service exists
grep -A 10 "researcher-crew:" docker-compose.yml
```

### Step 12: Restart All Services (Optional)

```bash
# Full restart to ensure clean state
docker-compose down
docker-compose up -d

# Verify all services healthy
docker-compose ps

# All services should show "(healthy)"
```

## Verification Checklist

After migration, verify the following:

### Functional Verification
- [ ] Health check returns "healthy"
- [ ] A2A agent card accessible
- [ ] Research endpoint accepts requests
- [ ] Research results have correct structure
- [ ] Event Hub receives research events
- [ ] Reporter can call researcher
- [ ] Full workflow completes successfully

### Performance Verification
- [ ] Container starts within 20 seconds
- [ ] Health check responds < 100ms
- [ ] Research requests complete within 30 seconds
- [ ] Memory usage < 500 MB
- [ ] No memory leaks over time

### Integration Verification
- [ ] MCP Server accessible from researcher
- [ ] Event Hub receives events
- [ ] Reporter discovers researcher via A2A
- [ ] React UI shows research events
- [ ] Logs appear in shared logs/ directory

## Rollback Procedure

If issues arise, you can rollback to the A2A researcher:

### Rollback Step 1: Stop CrewAI Researcher

```bash
docker-compose down researcher-crew
```

### Rollback Step 2: Re-enable A2A Researcher

Edit `docker-compose.yml`:

```yaml
# In newsroom-agents service, uncomment port 8083:
services:
  newsroom-agents:
    ports:
      - "8083:8083"  # Researcher (A2A)

# Comment out or remove researcher-crew service:
# researcher-crew:
#   build: ...
```

### Rollback Step 3: Re-add to docker_entrypoint.py

Edit `scripts/docker_entrypoint.py`:

```python
AGENTS = [
    {"name": "MCP Server", "port": 8095, ...},
    {"name": "Event Hub", "port": 8090, ...},
    {"name": "Article API", "port": 8085, ...},
    {"name": "News Chief", "port": 8080, ...},
    {"name": "Reporter", "port": 8081, ...},
    {"name": "Editor", "port": 8082, ...},
    {"name": "Researcher", "port": 8083, "module": "agents.researcher:app"},  # Re-added
    {"name": "Publisher", "port": 8084, ...},
]
```

### Rollback Step 4: Restart Services

```bash
docker-compose up -d

# Verify A2A researcher is running
curl http://localhost:8083/.well-known/agent-card.json

# Check "implementation" field:
# - A2A: "implementation" will not exist or be "python"
# - CrewAI: "implementation": "crewai"
```

## Troubleshooting

### Issue: Container Fails Health Check

**Symptoms:**
- `docker-compose ps` shows "(unhealthy)"
- Container restarts repeatedly

**Solution:**
```bash
# Check logs
docker-compose logs researcher-crew

# Common causes:
# - ANTHROPIC_API_KEY missing → Add to .env
# - Port 8083 already in use → Stop conflicting service
# - MCP Server not running → Start newsroom-agents first

# Fix and restart
docker-compose restart researcher-crew
```

### Issue: "Mock research data" in Results

**Symptoms:**
- Research results contain "Mock research data generated"
- Articles are very short

**Solution:**
```bash
# Verify ANTHROPIC_API_KEY
docker exec elastic-news-researcher-crew printenv | grep ANTHROPIC

# If missing, add to .env and restart
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." >> .env
docker-compose restart researcher-crew
```

### Issue: Reporter Can't Connect

**Symptoms:**
- Reporter logs show "Failed to contact Researcher"
- Workflow times out

**Solution:**
```bash
# Verify researcher is healthy
curl http://localhost:8083/health

# Test from Reporter container
docker exec elastic-news-agents curl http://researcher-crew:8083/health

# If fails, check Docker networking
docker network inspect elastic-news-network
# Both containers should be on same network
```

### Issue: No Events in UI

**Symptoms:**
- Research completes but UI shows no events
- Event Hub stream silent

**Solution:**
```bash
# Verify Event Hub is running
curl http://localhost:8090/health

# Check EVENT_HUB_ENABLED in researcher
docker exec elastic-news-researcher-crew printenv | grep EVENT_HUB

# Verify Event Hub URL
docker exec elastic-news-researcher-crew printenv | grep EVENT_HUB_URL
# Should be: http://newsroom-agents:8090

# Restart researcher
docker-compose restart researcher-crew
```

## Post-Migration Tasks

### 1. Update Documentation
- [ ] Update CLAUDE.md with CrewAI researcher info
- [ ] Update architecture diagrams
- [ ] Update README.md references

### 2. Monitor for 24 Hours
- [ ] Check container uptime
- [ ] Monitor memory usage
- [ ] Review logs for errors
- [ ] Test edge cases

### 3. Performance Tuning (Optional)
- [ ] Adjust max_iter in agent config
- [ ] Adjust temperature in LLM config
- [ ] Optimize Docker image size
- [ ] Configure resource limits

### 4. Cleanup (After 1 Week)
- [ ] Remove A2A researcher code (optional)
- [ ] Archive old logs
- [ ] Update CI/CD pipelines
- [ ] Document lessons learned

## Success Criteria

Migration is considered successful when:

✅ **Functional**
- All research requests complete successfully
- Reporter integration works without changes
- Event Hub receives all events
- UI displays research progress in real-time

✅ **Performance**
- Response times ≤ A2A researcher
- Memory usage < 500 MB
- No container restarts
- No errors in logs

✅ **Operational**
- Health checks pass continuously
- Docker logs show no warnings
- Full workflow tests pass
- Documentation is up-to-date

## Support

If you encounter issues not covered in this guide:

1. Check `crewai_agents/researcher_crew/README.md` for detailed documentation
2. Review `crewai_agents/PHASE_REPORTS.md` for implementation details
3. Check logs: `docker-compose logs -f researcher-crew`
4. Test endpoints individually using curl examples above
5. Verify environment variables are set correctly

## Timeline

**Estimated Migration Time**: 30-60 minutes
- Step 1-5: 10 minutes (setup and build)
- Step 6-10: 20 minutes (testing and verification)
- Step 11-12: 10 minutes (finalization)

**Recommended Schedule**:
- Day 1: Steps 1-7 (parallel deployment and basic testing)
- Day 2: Steps 8-10 (integration testing and monitoring)
- Day 3-7: Monitor performance and stability
- Week 2: Step 11 (finalize migration)

## Conclusion

The CrewAI Researcher is a drop-in replacement for the A2A Researcher with enhanced capabilities and maintainability. The migration is designed to be seamless with zero downtime and full backward compatibility.

Good luck with your migration!

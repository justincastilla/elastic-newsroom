# Elastic News - Detailed Workflow Test

This test demonstrates the complete multi-agent newsroom workflow with real-time monitoring and detailed output showing what each agent is doing at every step.

## Overview

The detailed workflow test is designed to showcase the best-case scenario of the Elastic News multi-agent system. It provides:

- **Real-time agent status updates** - See what each agent is doing as it happens
- **Detailed timing information** - Track how long each step takes
- **Step-by-step workflow visualization** - Understand the complete process
- **Comprehensive error handling** - Graceful fallbacks if something goes wrong
- **Performance metrics** - See the efficiency of the multi-agent system

## What the Test Does

The test runs through the complete newsroom workflow:

1. **Health Check** - Verifies all 5 agents are running and healthy
2. **Story Assignment** - Assigns a story to the News Chief
3. **Multi-Agent Writing** - Reporter coordinates with Researcher, Archivist, Editor, and Publisher
4. **Status Verification** - Confirms all agents completed their tasks successfully

## Prerequisites

### 1. Start All Agents

```bash
# Start all 5 agents
./start_newsroom.sh

# Or start with hot reload for development
./start_newsroom.sh --reload
```

### 2. Environment Variables

Create a `.env` file with required credentials:

```bash
# Required for AI content generation
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required for Elasticsearch indexing
ELASTICSEARCH_ENDPOINT=https://your-cluster.es.region.gcp.elastic.cloud:443
ELASTICSEARCH_API_KEY=your_elastic_api_key_here
ELASTIC_ARCHIVIST_INDEX=news_archive

# Optional for historical search (Archivist)
ELASTIC_ARCHIVIST_AGENT_CARD_URL=https://your-kb.kb.region.gcp.elastic.cloud/.well-known/a2a/agent-card.json
ELASTIC_ARCHIVIST_API_KEY=your_elastic_archivist_api_key_here
```

### 3. Create Elasticsearch Index

```bash
python scripts/create_elasticsearch_index.py
```

## Running the Test

### Option 1: Using the Runner Script (Recommended)

```bash
python run_detailed_test.py
```

The runner script will:
- Check if all agents are running
- Verify the test file exists
- Run the detailed test with proper error handling

### Option 2: Direct Execution

```bash
python tests/test_newsroom_workflow_detailed.py
```

## Expected Output

The test provides detailed real-time output like this:

```
🏢 Elastic News - Detailed Workflow Test (Best Case Scenario)
================================================================================
This test demonstrates the complete multi-agent newsroom workflow
with real-time status updates and detailed timing information.
================================================================================

⏱️  [   0.0s] HEALTH_CHECK: Verifying all agents are online and healthy
    ✅ News Chief is healthy (v1.0.0)
    ✅ Reporter is healthy (v1.0.0)
    ✅ Editor is healthy (v1.0.0)
    ✅ Researcher is healthy (v1.0.0)
    ✅ Publisher is healthy (v1.0.0)
    ✅ Completed in 2.1s - All 5 agents healthy

⏱️  [   2.1s] INIT_CLIENTS: Initializing A2A clients for all agents
    🤖 [   2.2s] News Chief: Client initialized (3 skills)
    🤖 [   2.3s] Reporter: Client initialized (6 skills)
    🤖 [   2.4s] Editor: Client initialized (3 skills)
    🤖 [   2.5s] Researcher: Client initialized (3 skills)
    🤖 [   2.6s] Publisher: Client initialized (3 skills)
    ✅ Completed in 0.5s - 5 clients ready

⏱️  [   2.6s] STORY_ASSIGNMENT: Assigning story to News Chief
    📝 Story Details:
       Topic: AI Agents Transform Modern Newsrooms
       Angle: How A2A protocol enables multi-agent collaboration in journalism
       Target Length: 1200 words
       Priority: high
    🤖 [   3.1s] News Chief: Story assigned ID: story_20250108_143022
    🤖 [   3.2s] Reporter: Assignment accepted Status: success
    ✅ Completed in 0.6s - Story ID: story_20250108_143022

⏱️  [   3.2s] ARTICLE_WRITING: Reporter coordinates multi-agent article writing
    🔄 Multi-Agent Workflow:
       1. Reporter generates outline and research questions
       2. Researcher + Archivist work in parallel
       3. Reporter writes article with all data
       4. Editor reviews and provides feedback
       5. Reporter applies editorial suggestions
       6. Publisher indexes to Elasticsearch
    🤖 [   8.5s] Reporter: Article written Word count: 1247
    🤖 [   8.6s] Researcher: Research completed Questions: 5
    🤖 [   8.7s] Archivist: Archive search completed Historical context gathered
    🤖 [   8.8s] Editor: Review completed Status: approved
    🤖 [   8.9s] Publisher: Article published ES indexed: news_archive
    ✅ Completed in 5.7s Complete multi-agent workflow finished

⏱️  [   8.9s] STATUS_VERIFICATION: Verifying final status of all agents
    🤖 [   9.1s] News Chief: Story status Status: completed
    🤖 [   9.2s] Reporter: Final status Draft: published
    ✅ Completed in 0.3s All agents verified

================================================================================
🎉 WORKFLOW COMPLETED SUCCESSFULLY
================================================================================

⏱️  Total Execution Time: 9.2 seconds

📊 Step Breakdown:
   ✅ HEALTH_CHECK: 2.1s - Verifying all agents are online and healthy
   ✅ INIT_CLIENTS: 0.5s - Initializing A2A clients for all agents
   ✅ STORY_ASSIGNMENT: 0.6s - Assigning story to News Chief
   ✅ ARTICLE_WRITING: 5.7s - Reporter coordinates multi-agent article writing
   ✅ STATUS_VERIFICATION: 0.3s - Verifying final status of all agents

🤖 Final Agent Status:
   • News Chief: Story status - Status: completed
   • Reporter: Final status - Draft: published
   • Researcher: Research completed - Questions: 5
   • Archivist: Archive search completed - Historical context gathered
   • Editor: Review completed - Status: approved
   • Publisher: Article published - ES indexed: news_archive

🔄 Multi-Agent Workflow Summary:
   ✓ News Chief: Coordinated story assignment and workflow
   ✓ Reporter: Generated outline, coordinated research, wrote article
   ✓ Researcher: Provided factual data and background information
   ✓ Archivist: Searched historical articles for context
   ✓ Editor: Reviewed article for quality and consistency
   ✓ Publisher: Indexed article to Elasticsearch

📈 Performance Metrics:
   • Agents Involved: 5
   • A2A Messages: ~15-20 inter-agent communications
   • Parallel Execution: Researcher + Archivist ran simultaneously
   • AI Model Calls: ~6 Anthropic API calls
   • Elasticsearch Operations: 2 (search + index)

================================================================================
✨ This demonstrates a fully functional multi-agent AI newsroom!
   Each agent has specialized capabilities and communicates
   seamlessly via the A2A protocol to produce high-quality news articles.
================================================================================
```

## Understanding the Workflow

### Agent Responsibilities

- **News Chief (8080)**: Coordinates the entire workflow, assigns stories
- **Reporter (8081)**: Writes articles, coordinates with other agents
- **Researcher (8083)**: Gathers factual information and background data
- **Archivist**: Searches historical articles for context (Elastic Cloud)
- **Editor (8082)**: Reviews articles for quality, grammar, and consistency
- **Publisher (8084)**: Indexes articles to Elasticsearch, generates tags

### Parallel Execution

The test demonstrates the efficiency of parallel execution:
- Researcher and Archivist work simultaneously
- This saves approximately 20 seconds compared to sequential execution
- The Reporter coordinates both agents and integrates their results

### A2A Protocol

All agents communicate using the Agent2Agent (A2A) protocol:
- Internal agents use A2A JSONRPC 2.0
- Archivist uses Elastic Agent Builder Converse API
- Each agent exposes its capabilities via agent cards

## Troubleshooting

### Common Issues

1. **Agents not running**
   ```bash
   # Check if agents are running
   ./start_newsroom.sh --stop
   ./start_newsroom.sh
   ```

2. **Environment variables not set**
   ```bash
   # Check your .env file
   cat .env
   ```

3. **Elasticsearch index not created**
   ```bash
   python scripts/create_elasticsearch_index.py
   ```

4. **Port conflicts**
   ```bash
   # Check what's using the ports
   lsof -i :8080-8084
   ```

### Debug Mode

To see detailed logs from each agent:

```bash
# View all agent logs
tail -f logs/*.log

# View specific agent logs
tail -f logs/Reporter.log
tail -f logs/News_Chief.log
```

## Performance Expectations

- **Total Time**: 8-15 seconds (depending on API response times)
- **Agent Health Check**: ~2 seconds
- **Story Assignment**: ~1 second
- **Article Writing**: 5-10 seconds (includes all AI calls)
- **Status Verification**: ~1 second

The actual timing depends on:
- Anthropic API response times
- Archivist search performance
- Network conditions
- System load

## What This Demonstrates

This test showcases:

1. **Multi-Agent Coordination**: How specialized agents work together
2. **A2A Protocol**: Seamless agent-to-agent communication
3. **Parallel Processing**: Efficient use of resources
4. **AI Integration**: Multiple AI model calls working in harmony
5. **Elasticsearch Integration**: Both search and indexing operations
6. **Error Handling**: Graceful fallbacks and comprehensive logging
7. **Real-time Monitoring**: Live status updates throughout the workflow

This is a production-ready demonstration of how AI agents can collaborate to produce high-quality content at scale.

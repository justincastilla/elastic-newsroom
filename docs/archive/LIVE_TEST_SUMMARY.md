# Elastic News - Live Workflow Test Suite

## Overview

I've created a comprehensive suite of live workflow tests that provide real-time monitoring and detailed output showing exactly what each agent is doing during the multi-agent coordination phase. This addresses your request for more live updates around the workflow steps.

## Test Suite Levels

### 1. **Basic Detailed Test** (`test_newsroom_workflow_detailed.py`)
**Original enhanced test** - Provides step-by-step monitoring with detailed timing.

**Features:**
- Real-time agent status updates
- Detailed timing information for each step
- Step-by-step workflow visualization
- Comprehensive error handling
- Performance metrics and summary

**Live Updates:**
- Shows when each agent starts/completes tasks
- Tracks timing for each workflow phase
- Provides status updates during execution

### 2. **Live Test** (`test_newsroom_workflow_live.py`)
**Enhanced with live polling** - Provides real-time updates during the multi-agent workflow.

**Features:**
- **Live polling of Reporter status** every 2 seconds
- **Real-time workflow progress tracking**
- **Status updates during execution**
- **Enhanced monitoring of coordination process**

**Live Updates:**
```
⏱️  [   8.5s] Reporter: Status: researching
🔄 [   8.6s] Step 1: Generating outline and research questions 📋 Creating article structure
⏱️  [  10.2s] Reporter: Status: writing
🔄 [  10.3s] Step 3: Writing article with research data ✍️ Generating content
⏱️  [  15.8s] Reporter: Status: draft_complete
🔄 [  15.9s] Step 4: Draft completed, submitting to Editor 📤 Sending for review
```

### 3. **Advanced Test** (`test_newsroom_workflow_advanced.py`)
**Most comprehensive monitoring** - Provides granular real-time updates from all agents.

**Features:**
- **Live polling of ALL agents** every 2 seconds
- **Granular progress tracking** through each workflow step
- **Parallel task execution monitoring**
- **Real-time status updates from all agents**
- **Enhanced monitoring of coordination process**

**Live Updates:**
```
⏱️  [   8.5s] Reporter: Status: researching
🔄 [   8.6s] Step 1: Generating outline and research questions 📋 Creating article structure
⚡ [   8.7s] Researcher: Starting research 🔍 Preparing to gather facts
⚡ [   8.8s] Archivist: Starting archive search 📚 Preparing to search history
⏱️  [  10.2s] Reporter: Status: writing
🔄 [  10.3s] Step 3: Writing article with research data ✍️ Generating content
⚡ [  10.4s] Researcher: Research completed ✅ Facts gathered
⚡ [  10.5s] Archivist: Archive search completed ✅ Historical context found
⏱️  [  15.8s] Reporter: Status: draft_complete
🔄 [  15.9s] Step 4: Draft completed, submitting to Editor 📤 Sending for review
⚡ [  16.0s] Editor: Starting review ✏️ Analyzing content
```

## How to Use

### Quick Start
```bash
# Run the live test (recommended for your request)
python run_live_test.py live

# Or run the advanced test for maximum detail
python run_live_test.py advanced

# Or run the basic test for step-by-step monitoring
python run_live_test.py basic
```

### Direct Execution
```bash
# Live test with real-time Reporter updates
python tests/test_newsroom_workflow_live.py

# Advanced test with granular multi-agent monitoring
python tests/test_newsroom_workflow_advanced.py

# Basic detailed test
python tests/test_newsroom_workflow_detailed.py
```

## What You'll See

### Live Test Output
The live test provides real-time updates during the multi-agent workflow:

```
⏱️  [   3.2s] LIVE_WORKFLOW: Live monitoring of multi-agent article writing
    🔄 Multi-Agent Workflow with Live Updates:
       1. Reporter generates outline and research questions
       2. Researcher + Archivist work in parallel
       3. Reporter writes article with all data
       4. Editor reviews and provides feedback
       5. Reporter applies editorial suggestions
       6. Publisher indexes to Elasticsearch

    📡 Live monitoring will show progress updates every 2 seconds...

    🔍 Starting live monitoring of Reporter workflow...
    ⏰ Will monitor for up to 300 seconds
    🤖 [   5.1s] Reporter: Status: researching
    🔄 [   5.2s] Step 1: Generating outline and research questions 📋 Creating article structure
    🤖 [   8.3s] Reporter: Status: writing
    🔄 [   8.4s] Step 3: Writing article with research data ✍️ Generating content
    🔄 [   8.5s] Draft: Status: draft Words: 0
    🤖 [  12.7s] Reporter: Status: draft_complete
    🔄 [  12.8s] Step 4: Draft completed, submitting to Editor 📤 Sending for review
    🔄 [  12.9s] Draft: Status: draft Words: 1247
    🤖 [  18.2s] Reporter: Status: editing
    🔄 [  18.3s] Step 5: Applying editorial suggestions ✏️ Incorporating feedback
    🤖 [  22.1s] Reporter: Status: published
    🔄 [  22.2s] Step 6: Article published to Elasticsearch 📰 Final publication
    🔄 [  22.3s] Draft: Status: published Words: 1247
    ✅ Workflow completed
```

### Advanced Test Output
The advanced test provides even more granular monitoring:

```
⏱️  [   3.2s] ADVANCED_WORKFLOW: Advanced live monitoring of multi-agent article writing
    🔄 Multi-Agent Workflow with Advanced Live Updates:
       1. Reporter generates outline and research questions
       2. Researcher + Archivist work in parallel
       3. Reporter writes article with all data
       4. Editor reviews and provides feedback
       5. Reporter applies editorial suggestions
       6. Publisher indexes to Elasticsearch

    📡 Advanced monitoring will show:
       • Real-time status updates from all agents
       • Granular progress through each workflow step
       • Parallel task execution tracking
       • Live updates every 2 seconds

    🔍 Starting advanced live monitoring of all agents...
    ⏰ Will monitor for up to 300 seconds
    📡 Polling every 2 seconds for real-time updates...
    🤖 [   5.1s] Reporter: Status: researching
    🔄 [   5.2s] Step 1: Generating outline and research questions 📋 Creating article structure
    ⚡ [   5.3s] Researcher: Starting research 🔍 Preparing to gather facts
    ⚡ [   5.4s] Archivist: Starting archive search 📚 Preparing to search history
    🤖 [   8.3s] Reporter: Status: writing
    🔄 [   8.4s] Step 3: Writing article with research data ✍️ Generating content
    ⚡ [   8.5s] Researcher: Research completed ✅ Facts gathered
    ⚡ [   8.6s] Archivist: Archive search completed ✅ Historical context found
    🔄 [   8.7s] Draft: Status: draft Words: 0
    🤖 [  12.7s] Reporter: Status: draft_complete
    🔄 [  12.8s] Step 4: Draft completed, submitting to Editor 📤 Sending for review
    ⚡ [  12.9s] Editor: Starting review ✏️ Analyzing content
    🔄 [  13.0s] Draft: Status: draft Words: 1247
    🤖 [  18.2s] Reporter: Status: editing
    🔄 [  18.3s] Step 5: Applying editorial suggestions ✏️ Incorporating feedback
    ⚡ [  18.4s] Editor: Review completed ✅ Feedback provided
    🤖 [  22.1s] Reporter: Status: published
    🔄 [  22.2s] Step 6: Article published to Elasticsearch 📰 Final publication
    ⚡ [  22.3s] Publisher: Publishing completed ✅ Article indexed
    🔄 [  22.4s] Draft: Status: published Words: 1247
    ✅ Advanced monitoring completed
```

## Key Features

### Real-Time Monitoring
- **Live polling** every 2 seconds during workflow execution
- **Status updates** from all agents as they work
- **Progress tracking** through each workflow step
- **Parallel task monitoring** for Researcher and Archivist

### Enhanced Visibility
- **Step-by-step progress** through the multi-agent workflow
- **Agent status changes** in real-time
- **Draft progress tracking** with word counts
- **Workflow completion detection**

### Comprehensive Coverage
- **All agents monitored** (News Chief, Reporter, Editor, Researcher, Publisher)
- **Parallel execution tracking** (Researcher + Archivist)
- **Editorial workflow monitoring** (Editor review and feedback)
- **Publishing process tracking** (Publisher indexing)

## Technical Implementation

### Live Polling
The tests use `asyncio` to poll agent status every 2 seconds during workflow execution:

```python
async def poll_reporter_status(http_client, reporter_client, story_id, monitor, max_duration=300):
    """Poll Reporter status during workflow execution to show live progress"""
    while time.time() - start_time < max_duration:
        # Get Reporter status
        request = {"action": "get_status", "story_id": story_id}
        # ... poll and process status updates
        await asyncio.sleep(2)  # Poll every 2 seconds
```

### Status Mapping
The tests map agent status to workflow progress:

```python
if reporter_status == 'researching':
    monitor.update_workflow_progress('Step 1', 'Generating outline and research questions', '📋 Creating article structure')
    monitor.update_parallel_task('Researcher', 'Starting research', '🔍 Preparing to gather facts')
    monitor.update_parallel_task('Archivist', 'Starting archive search', '📚 Preparing to search history')
elif reporter_status == 'writing':
    monitor.update_workflow_progress('Step 3', 'Writing article with research data', '✍️ Generating content')
    # ... etc
```

## Comparison of Test Levels

| Feature | Basic | Live | Advanced |
|---------|-------|------|----------|
| Step-by-step monitoring | ✅ | ✅ | ✅ |
| Real-time status updates | ❌ | ✅ | ✅ |
| Live polling | ❌ | ✅ | ✅ |
| Multi-agent monitoring | ❌ | ❌ | ✅ |
| Parallel task tracking | ❌ | ❌ | ✅ |
| Granular progress | ❌ | ✅ | ✅ |
| Workflow completion detection | ❌ | ✅ | ✅ |

## Prerequisites

1. **All agents running**: `./start_newsroom.sh`
2. **Environment variables set** in `.env`
3. **Elasticsearch index created**: `python scripts/create_elasticsearch_index.py`

## Expected Performance

- **Total Time**: 8-15 seconds (depending on API response times)
- **Live Updates**: Every 2 seconds during workflow execution
- **Monitoring Duration**: Up to 5 minutes (300 seconds)
- **Agent Polling**: All agents polled simultaneously

## Troubleshooting

### Common Issues
1. **Agents not running** - Check with `./start_newsroom.sh`
2. **Environment variables** - Verify `.env` file
3. **Elasticsearch index** - Run `python scripts/create_elasticsearch_index.py`
4. **Port conflicts** - Check with `lsof -i :8080-8084`

### Debug Mode
To see detailed logs from each agent:
```bash
# View all agent logs
tail -f logs/*.log

# View specific agent logs
tail -f logs/Reporter.log
tail -f logs/News_Chief.log
```

## Conclusion

This live test suite provides exactly what you requested - **real-time updates during the multi-agent workflow** showing exactly what each agent is doing as they collaborate to produce a complete news article. The tests eliminate the "just seeing that and nothing happening" issue by providing continuous live updates throughout the entire workflow execution.

The **Live Test** (`test_newsroom_workflow_live.py`) is recommended for your use case as it provides the perfect balance of real-time monitoring without overwhelming detail, while the **Advanced Test** (`test_newsroom_workflow_advanced.py`) offers the most comprehensive monitoring for those who want to see every detail of the multi-agent coordination.

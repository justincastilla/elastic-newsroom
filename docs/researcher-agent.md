# Researcher Agent

## Overview

The Researcher Agent provides **factual information, background context, and supporting data** for news articles. It uses Claude Sonnet 4 to synthesize research responses with structured data, facts, figures, and sources.

## Agent Details

**Name:** Researcher  
**Port:** 8083  
**URL:** `http://localhost:8083`  
**Protocol Version:** A2A SDK v0.3.8  
**Transport:** JSONRPC  

## Capabilities

- **Streaming:** No
- **Push Notifications:** Yes
- **State Transition History:** Yes
- **Max Concurrent Tasks:** 30

## Skills

### 1. Research Questions (`research.questions.bulk_research`)

Researches multiple questions and returns structured data with facts, figures, and sources.

**Tags:** `research`, `fact-checking`, `data`

**Example Request:**
```json
{
  "action": "research_questions",
  "story_id": "story_123",
  "topic": "AI in Journalism",
  "questions": [
    "What percentage of news organizations use AI?",
    "Who are the leading companies in AI journalism tools?",
    "What are the main benefits of AI in newsrooms?",
    "What concerns exist about AI-generated content?",
    "What is the projected growth of AI in media?"
  ]
}
```

**Response:**
```json
{
  "status": "completed",
  "research_id": "research_story_123_20250107_120000",
  "story_id": "story_123",
  "topic": "AI in Journalism",
  "research_results": [
    {
      "question": "What percentage of news organizations use AI?",
      "answer": "According to recent industry surveys, approximately 65% of news organizations have implemented some form of AI technology...",
      "confidence": "high",
      "sources": ["Industry Report 2024", "Media Technology Survey"]
    },
    // ... 4 more answers
  ],
  "total_questions": 5,
  "timestamp": "2025-01-07T12:00:00"
}
```

### 2. Get Research History (`research.history.get_history`)

Retrieves past research by research_id or story_id.

**Tags:** `history`, `retrieval`

**Example Requests:**
```json
{
  "action": "get_history",
  "research_id": "research_story_123_20250107_120000"
}
```

Or:
```json
{
  "action": "get_history",
  "story_id": "story_123"
}
```

**Response:**
```json
{
  "status": "success",
  "research_records": [
    {
      "research_id": "research_story_123_20250107_120000",
      "story_id": "story_123",
      "topic": "AI in Journalism",
      "completed_at": "2025-01-07T12:00:00",
      "question_count": 5
    }
  ],
  "total_count": 1
}
```

### 3. Get Status (`research.status`)

Returns current status and history of all research requests.

**Tags:** `status`, `reporting`

**Example Request:**
```json
{
  "action": "get_status"
}
```

**Response:**
```json
{
  "status": "success",
  "total_research_completed": 15,
  "research_history": [
    {
      "research_id": "research_story_123_20250107_120000",
      "story_id": "story_123",
      "status": "completed",
      "completed_at": "2025-01-07T12:00:00"
    }
  ]
}
```

## Research Structure

Each research response includes:

### Question Object
```json
{
  "question": "Original question text",
  "answer": "Comprehensive answer with facts and figures",
  "confidence": "high|medium|low",
  "sources": ["Source 1", "Source 2"]
}
```

### Confidence Levels
- **High:** Well-established facts with multiple sources
- **Medium:** Reasonable data with some sources
- **Low:** Limited data or speculative information

## Workflow

```
Researcher
    │
    ├─► Receives research request from Reporter
    │
    ├─► Generates comprehensive answers using Claude Sonnet 4
    │   ├─ Facts and statistics
    │   ├─ Company/stakeholder information
    │   ├─ Industry context
    │   ├─ Impact analysis
    │   └─ Future trends
    │
    ├─► Structures data for article integration
    │
    └─► Returns research results to Reporter
```

## Integration with Other Agents

### Reporter Agent
- **URL:** `http://localhost:8081`
- **Interaction:** Reporter sends research questions, Researcher returns structured answers
- **Execution:** Called in parallel with Archivist
- **Data Format:** JSON with structured research results

### Parallel Execution

The Researcher is designed to be called in parallel with other agents:
- Reporter calls Researcher and Archivist simultaneously
- Researcher processes questions independently
- Results are available as soon as processing completes

## Research Prompt Structure

The Researcher uses structured prompts to ensure high-quality research:

### Input Requirements
- **Topic:** Main subject of the article
- **Questions:** Specific research questions (typically 5)
- **Story ID:** For tracking and history

### Output Structure
- **Facts & Statistics:** Concrete data points with percentages
- **Company Names:** Specific organizations and stakeholders
- **Context:** Background information and trends
- **Sources:** References for credibility
- **Confidence:** Assessment of data reliability

### AI-Powered Research

When Anthropic API is available:
- Uses Claude Sonnet 4 for research synthesis
- Generates comprehensive, structured responses
- Provides confidence levels and sources
- Formats data for natural article integration

When API is not available:
- Falls back to mock research data
- Logs warning: `ANTHROPIC_API_KEY not set - will use mock research`
- System remains functional with placeholder data

## Configuration

### Environment Variables

```bash
# Required: Anthropic API for AI-powered research
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
```

### Port Configuration

```bash
uvicorn agents.researcher:app --host localhost --port 8083
```

## Running the Agent

### Start via Script
```bash
./start_newsroom.sh
```

### Start Individually
```bash
uvicorn agents.researcher:app --host localhost --port 8083
```

### Start with Hot Reload (Development)
```bash
uvicorn agents.researcher:app --host localhost --port 8083 --reload
```

## Agent Card

Access the agent card at:
```
http://localhost:8083/.well-known/agent-card.json
```

## Logging

Logs are written to `newsroom.log` with the `[RESEARCHER]` prefix.

Example log output:
```
2025-01-07 12:00:00 [RESEARCHER] INFO: 📥 Received query: {"action": "research_questions", ...
2025-01-07 12:00:00 [RESEARCHER] INFO: 🎯 Action: research_questions
2025-01-07 12:00:05 [RESEARCHER] INFO: 🔬 Researching 5 questions for story_123...
2025-01-07 12:00:10 [RESEARCHER] INFO: ✅ Research completed for story_123
```

## Error Handling

### Invalid Action
```json
{
  "status": "error",
  "message": "Unknown action: invalid_action",
  "available_actions": [
    "research_questions",
    "get_history",
    "get_status"
  ]
}
```

### Missing Required Fields
```json
{
  "status": "error",
  "message": "Missing required field: questions"
}
```

### Research Failure
```json
{
  "status": "error",
  "message": "Failed to complete research: [error details]"
}
```

## Testing

The Researcher is tested as part of the end-to-end workflow:

```bash
python tests/test_newsroom_workflow.py
```

Expected output:
```
✅ RESEARCHER: Research completed
   Questions: 5
   Confidence: high
```

## Best Practices

1. **Question Quality:** Provide specific, focused questions for better answers
2. **Question Count:** 3-7 questions optimal for comprehensive coverage
3. **Topic Context:** Include topic for better context-aware responses
4. **History Tracking:** Use research_id for tracking and retrieval

## Research Question Examples

### Good Questions
- "What percentage of Fortune 500 companies use AI for customer service?"
- "Who are the top 3 cloud infrastructure providers by market share?"
- "What are the main security concerns with IoT devices?"

### Questions to Avoid
- Overly broad: "Tell me everything about AI"
- Yes/No: "Is AI good?"
- Opinion-based: "What do you think about technology?"

## Data Quality

The Researcher emphasizes:
- **Specificity:** Concrete numbers and percentages
- **Currency:** Recent data and trends
- **Attribution:** Clear source references
- **Objectivity:** Balanced, fact-based responses
- **Relevance:** Information directly applicable to the article

## Future Enhancements

1. **Real-Time Data:** Integration with live data APIs
2. **Source Verification:** Automatic fact-checking against databases
3. **Citation Management:** Structured bibliography generation
4. **Multi-Language:** Research in multiple languages
5. **Domain Expertise:** Specialized research for different topics

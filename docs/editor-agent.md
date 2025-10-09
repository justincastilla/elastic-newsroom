# Editor Agent

## Overview

The Editor Agent **reviews article drafts** for grammar, tone, consistency, and length. It provides detailed editorial feedback using Claude Sonnet 4 and ensures articles meet publication standards before being sent to the Publisher.

## Agent Details

**Name:** Editor  
**Port:** 8082  
**URL:** `http://localhost:8082`  
**Protocol Version:** A2A SDK v0.3.8  
**Transport:** JSONRPC  

## Capabilities

- **Streaming:** No
- **Push Notifications:** Yes
- **State Transition History:** Yes
- **Max Concurrent Tasks:** 20

## Skills

### 1. Review Draft (`editorial.review.draft_review`)

Reviews article drafts for grammar, professional tone, consistency, and appropriate length.

**Tags:** `editing`, `review`, `quality-control`

**Example Request:**
```json
{
  "action": "review_draft",
  "draft": {
    "story_id": "story_123",
    "content": "[Article content...]",
    "headline": "AI Agents Transform Modern Newsrooms",
    "word_count": 950,
    "assignment": {
      "topic": "AI in Journalism",
      "target_length": 1000,
      "priority": "high"
    }
  }
}
```

**Response:**
```json
{
  "status": "reviewed",
  "review_id": "review_story_123_20250107_120000",
  "story_id": "story_123",
  "approval_status": "approved",
  "feedback": {
    "grammar": "Excellent. No grammatical errors detected.",
    "tone": "Professional and balanced. Appropriate for news publication.",
    "consistency": "Well-structured with clear narrative flow.",
    "length": "950 words (target: 1000). Within acceptable range.",
    "suggestions": [
      "Consider adding transition to third paragraph",
      "Headline could be more specific"
    ]
  },
  "metadata": {
    "tags": ["ai", "journalism", "technology"],
    "summary": "Article examines how AI agents transform newsrooms...",
    "headline_suggestion": "AI Agents Transform Newsrooms Through Multi-Agent Collaboration"
  }
}
```

### 2. Get Review (`editorial.review.get_review`)

Retrieves a specific review by review_id or story_id.

**Tags:** `review`, `retrieval`

**Example Requests:**
```json
{
  "action": "get_review",
  "review_id": "review_story_123_20250107_120000"
}
```

Or:
```json
{
  "action": "get_review",
  "story_id": "story_123"
}
```

**Response:**
```json
{
  "status": "success",
  "review": {
    "review_id": "review_story_123_20250107_120000",
    "story_id": "story_123",
    "approval_status": "approved",
    "reviewed_at": "2025-01-07T12:00:00"
  }
}
```

### 3. Get Status (`editorial.review.status`)

Returns current status of all reviews and drafts under review.

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
  "total_reviews": 10,
  "drafts_under_review": 2,
  "recent_reviews": [
    {
      "review_id": "review_story_123_20250107_120000",
      "story_id": "story_123",
      "approval_status": "approved",
      "reviewed_at": "2025-01-07T12:00:00"
    }
  ]
}
```

## Review Criteria

The Editor evaluates articles across multiple dimensions:

### 1. Grammar & Language
- Spelling errors
- Grammatical mistakes
- Punctuation issues
- Sentence structure
- Word choice

### 2. Tone & Style
- Professional and objective
- Appropriate for news publication
- Balanced reporting
- Clear and concise
- Avoids sensationalism

### 3. Consistency
- Narrative flow
- Paragraph transitions
- Logical structure
- Topic coherence
- Consistent terminology

### 4. Length
- Word count vs. target
- Appropriate depth
- No unnecessary padding
- Complete coverage

### 5. SEO & Metadata
- Relevant tags
- Compelling summary
- Optimized headline
- Keyword integration

## Workflow

```
Editor
    │
    ├─► Receives draft from Reporter
    │
    ├─► Analyzes content with Claude Sonnet 4
    │   ├─ Grammar check
    │   ├─ Tone assessment
    │   ├─ Consistency review
    │   ├─ Length verification
    │   └─ SEO metadata generation
    │
    ├─► Generates detailed feedback
    │
    ├─► Determines approval status
    │   ├─ approved: Ready for publication
    │   ├─ approved_with_suggestions: Minor improvements recommended
    │   └─ needs_revision: Requires significant changes
    │
    └─► Returns review to Reporter
```

## Approval Statuses

### Approved
- Article meets all publication standards
- No revisions required
- Ready for Publisher
- Minor suggestions may be included

### Approved with Suggestions
- Article is acceptable for publication
- Optional improvements recommended
- Can proceed to Publisher or revise
- Typically formatting or minor style notes

### Needs Revision
- Significant issues detected
- Requires Reporter revision
- Not ready for publication
- Detailed feedback provided

## Integration with Other Agents

### Reporter Agent
- **URL:** `http://localhost:8081`
- **Interaction:** Reporter submits drafts, receives editorial feedback
- **Flow:** Reporter → Editor → Reporter (if revisions) → Publisher

### Publisher Agent
- **URL:** `http://localhost:8084`
- **Condition:** Only approved articles proceed to Publisher
- **Data:** Editor metadata (tags, summary) included in publication

## AI-Powered Review

The Editor uses Claude Sonnet 4 for comprehensive analysis:

### Review Prompt Structure
```
You are an experienced editor for Elastic News...

Review the article for:
1. Grammar and language quality
2. Professional tone and objectivity
3. Narrative consistency and flow
4. Appropriate length (target: [N] words, actual: [M] words)
5. Publication readiness

Provide:
- Overall assessment
- Specific feedback for each criterion
- Actionable suggestions
- Approval recommendation
```

### Metadata Generation
- **Tags:** Automatically generated from content
- **Summary:** 1-2 sentence article summary
- **Headline:** Alternative headline suggestions
- **Categories:** Content classification

## Configuration

### Environment Variables

```bash
# Required: Anthropic API for AI-powered editing
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
```

### Port Configuration

```bash
uvicorn agents.editor:app --host localhost --port 8082
```

## Running the Agent

### Start via Script
```bash
./start_newsroom.sh
```

### Start Individually
```bash
uvicorn agents.editor:app --host localhost --port 8082
```

### Start with Hot Reload (Development)
```bash
uvicorn agents.editor:app --host localhost --port 8082 --reload
```

## Agent Card

Access the agent card at:
```
http://localhost:8082/.well-known/agent-card.json
```

## Logging

Logs are written to `newsroom.log` with the `[EDITOR]` prefix.

Example log output:
```
2025-01-07 12:00:00 [EDITOR] INFO: 📥 Received query: {"action": "review_draft", ...
2025-01-07 12:00:00 [EDITOR] INFO: 🎯 Action: review_draft
2025-01-07 12:00:05 [EDITOR] INFO: 📝 Reviewing draft for story_123 (950 words)...
2025-01-07 12:00:10 [EDITOR] INFO: ✅ Review completed: approved
```

## Error Handling

### Invalid Action
```json
{
  "status": "error",
  "message": "Unknown action: invalid_action",
  "available_actions": [
    "review_draft",
    "get_review",
    "get_status"
  ]
}
```

### Missing Draft Data
```json
{
  "status": "error",
  "message": "No draft data provided"
}
```

### Review Failure
```json
{
  "status": "error",
  "message": "Failed to complete review: [error details]"
}
```

### Missing Anthropic API Key
If `ANTHROPIC_API_KEY` is not set:
- Warning logged: `ANTHROPIC_API_KEY not set - will use mock reviews`
- Mock review generated as fallback
- System remains functional

## Testing

The Editor is tested as part of the end-to-end workflow:

```bash
python tests/test_newsroom_workflow.py
```

Expected output:
```
✅ EDITOR: Draft reviewed
   Status: approved
   Word Count: 950 / 1000
   Tags: ai, journalism, technology
```

## Best Practices

1. **Complete Drafts:** Submit fully written articles, not outlines
2. **Target Length:** Include target word count for length assessment
3. **Context:** Provide assignment details for better review
4. **Revision Loop:** Implement revision workflow for "needs_revision" status

## Review Turnaround

Typical review times:
- **Short articles (< 500 words):** 5-10 seconds
- **Medium articles (500-1500 words):** 10-20 seconds
- **Long articles (> 1500 words):** 20-30 seconds

Times vary based on:
- Claude API response time
- Article complexity
- Network latency

## Quality Standards

The Editor enforces Elastic News quality standards:

### Must Have
- ✅ Grammatically correct
- ✅ Professional tone
- ✅ Logical structure
- ✅ Appropriate length

### Should Have
- ✅ Engaging headline
- ✅ Clear introduction
- ✅ Supporting evidence
- ✅ Proper citations

### Nice to Have
- ✅ Compelling narrative
- ✅ Unique angle
- ✅ Strong conclusion
- ✅ Optimized SEO

## Future Enhancements

1. **Style Guide Integration:** Custom style rules per publication
2. **Fact Checking:** Verify claims against databases
3. **Plagiarism Detection:** Check for content originality
4. **Readability Scores:** Flesch-Kincaid and similar metrics
5. **Multi-Reviewer:** Consensus from multiple editorial perspectives

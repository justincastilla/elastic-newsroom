# Code Optimization Patterns

This document describes coding patterns and best practices used in the Elastic News codebase.

## Reporter Agent Helper Methods (DRY Principle)

The Reporter agent uses helper methods to reduce code duplication and improve maintainability.

### Response Builders

```python
def _error_response(self, message: str, **kwargs) -> Dict[str, Any]:
    """Build error response dictionary"""
    logger.error(f"❌ {message}")
    return {"status": "error", "message": message, **kwargs}

def _success_response(self, message: str, **kwargs) -> Dict[str, Any]:
    """Build success response dictionary"""
    return {"status": "success", "message": message, **kwargs}
```

### A2A Communication Helpers

```python
async def _create_a2a_client(self, http_client: httpx.AsyncClient, agent_url: str, agent_name: str):
    """Create A2A client for communication with another agent"""
    # Discovers agent card and creates client
    # Eliminates ~15 lines of duplicate code per method

async def _parse_a2a_response(self, client, message) -> Optional[Dict[str, Any]]:
    """Parse response from A2A client"""
    # Standardizes response parsing across all A2A calls
```

### Anthropic API Helper

```python
async def _call_anthropic(self, prompt: str, max_tokens: int = 2000, fallback=None):
    """Call Anthropic API with consistent error handling"""
    # Centralizes all Anthropic API calls
    # Provides fallback support for when API is unavailable
```

### Performance Optimizations

```python
# Archivist URL parsing cached in __init__ (called once vs. 3x per workflow)
def _parse_archivist_url(self):
    """Parse Archivist URL once during initialization for efficiency"""
    self._archivist_endpoint = f"{base_url}/api/agent_builder/converse"
    self._archivist_agent_id = agent_id
```

### JSON Utilities

```python
def _strip_json_codeblocks(self, text: str) -> str:
    """Remove markdown code blocks from JSON response"""
    # Handles Claude's tendency to wrap JSON in markdown
```

## Benefits

These optimizations provide:
- **Reduced code duplication**: ~100-120 lines of duplicate code eliminated
- **Improved performance**: 3x faster Archivist initialization through caching
- **Better maintainability**: Centralized logic is easier to update and test
- **Standardized error handling**: Consistent error responses across the agent

## Implementation Reference

See `agents/reporter.py` lines 82-135 for complete helper method implementations.

## Best Practices

When extending agents:
1. **Extract common patterns**: If you write the same code 3+ times, create a helper method
2. **Cache expensive operations**: Parse URLs and configuration once during initialization
3. **Standardize responses**: Use consistent response builders for success/error cases
4. **Centralize API calls**: Single point of control for external service integration
5. **Handle edge cases**: Account for API quirks (e.g., Claude wrapping JSON in markdown)

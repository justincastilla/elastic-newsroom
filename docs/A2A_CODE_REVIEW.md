# A2A Protocol Standards Compliance Code Review

## Executive Summary

This code review evaluates the elastic-newsroom project against the A2A (Agent-to-Agent) Protocol standards as defined in the official [A2A repository](https://github.com/a2aproject/A2A). The project implements a multi-agent newsroom system using the A2A Python SDK v0.3.8.

**Overall Assessment:** The project demonstrates good A2A SDK integration with several areas for improvement to ensure full compliance with protocol standards.

---

## 1. Agent Card Standards

### Current State
All agents implement Agent Cards with basic metadata:
- ✅ Name, description, URL, version
- ✅ Skills with IDs, names, descriptions, tags, and examples
- ✅ Capabilities (streaming, pushNotifications, stateTransitionHistory)
- ✅ Default input/output modes (application/json)
- ✅ Provider information

### Issues & Recommendations

#### 1.1 Missing Security Declarations ⚠️ CRITICAL
**File:** All agent files (`agents/*.py`)

**Issue:** Agent Cards do not declare authentication/security schemes in the `security` field.

**A2A Standard:** 
> "The A2A server's Agent Card describes the authentication schemes it supports in its `security` field and aligns with those defined in the OpenAPI Specification for authentication."
> — [Enterprise-Ready Features](https://github.com/a2aproject/A2A/blob/main/docs/topics/enterprise-ready.md)

**Impact:** Clients cannot determine what authentication is required to interact with agents. This violates enterprise security best practices.

**Recommendation:**
Add `security` field to all Agent Cards:

```python
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="News Chief",
        description="...",
        url=f"http://{host}:{port}",
        version="1.0.0",
        preferred_transport="JSONRPC",
        security=[
            {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for authentication"
            }
        ],
        # ... rest of card
    )
```

**Priority:** HIGH - Required for enterprise compliance

---

#### 1.2 Missing Protocol Version Declaration ⚠️
**File:** All agent files (`agents/*.py`)

**Issue:** Agent Cards don't explicitly declare `protocolVersion`.

**A2A Standard:** 
> "The version of the A2A protocol this agent supports. Defaults to '0.3.0' if not specified."

**Current Behavior:** Relies on SDK default, which may not match the actual implementation.

**Recommendation:**
Explicitly declare protocol version:

```python
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="News Chief",
        protocol_version="0.3.0",  # Match SDK version
        # ... rest of card
    )
```

**Priority:** MEDIUM

---

#### 1.3 Missing Transport Declarations ℹ️
**File:** All agent files (`agents/*.py`)

**Issue:** Agent Cards specify `preferred_transport="JSONRPC"` but don't declare `additionalInterfaces` for transport negotiation.

**A2A Standard:**
> "A list of additional supported interfaces (transport and URL combinations). This allows agents to expose multiple transports, potentially at different URLs."

**Recommendation:**
Add `additionalInterfaces` to enable proper transport negotiation:

```python
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="News Chief",
        url=f"http://{host}:{port}",
        preferred_transport="JSONRPC",
        additional_interfaces=[
            AgentInterface(
                url=f"http://{host}:{port}",
                transport="JSONRPC"
            )
        ],
        # ... rest of card
    )
```

**Priority:** LOW - Nice to have for clarity

---

#### 1.4 Missing Documentation URLs ℹ️
**File:** Only `reporter.py` has `documentation_url`

**Issue:** Most agents don't provide `documentationUrl` or `iconUrl`.

**Recommendation:**
Add documentation URLs for all agents to improve discoverability:

```python
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        name="News Chief",
        documentation_url="https://github.com/justincastilla/elastic-newsroom/blob/main/docs/news-chief-agent.md",
        icon_url="https://github.com/justincastilla/elastic-newsroom/blob/main/docs/icons/news-chief.svg",
        # ... rest of card
    )
```

**Priority:** LOW - Enhances usability

---

## 2. Enterprise Security Standards

### Current State
- ❌ No authentication implemented on any agent endpoints
- ❌ No HTTPS enforcement in production
- ⚠️ Agent Cards don't declare security requirements
- ✅ CORS middleware configured for UI access

### Issues & Recommendations

#### 2.1 Missing Authentication Implementation ⚠️ CRITICAL
**File:** All agent files (`agents/*.py`)

**Issue:** Agents accept unauthenticated requests.

**A2A Standard:**
> "The A2A server MUST authenticate every incoming request using the credentials provided in the HTTP headers."
> — [Enterprise-Ready Features](https://github.com/a2aproject/A2A/blob/main/docs/topics/enterprise-ready.md)

**Security Risk:** Any client can invoke agent skills without authorization.

**Recommendation:**
Implement authentication middleware:

```python
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser, AuthCredentials
)

class APIKeyAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        api_key = conn.headers.get("X-API-Key")
        if not api_key:
            return None
        
        # Validate API key against environment or database
        expected_key = os.getenv("AGENT_API_KEY")
        if api_key != expected_key:
            raise AuthenticationError("Invalid API key")
        
        return AuthCredentials(["authenticated"]), SimpleUser("agent_client")

def create_app(host='localhost', port=8080):
    # ... existing code ...
    
    app.add_middleware(
        AuthenticationMiddleware,
        backend=APIKeyAuthBackend()
    )
    
    return app
```

**Priority:** CRITICAL - Security vulnerability

---

#### 2.2 No HTTPS Enforcement ⚠️ CRITICAL
**File:** All agent startup scripts and `utils/server_utils.py`

**Issue:** Agents run on HTTP in all environments.

**A2A Standard:**
> "All A2A communication in production environments must occur over HTTPS."
> — [Enterprise-Ready Features](https://github.com/a2aproject/A2A/blob/main/docs/topics/enterprise-ready.md)

**Recommendation:**
1. Add TLS certificate configuration for production
2. Enforce HTTPS in production environments
3. Update Agent Card URLs to use HTTPS in production

```python
def run_agent_server(agent_name, host, port, create_app_func, logger, reload=False, reload_module=None):
    # Check for production environment
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    if is_production:
        # Load TLS certificates
        ssl_keyfile = os.getenv("TLS_KEY_FILE")
        ssl_certfile = os.getenv("TLS_CERT_FILE")
        
        if not ssl_keyfile or not ssl_certfile:
            logger.error("TLS certificates required in production")
            sys.exit(1)
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        # Development mode - HTTP is acceptable
        uvicorn.run(app, host=host, port=port)
```

**Priority:** CRITICAL - Production security requirement

---

#### 2.3 Missing Authorization Logic ⚠️
**File:** All agent files (`agents/*.py`)

**Issue:** No skill-based or role-based authorization.

**A2A Standard:**
> "Authorization SHOULD be applied based on the authenticated identity... Access can be controlled on a per-skill basis."

**Recommendation:**
Implement authorization decorators:

```python
def require_skill_permission(skill_id: str):
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Check if authenticated user has permission for this skill
            # This is simplified - implement based on your auth system
            if not hasattr(self, 'current_user'):
                raise Exception("Authentication required")
            
            if not self._has_skill_permission(self.current_user, skill_id):
                raise Exception(f"Permission denied for skill: {skill_id}")
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator

class NewsChiefAgent(BaseAgent):
    @require_skill_permission("newsroom.coordination.story_assignment")
    async def _assign_story(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # ... existing code ...
```

**Priority:** HIGH - Enterprise requirement

---

## 3. Agent Discovery Standards

### Current State
- ✅ Agent Cards served at `/.well-known/agent-card.json`
- ❌ No authenticated extended card support
- ❌ No registry integration

### Issues & Recommendations

#### 3.1 Missing Authenticated Extended Card Support ⚠️
**File:** All agent files (`agents/*.py`)

**Issue:** Agents don't implement `agent/getAuthenticatedExtendedCard` method for sensitive information.

**A2A Standard:**
> "We recommend the use of authenticated extended agent cards for sensitive information or for serving a more detailed version of the card."
> — [Agent Discovery](https://github.com/a2aproject/A2A/blob/main/docs/topics/agent-discovery.md)

**Recommendation:**
Implement extended card method:

```python
class NewsChiefAgentExecutor(AgentExecutor):
    async def get_authenticated_extended_card(self, context) -> AgentCard:
        """Return extended card with sensitive information for authenticated clients"""
        # Verify authentication
        if not context.is_authenticated():
            raise Exception("Authentication required for extended card")
        
        # Return card with additional sensitive details
        return create_extended_agent_card(
            host="localhost",
            port=8080,
            include_internal_skills=True
        )
```

**Priority:** MEDIUM - Security best practice

---

## 4. Task Lifecycle & State Management

### Current State
- ⚠️ Using A2A SDK's InMemoryTaskStore
- ✅ Basic task state tracking in agent memory
- ❌ No distributed task state management

### Issues & Recommendations

#### 4.1 In-Memory Task Store Limitations ℹ️
**File:** All agent files (`agents/*.py`)

**Issue:** Tasks are lost on agent restart. No persistence.

**A2A Standard:**
Task lifecycle should support long-running operations with proper state persistence.

**Recommendation:**
Implement persistent task store:

```python
from a2a.server.tasks import TaskStore
import redis
import json

class RedisTaskStore(TaskStore):
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def save_task(self, task):
        key = f"task:{task.task_id}"
        self.redis.set(key, json.dumps(task.to_dict()))
    
    async def get_task(self, task_id):
        key = f"task:{task_id}"
        data = self.redis.get(key)
        if data:
            return Task.from_dict(json.loads(data))
        return None

# Use in agent setup
request_handler = DefaultRequestHandler(
    agent_executor=NewsChiefAgentExecutor(),
    task_store=RedisTaskStore(redis_client),
)
```

**Priority:** MEDIUM - Production scalability

---

## 5. Error Handling & Responses

### Current State
- ✅ Consistent error response format in agents
- ⚠️ Some exceptions not following A2A error types
- ✅ Proper status codes in most cases

### Issues & Recommendations

#### 5.1 Non-Standard Error Responses ⚠️
**File:** All agent files (`agents/*.py`)

**Issue:** Custom error responses don't align with A2A error types.

**A2A Standard:**
Errors should use standard JSON-RPC 2.0 error codes and A2A error extensions.

**Current Code:**
```python
return {
    "status": "error",
    "message": "Story not found"
}
```

**Recommendation:**
Use A2A error types:

```python
from a2a.types import TaskNotFoundError, InvalidParamsError

# In agent executor
async def execute(self, context, event_queue):
    try:
        query = context.get_user_input()
        result = await self.agent.invoke(query)
        await event_queue.enqueue_event(
            new_agent_text_message(json.dumps(result))
        )
    except KeyError as e:
        # Use standard A2A error
        raise TaskNotFoundError(
            message=f"Task not found: {e}",
            data={"task_id": context.get_task_id()}
        )
    except ValueError as e:
        raise InvalidParamsError(
            message=f"Invalid parameters: {e}"
        )
```

**Priority:** MEDIUM - Protocol compliance

---

## 6. Message & Part Handling

### Current State
- ✅ Using `create_text_message_object` for messages
- ✅ Proper JSON serialization
- ⚠️ Limited use of Part types (only TextPart)
- ❌ No FilePart or DataPart usage

### Issues & Recommendations

#### 6.1 Limited Part Type Usage ℹ️
**File:** `agents/reporter.py`, `agents/publisher.py`

**Issue:** Agents only use TextPart for all content, even structured data.

**A2A Standard:**
> "DataPart: Carries structured JSON data. This is useful for forms, parameters, or any machine-readable information."

**Current Code:**
```python
message = create_text_message_object(content=json.dumps(request))
```

**Recommendation:**
Use DataPart for structured data:

```python
from a2a.types import Message, DataPart

# For structured data
data_part = DataPart(data={"action": "assign_story", "story": {...}})
message = Message(
    role="user",
    parts=[data_part]
)

# For text content
text_part = TextPart(text="Write an article about AI")
message = Message(
    role="user",
    parts=[text_part]
)
```

**Priority:** LOW - Better type safety

---

## 7. Streaming & Async Operations

### Current State
- ✅ Agent Cards declare `streaming: False`
- ✅ Agent Cards declare `pushNotifications: True`
- ❌ Push notifications not implemented
- ❌ SSE streaming not implemented

### Issues & Recommendations

#### 7.1 Push Notifications Not Implemented ⚠️
**File:** All agent files

**Issue:** Agents declare `pushNotifications: True` but don't support the required methods.

**A2A Standard:**
If `pushNotifications: true`, agents must implement:
- `task/setPushNotificationConfig`
- `task/getPushNotificationConfig`
- `task/listPushNotificationConfigs`
- `task/deletePushNotificationConfig`

**Recommendation:**
Either:
1. Set `pushNotifications: False` in capabilities, OR
2. Implement push notification methods:

```python
class NewsChiefAgentExecutor(AgentExecutor):
    async def set_push_notification_config(self, context, config):
        """Set webhook URL for task updates"""
        task_id = context.get_task_id()
        webhook_url = config.get('webhook_url')
        # Store webhook configuration
        self.agent.push_configs[task_id] = webhook_url
        return {"status": "success"}
    
    async def send_push_notification(self, task_id, update):
        """Send update to registered webhook"""
        webhook_url = self.agent.push_configs.get(task_id)
        if webhook_url:
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json=update)
```

**Priority:** MEDIUM - Feature parity

---

## 8. Observability & Monitoring

### Current State
- ✅ Comprehensive logging with loguru
- ✅ Log files per agent
- ❌ No distributed tracing
- ❌ No metrics exposure
- ❌ No audit logging

### Issues & Recommendations

#### 8.1 No Distributed Tracing ⚠️
**File:** All agent files and `utils/server_utils.py`

**Issue:** No trace context propagation between agents.

**A2A Standard:**
> "A2A Clients and Servers SHOULD participate in distributed tracing systems. For example, use OpenTelemetry to propagate trace context."

**Recommendation:**
Add OpenTelemetry instrumentation:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

# Instrument HTTP clients and servers
HTTPXClientInstrumentor().instrument()
StarletteInstrumentor().instrument_app(app)

# Use in agent methods
tracer = trace.get_tracer(__name__)

async def _assign_story(self, request):
    with tracer.start_as_current_span("assign_story") as span:
        span.set_attribute("story.topic", request["story"]["topic"])
        # ... existing code ...
```

**Priority:** HIGH - Enterprise observability

---

#### 8.2 No Metrics Exposure ℹ️
**File:** All agent files

**Issue:** No Prometheus/metrics endpoint for monitoring.

**Recommendation:**
Add metrics endpoint:

```python
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

# Define metrics
task_counter = Counter('a2a_tasks_total', 'Total tasks processed', ['agent', 'status'])
task_duration = Histogram('a2a_task_duration_seconds', 'Task processing time', ['agent'])

# Add metrics endpoint
async def metrics_endpoint(request):
    return Response(generate_latest(), media_type="text/plain")

app.router.routes.append(
    Route("/metrics", metrics_endpoint, methods=["GET"])
)

# Use in agent methods
with task_duration.labels(agent="news_chief").time():
    result = await self._assign_story(request)
    task_counter.labels(agent="news_chief", status=result["status"]).inc()
```

**Priority:** MEDIUM - Operational visibility

---

## 9. Data Handling & Serialization

### Current State
- ✅ JSON serialization working
- ✅ Helper methods for JSON cleanup (_strip_json_codeblocks)
- ⚠️ No schema validation
- ⚠️ No data type declarations in skills

### Issues & Recommendations

#### 9.1 Missing Input/Output Schema Validation ℹ️
**File:** All agent skills in agent cards

**Issue:** Skills don't declare expected input/output schemas.

**A2A Standard:**
Skills should declare `inputModes` and `outputModes` MIME types.

**Recommendation:**
Add schema information to skills:

```python
AgentSkill(
    id="newsroom.coordination.story_assignment",
    name="Story Assignment",
    description="Assigns stories to reporter agents",
    tags=["coordination", "story-assignment"],
    input_modes=["application/json"],
    output_modes=["application/json"],
    examples=[
        '{"action": "assign_story", "story": {"topic": "AI in Journalism", "priority": "high"}}',
    ],
    # Add JSON schema for validation
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "const": "assign_story"},
            "story": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]}
                },
                "required": ["topic"]
            }
        },
        "required": ["action", "story"]
    }
)
```

**Priority:** LOW - Better validation

---

## 10. Protocol Version & Compatibility

### Current State
- ⚠️ Using SDK v0.3.8 but protocol version may vary
- ⚠️ No version negotiation
- ✅ Proper use of SDK abstractions

### Issues & Recommendations

#### 10.1 Version Declaration Mismatch ℹ️
**File:** `docs/agent-relationships.json`, Agent Cards

**Issue:** Documentation says "A2A 0.3.0" but SDK is v0.3.8.

**Recommendation:**
1. Verify which protocol version SDK implements
2. Update all references to match
3. Add version to Agent Cards explicitly

```python
def create_agent_card(host: str, port: int) -> AgentCard:
    return AgentCard(
        protocol_version="0.3.0",  # Explicitly declare
        # ... rest
    )
```

**Priority:** LOW - Documentation consistency

---

## Summary of Priorities

### CRITICAL (Must Fix)
1. ⚠️ Missing security declarations in Agent Cards
2. ⚠️ No authentication implementation
3. ⚠️ No HTTPS enforcement for production

### HIGH (Should Fix)
4. ⚠️ Missing authorization logic
5. ⚠️ No distributed tracing

### MEDIUM (Recommended)
6. ⚠️ Missing protocol version declaration
7. ⚠️ Authenticated extended card support
8. ⚠️ Persistent task store for production
9. ⚠️ Non-standard error responses
10. ⚠️ Push notifications declared but not implemented
11. ℹ️ No metrics exposure

### LOW (Nice to Have)
12. ℹ️ Missing transport declarations
13. ℹ️ Missing documentation URLs
14. ℹ️ Limited Part type usage
15. ℹ️ Missing input/output schemas
16. ℹ️ Version declaration consistency

---

## Recommendations for Implementation

### Phase 1: Security & Compliance (Week 1-2)
- Add security declarations to all Agent Cards
- Implement API key authentication
- Add HTTPS configuration for production
- Implement basic authorization

### Phase 2: Enterprise Features (Week 3-4)
- Add OpenTelemetry distributed tracing
- Implement metrics endpoints
- Add audit logging
- Set up persistent task store

### Phase 3: Protocol Enhancements (Week 5-6)
- Implement authenticated extended cards
- Either implement push notifications or disable capability
- Add proper error handling with A2A error types
- Implement schema validation

### Phase 4: Polish & Documentation (Week 7-8)
- Add missing documentation URLs
- Update protocol version declarations
- Add DataPart usage where appropriate
- Complete documentation updates

---

## Conclusion

The elastic-newsroom project demonstrates a solid foundation with the A2A SDK but requires critical security enhancements and several protocol compliance improvements to meet enterprise A2A standards. The priority items focus on security, observability, and proper protocol implementation.

**Key Strengths:**
- Good use of A2A SDK patterns
- Well-structured agent architecture
- Comprehensive logging
- Clear skill definitions

**Key Gaps:**
- Missing authentication/authorization
- No HTTPS in production
- Limited observability (no tracing, metrics)
- Some protocol features declared but not implemented

Following the phased approach above will bring the project into full A2A protocol compliance.

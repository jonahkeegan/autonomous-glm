# Epic M5-1: Message Infrastructure

> **Milestone:** 5 - Agent Communication Protocol  
> **Priority:** Critical  
> **Dependencies:** Epic M4-4 (Reports & Persistence)  
> **Status:** 🔲 Not Started

---

## Objective

Build the foundational message transport layer and structured message format that enables communication between autonomous-glm and other agents (Claude, Minimax, Codex) via Unix domain sockets on macOS.

---

## Scope

### In Scope
- Unix domain socket server/client for macOS local communication
- Structured JSON message format with full metadata
- Message type definitions (AUDIT_COMPLETE, DESIGN_PROPOSAL, DISPUTE, HUMAN_REQUIRED)
- Schema validation using existing `/interfaces/*.schema.json`
- Message routing (send to specific agent, broadcast to all)
- Basic send/receive with acknowledgment pattern
- Protocol configuration in config files

### Out of Scope
- Agent discovery/handshake protocol (M5-2)
- Retry/backoff logic for failed messages (M5-3)
- Arbitration routing logic (M5-3)
- Human escalation triggers (M5-3)

---

## Deliverables

### 1. Message Models (`src/protocol/message.py`)

Pydantic models for message data:
- `AgentType` — Enum (autonomous_glm, autonomous_claude, autonomous_minimax, autonomous_codex, human)
- `MessageType` — Enum (AUDIT_COMPLETE, DESIGN_PROPOSAL, DISPUTE, HUMAN_REQUIRED, HELLO, ACK, READY, ERROR)
- `AgentMessage` — {message_id, source_agent, target_agent, message_type, payload, timestamp, requires_response}
- `MessageAck` — {message_id, status, error_message?}
- Payload models for each message type

### 2. Transport Layer (`src/protocol/transport.py`)

Unix domain socket implementation:
- `SocketConfig` — Configuration for socket paths, timeouts, buffer sizes
- `UnixSocketServer` — Async server listening on domain socket
- `UnixSocketClient` — Async client for connecting to agent sockets
- `send_message(agent: AgentType, message: AgentMessage) -> MessageAck`
- `receive_message() -> AgentMessage`
- `broadcast(message: AgentMessage) -> list[MessageAck]`

### 3. Message Router (`src/protocol/router.py`)

Routing logic:
- `MessageRouter` — Routes messages to appropriate agents
- `route(message: AgentMessage) -> MessageAck`
- `register_handler(message_type: MessageType, handler: Callable)`
- Connection pooling for multiple agents

### 4. Schema Validation (`src/protocol/validator.py`)

JSON schema validation:
- `MessageValidator` — Validates messages against schemas
- `validate_message(message: AgentMessage) -> bool`
- `validate_payload(message_type: MessageType, payload: dict) -> bool`
- Uses existing `/interfaces/*.schema.json` files

### 5. Configuration

Add to existing config system:
- `protocol.socket_dir` — Directory for socket files (default: `/var/run/autonomous-glm/`)
- `protocol.socket_timeout` — Socket timeout in seconds
- `protocol.buffer_size` — Buffer size for messages
- `protocol.agents` — Agent endpoint configuration

---

## Technical Decisions

### Unix Domain Sockets
- **Decision:** Use Unix domain sockets (`AF_UNIX`) for local agent communication
- **Rationale:**
  - PRD specifies "domain sockets for low-latency agent communication on macOS"
  - Lower latency than TCP loopback
  - Simpler security model (filesystem permissions)
  - No port conflicts

**Socket Path Convention:**
```
/var/run/autonomous-glm/autonomous-glm.sock
/var/run/autonomous-glm/autonomous-claude.sock
/var/run/autonomous-glm/autonomous-minimax.sock
/var/run/autonomous-glm/autonomous-codex.sock
```

### Message Format
- **Decision:** JSON with UUID, source/target, type, payload, timestamp
- **Rationale:**
  - Human-readable for debugging
  - Schema-validatable
  - Compatible with existing interface schemas

**Message Structure:**
```json
{
  "message_id": "uuid-v4",
  "source_agent": "autonomous_glm",
  "target_agent": "autonomous_claude",
  "message_type": "AUDIT_COMPLETE",
  "payload": {
    "artifact_id": "uuid",
    "findings_count": 12,
    "critical_count": 2,
    "phases": ["Critical", "Refinement", "Polish"]
  },
  "timestamp": "2026-03-04T20:00:00Z",
  "requires_response": true
}
```

### Async I/O
- **Decision:** Use `asyncio` with async socket operations
- **Rationale:**
  - Non-blocking for multiple concurrent connections
  - Native Python 3.10+ support
  - Consistent with async patterns in codebase

---

## File Structure

```
src/
└── protocol/
    ├── __init__.py           # Module exports
    ├── message.py            # Pydantic message models
    ├── transport.py          # Unix socket server/client
    ├── router.py             # Message routing logic
    └── validator.py          # Schema validation
config/
└── default.yaml              # Updated with protocol config
interfaces/
├── audit-complete.schema.json    # Existing
├── design-proposal.schema.json   # Existing
├── dispute.schema.json           # Existing
├── human-required.schema.json    # Existing
└── agent-message.schema.json     # NEW: Generic message schema
tests/
└── unit/
    ├── test_message.py
    ├── test_transport.py
    ├── test_router.py
    └── test_protocol_validator.py
```

---

## Tasks

### Phase 1: Message Models
- [ ] Create `src/protocol/` directory structure
- [ ] Create `src/protocol/__init__.py` with module exports
- [ ] Create `src/protocol/message.py` with Pydantic models
- [ ] Define `AgentType` enum (5 agent types)
- [ ] Define `MessageType` enum (8 message types)
- [ ] Create `AgentMessage` model with all required fields
- [ ] Create `MessageAck` model for acknowledgments
- [ ] Create payload models for each message type
- [ ] Add JSON encoders for datetime/UUID
- [ ] Write unit tests for message models

### Phase 2: Transport Layer
- [ ] Create `src/protocol/transport.py`
- [ ] Implement `SocketConfig` dataclass
- [ ] Implement `UnixSocketServer` class with asyncio
- [ ] Implement `UnixSocketClient` class with asyncio
- [ ] Implement `send_message()` method
- [ ] Implement `receive_message()` method
- [ ] Implement `broadcast()` method
- [ ] Handle socket creation/cleanup
- [ ] Handle connection errors gracefully
- [ ] Write unit tests for transport layer

### Phase 3: Message Router
- [ ] Create `src/protocol/router.py`
- [ ] Implement `MessageRouter` class
- [ ] Implement `route()` method
- [ ] Implement `register_handler()` for message type handlers
- [ ] Implement connection pooling for multiple agents
- [ ] Add agent endpoint resolution
- [ ] Write unit tests for router

### Phase 4: Schema Validation
- [ ] Create `src/protocol/validator.py`
- [ ] Implement `MessageValidator` class
- [ ] Implement `validate_message()` method
- [ ] Implement `validate_payload()` method
- [ ] Create `interfaces/agent-message.schema.json`
- [ ] Load and cache existing schemas
- [ ] Write unit tests for validator

### Phase 5: Configuration & Integration
- [ ] Add `protocol:` section to `config/default.yaml`
- [ ] Add `ProtocolConfig` to `src/config/schema.py`
- [ ] Create socket directory in startup sequence
- [ ] Create integration tests for full message flow
- [ ] Test message exchange with mock agent
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Message models validate correctly with all fields
- [ ] Unix socket server starts and accepts connections
- [ ] Messages transmit successfully to mock agents
- [ ] Schema validation catches malformed messages
- [ ] Router correctly routes to target agents
- [ ] Configuration controls socket behavior
- [ ] Unit test coverage > 90% for `src/protocol/`
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Socket permission denied | Document setup with proper permissions; use sudo for /var/run |
| Agent socket not available | Graceful error handling; connection state tracking |
| Message format drift | Schema validation on send and receive |
| Large message sizes | Implement message size limits; chunking if needed |
| Socket file leftover from crash | Cleanup on startup; stale socket detection |

---

## Validation

Run after completion:
```bash
# Run protocol module tests
python -m pytest tests/unit/test_message.py tests/unit/test_transport.py tests/unit/test_router.py tests/unit/test_protocol_validator.py -v

# Test message creation
python -c "
from src.protocol.message import AgentMessage, AgentType, MessageType
import uuid

msg = AgentMessage(
    message_id=str(uuid.uuid4()),
    source_agent=AgentType.AUTONOMOUS_GLM,
    target_agent=AgentType.AUTONOMOUS_CLAUDE,
    message_type=MessageType.AUDIT_COMPLETE,
    payload={'artifact_id': 'test', 'findings_count': 5},
    requires_response=True
)
print(f'Created message: {msg.message_id}')
"

# Test socket server startup
python -c "
import asyncio
from src.protocol.transport import UnixSocketServer

async def test():
    server = UnixSocketServer('/tmp/test-glm.sock')
    await server.start()
    print('Server started successfully')
    await server.stop()

asyncio.run(test())
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- No new external dependencies (uses asyncio, socket stdlib)

### System Dependencies
- Unix domain socket support (macOS native)
- Write permission to `/var/run/autonomous-glm/`

---

*Created: 2026-03-04*
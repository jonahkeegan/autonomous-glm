# Epic M5-2: Agent Handshake Protocol

> **Milestone:** 5 - Agent Communication Protocol  
> **Priority:** Critical  
> **Dependencies:** Epic M5-1 (Message Infrastructure)  
> **Status:** 🔲 Not Started

---

## Objective

Implement the agent discovery and handshake protocol that establishes connections between autonomous-glm and other agents (Claude, Minimax, Codex) at startup, with connection state management and health monitoring.

---

## Scope

### In Scope
- Config-based agent discovery (endpoints, capabilities)
- Handshake sequence (HELLO → ACK → READY)
- Connection state management (disconnected, connecting, connected, error)
- Agent registry with capability tracking
- Heartbeat/ping for connection health
- Reconnection handling for dropped connections

### Out of Scope
- Transport layer (M5-1)
- Retry/backoff logic for failed messages (M5-3)
- Arbitration routing (M5-3)
- Sync logging (M5-3)

---

## Deliverables

### 1. Handshake Models (`src/protocol/handshake.py`)

Pydantic models for handshake protocol:
- `HandshakeState` — Enum (DISCONNECTED, CONNECTING, HANDSHAKING, CONNECTED, ERROR)
- `HelloMessage` — Initial greeting with agent info and capabilities
- `AckMessage` — Acknowledgment with peer status
- `ReadyMessage` — Final ready confirmation
- `AgentInfo` — {agent_type, version, capabilities, socket_path}
- `HandshakeResult` — {success, agent_info, error_message?}

### 2. Agent Registry (`src/protocol/registry.py`)

Agent discovery and tracking:
- `AgentRegistry` — Central registry of known agents
- `register_agent(agent_info: AgentInfo)` — Add agent to registry
- `get_agent(agent_type: AgentType) -> AgentInfo`
- `get_connected_agents() -> list[AgentInfo]`
- `update_status(agent_type: AgentType, status: HandshakeState)`
- Load agents from configuration

### 3. Connection State Machine (`src/protocol/state.py`)

State management:
- `ConnectionState` — State machine for single agent connection
- `ConnectionManager` — Manages all agent connections
- `get_state(agent_type: AgentType) -> HandshakeState`
- `transition(agent_type: AgentType, new_state: HandshakeState)`
- `is_connected(agent_type: AgentType) -> bool`
- `is_ready() -> bool` — All required agents connected

### 4. Handshake Protocol (`src/protocol/handshake.py`)

Handshake execution:
- `Handshaker` — Executes handshake protocol
- `initiate_handshake(agent_type: AgentType) -> HandshakeResult`
- `receive_hello(message: HelloMessage) -> AckMessage`
- `receive_ack(message: AckMessage) -> ReadyMessage`
- `handle_handshake_timeout(agent_type: AgentType)`
- Configurable handshake timeout

### 5. Health Monitor (`src/protocol/health.py`)

Connection health:
- `HealthMonitor` — Monitors agent connection health
- `start_heartbeat(agent_type: AgentType, interval: float)`
- `stop_heartbeat(agent_type: AgentType)`
- `check_agent_health(agent_type: AgentType) -> bool`
- `handle_heartbeat_failure(agent_type: AgentType)`

---

## Technical Decisions

### Config-Based Discovery
- **Decision:** Agents defined in configuration file, not dynamic discovery
- **Rationale:**
  - Agents are known at deployment time
  - Simpler implementation for MVP
  - No need for service discovery on single-node macOS

**Configuration Format:**
```yaml
protocol:
  agents:
    - type: autonomous_claude
      socket_path: /var/run/autonomous-glm/autonomous-claude.sock
      capabilities: [arbitration, design_approval, human_escalation]
      required: true
    - type: autonomous_minimax
      socket_path: /var/run/autonomous-glm/autonomous-minimax.sock
      capabilities: [frontend_implementation]
      required: false
    - type: autonomous_codex
      socket_path: /var/run/autonomous-glm/autonomous-codex.sock
      capabilities: [backend_implementation]
      required: false
```

### Handshake Sequence
- **Decision:** Three-way handshake (HELLO → ACK → READY)
- **Rationale:**
  - Both parties confirm identity and capabilities
  - Clear state transitions for debugging
  - Extensible for future authentication

**Sequence Diagram:**
```
GLM                           Claude
 |                              |
 |------ HELLO --------------->|
 |  {agent, version, caps}     |
 |                              |
 |<----- ACK ------------------|
 |  {agent, status, caps}      |
 |                              |
 |------ READY --------------->|
 |  {status: operational}      |
 |                              |
 |<----- (connection ready) ---|
```

### Heartbeat Strategy
- **Decision:** Periodic ping with configurable interval (default 30s)
- **Rationale:**
  - Detect stale connections
  - Allow reconnection on failure
  - Minimal overhead

---

## File Structure

```
src/
└── protocol/
    ├── __init__.py           # Updated exports
    ├── handshake.py          # Handshake models + protocol
    ├── registry.py           # Agent registry
    ├── state.py              # Connection state machine
    └── health.py             # Health monitor
config/
└── default.yaml              # Updated with agent configs
interfaces/
└── handshake.schema.json     # NEW: Handshake message schema
tests/
└── unit/
    ├── test_handshake.py
    ├── test_registry.py
    ├── test_state.py
    └── test_health.py
```

---

## Tasks

### Phase 1: Agent Registry
- [ ] Create `src/protocol/registry.py`
- [ ] Implement `AgentInfo` model
- [ ] Implement `AgentRegistry` class
- [ ] Implement `register_agent()` method
- [ ] Implement `get_agent()` method
- [ ] Implement `get_connected_agents()` method
- [ ] Implement `update_status()` method
- [ ] Load agents from configuration
- [ ] Write unit tests for registry

### Phase 2: Connection State Machine
- [ ] Create `src/protocol/state.py`
- [ ] Implement `HandshakeState` enum
- [ ] Implement `ConnectionState` class
- [ ] Implement state transitions
- [ ] Implement `ConnectionManager` class
- [ ] Implement `get_state()` method
- [ ] Implement `is_connected()` method
- [ ] Implement `is_ready()` method
- [ ] Write unit tests for state machine

### Phase 3: Handshake Protocol
- [ ] Create `src/protocol/handshake.py`
- [ ] Implement `HelloMessage` model
- [ ] Implement `AckMessage` model
- [ ] Implement `ReadyMessage` model
- [ ] Implement `HandshakeResult` model
- [ ] Implement `Handshaker` class
- [ ] Implement `initiate_handshake()` method
- [ ] Implement `receive_hello()` handler
- [ ] Implement `receive_ack()` handler
- [ ] Implement timeout handling
- [ ] Write unit tests for handshake

### Phase 4: Health Monitor
- [ ] Create `src/protocol/health.py`
- [ ] Implement `HealthMonitor` class
- [ ] Implement `start_heartbeat()` method
- [ ] Implement `stop_heartbeat()` method
- [ ] Implement `check_agent_health()` method
- [ ] Implement `handle_heartbeat_failure()` method
- [ ] Add heartbeat configuration
- [ ] Write unit tests for health monitor

### Phase 5: Configuration & Integration
- [ ] Add agent definitions to `config/default.yaml`
- [ ] Add `AgentConfig` to `src/config/schema.py`
- [ ] Create `interfaces/handshake.schema.json`
- [ ] Update `src/protocol/__init__.py` with exports
- [ ] Create integration tests for full handshake flow
- [ ] Test handshake with mock agents
- [ ] Test reconnection scenarios
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Agent registry loads from configuration
- [ ] State machine transitions correctly through all states
- [ ] Handshake completes successfully with mock agents
- [ ] Health monitor detects disconnections
- [ ] Reconnection works after agent restart
- [ ] Configuration controls agent endpoints
- [ ] Unit test coverage > 90% for handshake modules
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Agent not running at startup | Graceful degradation; mark as disconnected; retry later |
| Handshake timeout | Configurable timeout; clear error messages |
| State machine gets stuck | Timeout-based state reset; logging for debugging |
| Heartbeat false positives | Configurable interval; tolerance for occasional misses |

---

## Validation

Run after completion:
```bash
# Run handshake module tests
python -m pytest tests/unit/test_handshake.py tests/unit/test_registry.py tests/unit/test_state.py tests/unit/test_health.py -v

# Test agent registry
python -c "
from src.protocol.registry import AgentRegistry
from src.protocol.message import AgentType

registry = AgentRegistry()
registry.load_from_config()
print(f'Known agents: {[a.value for a in registry.get_all_agents()]}')
"

# Test state machine
python -c "
from src.protocol.state import ConnectionManager, HandshakeState
from src.protocol.message import AgentType

manager = ConnectionManager()
manager.transition(AgentType.AUTONOMOUS_CLAUDE, HandshakeState.CONNECTED)
print(f'Claude state: {manager.get_state(AgentType.AUTONOMOUS_CLAUDE)}')
"

# Test handshake
python -c "
import asyncio
from src.protocol.handshake import Handshaker
from src.protocol.message import AgentType

async def test():
    handshaker = Handshaker()
    result = await handshaker.initiate_handshake(AgentType.AUTONOMOUS_CLAUDE)
    print(f'Handshake result: {result.success}')

asyncio.run(test())
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- M5-1 message infrastructure (transport, models)

### System Dependencies
- Agent sockets available (or graceful handling when not)

---

*Created: 2026-03-04*
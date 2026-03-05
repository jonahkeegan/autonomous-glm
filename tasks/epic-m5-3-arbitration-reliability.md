# Epic M5-3: Arbitration & Reliability

> **Milestone:** 5 - Agent Communication Protocol  
> **Priority:** High  
> **Dependencies:** Epic M5-2 (Agent Handshake Protocol)  
> **Status:** 🔲 Not Started

---

## Objective

Implement message reliability features including exponential backoff retry logic, arbitration routing for disputes, human-in-the-loop escalation triggers, and sync logging to ensure robust agent communication.

---

## Scope

### In Scope
- Exponential backoff retry logic (max 1800s per PRD)
- Arbitration routing (disputes → Claude as arbiter)
- Human-in-the-loop escalation triggers
- Sync logging to `/logs/sync-log.ndjson`
- Dead letter queue for permanently failed messages
- Message deduplication (idempotency)

### Out of Scope
- Transport layer (M5-1)
- Handshake protocol (M5-2)
- Message format definitions (M5-1)

---

## Deliverables

### 1. Retry Logic (`src/protocol/retry.py`)

Exponential backoff implementation:
- `RetryConfig` — {max_retries, base_delay, max_delay, jitter}
- `RetryState` — {attempt, next_delay, last_error}
- `RetryManager` — Manages retry state per message
- `calculate_backoff(attempt: int) -> float`
- `should_retry(error: Exception) -> bool`
- `execute_with_retry(func: Callable, message: AgentMessage) -> MessageAck`

### 2. Arbitration Routing (`src/protocol/arbitration.py`)

Dispute handling:
- `Arbitrator` — Routes disputes to Claude
- `create_dispute(finding_id: str, reason: str) -> DisputeMessage`
- `route_to_arbiter(message: AgentMessage) -> MessageAck`
- `track_dispute_status(dispute_id: str) -> DisputeStatus`
- `handle_arbiter_response(response: AgentMessage)`

### 3. Human Escalation (`src/protocol/escalation.py`)

Human-in-the-loop triggers:
- `EscalationTrigger` — Enum (DESIGN_SYSTEM_CHANGE, DISPUTED_FINDING, CRITICAL_SEVERITY, MANUAL_REQUEST)
- `EscalationManager` — Manages human escalations
- `check_escalation_triggers(message: AgentMessage) -> list[EscalationTrigger]`
- `escalate_to_human(message: AgentMessage, trigger: EscalationTrigger) -> MessageAck`
- `track_escalation(escalation_id: str) -> EscalationStatus`

### 4. Sync Logging (`src/protocol/sync.py`)

Message synchronization logging:
- `SyncLogger` — Logs to `/logs/sync-log.ndjson`
- `log_send(message: AgentMessage, status: str)`
- `log_receive(message: AgentMessage, status: str)`
- `log_retry(message: AgentMessage, attempt: int, delay: float)`
- `log_failure(message: AgentMessage, error: str)`
- `get_sync_stats() -> SyncStats`

### 5. Dead Letter Queue (`src/protocol/dead_letter.py`)

Failed message handling:
- `DeadLetterQueue` — Stores permanently failed messages
- `add_to_dlq(message: AgentMessage, error: str, attempts: int)`
- `get_dlq_entries(limit: int) -> list[DeadLetterEntry]`
- `replay_dlq_entry(entry_id: str) -> bool`
- `purge_dlq(before: datetime) -> int`

### 6. Message Deduplication (`src/protocol/dedup.py`)

Idempotency support:
- `DeduplicationCache` — In-memory LRU cache for message IDs
- `is_duplicate(message_id: str) -> bool`
- `mark_processed(message_id: str, ttl: int)`
- `cleanup_expired()` — Remove expired entries

---

## Technical Decisions

### Exponential Backoff Strategy
- **Decision:** Full jitter exponential backoff with configurable parameters
- **Rationale:**
  - Prevents thundering herd on recovery
  - Full jitter (randomize within range) avoids synchronized retries
  - Configurable for different deployment scenarios

**Backoff Formula:**
```
delay = min(max_delay, base_delay * 2^attempt)
jittered_delay = random(0, delay)
```

**Default Configuration:**
| Parameter | Default | Max |
|-----------|---------|-----|
| base_delay | 1s | - |
| max_delay | 60s | 1800s (per PRD) |
| max_retries | 5 | - |
| jitter | True | - |

### Arbitration Pattern
- **Decision:** Claude is the designated arbiter for all disputes
- **Rationale:**
  - PRD specifies "Arbitration signals routed via autonomous-claude"
  - Claude acts as Product Manager role
  - Human escalation available for complex disputes

**Dispute Flow:**
```
GLM → Minimax: Audit finding
Minimax → GLM: Dispute finding
GLM → Claude: Route dispute
Claude → GLM: Arbitration decision
GLM → Minimax: Communicate decision
```

### Escalation Triggers (from AGENTS.md)
Per the agent operating rules, always escalate:
1. **Design System Changes** — Any proposal to add/modify tokens, components, or standards
2. **Disputed Findings** — When agents contest an audit finding
3. **Critical Severity Issues** — Visual/interaction problems rated as critical
4. **Subjective Polish** — Decisions where "taste" is the primary discriminator

### Sync Log Format
- **Decision:** NDJSON (newline-delimited JSON) for structured logging
- **Rationale:**
  - Easy to parse programmatically
  - Supports streaming reads
  - Compatible with log aggregation tools

**Log Entry Format:**
```json
{
  "timestamp": "2026-03-04T20:00:00.000Z",
  "event": "SEND|RECEIVE|RETRY|FAILURE|DLQ",
  "message_id": "uuid-v4",
  "source_agent": "autonomous_glm",
  "target_agent": "autonomous_claude",
  "message_type": "AUDIT_COMPLETE",
  "status": "success|pending|failed",
  "attempt": 1,
  "delay_ms": 1000,
  "error": "optional error message"
}
```

---

## File Structure

```
src/
└── protocol/
    ├── __init__.py           # Updated exports
    ├── retry.py              # Exponential backoff
    ├── arbitration.py        # Dispute routing
    ├── escalation.py         # Human escalation
    ├── sync.py               # Sync logging
    ├── dead_letter.py        # Dead letter queue
    └── dedup.py              # Message deduplication
logs/
└── sync-log.ndjson           # Sync log file
tests/
└── unit/
    ├── test_retry.py
    ├── test_arbitration.py
    ├── test_escalation.py
    ├── test_sync.py
    ├── test_dead_letter.py
    └── test_dedup.py
```

---

## Tasks

### Phase 1: Retry Logic
- [ ] Create `src/protocol/retry.py`
- [ ] Implement `RetryConfig` dataclass
- [ ] Implement `RetryState` model
- [ ] Implement `RetryManager` class
- [ ] Implement `calculate_backoff()` with full jitter
- [ ] Implement `should_retry()` for different error types
- [ ] Implement `execute_with_retry()` async wrapper
- [ ] Add retry configuration to `config/default.yaml`
- [ ] Write unit tests for retry logic

### Phase 2: Sync Logging
- [ ] Create `src/protocol/sync.py`
- [ ] Implement `SyncLogger` class
- [ ] Implement `log_send()` method
- [ ] Implement `log_receive()` method
- [ ] Implement `log_retry()` method
- [ ] Implement `log_failure()` method
- [ ] Implement `get_sync_stats()` method
- [ ] Ensure thread-safe writes
- [ ] Write unit tests for sync logger

### Phase 3: Message Deduplication
- [ ] Create `src/protocol/dedup.py`
- [ ] Implement `DeduplicationCache` class (LRU)
- [ ] Implement `is_duplicate()` method
- [ ] Implement `mark_processed()` method
- [ ] Implement `cleanup_expired()` method
- [ ] Configure TTL for processed messages
- [ ] Write unit tests for deduplication

### Phase 4: Arbitration & Escalation
- [ ] Create `src/protocol/arbitration.py`
- [ ] Implement `Arbitrator` class
- [ ] Implement `create_dispute()` method
- [ ] Implement `route_to_arbiter()` method
- [ ] Implement dispute status tracking
- [ ] Create `src/protocol/escalation.py`
- [ ] Implement `EscalationTrigger` enum
- [ ] Implement `EscalationManager` class
- [ ] Implement `check_escalation_triggers()` method
- [ ] Implement `escalate_to_human()` method
- [ ] Write unit tests for arbitration and escalation

### Phase 5: Dead Letter Queue
- [ ] Create `src/protocol/dead_letter.py`
- [ ] Implement `DeadLetterEntry` model
- [ ] Implement `DeadLetterQueue` class
- [ ] Implement `add_to_dlq()` method
- [ ] Implement `get_dlq_entries()` method
- [ ] Implement `replay_dlq_entry()` method
- [ ] Implement `purge_dlq()` method
- [ ] Configure DLQ size limits
- [ ] Write unit tests for DLQ

### Phase 6: Configuration & Integration
- [ ] Add retry/escalation config to `config/default.yaml`
- [ ] Add config models to `src/config/schema.py`
- [ ] Update `src/protocol/__init__.py` with exports
- [ ] Create integration tests for full reliability flow
- [ ] Test retry scenarios with mock agents
- [ ] Test arbitration flow end-to-end
- [ ] Test escalation triggers
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Retry logic handles transient failures with backoff
- [ ] Max backoff respects 1800s limit from PRD
- [ ] Arbitration routes disputes to Claude correctly
- [ ] Escalation triggers fire for all 4 trigger types
- [ ] Sync log writes valid NDJSON
- [ ] Dead letter queue captures permanently failed messages
- [ ] Deduplication prevents duplicate processing
- [ ] Unit test coverage > 90% for reliability modules
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Retry storms | Full jitter; max retry limits; circuit breaker pattern |
| DLQ grows unbounded | Size limits; automatic purge; monitoring alerts |
| Sync log disk full | Log rotation; size limits; fail-open logging |
| Arbitration deadlock | Timeout on arbiter response; escalation to human |

---

## Validation

Run after completion:
```bash
# Run reliability module tests
python -m pytest tests/unit/test_retry.py tests/unit/test_arbitration.py tests/unit/test_escalation.py tests/unit/test_sync.py tests/unit/test_dead_letter.py tests/unit/test_dedup.py -v

# Test retry backoff
python -c "
from src.protocol.retry import RetryManager, RetryConfig

config = RetryConfig(base_delay=1.0, max_delay=60.0, max_retries=5)
manager = RetryManager(config)
for i in range(5):
    delay = manager.calculate_backoff(i)
    print(f'Attempt {i+1}: delay={delay:.2f}s')
"

# Test sync logging
python -c "
from src.protocol.sync import SyncLogger
from src.protocol.message import AgentMessage, AgentType, MessageType

logger = SyncLogger()
msg = AgentMessage(
    message_id='test-123',
    source_agent=AgentType.AUTONOMOUS_GLM,
    target_agent=AgentType.AUTONOMOUS_CLAUDE,
    message_type=MessageType.AUDIT_COMPLETE,
    payload={},
    requires_response=False
)
logger.log_send(msg, 'success')
print('Sync log entry written')
"

# Test escalation triggers
python -c "
from src.protocol.escalation import EscalationManager, EscalationTrigger

manager = EscalationManager()
triggers = manager.check_escalation_triggers(
    message_type='DESIGN_PROPOSAL',
    severity='CRITICAL'
)
print(f'Escalation triggers: {[t.value for t in triggers]}')
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- M5-1 message infrastructure
- M5-2 handshake protocol

### System Dependencies
- Write permission to `/logs/sync-log.ndjson`
- Sufficient disk space for DLQ and logs

---

*Created: 2026-03-04*
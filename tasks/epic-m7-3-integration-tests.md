# Epic M7-3: Integration Tests

> **Milestone:** 7 - Testing Infrastructure  
> **Priority:** High  
> **Dependencies:** None (can run in parallel with M7-1 and M7-2)  
> **Status:** ✅ Complete

---

## Objective

Create comprehensive integration tests with agent mocks to validate protocol flows, database integration, and cross-module interactions.

---

## Scope

### In Scope
- Agent mock implementations (Claude, Minimax, Codex, Human)
- Protocol flow tests (ingest → audit → report → proposal)
- Database integration tests with real SQLite
- Unix socket transport tests
- Handshake sequence tests with mocks
- Arbitration flow tests
- End-to-end pipeline tests (within single process)
- Test fixtures for integration scenarios

### Out of Scope
- Golden dataset creation (M7-1)
- Coverage/performance testing (M7-2)
- Multi-process E2E tests (M7-4)
- CI pipeline configuration (M7-4)

---

## Deliverables

### 1. Agent Mocks (`tests/integration/mocks/`)

Mock implementations of collaborating agents:

```
mocks/
├── __init__.py
├── base_mock.py           # BaseAgentMock class
├── claude_mock.py         # Claude (PM/Arbiter) mock
├── minimax_mock.py        # Minimax (FE Engineer) mock
├── codex_mock.py          # Codex (BE Engineer) mock
├── human_mock.py          # Human (Design Lead) mock
└── mock_server.py         # Unix socket mock server
```

**Mock Capabilities:**
- Configurable responses (accept, reject, escalate)
- Message logging for verification
- State tracking (connected, handshake complete)
- Simulated delays for timing tests
- Error injection for failure scenarios

### 2. Protocol Flow Tests (`tests/integration/test_protocol_flows.py`)

Tests for complete protocol sequences:

- `test_full_audit_flow()` — Ingest → Audit → Report → Proposal
- `test_feedback_flow()` — Send feedback, receive arbitration
- `test_dispute_flow()` — Dispute finding, route to Claude
- `test_escalation_flow()` — Trigger human escalation
- `test_design_proposal_flow()` — Generate and send design proposal

**Flow Diagram:**
```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Ingest  │───▶│  Audit  │───▶│  Plan   │───▶│ Report  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                  │
                                  ▼
                            ┌─────────┐
                            │ Propose │───▶ Claude/Minimax
                            └─────────┘
```

### 3. Database Integration Tests (`tests/integration/test_database_integration.py`)

Tests for database operations with real SQLite:

- `test_full_audit_persistence()` — Create, read, update audit session
- `test_finding_cascade()` — Cascade delete findings when screen deleted
- `test_plan_phase_persistence()` — Plan phases persist correctly
- `test_component_token_relationships()` — Component-token M:N relationships
- `test_concurrent_access()` — Multiple connections, transaction safety
- `test_migration_idempotency()` — Schema can be re-run safely

**Database Test Patterns:**
- Use `:memory:` SQLite for speed
- Isolated transactions per test
- Fixture for pre-populated database

### 4. Unix Socket Transport Tests (`tests/integration/test_transport.py`)

Tests for Unix domain socket communication:

- `test_socket_server_startup()` — Server starts and listens
- `test_client_connect()` — Client connects to server
- `test_message_roundtrip()` — Send message, receive response
- `test_large_message()` — Messages > 64KB chunked correctly
- `test_concurrent_clients()` — Multiple clients simultaneously
- `test_server_shutdown()` — Graceful shutdown, clients notified
- `test_connection_recovery()` — Reconnect after server restart

### 5. Handshake Integration Tests (`tests/integration/test_handshake.py`)

Tests for agent handshake protocol:

- `test_hello_ack_ready_sequence()` — Full 3-way handshake
- `test_rejected_handshake()` — Agent rejects, proper handling
- `test_handshake_timeout()` — Timeout waiting for ACK
- `test_reconnection_handshake()` — Re-handshake after disconnect
- `test_capability_negotiation()` — Capabilities exchanged correctly
- `test_multi_agent_handshake()` — All 4 agents handshake

**Handshake Sequence:**
```
GLM                Claude
 │                    │
 │──── HELLO ────────▶│
 │                    │
 │◀──── ACK ──────────│
 │                    │
 │──── READY ────────▶│
 │                    │
 │◀──── CONFIRM ──────│
 │                    │
 [CONNECTED]     [CONNECTED]
```

### 6. Arbitration Integration Tests (`tests/integration/test_arbitration.py`)

Tests for arbitration and dispute resolution:

- `test_dispute_to_claude()` — Dispute routes to Claude (arbiter)
- `test_claude_resolution()` — Claude resolves, parties notified
- `test_escalation_to_human()` — Claude escalates to human
- `test_dispute_timeout()` — Dispute times out, auto-escalate
- `test_multiple_disputes()` — Queue handling for multiple disputes
- `test_dead_letter_queue()` — Failed messages go to DLQ

### 7. Audit Pipeline Integration Tests (`tests/integration/test_audit_pipeline.py`)

Tests for complete audit pipeline:

- `test_screenshot_audit_pipeline()` — Screenshot → Detection → Audit → Findings
- `test_video_audit_pipeline()` — Video → Frames → Detection → Audit
- `test_batch_audit_pipeline()` — Multiple screenshots in batch
- `test_audit_with_persistence()` — Audit results persist to DB
- `test_audit_to_plan_pipeline()` — Audit findings → Plan phases
- `test_plan_to_proposal_pipeline()` — Plan → Design system proposals

### 8. Integration Test Fixtures (`tests/integration/conftest.py`)

Shared fixtures for integration tests:

```python
@pytest.fixture
def mock_agents():
    """All 4 agent mocks connected and ready."""
    
@pytest.fixture
def integration_db():
    """Real SQLite database for integration tests."""
    
@pytest.fixture
def socket_pair():
    """Paired Unix socket server and client."""
    
@pytest.fixture
def golden_screenshot():
    """Screenshot from golden dataset with known issues."""
    
@pytest.fixture
def mock_vision_api():
    """Mock GPT-4 Vision API responses."""
```

---

## Technical Decisions

### Mock Strategy: In-Process Mocks
- **Decision:** Use in-process mocks, not separate processes
- **Rationale:**
  - Faster test execution
  - Easier state inspection
  - No port/socket conflicts
  - Sufficient for integration testing

**For E2E (M7-4):** Use separate processes

### Database: In-Memory SQLite
- **Decision:** Use `:memory:` SQLite for integration tests
- **Rationale:**
  - Fast test execution
  - Isolated per-test database
  - Same schema as production
  - No file cleanup needed

### Socket Testing: Temporary Paths
- **Decision:** Use temp directory for Unix sockets
- **Rationale:**
  - No permission issues
  - Automatic cleanup
  - No conflicts with production sockets

### Vision API: Recorded Responses
- **Decision:** Use recorded/hardcoded Vision API responses
- **Rationale:**
  - No API costs during testing
  - Deterministic test results
  - No network dependency
  - Fast execution

---

## File Structure

```
tests/
├── integration/
│   ├── __init__.py
│   ├── conftest.py               # Shared integration fixtures
│   ├── mocks/
│   │   ├── __init__.py
│   │   ├── base_mock.py          # BaseAgentMock class
│   │   ├── claude_mock.py        # Claude mock
│   │   ├── minimax_mock.py       # Minimax mock
│   │   ├── codex_mock.py         # Codex mock
│   │   ├── human_mock.py         # Human mock
│   │   └── mock_server.py        # Unix socket mock server
│   ├── test_protocol_flows.py    # Protocol sequence tests
│   ├── test_database_integration.py
│   ├── test_transport.py         # Unix socket tests
│   ├── test_handshake.py         # Handshake sequence tests
│   ├── test_arbitration.py       # Arbitration flow tests
│   └── test_audit_pipeline.py    # Full pipeline tests
```

---

## Tasks

### Phase 1: Mock Infrastructure
- [ ] Create `tests/integration/` directory structure
- [ ] Create `tests/integration/conftest.py` with shared fixtures
- [ ] Create `mocks/base_mock.py` with `BaseAgentMock` class
- [ ] Create `mocks/claude_mock.py` with Claude mock (arbiter role)
- [ ] Create `mocks/minimax_mock.py` with Minimax mock
- [ ] Create `mocks/codex_mock.py` with Codex mock
- [ ] Create `mocks/human_mock.py` with Human mock
- [ ] Create `mocks/mock_server.py` with Unix socket server
- [ ] Write unit tests for mock infrastructure

### Phase 2: Transport & Handshake Tests
- [ ] Create `test_transport.py` with socket tests
- [ ] Implement `test_socket_server_startup()`
- [ ] Implement `test_client_connect()`
- [ ] Implement `test_message_roundtrip()`
- [ ] Implement `test_concurrent_clients()`
- [ ] Create `test_handshake.py` with handshake tests
- [ ] Implement `test_hello_ack_ready_sequence()`
- [ ] Implement `test_multi_agent_handshake()`

### Phase 3: Database Integration Tests
- [ ] Create `test_database_integration.py`
- [ ] Implement `test_full_audit_persistence()`
- [ ] Implement `test_finding_cascade()`
- [ ] Implement `test_component_token_relationships()`
- [ ] Implement `test_concurrent_access()`
- [ ] Add database fixtures to conftest.py

### Phase 4: Protocol Flow Tests
- [ ] Create `test_protocol_flows.py`
- [ ] Implement `test_full_audit_flow()`
- [ ] Implement `test_feedback_flow()`
- [ ] Implement `test_dispute_flow()`
- [ ] Implement `test_escalation_flow()`
- [ ] Implement `test_design_proposal_flow()`

### Phase 5: Arbitration Tests
- [ ] Create `test_arbitration.py`
- [ ] Implement `test_dispute_to_claude()`
- [ ] Implement `test_claude_resolution()`
- [ ] Implement `test_escalation_to_human()`
- [ ] Implement `test_dead_letter_queue()`

### Phase 6: Audit Pipeline Tests
- [ ] Create `test_audit_pipeline.py`
- [ ] Implement `test_screenshot_audit_pipeline()`
- [ ] Implement `test_video_audit_pipeline()`
- [ ] Implement `test_batch_audit_pipeline()`
- [ ] Implement `test_audit_to_plan_pipeline()`
- [ ] Add mock Vision API fixtures

### Phase 7: Integration & Validation
- [ ] Run all integration tests
- [ ] Verify no flaky tests (run 3x)
- [ ] Add integration test markers to pytest.ini
- [ ] Document integration test coverage
- [ ] Run full test suite (unit + integration)

---

## Success Criteria

- [ ] All 4 agent mocks implemented and tested
- [ ] Protocol flow tests cover 5+ scenarios
- [ ] Database integration tests pass with real SQLite
- [ ] Unix socket transport tests pass
- [ ] Handshake sequence tests pass
- [ ] Arbitration flow tests pass
- [ ] Audit pipeline tests pass
- [ ] All integration tests run in < 60 seconds
- [ ] Zero flaky tests (3 consecutive runs pass)
- [ ] Integration tests isolated from unit tests

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Socket cleanup issues | Use temp directories, cleanup fixtures |
| Test ordering dependencies | Isolated fixtures, no shared state |
| Mock divergence from real agents | Document mock assumptions, update with protocol changes |
| Slow integration tests | Mark separately, run selectively in CI |
| Flaky async tests | Use pytest-asyncio properly, avoid race conditions |

---

## Validation

Run after completion:
```bash
# Run integration tests only
python -m pytest tests/integration/ -v

# Run with coverage
python -m pytest tests/integration/ --cov=src --cov-report=term-missing

# Run specific test file
python -m pytest tests/integration/test_protocol_flows.py -v

# Run integration tests 3x to check for flakiness
for i in 1 2 3; do python -m pytest tests/integration/ -v || exit 1; done

# Run full test suite (unit + integration)
python -m pytest tests/ -v

# Verify integration test markers
python -m pytest tests/integration/ -v -m integration
```

---

## Dependencies

### Python Dependencies
- `pytest>=7.0.0` — Already installed
- `pytest-asyncio>=0.21.0` — Already installed
- No new dependencies required

### Internal Dependencies
- `src.protocol.*` — Protocol modules for testing
- `src.db.*` — Database modules for testing
- `src.audit.*` — Audit modules for testing
- `src.vision.*` — Vision modules for testing

---

*Created: 2026-03-13*
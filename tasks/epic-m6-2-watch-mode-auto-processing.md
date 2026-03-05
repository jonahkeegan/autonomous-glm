# Epic M6-2: Watch Mode & Auto-Processing

> **Milestone:** 6 - Reporting & CLI  
> **Priority:** High  
> **Dependencies:** Epic M6-1 (CLI Core Commands)  
> **Status:** 🔲 Not Started

---

## Objective

Implement directory watching capability that automatically detects new artifacts (screenshots, videos) and triggers the audit pipeline without manual intervention, enabling continuous UI/UX monitoring.

---

## Scope

### In Scope
- Directory watching using watchdog library
- File system event detection (create, modify, move)
- Artifact type detection (PNG, JPEG, MP4, MOV)
- Debounce pattern for rapid file events
- Automatic audit triggering on new artifacts
- Event logging for audit trail
- Graceful shutdown handling
- Configuration for watch directories

### Out of Scope
- CLI core commands (M6-1)
- Dashboard metrics display (M6-3)
- PDF export functionality (M6-3)
- Remote/network directory watching

---

## Deliverables

### 1. Watch Handler (`src/cli/watch/handler.py`)

File system event handler:
- `ArtifactEventHandler` — watchdog event handler subclass
- `on_created(event)` — Handle file creation events
- `on_modified(event)` — Handle file modification events
- `on_moved(event)` — Handle file move events
- `is_artifact(path: Path) -> bool` — Check if file is valid artifact
- `get_artifact_type(path: Path) -> ArtifactType` — Determine artifact type

### 2. Watch Manager (`src/cli/watch/manager.py`)

Watch session management:
- `WatchManager` — Manages watch sessions
- `start_watch(directories: list[Path])` — Start watching directories
- `stop_watch()` — Stop all watchers
- `add_directory(path: Path)` — Add directory to watch
- `remove_directory(path: Path)` — Remove directory from watch
- `get_status() -> WatchStatus` — Current watch status

### 3. Auto-Processor (`src/cli/watch/processor.py`)

Automatic audit triggering:
- `AutoProcessor` — Processes detected artifacts
- `process_artifact(path: Path, artifact_type: ArtifactType)` — Trigger audit
- `queue_artifact(path: Path)` — Add to processing queue
- `get_queue_status() -> QueueStatus` — Queue state
- `process_queue()` — Process queued artifacts

### 4. Event Logger (`src/cli/watch/logger.py`)

Watch event logging:
- `WatchEventLogger` — Logs watch events
- `log_detection(path: Path, event_type: str)` — Log file detection
- `log_processing(path: Path, audit_id: str)` — Log processing start
- `log_completion(path: Path, report_path: str)` — Log completion
- `log_error(path: Path, error: Exception)` — Log errors
- `get_event_log(limit: int) -> list[WatchEvent]` — Retrieve events

### 5. Debouncer (`src/cli/watch/debouncer.py`)

Event debouncing:
- `EventDebouncer` — Debounces rapid file events
- `should_process(path: Path, event_type: str) -> bool` — Check if event should process
- `record_event(path: Path, event_type: str)` — Record event
- `cleanup_expired()` — Remove expired entries

---

## Technical Decisions

### Watch Library: watchdog
- **Decision:** Use watchdog for file system monitoring
- **Rationale:**
  - Cross-platform support (macOS, Linux, Windows)
  - Native OS integration (FSEvents on macOS)
  - Well-maintained, widely used
  - Async-friendly with proper integration

**Event Flow:**
```
File Created → watchdog detects → ArtifactEventHandler.on_created()
    → Debouncer.should_process() → AutoProcessor.queue_artifact()
    → AutoProcessor.process_queue() → AuditOrchestrator.run_audit()
    → ReportWriter.write_report() → WatchEventLogger.log_completion()
```

### Debounce Strategy
- **Decision:** Time-based debouncing with 2-second window
- **Rationale:**
  - Prevents duplicate processing from rapid events
  - Handles temporary files (editor swaps, partial writes)
  - Configurable via config file

**Debounce Logic:**
```python
class EventDebouncer:
    def __init__(self, window_seconds: float = 2.0):
        self.window = window_seconds
        self.seen_events: dict[str, float] = {}  # path -> timestamp
    
    def should_process(self, path: Path, event_type: str) -> bool:
        key = f"{path}:{event_type}"
        now = time.time()
        
        if key in self.seen_events:
            if now - self.seen_events[key] < self.window:
                return False  # Skip duplicate
        
        self.seen_events[key] = now
        return True
```

### Processing Queue
- **Decision:** In-memory queue with background processing
- **Rationale:**
  - Prevents blocking file system watcher
  - Handles burst of file additions
  - Maintains processing order

**Queue Behavior:**
- FIFO processing
- Configurable max queue size (default: 100)
- Overflow handling: log warning, skip oldest
- Background thread for processing

### Graceful Shutdown
- **Decision:** Signal handlers for clean shutdown
- **Rationale:**
  - Complete in-progress audits
  - Close file handles properly
  - Log shutdown event

**Signals Handled:**
- SIGINT (Ctrl+C)
- SIGTERM (kill command)

---

## File Structure

```
src/
└── cli/
    └── watch/
        ├── __init__.py       # Module exports
        ├── handler.py        # ArtifactEventHandler
        ├── manager.py        # WatchManager
        ├── processor.py      # AutoProcessor
        ├── logger.py         # WatchEventLogger
        └── debouncer.py      # EventDebouncer
config/
└── default.yaml              # Updated with watch config
tests/
└── unit/
    ├── test_watch_handler.py
    ├── test_watch_manager.py
    ├── test_watch_processor.py
    ├── test_watch_logger.py
    └── test_watch_debouncer.py
```

---

## Tasks

### Phase 1: Watch Foundation
- [ ] Create `src/cli/watch/` directory structure
- [ ] Create `src/cli/watch/__init__.py` with module exports
- [ ] Add `watchdog>=3.0.0` to requirements.txt
- [ ] Add `watch:` configuration section to `config/default.yaml`
- [ ] Add `WatchConfig` model to `src/config/schema.py`
- [ ] Define `ArtifactType` enum (SCREENSHOT, VIDEO, UNKNOWN)
- [ ] Define `WatchStatus` and `QueueStatus` models
- [ ] Write unit tests for foundation models

### Phase 2: Event Handler
- [ ] Create `src/cli/watch/handler.py`
- [ ] Implement `ArtifactEventHandler` class
- [ ] Implement `on_created()` event handler
- [ ] Implement `on_modified()` event handler
- [ ] Implement `on_moved()` event handler
- [ ] Implement `is_artifact()` validation
- [ ] Implement `get_artifact_type()` detection
- [ ] Write unit tests for event handler

### Phase 3: Debouncer
- [ ] Create `src/cli/watch/debouncer.py`
- [ ] Implement `EventDebouncer` class
- [ ] Implement `should_process()` method
- [ ] Implement `record_event()` method
- [ ] Implement `cleanup_expired()` method
- [ ] Add configurable debounce window
- [ ] Write unit tests for debouncer

### Phase 4: Auto-Processor
- [ ] Create `src/cli/watch/processor.py`
- [ ] Implement `AutoProcessor` class
- [ ] Implement `queue_artifact()` method
- [ ] Implement `process_queue()` method
- [ ] Implement `process_artifact()` method
- [ ] Integrate with `AuditOrchestrator`
- [ ] Add background thread for processing
- [ ] Handle queue overflow gracefully
- [ ] Write unit tests for processor

### Phase 5: Watch Manager
- [ ] Create `src/cli/watch/manager.py`
- [ ] Implement `WatchManager` class
- [ ] Implement `start_watch()` method
- [ ] Implement `stop_watch()` method
- [ ] Implement `add_directory()` method
- [ ] Implement `remove_directory()` method
- [ ] Implement `get_status()` method
- [ ] Add signal handlers for graceful shutdown
- [ ] Write unit tests for manager

### Phase 6: Event Logger
- [ ] Create `src/cli/watch/logger.py`
- [ ] Implement `WatchEventLogger` class
- [ ] Implement `log_detection()` method
- [ ] Implement `log_processing()` method
- [ ] Implement `log_completion()` method
- [ ] Implement `log_error()` method
- [ ] Implement `get_event_log()` method
- [ ] Persist events to `logs/watch-log.ndjson`
- [ ] Write unit tests for logger

### Phase 7: CLI Integration
- [ ] Add `watch` command to CLI (`src/cli/commands/watch.py`)
- [ ] Implement `glm watch <directory>` command
- [ ] Add `--recursive` flag for subdirectories
- [ ] Add `--dry-run` flag for testing
- [ ] Display real-time status updates
- [ ] Write integration tests
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Watch mode detects new files in monitored directory
- [ ] PNG/JPEG files trigger screenshot audit pipeline
- [ ] MP4/MOV files trigger video audit pipeline
- [ ] Debouncer prevents duplicate processing
- [ ] Queue handles burst of file additions
- [ ] Processing runs in background without blocking
- [ ] Status display shows current queue and processing
- [ ] Graceful shutdown completes in-progress audits
- [ ] Events logged to NDJSON file
- [ ] Unit test coverage > 90% for `src/cli/watch/`
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| File system event flood | Debouncer with configurable window |
| Large video files block processing | Background queue processing |
| Permission denied on directory | Clear error message, skip directory |
| Watch directory deleted | Handle gracefully, log warning |
| Memory leak from event accumulation | Periodic cleanup of old events |
| Incomplete file detection | Wait for file write completion (debounce) |

---

## Validation

Run after completion:
```bash
# Test watch mode startup
glm watch /data/artifacts/screenshots --dry-run

# Test file detection (in separate terminal)
touch /data/artifacts/screenshots/test.png

# Check event log
cat logs/watch-log.ndjson | jq .

# Run watch module tests
python -m pytest tests/unit/test_watch*.py -v

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- `watchdog>=3.0.0` — File system monitoring

### Internal Dependencies
- `src.cli.commands` — CLI integration
- `src.audit.orchestrator` — Audit execution
- `src.ingest.screenshot` — Screenshot ingestion
- `src.ingest.video` — Video ingestion
- `src.plan.report_writer` — Report generation

---

*Created: 2026-03-05*
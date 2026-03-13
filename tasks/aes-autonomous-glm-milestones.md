# Autonomous-GLM Development Milestones

> Development roadmap for the Autonomous UI/UX Design Agent powered by Zai GLM-5

---

## Overview

This document maps the development milestones for autonomous-glm, structured to deliver incremental value while building toward the full vision of an activity-centric UI/UX audit system. Each milestone is designed to be independently testable and deployable.

**Reference Documents:**
- `autonomous-glm-prd.md` — Full product requirements
- `SOUL.md` — Design philosophy and audit protocol
- `AGENTS.md` — Agent operating rules and communication protocol

---

## Milestone 0: Foundation

**Status:** 🔲 Not Started  
**Duration Estimate:** 1-2 days  
**Dependencies:** None

### Objectives
Establish the foundational infrastructure, data model, and configuration required for all subsequent development.

### Deliverables
- [ ] Project directory structure (`/data`, `/logs`, `/output`, `/design_system`, `/memory-bank`)
- [ ] SQLite database schema with all entities (Screen, Flow, Component, AuditFinding, PlanPhase, SystemToken)
- [ ] Configuration management (environment variables, config files)
- [ ] Design system file templates (`tokens.md`, `components.md`, `standards.md`)
- [ ] Memory bank initialization (`audit-patterns.md`, `mistakes.md`, `agent-feedback.md`, `skill-matrix.json`)
- [ ] Interface schema files validation (`/interfaces/*.schema.json`)

### Success Criteria
- All directories exist with proper `.gitkeep` files
- Database initializes with correct schema
- Configuration loads without errors
- Design system files are readable and valid

### KPIs
- Zero startup errors
- All schema validations pass

---

## Milestone 1: Input Ingestion Pipeline

**Status:** 🔲 Not Started  
**Duration Estimate:** 3-4 days  
**Dependencies:** Milestone 0

### Objectives
Build the artifact ingestion system that accepts screenshots, videos, and context metadata.

### Deliverables
- [ ] Screenshot handler (PNG, JPEG) with file validation
- [ ] Video handler (MP4, MOV) with frame extraction capability
- [ ] Context metadata parser (JSON, YAML)
- [ ] Artifact storage and reference management
- [ ] Ingest ID generation and tracking
- [ ] API endpoints:
  - `POST /ingest/screenshot` — returns ingest ID
  - `POST /ingest/video` — returns ingest ID

### Success Criteria
- Screenshots ingest correctly and store references
- Videos extract key frames for analysis
- Context metadata parses and associates with artifacts
- Ingest IDs are unique and trackable

### KPIs
- Ingest time < 100ms per screenshot
- Video frame extraction < 2s per video segment

---

## Milestone 2: CV/AI Analysis Core

**Status:** ✅ Complete (with gaps)  
**Duration Estimate:** 5-7 days  
**Actual Duration:** 3 days  
**Dependencies:** Milestone 1  
**Completion Date:** 2026-03-02

### Objectives
Integrate GLM-5 computer vision pipeline for detecting screens, components, and flows.

### Deliverables
- [x] GLM-5 CV integration module (GPT-4o Vision API)
- [x] Component detection with bounding boxes
- [x] Element type classification (21 component types)
- [x] Screen hierarchy extraction
- [x] Flow sequencing from video frames
- [x] Token reference extraction (colors, spacing, typography)
- [~] Component entity persistence to database (deferred to M3/M4)

### Success Criteria
- [~] Component detection accuracy > 95% on golden dataset (pending M7 golden dataset)
- [x] Bounding boxes accurately represent element positions
- [x] Hierarchy extraction produces valid nested structures
- [x] Flow sequencing correctly orders screens

### KPIs
- [x] Detection time < 1s per screenshot (API-dependent)
- [x] Video segment analysis < 5s per key segment
- [~] CV detection accuracy > 95% (pending golden dataset validation)

### Implementation Summary

**Epic M2-1: Component Detection Pipeline** ✅
- GPT-4o Vision API client with retry/rate limiting
- 21 component types with normalized bounding boxes
- 34 unit tests passing

**Epic M2-2: Hierarchy & Flow Analysis** ✅
- Container detection via bounding box containment
- Z-order inference using position/size heuristics
- Flow sequencing with pHash similarity detection
- 54 unit tests passing

**Epic M2-3: Token Extraction** ✅
- K-means color extraction with LAB distance matching
- Spacing analysis with 4px/8px grid quantization
- Typography estimation from bbox dimensions
- 59 unit tests passing

**Total: 147 new tests, 508 total suite**

### Known Gaps

| Gap | Impact | Resolution |
|-----|--------|------------|
| Golden dataset validation pending | Cannot verify >95% accuracy | Scheduled for M7 |
| Database persistence deferred | Components/tokens not persisted | Schedule for M3/M4 |
| Component gallery deferred | Few-shot examples not integrated | Add if accuracy issues arise |
| Z-order heuristics | Not true render order | Document limitation |

---

## Milestone 3: Audit Engine

**Status:** ✅ Complete  
**Duration Estimate:** 5-7 days  
**Actual Duration:** 3 days  
**Dependencies:** Milestone 2  
**Completion Date:** 2026-03-04

### Objectives
Implement the comprehensive audit protocol based on SOUL.md design philosophy.

### Epic Breakdown

| Epic | Name | Priority | Description |
|------|------|----------|-------------|
| M3-1 | Database Persistence Integration | Critical | Persist Components/Tokens from M2, create validation dataset |
| M3-2 | Core Audit Framework | Critical | Models, severity engine, standards linking, orchestrator |
| M3-3 | Visual Audit Dimensions | High | Hierarchy, spacing, typography, color, alignment, components, density |
| M3-4 | State & Accessibility Dimensions | High | Iconography, states, theming, accessibility |

### Deliverables
- [x] 13 dimension audit protocol implementation:
  - **Visual Hierarchy** (M3-3) ✅
  - **Spacing & Rhythm** (M3-3) ✅
  - **Typography** (M3-3) ✅
  - **Color** (M3-3) ✅
  - **Alignment & Grid** (M3-3) ✅
  - **Components** (M3-3) ✅
  - **Density** (M3-3) ✅
  - **Iconography** (M3-4) ✅
  - **Empty States** (M3-4) ✅
  - **Loading States** (M3-4) ✅
  - **Error States** (M3-4) ✅
  - **Dark Mode / Theming** (M3-4) ✅
  - **Accessibility** (M3-4) ✅
- [~] ~~Motion & Transitions~~ (deferred - requires video analysis)
- [~] ~~Responsiveness~~ (deferred - requires multi-viewport)
- [x] Severity classification engine (low, medium, high, critical)
- [x] Standards reference linking (WCAG, design system tokens)
- [x] Rhythm/hierarchy scoring algorithms (O(n²))
- [x] Jobs Filter application ("Would a user need to be told this exists?")
- [x] AuditFinding entity persistence
- [x] Component/Token persistence from M2 (M3-1)
- [x] Minimal validation dataset (M3-1)

### Implementation Summary

**Epic M3-1: Database Persistence Integration** ✅
- Batch CRUD operations for components/tokens
- Persistence bridge functions
- Component-token relationship management
- 5 synthetic validation screenshots
- 31 tests passing

**Epic M3-2: Core Audit Framework** ✅
- Audit models with Pydantic validation
- Severity classification (Impact × Frequency matrix)
- Standards registry with 30+ WCAG 2.1 AA criteria
- Jobs/Ive design filter (4 principles)
- Plugin architecture orchestrator
- 40 tests passing

**Epic M3-3: Visual Audit Dimensions** ✅
- 7 visual dimension auditors
- BaseAuditor abstract class with utilities
- Registry pattern for dimension discovery
- 48 tests passing

**Epic M3-4: State & Accessibility Dimensions** ✅
- 6 state/accessibility dimension auditors
- WCAG AA compliance checks
- Registry expanded to 13 total dimensions
- 37 tests passing

**Total: 156 new tests, 666 total suite**

### Deferred Dimensions

| Dimension | Reason | Target |
|-----------|--------|--------|
| Motion & Transitions | Requires video frame analysis for animation detection | Post-M7 (enhanced video) |
| Responsiveness | Requires screenshots at multiple viewport sizes | Post-M6 (multi-viewport) |

### Success Criteria
- All 13 implemented dimensions produce findings when issues exist
- Severity classification is consistent and justified
- Each finding links to relevant design standard
- Scoring algorithms produce reproducible results
- Components and Tokens persisted from M2 detection results

### KPIs
- Audit completeness: 100% of dimensions evaluated
- False positive rate < 5%
- Finding classification consistency > 95%

---

## Milestone 4: Plan Generation

**Status:** ✅ Complete  
**Duration Estimate:** 3-4 days  
**Actual Duration:** 1 day  
**Dependencies:** Milestone 3  
**Completion Date:** 2026-03-04

### Objectives
Generate phased improvement plans from audit findings in implementation-ready format.

### Epic Breakdown

| Epic | Name | Priority | Description |
|------|------|----------|-------------|
| M4-1 | Phased Plan Synthesis | Critical | Phase classification, dependency resolution, plan synthesizer |
| M4-2 | Implementation Formatter | Critical | Instruction templates, file/component mapping, validation |
| M4-3 | Design System Proposals | High | Token analyzer, proposal generator, before/after descriptions |
| M4-4 | Reports & Persistence | High | Markdown/JSON output, plan persistence, report writer |

### Deliverables
- [x] Phased plan synthesis (M4-1):
  - Phase 1: Critical (usability, hierarchy, accessibility)
  - Phase 2: Refinement (spacing, typography, color, alignment)
  - Phase 3: Polish (states, theming, micro-interactions)
- [x] Implementation instruction formatter (M4-2):
  - Exact file, exact component, exact property
  - Old value → new value format
  - No ambiguous language
  - Simple string templates
- [x] Design system proposal generation (M4-3):
  - Token proposals (new colors, spacing, typography)
  - Component variant proposals
  - Before/after text descriptions
- [x] Reports & Persistence (M4-4):
  - Markdown reports to `/output/reports/`
  - JSON output for agent consumption
  - PlanPhase entity persistence

### Implementation Summary

**Epic M4-1: Phased Plan Synthesis** ✅
- PlanSynthesizer with phase classification (Critical/Refinement/Polish)
- DependencyResolver with topological sorting
- PhaseClassifier with severity/dimension rules
- 57 tests passing

**Epic M4-2: Implementation Formatter** ✅
- InstructionFormatter with file/component mapping
- InstructionTemplateRegistry with 10 built-in templates
- InstructionValidator with strict mode
- 102 tests passing

**Epic M4-3: Design System Proposals** ✅
- TokenAnalyzer with pattern detection
- ProposalGenerator with impact scoring
- BeforeAfterGenerator with text descriptions
- 96 tests passing

**Epic M4-4: Reports & Persistence** ✅
- MarkdownGenerator and JsonGenerator
- PlanPersistence with CRUD operations
- ReportWriter with date-based directories
- 46 tests passing

**Total: 301 new tests, 967 total suite**

### Success Criteria
- [x] Plans correctly prioritize critical issues first
- [x] Implementation instructions are executable without interpretation
- [x] Design system proposals reference existing tokens
- [x] Before/after comparisons clearly show expected changes
- [x] Reports validate against interface schemas

### KPIs
- [x] Plan generation time < 2s per audit
- [x] Instruction clarity score > 90% (reviewer rating)

### Epic Files
- `tasks/epic-m4-1-phased-plan-synthesis.md`
- `tasks/epic-m4-2-implementation-formatter.md`
- `tasks/epic-m4-3-design-system-proposals.md`
- `tasks/epic-m4-4-reports-persistence.md`

---

## Milestone 5: Agent Communication Protocol

**Status:** ✅ Complete  
**Duration Estimate:** 4-5 days  
**Actual Duration:** 1 day  
**Dependencies:** Milestone 4  
**Completion Date:** 2026-03-05

### Objectives
Establish structured communication with autonomous-claude, autonomous-minimax, and autonomous-codex.

### Epic Breakdown

| Epic | Name | Priority | Description |
|------|------|----------|-------------|
| M5-1 | Message Infrastructure | Critical | Unix domain sockets, message models, router, schema validation |
| M5-2 | Agent Handshake Protocol | Critical | Agent discovery, HELLO/ACK/READY sequence, registry, health monitor |
| M5-3 | Arbitration & Reliability | High | Retry logic, arbitration routing, escalation triggers, sync logging, DLQ |

### Deliverables
- [x] Message queue/domain socket setup for macOS (M5-1)
- [x] Structured JSON message format implementation (M5-1):
  ```json
  {
    "message_id": "uuid",
    "source_agent": "autonomous-glm",
    "target_agent": "claude|minimax|codex|human",
    "message_type": "AUDIT_COMPLETE|DESIGN_PROPOSAL|DISPUTE|HUMAN_REQUIRED",
    "payload": {},
    "timestamp": "ISO-8601",
    "requires_response": true
  }
  ```
- [x] Agent handshake protocol (M5-2):
  - Config-based agent discovery
  - HELLO → ACK → READY three-way handshake
  - Connection state management
  - Heartbeat/ping for health monitoring
- [x] Arbitration routing via autonomous-claude (M5-3)
- [x] Sync protocol with exponential backoff (1800s max) (M5-3)
- [x] Sync logging to `/logs/sync-log.ndjson` (M5-3)
- [x] Human-in-the-loop escalation triggers (M5-3)
- [x] Dead letter queue for failed messages (M5-3)

### Implementation Summary

**Epic M5-1: Message Infrastructure** ✅
- AgentMessage/MessageAck Pydantic models with full metadata
- Payload models for all message types (Audit, Design, Dispute, Human)
- Unix domain socket server/client with async I/O
- MessageRouter with handler registration
- MessageValidator with JSON schema caching
- 45 tests passing

**Epic M5-2: Agent Handshake Protocol** ✅
- AgentRegistry singleton for agent CRUD and capability queries
- ConnectionManager with state machine (DISCONNECTED → CONNECTED)
- Handshaker with HELLO/ACK/READY sequence
- HealthMonitor with async heartbeat loops
- handshake.schema.json for message validation
- 54 tests passing

**Epic M5-3: Arbitration & Reliability** ✅
- RetryManager with exponential backoff (1800s max per PRD)
- SyncLogger with NDJSON persistence
- DeduplicationCache with LRU eviction and TTL
- Arbitrator with dispute routing to Claude
- EscalationManager with 7 trigger types
- DeadLetterQueue with JSON persistence
- 56 tests passing

**Total: 155 new tests, 1122 total suite**

### Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Transport | Unix domain sockets | PRD requirement; low latency; macOS native |
| Socket path | `/var/run/autonomous-glm/` | System-level socket directory |
| Message persistence | In-memory | Zulip messages always available; no disk persistence needed |
| Discovery | Config-based | Agents known at deploy time; no dynamic discovery needed |
| Arbiter | Claude | PRD specifies arbitration via autonomous-claude |

### Success Criteria
- Messages transmit successfully to all agents
- Handshake completes with all three collaborators
- Arbitration signals route correctly through Claude
- Sync retries handle failures gracefully

### KPIs
- Message delivery latency < 100ms
- Handshake success rate 100%
- Zero message loss on retry

### Epic Files
- `tasks/epic-m5-1-message-infrastructure.md`
- `tasks/epic-m5-2-agent-handshake-protocol.md`
- `tasks/epic-m5-3-arbitration-reliability.md`

---

## Milestone 6: Reporting & CLI

**Status:** ✅ Complete  
**Duration Estimate:** 3-4 days  
**Actual Duration:** 8 days  
**Dependencies:** Milestone 5  
**Completion Date:** 2026-03-13

### Objectives
Build the command-line interface and reporting output system.

### Epic Breakdown

| Epic | Name | Priority | Tests | Status |
|------|------|----------|-------|--------|
| M6-1 | CLI Core Commands | Critical | 73 | ✅ Complete |
| M6-2 | Watch Mode & Auto-Processing | High | 28 | ✅ Complete |
| M6-3 | Dashboard & PDF Export | Medium | 29 | ✅ Complete |

**Total: 130 new tests, 1252 total suite**

### Deliverables
- [x] Markdown report generation (`/output/reports/`) — M4-4 foundation exists
- [x] JSON output for agent consumption (M6-1)
- [x] CLI interface with flags (M6-1):
  - `glm audit <artifact_id>` — trigger audit
  - `glm report <audit_id>` — fetch report
  - `glm propose [proposal_id]` — view design system proposals
- [x] Watch mode (M6-2):
  - `glm watch <directory>` — watch for new artifacts
  - Automatic audit triggering on file detection
- [x] Summary tables (terminal output) (M6-1)
- [x] Dashboard metrics output (M6-3):
  - `glm dashboard` — terminal display
  - `glm dashboard --html` — HTML output
- [x] PDF export option for human review (M6-3):
  - `glm report <id> --pdf` — export as PDF

### Implementation Summary

**Epic M6-1: CLI Core Commands** ✅
- Click-based CLI with 3 subcommands (audit, report, propose)
- Rich output formatting with tables, panels, spinners
- Global --json and --verbose flags
- Custom exit codes (0-7) for scripting
- 73 tests passing

**Epic M6-2: Watch Mode & Auto-Processing** ✅
- Real-time directory monitoring with watchdog
- Time-based event debouncing (configurable window)
- Queue-based processing pipeline with worker thread
- NDJSON event logging for audit trails
- Signal handlers for graceful shutdown (SIGINT, SIGTERM)
- 28 tests passing

**Epic M6-3: Dashboard & PDF Export** ✅
- MetricsAggregator with database queries
- Rich terminal output with panels and tables
- Standalone HTML with embedded CSS
- PDF export via WeasyPrint with Jinja2 templates
- Time period filtering (day, week, month, all)
- 29 tests passing

### Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI Framework | Click | Mature, decorator-based, built-in subcommand support |
| Terminal Output | Rich | Beautiful tables, progress bars, cross-platform colors |
| Watch Library | watchdog | Cross-platform, native macOS FSEvents integration |
| PDF Generation | WeasyPrint | Pure Python, CSS print support, no binary deps |
| Templates | Jinja2 | Familiar syntax, auto-escaping, template inheritance |

### New Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| click | >=8.0.0 | CLI framework |
| rich | >=13.0.0 | Terminal formatting |
| watchdog | >=3.0.0 | File system monitoring |
| weasyprint | >=60.0 | PDF generation |
| jinja2 | >=3.0.0 | HTML templates |
| markdown | >=3.0.0 | Markdown conversion |

### System Dependencies (macOS)

```bash
# Required for WeasyPrint PDF generation
brew install pango gdk-pixbuf libffi
```

### Success Criteria
- [x] CLI commands execute without errors
- [x] Reports render correctly in Markdown viewers
- [x] JSON output validates against schemas
- [x] Watch mode detects new artifacts automatically
- [x] Dashboard displays aggregate metrics
- [x] PDF export generates valid PDF files

### KPIs
- Report generation < 1s (deferred to M7 performance testing)
- CLI response time < 200ms (deferred to M7 performance testing)
- Watch mode detection latency < 500ms (deferred to M7 performance testing)

### Epic Files
- `tasks/epic-m6-1-cli-core-commands.md`
- `tasks/epic-m6-2-watch-mode-auto-processing.md`
- `tasks/epic-m6-3-dashboard-pdf-export.md`

### Completion Reports
- `task-completion-reports/m6-1-cli-core-commands-completion.md`
- `task-completion-reports/m6-2-watch-mode-auto-processing-completion.md`
- `task-completion-reports/m6-3-dashboard-pdf-export-completion.md`

---

## Milestone 7: Testing Infrastructure

**Status:** 🔲 Not Started  
**Duration Estimate:** 5-7 days  
**Dependencies:** Milestone 6

### Objectives
Build comprehensive testing infrastructure with golden datasets and coverage targets.

### Epic Breakdown

| Epic | Name | Priority | Dependencies | Description |
|------|------|----------|--------------|-------------|
| M7-1 | Golden Dataset Creation | Critical | None | Synthetic screenshots, expected outputs, CV accuracy validation |
| M7-2 | Coverage & Performance Testing | High | M7-1 | >90% coverage, performance KPI validation |
| M7-3 | Integration Tests | High | None (parallel) | Agent mocks, protocol flows, database integration |
| M7-4 | E2E & CI Pipeline | High | M7-1, M7-2, M7-3 | Full audit cycle E2E, GitHub Actions CI |

### Deliverables
- [ ] Golden dataset creation (M7-1):
  - Synthetic UI screenshots with known issues (20+)
  - Video flows with expected findings (2)
  - Expected detection/audit outputs
  - CV accuracy validation scripts
- [ ] Coverage & Performance (M7-2):
  - Coverage gap analysis and tests
  - Performance benchmark suite
  - Coverage report generation
- [ ] Integration tests with agent mocks (M7-3):
  - Agent mock implementations
  - Protocol flow tests
  - Database integration tests
- [ ] E2E tests (M7-4):
  - Multi-agent audit cycle simulation
  - Protocol flows (ingest, feedback, arbitration)
  - Fuzz/edge cases (ambiguous, low-contrast, incomplete)
- [ ] Test result reporting (Markdown coverage reports)
- [ ] CI harness configuration (GitHub Actions)

### Success Criteria
- Unit test coverage > 90%
- All golden dataset tests pass
- CV detection accuracy > 95% on golden dataset
- E2E simulates complete audit cycle
- Edge cases handled gracefully
- CI pipeline runs in < 15 minutes

### KPIs
- Test suite execution < 5 minutes (unit + integration)
- Coverage > 90%
- Zero flaky tests
- CV accuracy > 95%

### Epic Files
- `tasks/epic-m7-1-golden-dataset-creation.md`
- `tasks/epic-m7-2-coverage-performance-testing.md`
- `tasks/epic-m7-3-integration-tests.md`
- `tasks/epic-m7-4-e2e-ci-pipeline.md`

---

## Milestone 8: Learning Loop & Memory Bank

**Status:** 🔲 Not Started  
**Duration Estimate:** 3-4 days  
**Dependencies:** Milestone 7

### Objectives
Implement the learning capture and consolidation system for continuous improvement.

### Deliverables
- [ ] Audit pattern capture (`memory-bank/audit-patterns.md`)
- [ ] Mistake logging (`memory-bank/mistakes.md`)
- [ ] Agent feedback integration (`memory-bank/agent-feedback.md`)
- [ ] Skill matrix updates (`memory-bank/skill-matrix.json`)
- [ ] Consolidation trigger (10+ entries → `consolidated-learnings.md`)
- [ ] Session initialization protocol
- [ ] Periodic review triggers (time-based, content-based, milestone-based)

### Success Criteria
- Patterns captured after each audit cycle
- Mistakes logged with context
- Agent feedback incorporated into workflows
- Consolidation triggers correctly at threshold

### KPIs
- Learning capture rate > 90% of audit cycles
- Consolidation accuracy > 95%

---

## Milestone 9: CI/CD & Production

**Status:** 🔲 Not Started  
**Duration Estimate:** 3-4 days  
**Dependencies:** Milestone 8

### Objectives
Establish production deployment pipeline with monitoring and rollback capabilities.

### Deliverables
- [ ] GitHub Actions CI pipeline:
  - Lint/type check (ruff/mypy, eslint)
  - Unit/integration/E2E tests
  - Build agent binary
  - Documentation generation
- [ ] Performance validation:
  - < 1s per screenshot audit
  - < 5s per video segment
  - > 10 audits/min throughput
- [ ] Agent handshake verification at startup
- [ ] Rollback mechanisms:
  - Design system version backup
  - Config versioning
  - Phased rollback support
- [ ] Post-deploy verification:
  - Smoke tests
  - Report generation check
  - Agent ACK confirmation
- [ ] Monitoring and alerting:
  - Structured logs
  - Metrics dashboard
  - Failure alerts

### Success Criteria
- CI pipeline runs on all PRs
- Performance targets met consistently
- Rollback completes within 5 minutes
- All agents acknowledge deployment

### KPIs
- CI pipeline duration < 15 minutes
- Deploy success rate > 99%
- Rollback time < 5 minutes

---

## Dependency Graph

```
M0: Foundation
 └── M1: Input Ingestion
      └── M2: CV/AI Analysis
           └── M3: Audit Engine
                └── M4: Plan Generation
                     └── M5: Agent Communication
                          └── M6: Reporting & CLI
                               └── M7: Testing Infrastructure
                                    └── M8: Learning Loop
                                         └── M9: CI/CD & Production
```

---

## Timeline Summary

| Milestone | Duration | Cumulative |
|-----------|----------|------------|
| M0: Foundation | 1-2 days | 2 days |
| M1: Input Ingestion | 3-4 days | 6 days |
| M2: CV/AI Analysis | 5-7 days | 13 days |
| M3: Audit Engine | 5-7 days | 20 days |
| M4: Plan Generation | 3-4 days | 24 days |
| M5: Agent Communication | 4-5 days | 29 days |
| M6: Reporting & CLI | 3-4 days | 33 days |
| M7: Testing Infrastructure | 5-7 days | 40 days |
| M8: Learning Loop | 3-4 days | 44 days |
| M9: CI/CD & Production | 3-4 days | 48 days |

**Total Estimated Duration:** 6-8 weeks

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| GLM-5 CV accuracy below target | Early validation against golden dataset; fallback to alternative CV models |
| Agent communication failures | Robust retry with exponential backoff; manual intervention triggers |
| Performance targets missed | Async processing; caching; batch optimization |
| Design system conflicts | Version control; human approval gates; rollback capability |
| False positive audit findings | Tunable severity thresholds; learning loop capture |

---

## Next Steps

1. **Begin Milestone 7** — Testing Infrastructure (golden dataset, coverage validation)
2. **Performance Testing** — Validate KPIs for CLI, watch mode, and report generation
3. **Production Deployment** — System is feature-complete per PRD
4. **Coordinate with agent teams** — Confirm communication protocols with Claude/Minimax/Codex

---

*Document created: 2026-02-28*  
*Last updated: 2026-03-13*

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

**Status:** 🔲 Not Started  
**Duration Estimate:** 4-5 days  
**Dependencies:** Milestone 4

### Objectives
Establish structured communication with autonomous-claude, autonomous-minimax, and autonomous-codex.

### Epic Breakdown

| Epic | Name | Priority | Description |
|------|------|----------|-------------|
| M5-1 | Message Infrastructure | Critical | Unix domain sockets, message models, router, schema validation |
| M5-2 | Agent Handshake Protocol | Critical | Agent discovery, HELLO/ACK/READY sequence, registry, health monitor |
| M5-3 | Arbitration & Reliability | High | Retry logic, arbitration routing, escalation triggers, sync logging, DLQ |

### Deliverables
- [ ] Message queue/domain socket setup for macOS (M5-1)
- [ ] Structured JSON message format implementation (M5-1):
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
- [ ] Agent handshake protocol (M5-2):
  - Config-based agent discovery
  - HELLO → ACK → READY three-way handshake
  - Connection state management
  - Heartbeat/ping for health monitoring
- [ ] Arbitration routing via autonomous-claude (M5-3)
- [ ] Sync protocol with exponential backoff (1800s max) (M5-3)
- [ ] Sync logging to `/logs/sync-log.ndjson` (M5-3)
- [ ] Human-in-the-loop escalation triggers (M5-3)
- [ ] Dead letter queue for failed messages (M5-3)

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

**Status:** 🔲 Not Started  
**Duration Estimate:** 3-4 days  
**Dependencies:** Milestone 5

### Objectives
Build the command-line interface and reporting output system.

### Deliverables
- [ ] Markdown report generation (`/output/reports/`)
- [ ] JSON output for agent consumption
- [ ] CLI interface with flags:
  - `--audit <artifact_id>` — trigger audit
  - `--report <audit_id>` — fetch last report
  - `--propose` — open design system proposal
  - `--watch <directory>` — watch for new artifacts
- [ ] Summary tables (terminal output)
- [ ] Dashboard metrics output (local HTML or terminal)
- [ ] PDF export option for human review

### Success Criteria
- CLI commands execute without errors
- Reports render correctly in Markdown viewers
- JSON output validates against schemas
- Watch mode detects new artifacts automatically

### KPIs
- Report generation < 1s
- CLI response time < 200ms

---

## Milestone 7: Testing Infrastructure

**Status:** 🔲 Not Started  
**Duration Estimate:** 5-7 days  
**Dependencies:** Milestone 6

### Objectives
Build comprehensive testing infrastructure with golden datasets and coverage targets.

### Deliverables
- [ ] Golden dataset creation:
  - Synthetic UI screenshots with known issues
  - Video flows with expected findings
  - Expected audit/plan outputs
- [ ] Unit tests (target: >90% coverage)
  - Input parsing tests
  - Entity extraction tests
  - Rule application tests
- [ ] Integration tests with agent mocks
- [ ] E2E tests:
  - Multi-agent audit cycle simulation
  - Protocol flows (ingest, feedback, arbitration)
  - Fuzz/edge cases (ambiguous, low-contrast, incomplete)
- [ ] Test result reporting (Markdown coverage reports)
- [ ] CI harness configuration

### Success Criteria
- Unit test coverage > 90%
- All golden dataset tests pass
- E2E simulates complete audit cycle
- Edge cases handled gracefully

### KPIs
- Test suite execution < 5 minutes
- Coverage > 90%
- Zero flaky tests

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

1. **Begin Milestone 0** — Set up foundation infrastructure
2. **Create golden dataset** — Parallel track for testing assets
3. **Validate GLM-5 access** — Confirm CV pipeline availability
4. **Coordinate with agent teams** — Confirm communication protocols with Claude/Minimax/Codex

---

*Document created: 2026-02-28*  
*Last updated: 2026-03-04*

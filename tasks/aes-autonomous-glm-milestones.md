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

**Status:** 🔲 Not Started  
**Duration Estimate:** 5-7 days  
**Dependencies:** Milestone 1

### Objectives
Integrate GLM-5 computer vision pipeline for detecting screens, components, and flows.

### Deliverables
- [ ] GLM-5 CV integration module
- [ ] Component detection with bounding boxes
- [ ] Element type classification (button, input, modal, etc.)
- [ ] Screen hierarchy extraction
- [ ] Flow sequencing from video frames
- [ ] Token reference extraction (colors, spacing, typography)
- [ ] Component entity persistence to database

### Success Criteria
- Component detection accuracy > 95% on golden dataset
- Bounding boxes accurately represent element positions
- Hierarchy extraction produces valid nested structures
- Flow sequencing correctly orders screens

### KPIs
- Detection time < 1s per screenshot
- Video segment analysis < 5s per key segment
- CV detection accuracy > 95%

---

## Milestone 3: Audit Engine

**Status:** 🔲 Not Started  
**Duration Estimate:** 5-7 days  
**Dependencies:** Milestone 2

### Objectives
Implement the comprehensive audit protocol based on SOUL.md design philosophy.

### Deliverables
- [ ] 15+ dimension audit protocol implementation:
  - Visual Hierarchy
  - Spacing & Rhythm
  - Typography
  - Color
  - Alignment & Grid
  - Components
  - Iconography
  - Motion & Transitions
  - Empty States
  - Loading States
  - Error States
  - Dark Mode / Theming
  - Density
  - Responsiveness
  - Accessibility
- [ ] Severity classification engine (low, medium, high, critical)
- [ ] Standards reference linking (WCAG, design system tokens)
- [ ] Rhythm/hierarchy scoring algorithms (O(n²))
- [ ] Jobs Filter application ("Would a user need to be told this exists?")
- [ ] AuditFinding entity persistence

### Success Criteria
- All 15 dimensions produce findings when issues exist
- Severity classification is consistent and justified
- Each finding links to relevant design standard
- Scoring algorithms produce reproducible results

### KPIs
- Audit completeness: 100% of dimensions evaluated
- False positive rate < 5%
- Finding classification consistency > 95%

---

## Milestone 4: Plan Generation

**Status:** 🔲 Not Started  
**Duration Estimate:** 3-4 days  
**Dependencies:** Milestone 3

### Objectives
Generate phased improvement plans from audit findings in implementation-ready format.

### Deliverables
- [ ] Phased plan synthesis:
  - Phase 1: Critical (usability, hierarchy, responsiveness)
  - Phase 2: Refinement (spacing, typography, color, alignment)
  - Phase 3: Polish (micro-interactions, transitions, empty/loading/error states)
- [ ] Design system proposal generation
- [ ] Implementation instruction formatter:
  - Exact file, exact component, exact property
  - Old value → new value format
  - No ambiguous language
- [ ] Before/after comparison generation
- [ ] PlanPhase entity persistence

### Success Criteria
- Plans correctly prioritize critical issues first
- Implementation instructions are executable without interpretation
- Design system proposals reference existing tokens
- Before/after comparisons clearly show expected changes

### KPIs
- Plan generation time < 2s per audit
- Instruction clarity score > 90% (reviewer rating)

---

## Milestone 5: Agent Communication Protocol

**Status:** 🔲 Not Started  
**Duration Estimate:** 4-5 days  
**Dependencies:** Milestone 4

### Objectives
Establish structured communication with autonomous-claude, autonomous-minimax, and autonomous-codex.

### Deliverables
- [ ] Message queue/domain socket setup for macOS
- [ ] Structured JSON message format implementation:
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
- [ ] Agent handshake protocol (Claude, Minimax, Codex)
- [ ] Arbitration routing via autonomous-claude
- [ ] Sync protocol with exponential backoff (1800s max)
- [ ] Sync logging to `/logs/sync-log.ndjson`

### Success Criteria
- Messages transmit successfully to all agents
- Handshake completes with all three collaborators
- Arbitration signals route correctly through Claude
- Sync retries handle failures gracefully

### KPIs
- Message delivery latency < 100ms
- Handshake success rate 100%
- Zero message loss on retry

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
*Last updated: 2026-02-28*
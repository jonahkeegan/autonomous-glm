# Technical Design Document: Autonomous UI/UX Design Agent with Activity-Centric Analysis (GLM-5)

## Product Overview

The Autonomous UI/UX Design Agent, powered by Zai GLM-5, operates as a context- and process-customized LLM designer within a multi-agent macOS environment. It is engineered to autonomously analyze, audit, and propose enhancements for UI/UX artifacts—including static screenshots, video-based user flows, and live session captures—leveraging principles from activity theory and design standards exemplified by Jobs/Ive. The agent interfaces seamlessly with autonomous-claude (product manager), autonomous-minimax (frontend engineer), and autonomous-codex (backend engineer), integrating agentic collaboration and dispute resolution processes with human oversight.

The design agent’s mission is to embed activity-centric analysis into the UI/UX lifecycle, focusing not just on artifact inspection but also the underlying user activity flows. This foundation positions the system for incrementally deeper computer vision (CV) and interaction analysis as agent and model capabilities evolve.

### Purpose

The Design Agent addresses both technical and qualitative challenges:

* **Problem Addressed**: UI/UX quality often degrades due to invisible design debt, inconsistent component usage, and lack of context-aware audits. Human reviews are time-consuming, infrequent, and often lack systemic insight into user activity and interaction patterns, especially as products and design systems evolve.

* **Opportunity Captured**: By autonomously ingesting screens and flows (both images and video), the agent can rapidly audit for visual/interaction debt, propose standards-driven improvements, and align outputs with activity and intent—capturing both artifact and process context.

**User Scenarios:**

* Claude (Product Manager) requests an audit of a new feature’s UI flows via screenshot folder and user session video.

* Minimax (FE engineer) pushes an interim build; GLM-5 agent identifies off-system components and highlights rhythm/hierarchy breaks.

* Codex (BE engineer) consults the agent post-API integration for visual fit checks.

* A human designer intervenes, requesting justification and standards reference for a disputed audit finding.

### Target Audience

* **Personas**:

  * *LLM Agents*:

    * Claude (Product Manager/Arbiter) – needs systemic audits and arbitration capability.

    * Minimax (Frontend Engineer) – requires actionable, granular UI audit reports and visual clarity assessments.

    * Codex (Backend Engineer) – needs confirmation of visual fit post-integration.

  * *Human Product/Design Lead*: Oversight, arbitration, and injection of evolving standards.

* **Needs Addressed**:

  * *Seamless UI/UX evolution* amid rapid release cycles.

  * *Standards enforcement* to reduce visual and interaction variance.

  * *Qualitative fit analysis* rooted in activity and intent, not just pixels.

  * *Clear, actionable feedback* delivered in agent- and human-consumable formats.

### Expected Outcomes

* **Tangible Benefits**:

  * Consistently higher quality UI/UX across releases.

  * Comprehensive audit trails and phased remediation plans.

  * Direct proposals for design system updates (token/component evolution).

* **Key Metrics/KPIs**:

  * Design suggestion acceptance rate (track per cycle/agent).

  * Phase completion velocity (audit-to-adoption time).

  * Internal qualitative quality scores (periodic review).

* **Short-Term Impact**:

  * Rapid, high-precision audits on new/modified UIs.

  * Fewer missed UI/UX defects pre-release.

* **Long-Term Impact**:

  * Systemic uplift in design quality.

  * Measurable reduction in design debt and velocity drag.

## Architecture

The agent is embedded in a multi-agent system on macOS, operating alongside Claude, Minimax, and Codex. The architecture balances autonomy (full-cycle audits and proposals) and collaboration (accepting, incorporating, and arbitrating feedback) across a robust orchestration and agentic protocol.

### High-Level Architecture

* **Major Components**:

  * *Input Handlers*: Accept folders/files of screenshots (PNG, JPEG), video files (MP4, MOV), and context metadata (JSON/YAML).

  * *CV/AI Interpretation*: Uses GLM-5 computer vision (CV) pipeline for detecting screens, components, and flows.

  * *Audit/Plan Generator*: Applies activity-embedded heuristics to produce auditable findings and phased improvement plans.

  * *Design System Integration*: Reads/writes design system tokens/components in Markdown (.md), JSON, or YAML.

  * *Report Communication*: Outputs audit reports and plans to terminal/CLI logs, Markdown files, and via structured agent protocol.

  * *Orchestration/Feedback*: Supports agent-to-agent messaging, feedback loop, and arbitration mode led by Claude.

* **Process Flow**

  1. Artifact/context intake (screenshots, video, flow metadata)

  2. GLM-5 CV-based and LLM-based analysis

  3. Audit findings and phased plan generation

  4. Design system proposal output

  5. Feedback loop with Claude/agents/human guidance

* **Design Patterns**:

  * Event-driven for input processing and agent messaging

  * Modular layered architecture (input → CV/AI → audit/planning → reporting)

  * Command and arbitration pattern for dispute resolution

### Data Structures & Algorithms

* **Core Data Structures**:

  * *Screen*: Captured screen with hierarchy and layout data.

  * *Flow*: Sequence of Screens representing an activity.

  * *Component*: Parsed UI elements with bounding boxes, types, variant metadata.

  * *SystemToken*: Variables (color, spacing, typography) from design system.

  * *AuditFinding*: {location, issue, rationale, severity, relatedStandard}

  * *PlanPhase*: {phaseName, actionList, sequence, rationale}

* **Algorithms**:

  * CV-based snapshot detection: Fast object detection across screenshots/video frames (<1s per image).

  * Element parsing/labeling: Lightweight CNN or transformer with bounding box regression.

  * Rhythm/hierarchy scoring: Weighted scoring of alignment, spacing, and ordering (O(n^2)).

  * Audit plan synthesis: Greedy and heuristic planning to maximize impact per phase.

* **Extensibility**:  

  Video/deep interaction analysis phases to be modular, supporting growth of the CV and annotation pipeline as GLM-5/collaborators develop.

### System Interfaces

* **API Endpoints/Protocols**:

  * `/ingest/screenshot`: POST image(s), returns ingest ID

  * `/ingest/video`: POST video file, returns ingest ID

  * `/audit/{artifact_id}`: GET, returns audit findings JSON/MD

  * `/feedback/{audit_id}`: POST structured feedback, triggers arbitration if initiated by Claude

  * `/propose/design_update`: POST proposed changes, returns diff and rationale

* **Agent Protocols**:

  * Message queue/shared memory or domain sockets for low-latency agent communication on macOS.

  * Arbitration signals routed via autonomous-claude.

* **Data Exchange**:

  * Screenshots (PNG/JPEG), videos (MP4/MOV), context files (JSON/YAML), reports/plans (Markdown/JSON).

* **Autonomy vs. Arbitration**:

  * Default: autonomous operation, push updates.

  * Arbitration: feedback routed to and resolved by Claude, optionally relayed to human oversight.

### User Interface

* **CLI/Terminal UI**:

  * Structured output of audit/plans in Markdown and summary tables.

  * Logs for input/output events, errors, and arbitration events.

* **Rendered Artifacts**:

  * Option to export reports/plans as Markdown or PDF for human review.

  * Future support for GUI: react-based log/audit viewer, artifact browser.

* **Interaction Patterns**:

  * Input via command line args or watched directory.

  * CLI flags to trigger audit, fetch last report, or open design system proposal.

* **Accessibility/Responsiveness**:

  * All outputs structured for parsing and downstream agent consumption.

  * CLI text color/contrast accessible for visually impaired users.

## Data Model

### Entities

```
Screen
  - id: UUID (PK)
  - name: string (not null)
  - image_path: string (not null)
  - hierarchy: JSON (optional)
  - created_at: datetime

```

`Flow`

* `id: UUID (PK)`

* `name: string (not null)`

* `screens: [Screen] (1-N)`

* `video_path: string (optional)`

* `metadata: JSON`

`Component`

* `id: UUID (PK)`

* `screen_id: UUID (FK)`

* `type: string (button, input, modal, etc.)`

* `bounding_box: JSON {x, y, w, h}`

* `token_refs: [SystemToken]`

* `created_at: datetime`

`AuditFinding`

* `id: UUID (PK)`

* `entity_type: string (Screen, Flow, Component)`

* `entity_id: UUID (FK)`

* `issue: string`

* `rationale: string`

* `severity: enum (low, medium, high, critical)`

* `related_standard: string`

* `created_at: datetime`

`PlanPhase`

* `id: UUID (PK)`

* `audit_id: UUID (FK)`

* `sequence: int`

* `actions: JSON [{description, target_entity, fix, rationale}]`

* `status: enum (proposed, in-progress, complete)`

* `created_at: datetime`

`SystemToken`

* `id: UUID (PK)`

* `name: string`

* `type: enum (color, spacing, typography, etc.)`

* `value: string`

* `used_in: [Component]`  

### Relationships

* Flow → Screen: One-to-many (Flow can reference many Screens)

* Screen → Component: One-to-many (Screen has multiple Components)

* Component → SystemToken: Many-to-many (join table for tokens used in Components)

* AuditFinding → (Screen|Flow|Component): One-to-one (foreign key on entity_id)

* PlanPhase → AuditFinding: One-to-many (PlanPhase contains action list tied to findings)

### Storage

* **Database Technology**:  

  * Initial: Local SQLite with JSON fields for easy iteration

  * Alternatives: JSON/YAML files for compatibility with agent file/folder protocols

* **Caching**:  

  * In-memory caching of recent screens, flows, plan states (LRU)

  * Disk cache for processed video frames

* **File/Blob Handling**:  

  * Screenshots/videos: stored as file paths, referenced from database

  * Artifacts and exports managed via directory structure

### Data Flow

1. Screens/video uploaded or placed in watched folder

2. Input handler ingests and stores reference

3. CV/AI pipeline generates parsed entities (screens, components, flows)

4. Audit findings and plan phases persisted to local DB

5. Outputs exported for agent/collaborator consumption

## Testing Plan

### Testing Strategy

* **Unit Tests**:  

  * Test input parsing, entity extraction, rule application in audit engine.

  * Python/Pytest or equivalent, >90% coverage.

* **Integration Tests**:  

  * Exercise end-to-end artifact ingest through audit output with agent protocol mocks.

* **E2E Tests**:  

  * Simulate multi-agent audit cycle using synthetic images/video; framework: pytest-bdd (Python) or equivalent.

* **Performance Tests**:  

  * Load test with batch screenshots (100+), time per audit <1s/screen, <5s/video segment.

### Testing Tools

* CV simulators for screen/component mockups.

* Pytest/unit test frameworks.

* Structured golden dataset: known UI/UX issues with expected audit/plans.

* Log/approval test framework (snapshot diff).

* CI harness (GitHub Actions or macOS-native CI) running all test suites on PR.

### Key Test Cases

* Detect all visible components in synthetic screenshots.

* Correctly score and flag rhythm/hierarchy breaks in test UIs.

* Generate proper phase plans for multi-step design improvements.

* Exercise protocol flows: ingest, feedback, arbitration, response.

* Fuzz/edge: ambiguous, low-contrast, or incomplete screenshots/videos.

* Regression: known fixes/bugs from past audits.

### Reporting

* All test results output to structured logs and Markdown coverage reports.

* Summary dashboard (local HTML or terminal table) tracking pass/fail/coverage by module.

* Report snapshot diffs for proposed plan/audit output.

## Deployment Plan

### Environment Setup

* **Development**:  

  * macOS required, Python 3.10+/Node.js, pipenv or poetry for Python env, Homebrew for binaries.

  * Directory layout: `/data/artifacts`, `/logs`, `/design_system`, `/output/reports`.

  * Environment variable config for input/output paths.

  * Seeded with example artifacts and test images/videos.

* **Staging**:  

  * Separate config; restricted agent access

  * Staged artifact/data directories; synthetic data only

* **Production**:  

  * Local macOS launch as daemon or CLI command, auto-watching artifact directories.

  * Logs to rotating file and optional syslog/monitoring agent.

  * Orchestrate handshake with Claude/Minimax/Codex at startup.

### CI/CD Pipeline

* Steps:

  1. Lint/type check (ruff/mypy, eslint for JS modules)

  2. Run all unit/integration/E2E tests

  3. Build agent binary, prepare artifacts

  4. Generate/validate auto documentation for protocols/design tokens

  5. Deploy on merge to main; CI-driven manual deploy supported

* **Preview**: Each PR runs on local macOS VM, with logs/output posted to PR.

### Deploy Process

1. Artifact directory smoke check (verify readable artifacts, output paths)

2. Input/output full test (run audit on sample batch, confirm valid output files and logs)

3. Agent handshake (ping both inbound/outbound agent protocols, confirm arbitration channel)

### Rollback Strategy

* Backup/revert design system and plan files on each deploy

* Agent config (protocol, directory, arbitration settings) stored versioned; rollback by config switch

* Phased rollback: opt to revert only last phase of audit/plan if partial deploy required

### Post-Deploy Verification

* Run audit smoke test on curated sample (screens, flows)

* Confirm generation of Markdown/JSON reports

* Check logs for errors/tracebacks

* Await/confirm explicit ack from autonomous-claude, and at least one agent collaborator, within agent protocol

## Security & Performance

### Security

* **Agent Authentication**: process-level IDs and OS-level controls (no external port exposure)

* **Input Validation**: whitelist artifact types, check for corrupt/incomplete files

* **Secrets Management**: no runtime secrets in early phase; file permissions on design update paths

* **Dependency Scanning**: Use Dependabot or native scanning in CI

* **OWASP Considerations**: N/A for now due to lack of external exposure and personal data.

### Performance

* **Targets**:  

  * Image audit: <1s/screenshot

  * Video audit: <5s per key segment

  * Agent throughput: >10 audits/min in real usage

* **Optimization**:  

  * Cache component parsing for repeated screens/flows

  * Async agent messaging for multi-audit/concurrent protocols

  * Input batching for high artifact counts

* **Monitoring**:  

  * Log key metrics: audit duration, error count, disputed findings

  * Error tracking via structured local logs

* **Scaling**:  

  * Single-node (macOS) installation, horizontal for multi-agent setups; future CI/testing can parallelize additional agents

### Observability

* **Logging**:  

  * Structured logs: ingest events, audits, findings, feedback/disputes

  * All actions timestamped and tagged with agent/phase

  * Logs retained per audit cycle in `/logs` directory

* **Metrics**:  

  * Dashboard/table output for: audit time, pass/fail rate, arbitration count, plan acceptance metrics

* **Alerting**:  

  * Terminal or file-based alert for failed audits or unresolved disputes

  * Periodic report (Markdown/HTML) for review by human oversight or agent auditor

---

*This document defines the robust, evolvable foundation for the Autonomous UI/UX Design Agent. Engineers and contributors should use it as the implementation playbook and design reference as the system moves from foundational CV-based audits to increasing activity-centric, agent-cooperative UI/UX intelligence.*
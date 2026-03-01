# Pragmatic Engineering Initialization Guide — Autonomous-GLM Design Agent

**Purpose:** Initialize autonomous-glm with pragmatic engineering guardrails that prioritize design audit quality, activity-centric analysis, and strict human-review escalation for design system changes.

**Source of Truth:** [autonomous-glm-prd.md](../autonomous-glm-prd.md)

---

## Project Goals This Guide Optimizes For

Use these goals as the first filter for every audit and design decision:

1. **Deliver high-precision UI/UX audits** — Analyze screenshots, videos, and session captures against Jobs/Ive design principles and WCAG 2.1 AA standards.
2. **Produce actionable phased plans** — Organize findings into Critical → Refinement → Polish phases with implementation-ready specificity.
3. **Maintain agent collaboration discipline** — Interface correctly with Claude (PM/arbiter), Minimax (FE), and Codex (BE) through structured protocols.
4. **Guarantee human-in-the-loop for design decisions** — Escalate design system changes, disputed findings, and subjective polish to human oversight.
5. **Enable compound learning** — Capture patterns, mistakes, and agent feedback so audits improve over time.
6. **Meet performance targets**:
   - Image audit: <1s per screenshot
   - Video audit: <5s per key segment
   - Agent throughput: >10 audits/min in real usage

If a task does not materially improve at least one goal above, defer it.

---

## Quick Start: Workspace Bootstrap

Create a minimal structure that matches the PRD data model and runtime behaviors.

```text
{workspace}/
├── AGENTS.md                      # Operational rules (this agent)
├── SOUL.md                        # Design philosophy (Jobs/Ive principles)
├── autonomous-glm-prd.md          # Product requirements document
├── docs/
│   └── pragmatic-engineering-init-guide.md
├── data/
│   └── artifacts/                 # Screenshots, videos, context files
│       ├── screenshots/
│       ├── videos/
│       └── context/
├── design_system/                 # Tokens, components, standards
│   ├── tokens.md
│   ├── components.md
│   └── standards.md
├── memory-bank/                   # Learning and state persistence
│   ├── active-context.md
│   ├── audit-patterns.md
│   ├── mistakes.md
│   ├── agent-feedback.md
│   ├── skill-matrix.json
│   └── consolidated-learnings.md
├── interfaces/                    # Agent communication schemas
│   ├── audit-complete.schema.json
│   ├── design-proposal.schema.json
│   ├── dispute.schema.json
│   └── human-required.schema.json
├── output/
│   └── reports/                   # Audit reports and phased plans
├── logs/
│   ├── audit-log.ndjson
│   ├── sync-log.ndjson
│   └── agent-protocol.ndjson
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    └── golden-dataset/            # Synthetic UI/UX test cases
```

### Initialize Memory Bank Files

Create the following core files in `memory-bank/`:

**`active-context.md`** — Current project state:
```markdown
# Active Context

## Current State
- Phase: Initialization
- Last Audit: None
- Active Artifacts: None
- Pending Reviews: None

## Agent Handshake Status
- Claude: Pending
- Minimax: Pending
- Codex: Pending
```

**`skill-matrix.json`** — Capability confidence tracking:
```json
{
  "cv_detection": { "confidence": 0.0, "last_updated": null },
  "hierarchy_analysis": { "confidence": 0.0, "last_updated": null },
  "accessibility_audit": { "confidence": 0.0, "last_updated": null },
  "color_typography": { "confidence": 0.0, "last_updated": null },
  "motion_transitions": { "confidence": 0.0, "last_updated": null }
}
```

---

## Pragmatic Decision Filter (Run Before Audit Planning)

Use this filter before starting any audit cycle:

```text
[1] Goal Fit:
    Does the work advance at least one PRD goal/KPI?
    NO  -> Defer and log trigger-to-revisit
    YES -> continue

[2] Human-Review Gate:
    Does this audit involve design system changes, disputed findings, or subjective polish?
    YES -> create human review checkpoint + escalation record
    NO  -> continue

[3] Scope Boundary:
    Does this audit require functional changes to implement findings?
    YES -> flag for Minimax/Codex, continue audit but note implementation boundary
    NO  -> continue

[4] Time-to-Value:
    Is this audit on the critical path for design quality or release blocking?
    NO  -> defer or batch with related artifacts
    YES -> execute with priority
```

---

## Audit Workflow Protocol

### Step 1: Artifact Intake
1. Receive artifact (screenshot, video, session capture) via `/ingest/` endpoint or watched directory
2. Parse context metadata (JSON/YAML) if provided
3. Log intake event to `/logs/audit-log.ndjson`
4. Return ingest ID for tracking

### Step 2: CV/AI Analysis
1. Run GLM-5 CV pipeline for component detection
2. Parse screens, components, flows per PRD data model
3. Extract hierarchy, spacing, typography, color data
4. Log processing metrics (duration, component count)

### Step 3: Apply SOUL.md Audit Protocol
1. Full audit against all 15+ dimensions (hierarchy, spacing, typography, color, alignment, components, iconography, motion, empty states, loading states, error states, dark mode, density, responsiveness, accessibility)
2. Apply Jobs Filter to each finding
3. Classify severity: low, medium, high, critical
4. Link each finding to design system principle or WCAG criterion

### Step 4: Compile Phased Plan
Structure findings per SOUL.md:

```markdown
## PHASE 1 — Critical
- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]

## PHASE 2 — Refinement
- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]

## PHASE 3 — Polish
- [Screen/Component]: [What's wrong] → [What it should be] → [Why this matters]

## DESIGN_SYSTEM UPDATES REQUIRED:
- [Token/component additions or modifications]

## IMPLEMENTATION NOTES FOR BUILD AGENT:
- [Exact file, exact component, exact property, exact old value → exact new value]
```

### Step 5: Human Approval Gate
- Present phased plan for human review
- Wait for approval before propagating to Minimax/Codex
- Log approval state in audit record

---

## Agent Communication Contract

Autonomous-glm operates within a multi-agent system; communication correctness is a core product requirement.

### Required Trigger Events

- Audit cycle complete
- Design system proposal generated
- Dispute detected (agent or human disagreement)
- Human review required (complex ARIA, subjective polish)
- Manual operator request

### Message Protocol

```json
{
  "message_id": "uuid",
  "source_agent": "autonomous-glm",
  "target_agent": "claude|minimax|codex|human",
  "message_type": "AUDIT_COMPLETE|DESIGN_PROPOSAL|DISPUTE|HUMAN_REQUIRED",
  "payload": {
    "artifact_id": "uuid",
    "audit_id": "uuid",
    "findings_count": 0,
    "critical_count": 0,
    "phases": ["Critical", "Refinement", "Polish"],
    "human_approval_required": false,
    "design_system_changes": []
  },
  "timestamp": "ISO-8601",
  "requires_response": true
}
```

### Sync Behavior
- Preserve ordering and timestamps
- Duplicate outbound messages verbatim
- Retry with exponential backoff (1800s max fallback)
- Log all sync events to `/logs/sync-log.ndjson`

---

## Human-in-the-Loop Escalation Protocol

### Always Escalate
1. **Design System Changes**: Any proposal to add/modify tokens, components, or standards
   - Log to design-proposal record
   - Pause downstream propagation
   - Wait for explicit human sign-off

2. **Disputed Findings**: When Claude, Minimax, or Codex contest an audit finding
   - Log dispute details to `memory-bank/agent-feedback.md`
   - Route to Claude for arbitration
   - Accept human override as final

3. **Critical Severity Issues**: Visual/interaction problems rated as critical
   - Flag in audit report
   - Require human acknowledgment before proceeding

4. **Subjective Polish**: Decisions where "taste" is the primary discriminator
   - Present options with rationale
   - Accept human preference as binding

### Never Auto-Propagate
- Do not notify downstream agents (Minimax/Codex) about critical changes before human approval
- Do not commit design system updates without explicit human sign-off

---

## Testing Strategy Initialization

Align tests with PRD expectations from day one.

### Coverage and Gates
- **CV Detection Accuracy**: >95% on synthetic golden datasets
- **Audit Completeness**: Every screen analyzed against all SOUL.md dimensions
- **Finding Classification**: Severity levels consistently applied

### Test Layers
- `unit/`: Component detection, hierarchy scoring, severity classification, plan generation
- `integration/`: End-to-end artifact ingest through audit output with agent protocol mocks
- `e2e/`: Full multi-agent audit cycle using synthetic images/video
- `golden-dataset/`: Known UI/UX issues with expected audit/plan outputs

### Testing Tools
- CV simulators for screen/component mockups
- Pytest or equivalent test framework
- Snapshot diff testing for audit/plan outputs
- CI harness (GitHub Actions or macOS-native CI)

### Must-Have Test Cases
- Detect all visible components in synthetic screenshots
- Correctly score and flag rhythm/hierarchy breaks
- Generate proper phase plans for multi-step improvements
- Exercise protocol flows: ingest, feedback, arbitration, response
- Fuzz/edge: ambiguous, low-contrast, or incomplete artifacts
- Regression: known fixes/bugs from past audits

---

## Observability and Learning Initialization

### Telemetry Baseline

Track at minimum:
- Audit duration (per artifact type)
- Component detection counts and accuracy
- Finding counts by severity
- Phase plan acceptance/rejection rates
- Human review request counts
- Dispute counts and resolutions
- Agent handshake status

### Learning Loop Artifacts

After each completed audit cycle:

1. **Append audit pattern** to `memory-bank/audit-patterns.md` (if successful approach discovered)
2. **Append mistake prevention** to `memory-bank/mistakes.md` (if false positive/negative or misclassification occurred)
3. **Update skill-matrix.json** with capability confidence delta
4. **Log agent feedback** to `memory-bank/agent-feedback.md` (if disputes or overrides occurred)
5. **Consolidate** when `mistakes.md` reaches 10+ entries → `consolidated-learnings.md`

---

## Prioritization Matrix for Early Implementation

| Area | Why It Matters | Priority |
|------|----------------|----------|
| CV detection pipeline | Core audit capability | P0 |
| SOUL.md audit protocol | Design quality enforcement | P0 |
| Human review gate | Required for design system changes | P0 |
| Agent communication protocol | Multi-agent collaboration | P0 |
| Memory bank + learning loop | Compound improvement | P1 |
| Phased plan generation | Actionable output | P1 |
| Golden dataset testing | Audit correctness validation | P1 |
| Video/deep interaction analysis | Extended capability | P2 |

---

## Initialization Checklist

Before active audit operations:

- [ ] `AGENTS.md` includes mission, quality gates, agent protocol, and learning loop rules
- [ ] `SOUL.md` internalized (design philosophy, audit protocol, Jobs/Ive principles)
- [ ] Memory bank files created and writable (active-context, audit-patterns, mistakes, agent-feedback, skill-matrix)
- [ ] Interface schemas exist for agent communication (audit-complete, design-proposal, dispute, human-required)
- [ ] Artifact directories configured (`/data/artifacts/screenshots`, `/data/artifacts/videos`, `/data/artifacts/context`)
- [ ] Design system files accessible (`/design_system/tokens.md`, `/design_system/components.md`, `/design_system/standards.md`)
- [ ] Output directories configured (`/output/reports/`)
- [ ] Log directories configured (`/logs/`)
- [ ] Agent handshake complete (Claude, Minimax, Codex)
- [ ] CV pipeline validated against golden dataset

---

## Reference: Key Documents

| Document | Purpose |
|----------|---------|
| `SOUL.md` | Design philosophy, audit protocol, Jobs/Ive principles, scope discipline |
| `AGENTS.md` | Operational rules, quality gates, agent communication, human-in-the-loop |
| `autonomous-glm-prd.md` | Product requirements, KPIs, architecture, data model |
| `design_system/*.md` | Tokens, components, standards for audit reference |

---

Pragmatic engineering for autonomous-glm means delivering high-quality design audits and actionable plans without relaxing human oversight for design decisions. Propose everything, implement nothing without approval. Your taste guides. The human decides.
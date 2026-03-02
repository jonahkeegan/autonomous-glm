# Epic Planning Guide — Autonomous-GLM

> A comprehensive guide for creating, tracking, and completing implementation epics in the Autonomous-GLM project.

---

## Overview

### What is an Epic?

An **epic** is a detailed implementation breakdown of a milestone, containing:
- Specific objectives and scope boundaries
- Technical decisions and architecture choices
- Phased task breakdowns with checklists
- Success criteria and validation steps

### Hierarchy: Milestones → Epics → Tasks

```
Milestone (M0, M1, M2...)
├── Epic 1 (detailed implementation plan)
│   ├── Phase 1 tasks
│   ├── Phase 2 tasks
│   └── Phase N tasks
├── Epic 2
└── Epic N
```

| Level | Purpose | File Location | Granularity |
|-------|---------|---------------|-------------|
| **Milestone** | Roadmap phase with objectives, deliverables, KPIs | `tasks/aes-autonomous-glm-milestones.md` | High-level (days-weeks) |
| **Epic** | Detailed implementation breakdown | `tasks/epic-{milestone}-{number}-{name}.md` | Medium-level (hours-days) |
| **Task** | Atomic work items within epic phases | Inside epic files as checklists | Low-level (minutes-hours) |

### Relationship to Beads (bd) Issue Tracking

**Epic files and beads are separate systems:**

- **Epic files** (`/tasks/epic-*.md`) — Detailed implementation planning, technical decisions, phased task breakdowns
- **Beads** (`bd`) — Issue tracking, dependency management, work status, agent coordination

**Workflow:**
1. Create epic file for detailed planning
2. Optionally create beads issues to track epic progress
3. Update epic file as work progresses (checklists)
4. Complete epic with validation and completion report

---

## Epic Lifecycle

### Status Progression

```sequenceDiagram
participant Planner
participant EpicFile
participant Implementer
participant Validator
participant CompletionReport

Planner->>EpicFile: Create epic with objectives & scope
Note over EpicFile: Status: 🔲 Not Started
Implementer->>EpicFile: Begin work on Phase 1
Note over EpicFile: Status: 🔄 In Progress
Implementer->>EpicFile: Complete phases sequentially
Implementer->>EpicFile: Mark tasks complete
Validator->>EpicFile: Run validation commands
alt Validation passes
    Validator-->>EpicFile: All success criteria met
    EpicFile->>CompletionReport: Generate completion report
    Note over EpicFile: Status: ✅ COMPLETE
else Validation fails
    Validator-->>Implementer: Report failures
    Implementer->>EpicFile: Fix issues
    Validator->>EpicFile: Re-validate
end
```

### Status Indicators

| Status | Emoji | Meaning |
|--------|-------|---------|
| Not Started | 🔲 | Epic defined, no work begun |
| In Progress | 🔄 | Active development underway |
| Blocked | 🚫 | Dependencies not met, cannot proceed |
| Complete | ✅ | All tasks done, validation passed |

### Dependency Management

```sequenceDiagram
participant EpicA as Epic A
participant EpicB as Epic B
participant DependencyChecker
participant WorkQueue

EpicA->>DependencyChecker: Check dependencies
alt Dependencies met
    DependencyChecker-->>EpicA: Clear to proceed
    EpicA->>WorkQueue: Add to ready queue
else Dependencies not met
    DependencyChecker-->>EpicA: Block with reason
    EpicA->>EpicA: Status: 🚫 Blocked
    Note over EpicA: Depends on: Epic B
end
EpicB->>EpicB: Complete work
EpicB->>DependencyChecker: Signal completion
DependencyChecker->>EpicA: Unblock
EpicA->>WorkQueue: Add to ready queue
```

---

## Epic Template

### Standard Sections

Every epic should contain these sections:

```markdown
# Epic {milestone}-{number}: {Title}

> **Milestone:** {M#} - {Milestone Name}  
> **Priority:** Critical | High | Medium | Low  
> **Dependencies:** {None | List of epic dependencies}  
> **Status:** 🔲 Not Started | 🔄 In Progress | ✅ COMPLETE

---

## Objective

{1-2 sentence description of what this epic accomplishes}

---

## Scope

### In Scope
- {What this epic includes}

### Out of Scope
- {What this epic explicitly excludes}

---

## Deliverables

### 1. {Deliverable Name}
{Description}

### 2. {Deliverable Name}
{Description}

---

## Technical Decisions

### {Decision Topic}
- **Decision:** {What was decided}
- **Rationale:** {Why this approach}

---

## File Structure

```
{affected directories and files}
```

---

## Tasks

### Phase 1: {Phase Name}
- [ ] {Task 1}
- [ ] {Task 2}

### Phase 2: {Phase Name}
- [ ] {Task 1}
- [ ] {Task 2}

---

## Success Criteria

- [ ] {Measurable criterion 1}
- [ ] {Measurable criterion 2}

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| {Risk} | {Mitigation strategy} |

---

## Validation

```bash
# Commands to validate completion
```

---

*Created: {YYYY-MM-DD}*
```

### Required vs. Optional Fields

| Section | Required | Notes |
|---------|----------|-------|
| Header (milestone, priority, dependencies, status) | ✅ | Always include |
| Objective | ✅ | Clear, concise goal |
| Scope (In/Out) | ✅ | Prevents scope creep |
| Deliverables | ✅ | What gets created |
| Technical Decisions | ⚠️ | Include if decisions made |
| File Structure | ⚠️ | Include if creating files |
| Tasks (Phased) | ✅ | Core of the epic |
| Success Criteria | ✅ | Measurable outcomes |
| Risks & Mitigations | ⚠️ | Include for complex epics |
| Validation | ✅ | Commands to verify |

---

## Task Breakdown Methodology

### Phased Structure

Tasks should be organized into logical phases that represent distinct stages of work:

```sequenceDiagram
participant Planner
participant PhaseIdentifier
participant TaskDecomposer
participant DependencyMapper
participant ChecklistGenerator

Planner->>PhaseIdentifier: Identify work stages
PhaseIdentifier->>PhaseIdentifier: Group related work
PhaseIdentifier-->>Planner: Return phase list

loop For each phase
    Planner->>TaskDecomposer: Decompose into atomic tasks
    TaskDecomposer->>TaskDecomposer: Break down to granular level
    TaskDecomposer-->>Planner: Return task list
end

Planner->>DependencyMapper: Map task dependencies
DependencyMapper->>DependencyMapper: Identify ordering constraints
DependencyMapper-->>Planner: Return dependency graph

Planner->>ChecklistGenerator: Generate checklist format
ChecklistGenerator-->>Planner: Return formatted checklist
```

### Phase Naming Conventions

| Phase Type | Example Names |
|------------|---------------|
| Setup | "Project Setup", "Infrastructure", "Foundation" |
| Implementation | "Core Logic", "API Development", "Integration" |
| Testing | "Unit Tests", "Integration Tests", "Validation" |
| Documentation | "Docs", "README Update", "API Documentation" |
| Deployment | "CI/CD", "Production Deploy", "Release" |

### Task Granularity Rules

1. **Atomic**: Each task should be completable in one work session (15 min - 4 hours)
2. **Verifiable**: Each task should have a clear "done" state
3. **Independent**: Tasks should be orderable with minimal dependencies within a phase
4. **Specific**: Avoid vague tasks like "improve performance" — use "add index to X table"

### Checklist Format

```markdown
### Phase 1: Schema Definition
- [ ] Create `src/db/` directory structure
- [ ] Write `schema.sql` with all entity tables
- [ ] Add foreign key constraints and indexes
- [ ] Create initial migration file `001_initial.sql`
```

**Updating Status:**
```markdown
### Phase 1: Schema Definition
- [x] Create `src/db/` directory structure
- [x] Write `schema.sql` with all entity tables
- [ ] Add foreign key constraints and indexes
- [ ] Create initial migration file `001_initial.sql`
```

---

## Status & Progress Tracking

### Progress Calculation

```
Progress = (Completed Tasks / Total Tasks) × 100%
```

**Example:**
```markdown
### Phase 1: Schema Definition (4 tasks)
- [x] Create directory structure
- [x] Write schema.sql
- [x] Add constraints and indexes
- [ ] Create migration file

Phase 1 Progress: 75%
```

### Epic Header Updates

Update the status in the epic header as work progresses:

```markdown
# Epic M0-1: Database Schema & Data Layer

> **Milestone:** 0 - Foundation  
> **Priority:** Critical  
> **Dependencies:** None  
> **Status:** 🔄 In Progress  <!-- Updated from 🔲 Not Started -->
```

### Completion Update

When all phases are complete and validation passes:

```markdown
# Epic M0-1: Database Schema & Data Layer

> **Milestone:** 0 - Foundation  
> **Priority:** Critical  
> **Dependencies:** None  
> **Status:** ✅ COMPLETE
```

### Linking Completion Reports

Add a completion summary section at the end:

```markdown
---

## Completion Summary

**Completed:** 2026-03-01  
**Total Tasks:** 20/20  
**Duration:** 2 days  

### Files Created
- `src/db/schema.sql`
- `src/db/database.py`
- `src/db/models.py`
- `src/db/crud.py`

### Validation Results
- All 233 tests passing
- Coverage: 83%

---

*Created: 2026-02-28*  
*Completed: 2026-03-01*
```

---

## Validation & Completion

### Success Criteria Definition

Success criteria should be:
- **Measurable**: Can be verified programmatically or with clear metrics
- **Achievable**: Realistic given the scope
- **Complete**: Cover all aspects of the deliverable

**Examples:**
```markdown
## Success Criteria

- [ ] Database initializes without errors
- [ ] All 6 entity tables created with correct schema
- [ ] Foreign key relationships enforced
- [ ] CRUD operations work for all entities
- [ ] Migrations run idempotently
- [ ] No hardcoded paths (uses configuration)
```

### Validation Command Pattern

Every epic should include validation commands:

```markdown
## Validation

Run after completion:
```bash
# Initialize database
python -c "from src.db.database import init_database; init_database()"

# Verify tables created
sqlite3 data/autonomous_glm.db ".tables"

# Test CRUD operations
python -m pytest tests/unit/test_database.py -v
```
```

### Completion Workflow

```sequenceDiagram
participant Implementer
participant TestSuite
participant SuccessCriteria
participant EpicFile
participant CompletionReport

Implementer->>TestSuite: Run validation commands
TestSuite-->>Implementer: Return results

alt All tests pass
    Implementer->>SuccessCriteria: Check each criterion
    SuccessCriteria-->>Implementer: All criteria met
    Implementer->>EpicFile: Update status to COMPLETE
    Implementer->>CompletionReport: Create completion report
    Note over CompletionReport: Location: /task-completion-reports/
else Tests fail
    TestSuite-->>Implementer: Report failures
    Implementer->>Implementer: Fix issues
    Implementer->>TestSuite: Re-run tests
end
```

---

## Complete Epic Template

Copy and customize this template for new epics:

```markdown
# Epic {MILESTONE}-{NUMBER}: {TITLE}

> **Milestone:** {M#} - {Milestone Name}  
> **Priority:** Critical | High | Medium | Low  
> **Dependencies:** {None | epic-XX-YY, epic-XX-ZZ}  
> **Status:** 🔲 Not Started

---

## Objective

{Clear, concise description of what this epic accomplishes. 1-2 sentences.}

---

## Scope

### In Scope
- {Item 1}
- {Item 2}
- {Item 3}

### Out of Scope
- {Item 1}
- {Item 2}

---

## Deliverables

### 1. {Deliverable Name}
{Description of deliverable}

### 2. {Deliverable Name}
{Description of deliverable}

---

## Technical Decisions

### {Decision Topic}
- **Decision:** {What was decided}
- **Rationale:** {Why this approach}

---

## File Structure

```
{directory}/
├── {file1}
├── {file2}
└── {file3}
```

---

## Tasks

### Phase 1: {Phase Name}
- [ ] {Task 1}
- [ ] {Task 2}
- [ ] {Task 3}

### Phase 2: {Phase Name}
- [ ] {Task 1}
- [ ] {Task 2}
- [ ] {Task 3}

### Phase 3: {Phase Name}
- [ ] {Task 1}
- [ ] {Task 2}
- [ ] {Task 3}

---

## Success Criteria

- [ ] {Measurable criterion 1}
- [ ] {Measurable criterion 2}
- [ ] {Measurable criterion 3}

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| {Risk description} | {Mitigation strategy} |

---

## Validation

```bash
# Command 1
{command}

# Command 2
{command}
```

---

*Created: {YYYY-MM-DD}*
```

---

## Examples

### Reference: Completed Epic (M0-3)

The epic at `tasks/epic-m0-3-foundation-validation-suite.md` demonstrates:

✅ **Well-defined scope** — Clear in/out boundaries  
✅ **Phased tasks** — 7 logical phases with granular tasks  
✅ **Technical decisions** — Test framework, validation approach documented  
✅ **Success criteria** — Measurable outcomes defined  
✅ **Validation commands** — Specific commands to verify completion  
✅ **Completion summary** — Final status with metrics added at completion

### Creating a New Epic

1. **Identify the milestone** — Which milestone does this epic support?
2. **Define scope** — What's in and out? Be explicit.
3. **List deliverables** — What files, modules, or artifacts will be created?
4. **Document decisions** — Capture technical choices and rationale
5. **Break into phases** — Group related tasks logically
6. **Define success criteria** — How will you know it's done?
7. **Add validation** — What commands prove completion?
8. **Create the file** — Save to `tasks/epic-{milestone}-{number}-{name}.md`

### File Naming Convention

```
tasks/epic-{milestone}-{sequence}-{kebab-case-name}.md
```

**Examples:**
- `epic-m0-1-database-schema-data-layer.md`
- `epic-m0-2-configuration-management.md`
- `epic-m1-1-screenshot-ingestion.md`
- `epic-m2-1-cv-detection-pipeline.md`

---

## Quick Reference

### Epic Creation Checklist

- [ ] Header with milestone, priority, dependencies, status
- [ ] Clear objective statement
- [ ] Scope boundaries (in/out)
- [ ] List of deliverables
- [ ] Technical decisions documented
- [ ] File structure outlined
- [ ] Phased task breakdown
- [ ] Success criteria defined
- [ ] Risks identified with mitigations
- [ ] Validation commands included

### Status Update Checklist

- [ ] Update header status emoji
- [ ] Mark completed tasks in phases
- [ ] Update any changed technical decisions
- [ ] Add completion summary when done
- [ ] Create completion report in `/task-completion-reports/`

### Validation Checklist

- [ ] All phase tasks marked complete
- [ ] All success criteria verified
- [ ] Validation commands executed successfully
- [ ] No regressions in existing tests
- [ ] Documentation updated if needed

---

## Appendix: Workflow Diagrams

### Full Epic Lifecycle

```sequenceDiagram
participant Planner
participant EpicFile
participant Implementer
participant TestSuite
participant SuccessCriteria
participant CompletionReport

Note over Planner,EpicFile: Phase 1: Creation
Planner->>EpicFile: Create epic file
Planner->>EpicFile: Define objectives & scope
Planner->>EpicFile: Add deliverables & decisions
Planner->>EpicFile: Create phased task breakdown
Planner->>EpicFile: Define success criteria
Note over EpicFile: Status: 🔲 Not Started

Note over EpicFile,Implementer: Phase 2: Implementation
Implementer->>EpicFile: Update status to In Progress
Note over EpicFile: Status: 🔄 In Progress

loop For each phase
    Implementer->>EpicFile: Execute tasks
    Implementer->>EpicFile: Mark tasks complete
end

Note over EpicFile,CompletionReport: Phase 3: Validation
Implementer->>TestSuite: Run validation commands
TestSuite-->>Implementer: Return results

alt All tests pass
    Implementer->>SuccessCriteria: Verify all criteria
    SuccessCriteria-->>Implementer: All met
    Implementer->>EpicFile: Update status to COMPLETE
    Note over EpicFile: Status: ✅ COMPLETE
    Implementer->>CompletionReport: Create completion report
else Tests fail
    TestSuite-->>Implementer: Report failures
    Implementer->>Implementer: Fix issues
    Implementer->>TestSuite: Re-run validation
end
```

### Dependency Resolution Flow

```sequenceDiagram
participant EpicA as Epic A (blocked)
participant EpicB as Epic B (blocker)
participant DependencyTracker
participant WorkQueue

EpicA->>DependencyTracker: Check dependencies
DependencyTracker->>DependencyTracker: Query epic status
DependencyTracker-->>EpicA: Blocked by Epic B
Note over EpicA: Status: 🚫 Blocked

EpicB->>EpicB: Complete work
EpicB->>DependencyTracker: Signal completion
DependencyTracker->>EpicA: Notify unblocked
EpicA->>WorkQueue: Add to ready queue
Note over EpicA: Status: 🔲 Not Started (unblocked)
```

---

*Document created: 2026-03-01*  
*Last updated: 2026-03-01*
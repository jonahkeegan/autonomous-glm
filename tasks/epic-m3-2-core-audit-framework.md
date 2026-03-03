# Epic M3-2: Core Audit Framework

> **Milestone:** 3 - Audit Engine  
> **Priority:** Critical  
> **Dependencies:** Epic M3-1  
> **Status:** 🔲 Not Started

---

## Objective

Build the foundational audit framework that orchestrates all audit dimensions, classifies finding severity, links findings to design standards, and persists results to the database.

---

## Scope

### In Scope
- Audit session and finding Pydantic models
- Severity classification engine (low, medium, high, critical)
- Standards reference linking system (design tokens, WCAG criteria)
- Jobs Filter implementation ("Would a user need to be told this exists?")
- Audit orchestrator with plugin architecture for dimensions
- AuditFinding entity persistence
- Configuration for audit settings

### Out of Scope
- Individual audit dimension implementations (M3-3, M3-4)
- Report generation (M6)
- Agent communication (M5)
- Before/after comparisons (M4)

---

## Deliverables

### 1. Audit Models (`src/audit/models.py`)

Pydantic models for audit data:
- `AuditDimension` — Enum of all 15+ audit dimensions
- `Severity` — Enum (low, medium, high, critical)
- `StandardsReference` — Link to design token or WCAG criterion
- `AuditFinding` — {id, dimension, entity_type, entity_id, issue, rationale, severity, standards_refs, created_at}
- `AuditSession` — {id, screen_id, status, findings, started_at, completed_at}
- `AuditResult` — {session, findings_by_dimension, summary_stats}

### 2. Severity Classification Engine (`src/audit/severity.py`)

Classification logic:
- `SeverityEngine` — Main classification class
- `classify_finding(issue_type: str, impact: str, frequency: str) -> Severity`
- `SeverityMatrix` — Configurable matrix for impact × frequency → severity
- Predefined rules for common issue types

### 3. Standards Reference System (`src/audit/standards.py`)

Standards linking:
- `StandardsRegistry` — Registry of all design standards
- `DesignTokenReference` — Reference to specific design token
- `WCAGReference` — Reference to WCAG criterion (e.g., "1.4.3")
- `link_finding_to_standard(finding: AuditFinding, standard: str) -> StandardsReference`
- Load standards from `design_system/*.md` files

### 4. Jobs Filter (`src/audit/jobs_filter.py`)

Jobs/Ive design philosophy filter:
- `JobsFilter` — Filter class
- `apply_filter(finding: AuditFinding) -> bool` — Returns True if finding passes
- Filter questions:
  - "Would a user need to be told this exists?"
  - "Can this be removed without losing meaning?"
  - "Does this feel inevitable?"
- Findings that fail filter are flagged, not discarded

### 5. Audit Orchestrator (`src/audit/orchestrator.py`)

Main audit coordination:
- `AuditOrchestrator` — Main orchestrator class
- `register_dimension(dimension: AuditDimension, auditor: Callable) -> None`
- `run_audit(screen_id: UUID, dimensions: list[AuditDimension] = None) -> AuditResult`
- `run_dimension_audit(screen: Screen, dimension: AuditDimension) -> list[AuditFinding]`
- Plugin architecture for dimension implementations

### 6. Audit Persistence (`src/audit/persistence.py`)

Database integration:
- `save_audit_session(session: AuditSession) -> UUID`
- `save_audit_finding(finding: AuditFinding) -> UUID`
- `get_audit_session(session_id: UUID) -> AuditSession`
- `get_findings_by_screen(screen_id: UUID) -> list[AuditFinding]`
- `get_findings_by_dimension(dimension: AuditDimension) -> list[AuditFinding]`

### 7. Configuration

Add to existing config system:
- `audit.enabled_dimensions` — List of dimensions to run
- `audit.severity_threshold` — Minimum severity to report
- `audit.jobs_filter_enabled` — Enable/disable Jobs filter
- `audit.max_findings_per_dimension` — Limit findings per dimension

---

## Technical Decisions

### Plugin Architecture
- **Decision:** Dimensions register themselves with the orchestrator
- **Rationale:**
  - Easy to add/remove dimensions without modifying core
  - Each dimension is independently testable
  - Supports partial audits (run only specific dimensions)

### Severity Classification
- **Decision:** Matrix-based classification (impact × frequency)
- **Rationale:**
  - Consistent, reproducible severity assignments
  - Configurable without code changes
  - Explainable (can show why severity was assigned)

### Standards Linking
- **Decision:** Registry pattern with string-based references
- **Rationale:**
  - Design tokens are in Markdown files (string keys)
  - WCAG criteria are string identifiers
  - Allows runtime updates without code changes

### Jobs Filter
- **Decision:** Soft filter (flag, don't discard)
- **Rationale:**
  - Human may want to see all findings including filtered ones
  - Provides learning opportunity for tuning filter
  - Maintains audit completeness

### Persistence Strategy
- **Decision:** Save after each dimension completes
- **Rationale:**
  - Partial results preserved on failure
  - Progress trackable during long audits
  - Supports resume after interruption

---

## File Structure

```
src/
└── audit/
    ├── __init__.py           # Module exports
    ├── models.py             # Audit Pydantic models
    ├── severity.py           # Severity classification engine
    ├── standards.py          # Standards reference system
    ├── jobs_filter.py        # Jobs/Ive design filter
    ├── orchestrator.py       # Main audit orchestrator
    └── persistence.py        # Database persistence
config/
└── default.yaml              # Updated with audit config
tests/
└── unit/
    ├── test_audit_models.py
    ├── test_severity.py
    ├── test_standards.py
    ├── test_jobs_filter.py
    ├── test_orchestrator.py
    └── test_audit_persistence.py
```

---

## Tasks

### Phase 1: Audit Models
- [ ] Create `src/audit/` directory structure
- [ ] Create `src/audit/__init__.py` with module exports
- [ ] Create `src/audit/models.py` with Pydantic models
- [ ] Define `AuditDimension` enum (15+ dimensions)
- [ ] Define `Severity` enum (low, medium, high, critical)
- [ ] Create `AuditFinding` model with all fields
- [ ] Create `AuditSession` model with status tracking
- [ ] Create `AuditResult` model with summary stats
- [ ] Write unit tests for models

### Phase 2: Severity Classification
- [ ] Create `src/audit/severity.py`
- [ ] Implement `Severity` enum
- [ ] Implement `SeverityMatrix` class
- [ ] Implement `SeverityEngine.classify_finding()`
- [ ] Define predefined rules for common issues
- [ ] Add configuration for severity thresholds
- [ ] Write unit tests for severity classification

### Phase 3: Standards Reference System
- [ ] Create `src/audit/standards.py`
- [ ] Implement `StandardsRegistry` class
- [ ] Implement `DesignTokenReference` model
- [ ] Implement `WCAGReference` model
- [ ] Load design tokens from `design_system/tokens.md`
- [ ] Load WCAG criteria from standards file
- [ ] Implement `link_finding_to_standard()`
- [ ] Write unit tests for standards system

### Phase 4: Jobs Filter
- [ ] Create `src/audit/jobs_filter.py`
- [ ] Implement `JobsFilter` class
- [ ] Implement filter questions as boolean checks
- [ ] Implement `apply_filter()` method
- [ ] Add configuration to enable/disable filter
- [ ] Write unit tests for Jobs filter

### Phase 5: Audit Orchestrator
- [ ] Create `src/audit/orchestrator.py`
- [ ] Implement `AuditOrchestrator` class
- [ ] Implement dimension registration
- [ ] Implement `run_audit()` main method
- [ ] Implement `run_dimension_audit()` for single dimension
- [ ] Add progress tracking and logging
- [ ] Write unit tests with mock dimensions

### Phase 6: Audit Persistence
- [ ] Create `src/audit/persistence.py`
- [ ] Implement `save_audit_session()`
- [ ] Implement `save_audit_finding()`
- [ ] Implement `get_audit_session()`
- [ ] Implement `get_findings_by_screen()`
- [ ] Implement `get_findings_by_dimension()`
- [ ] Update `src/db/crud.py` if needed
- [ ] Write unit tests for persistence

### Phase 7: Configuration & Integration
- [ ] Add `audit:` section to `config/default.yaml`
- [ ] Add `AuditConfig` to `src/config/schema.py`
- [ ] Create integration tests for full audit flow
- [ ] Test with M3-1 validation dataset
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Audit models validate correctly with all fields
- [ ] Severity classification produces consistent, reproducible results
- [ ] Standards references link to actual design tokens and WCAG criteria
- [ ] Jobs filter correctly flags findings that fail Jobs/Ive principles
- [ ] Orchestrator runs all registered dimensions in sequence
- [ ] Audit sessions and findings persist correctly to database
- [ ] Configuration controls audit behavior
- [ ] Unit test coverage > 90% for `src/audit/` module
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Severity classification too subjective | Use explicit matrix; document rationale for each rule |
| Standards registry becomes stale | Load from source files at runtime; version control design system |
| Jobs filter too aggressive | Soft filter with flagging; allow configuration of threshold |
| Orchestrator fails mid-audit | Save after each dimension; support resume |
| Dimension implementations vary in quality | Define clear interface contract; integration tests |

---

## Validation

Run after completion:
```bash
# Run audit module tests
python -m pytest tests/unit/test_audit*.py -v

# Test severity classification
python -c "
from src.audit.severity import SeverityEngine
engine = SeverityEngine()
severity = engine.classify_finding('color_contrast', 'high', 'frequent')
print(f'Classified as: {severity}')
"

# Test orchestrator with mock dimension
python -c "
from src.audit.orchestrator import AuditOrchestrator
from src.audit.models import AuditDimension

orchestrator = AuditOrchestrator()

# Register a mock dimension
def mock_visual_hierarchy(screen):
    return []

orchestrator.register_dimension(AuditDimension.VISUAL_HIERARCHY, mock_visual_hierarchy)
print('Orchestrator ready with 1 dimension')
"

# Test standards registry
python -c "
from src.audit.standards import StandardsRegistry
registry = StandardsRegistry()
tokens = registry.get_design_tokens()
print(f'Loaded {len(tokens)} design tokens')
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- All M2 and M3-1 dependencies
- No new dependencies required

### System Dependencies
- SQLite database with M3-1 persistence layer
- Design system files (`design_system/*.md`)

---

*Created: 2026-03-02*
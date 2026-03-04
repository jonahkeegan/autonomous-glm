# Epic M4-1: Phased Plan Synthesis

> **Milestone:** 4 - Plan Generation  
> **Priority:** Critical  
> **Dependencies:** Epic M3-4 (State & Accessibility Dimensions)  
> **Status:** 🔲 Not Started

---

## Objective

Build the phased plan synthesis system that groups audit findings into priority phases (Critical → Refinement → Polish) based on severity, dimension, and cross-dimension dependencies.

---

## Scope

### In Scope
- PlanPhase and PlanAction Pydantic models
- Phase classification rules engine (severity + dimension → phase)
- Cross-dimension dependency handling (e.g., fix hierarchy before spacing)
- PlanSynthesizer to aggregate findings into sequenced phases
- PhaseType enum (CRITICAL, REFINEMENT, POLISH)
- Configuration for phase thresholds

### Out of Scope
- Instruction formatting (M4-2)
- Design system proposals (M4-3)
- Report generation (M4-4)
- Before/after comparisons (M4-3)

---

## Deliverables

### 1. Plan Models (`src/plan/models.py`)

Pydantic models for plan data:
- `PhaseType` — Enum (CRITICAL, REFINEMENT, POLISH)
- `PlanAction` — {id, finding_id, description, sequence, status}
- `PlanPhase` — {id, phase_type, actions, sequence, status, created_at}
- `Plan` — {id, audit_session_id, phases, summary, created_at}
- `PlanStatus` — Enum (PENDING, IN_PROGRESS, COMPLETED)

### 2. Phase Classifier (`src/plan/phasing.py`)

Classification logic:
- `PhaseClassifier` — Main classification class
- `classify_finding(finding: AuditFinding) -> PhaseType`
- `classify_by_severity(severity: Severity) -> PhaseType` — Critical/High → Phase 1, Medium → Phase 2, Low → Phase 3
- `classify_by_dimension(dimension: AuditDimension) -> PhaseType` — Hierarchy → Phase 1, Typography → Phase 2
- `get_phase_order(phase: PhaseType) -> int` — Returns sequence number

### 3. Dependency Resolver (`src/plan/dependencies.py`)

Cross-dimension dependency handling:
- `DependencyResolver` — Resolves action ordering
- `get_dependencies(dimension: AuditDimension) -> list[AuditDimension]`
- `resolve_order(findings: list[AuditFinding]) -> list[AuditFinding]`
- Predefined dependency rules (hierarchy before spacing, color before theming)

### 4. Plan Synthesizer (`src/plan/synthesizer.py`)

Main synthesis orchestration:
- `PlanSynthesizer` — Main synthesizer class
- `synthesize(audit_result: AuditResult) -> Plan`
- `group_by_phase(findings: list[AuditFinding]) -> dict[PhaseType, list[AuditFinding]]`
- `sequence_actions(findings: list[AuditFinding], phase: PhaseType) -> list[PlanAction]`
- `generate_summary(plan: Plan) -> PlanSummary`

### 5. Configuration

Add to existing config system:
- `plan.phase_thresholds` — Severity thresholds for each phase
- `plan.dimension_priorities` — Dimension → phase mappings
- `plan.dependency_rules` — Cross-dimension dependencies

---

## Technical Decisions

### Phase Classification Rules
- **Decision:** Rule-based with severity as primary, dimension as secondary
- **Rationale:**
  - Deterministic and explainable
  - Tunable via configuration
  - Severity is the most important factor for prioritization

**Default Rules:**
| Severity | Phase |
|----------|-------|
| Critical | CRITICAL |
| High | CRITICAL |
| Medium | REFINEMENT |
| Low | POLISH |

**Dimension Priorities (override severity):**
| Dimension | Phase Override |
|-----------|----------------|
| VISUAL_HIERARCHY | CRITICAL |
| ACCESSIBILITY | CRITICAL |
| SPACING_RHYTHM | REFINEMENT |
| TYPOGRAPHY | REFINEMENT |
| COLOR | REFINEMENT |
| DARK_MODE_THEMING | POLISH |
| EMPTY_STATES | POLISH |
| LOADING_STATES | POLISH |
| ERROR_STATES | POLISH |

### Dependency Resolution
- **Decision:** Predefined dependency graph with topological sort
- **Rationale:**
  - Some fixes must precede others (e.g., hierarchy before spacing)
  - Prevents wasted effort from out-of-order fixes
  - Explicit rules are easier to maintain

**Dependency Rules:**
- VISUAL_HIERARCHY → blocks SPACING_RHYTHM, TYPOGRAPHY
- COLOR → blocks DARK_MODE_THEMING
- COMPONENTS → blocks DENSITY

---

## File Structure

```
src/
└── plan/
    ├── __init__.py           # Module exports
    ├── models.py             # Plan Pydantic models
    ├── phasing.py            # Phase classification
    ├── dependencies.py       # Dependency resolution
    └── synthesizer.py        # Main synthesizer
config/
└── default.yaml              # Updated with plan config
tests/
└── unit/
    ├── test_plan_models.py
    ├── test_phasing.py
    ├── test_dependencies.py
    └── test_synthesizer.py
```

---

## Tasks

### Phase 1: Plan Models
- [ ] Create `src/plan/` directory structure
- [ ] Create `src/plan/__init__.py` with module exports
- [ ] Create `src/plan/models.py` with Pydantic models
- [ ] Define `PhaseType` enum (CRITICAL, REFINEMENT, POLISH)
- [ ] Define `PlanStatus` enum (PENDING, IN_PROGRESS, COMPLETED)
- [ ] Create `PlanAction` model with all fields
- [ ] Create `PlanPhase` model with actions list
- [ ] Create `Plan` model with phases and summary
- [ ] Create `PlanSummary` model with statistics
- [ ] Write unit tests for models

### Phase 2: Phase Classification
- [ ] Create `src/plan/phasing.py`
- [ ] Implement `PhaseType` enum
- [ ] Implement `PhaseClassifier` class
- [ ] Implement `classify_by_severity()` method
- [ ] Implement `classify_by_dimension()` method
- [ ] Implement `classify_finding()` combining both
- [ ] Add configuration for phase thresholds
- [ ] Write unit tests for classification

### Phase 3: Dependency Resolution
- [ ] Create `src/plan/dependencies.py`
- [ ] Implement `DependencyResolver` class
- [ ] Define dependency graph (hardcoded rules)
- [ ] Implement `get_dependencies()` method
- [ ] Implement `resolve_order()` with topological sort
- [ ] Add configuration for dependency rules
- [ ] Write unit tests for dependency resolution

### Phase 4: Plan Synthesizer
- [ ] Create `src/plan/synthesizer.py`
- [ ] Implement `PlanSynthesizer` class
- [ ] Implement `group_by_phase()` method
- [ ] Implement `sequence_actions()` method
- [ ] Implement `synthesize()` main method
- [ ] Implement `generate_summary()` method
- [ ] Write unit tests with mock audit results

### Phase 5: Configuration & Integration
- [ ] Add `plan:` section to `config/default.yaml`
- [ ] Add `PlanConfig` to `src/config/schema.py`
- [ ] Create integration tests for full synthesis flow
- [ ] Test with M3-1 validation dataset
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Plan models validate correctly with all fields
- [ ] Phase classification produces consistent, reproducible results
- [ ] Dependency resolution correctly orders actions
- [ ] Synthesizer generates complete plans from audit results
- [ ] Configuration controls phase behavior
- [ ] Unit test coverage > 90% for `src/plan/` module
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Phase classification too rigid | Make rules configurable; allow overrides |
| Dependency cycles | Detect cycles in resolver; log warning |
| Too many critical findings | Add severity threshold tuning |
| Synthesis fails mid-plan | Save partial results; support resume |

---

## Validation

Run after completion:
```bash
# Run plan module tests
python -m pytest tests/unit/test_plan*.py -v

# Test phase classification
python -c "
from src.plan.phasing import PhaseClassifier
from src.audit.models import AuditDimension
from src.db.models import Severity

classifier = PhaseClassifier()
phase = classifier.classify_finding(
    dimension=AuditDimension.VISUAL_HIERARCHY,
    severity=Severity.HIGH
)
print(f'Classified as: {phase}')
"

# Test synthesizer with mock data
python -c "
from src.plan.synthesizer import PlanSynthesizer
from src.audit.models import AuditResult, AuditSession

synthesizer = PlanSynthesizer()
# Create mock audit result
session = AuditSession(screen_id='test-screen')
result = AuditResult(session=session)
plan = synthesizer.synthesize(result)
print(f'Plan created with {len(plan.phases)} phases')
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- All M3 dependencies
- No new dependencies required

### System Dependencies
- SQLite database with M3 audit persistence
- Audit results from M3 orchestrator

---

*Created: 2026-03-04*
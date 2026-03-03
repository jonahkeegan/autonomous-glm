# Epic M3-3: Visual Audit Dimensions

> **Milestone:** 3 - Audit Engine  
> **Priority:** High  
> **Dependencies:** Epic M3-2  
> **Status:** 🔲 Not Started

---

## Objective

Implement the 7 primary visual audit dimensions that analyze screenshot-based UI properties: visual hierarchy, spacing/rhythm, typography, color, alignment/grid, components, and density.

---

## Scope

### In Scope
- Visual Hierarchy dimension (prominence, eye-flow analysis)
- Spacing & Rhythm dimension (consistency, breathing room)
- Typography dimension (size hierarchy, weight consistency)
- Color dimension (contrast ratios, palette consistency)
- Alignment & Grid dimension (pixel-perfect positioning)
- Components dimension (same component = same styling)
- Density dimension (information overload detection)
- Integration with M3-2 audit framework
- Unit tests for all dimensions

### Out of Scope
- State-dependent dimensions (M3-4)
- Accessibility audit (M3-4)
- Motion/transitions (deferred to future milestone)
- Responsiveness across viewports (deferred to future milestone)
- Report generation (M6)

---

## Deliverables

### 1. Visual Hierarchy Auditor (`src/audit/dimensions/visual_hierarchy.py`)

Analyze prominence and eye-flow:
- `VisualHierarchyAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Most important element is most prominent
- Check: Eye lands where it should (top-left bias, size hierarchy)
- Check: User can understand screen in 2 seconds
- Use M2-2 hierarchy tree for analysis

### 2. Spacing & Rhythm Auditor (`src/audit/dimensions/spacing.py`)

Analyze whitespace consistency:
- `SpacingRhythmAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Whitespace is consistent (uses 4px/8px grid)
- Check: Elements breathe (not cramped)
- Check: Vertical rhythm is harmonious
- Use M2-3 spacing analysis results

### 3. Typography Auditor (`src/audit/dimensions/typography.py`)

Analyze type hierarchy:
- `TypographyAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Type sizes establish clear hierarchy
- Check: Font weights don't compete
- Check: Typography feels calm, not chaotic
- Use M2-3 typography estimation results

### 4. Color Auditor (`src/audit/dimensions/color.py`)

Analyze color usage:
- `ColorAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Color used with restraint and purpose
- Check: Colors guide attention (not scatter it)
- Check: Contrast ratios meet WCAG AA (4.5:1 for text)
- Use M2-3 color extraction results

### 5. Alignment & Grid Auditor (`src/audit/dimensions/alignment.py`)

Analyze grid adherence:
- `AlignmentGridAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Elements sit on consistent grid
- Check: Nothing off by 1-2 pixels
- Check: Every element feels locked into layout
- Use bounding box coordinates for analysis

### 6. Components Auditor (`src/audit/dimensions/components.py`)

Analyze component consistency:
- `ComponentsAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Similar elements styled identically
- Check: Interactive elements obviously interactive
- Check: States (disabled, hover, focus) accounted for
- Compare components of same type across screen

### 7. Density Auditor (`src/audit/dimensions/density.py`)

Analyze information density:
- `DensityAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Nothing can be removed without losing meaning
- Check: No redundant elements
- Check: Every element earns its place
- Calculate component count per area

---

## Technical Decisions

### Auditor Interface
- **Decision:** All auditors implement same interface (`audit() -> list[AuditFinding]`)
- **Rationale:** Consistent interface for orchestrator; easy to test and register

### Finding Generation
- **Decision:** Each auditor generates findings with severity + standards references
- **Rationale:** Leverages M3-2 severity and standards systems; findings are actionable

### M2 Data Reuse
- **Decision:** Use M2 detection/extraction results as input, don't re-detect
- **Rationale:** Avoid redundant API calls; M2 data already in database

### Threshold Configuration
- **Decision:** Configurable thresholds per dimension (e.g., min contrast ratio)
- **Rationale:** Different contexts may need different standards; tunable without code changes

### Scoring Algorithms
- **Decision:** O(n²) max for hierarchy/rhythm scoring (acceptable for 50-100 components)
- **Rationale:** Simple implementation; performance acceptable for typical screens

---

## File Structure

```
src/
└── audit/
    └── dimensions/
        ├── __init__.py              # Dimension exports
        ├── base.py                  # Base auditor class
        ├── visual_hierarchy.py      # Visual hierarchy auditor
        ├── spacing.py               # Spacing & rhythm auditor
        ├── typography.py            # Typography auditor
        ├── color.py                 # Color auditor
        ├── alignment.py             # Alignment & grid auditor
        ├── components.py            # Components auditor
        └── density.py               # Density auditor
tests/
└── unit/
    └── test_dimensions/
        ├── test_visual_hierarchy.py
        ├── test_spacing.py
        ├── test_typography.py
        ├── test_color.py
        ├── test_alignment.py
        ├── test_components.py
        └── test_density.py
```

---

## Tasks

### Phase 1: Dimension Infrastructure
- [ ] Create `src/audit/dimensions/` directory
- [ ] Create `src/audit/dimensions/__init__.py` with exports
- [ ] Create `src/audit/dimensions/base.py` with `BaseAuditor` class
- [ ] Define common auditor interface
- [ ] Add dimension registration helper
- [ ] Write unit tests for base class

### Phase 2: Visual Hierarchy Dimension
- [ ] Create `src/audit/dimensions/visual_hierarchy.py`
- [ ] Implement `VisualHierarchyAuditor` class
- [ ] Implement hierarchy scoring algorithm
- [ ] Check prominence of primary elements
- [ ] Check eye-flow patterns
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 3: Spacing & Rhythm Dimension
- [ ] Create `src/audit/dimensions/spacing.py`
- [ ] Implement `SpacingRhythmAuditor` class
- [ ] Analyze margin/padding consistency
- [ ] Check breathing room between elements
- [ ] Verify vertical rhythm
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 4: Typography Dimension
- [ ] Create `src/audit/dimensions/typography.py`
- [ ] Implement `TypographyAuditor` class
- [ ] Analyze font size hierarchy
- [ ] Check font weight consistency
- [ ] Detect competing styles
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 5: Color Dimension
- [ ] Create `src/audit/dimensions/color.py`
- [ ] Implement `ColorAuditor` class
- [ ] Analyze color palette consistency
- [ ] Check contrast ratios (WCAG AA)
- [ ] Detect color usage issues
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 6: Alignment & Grid Dimension
- [ ] Create `src/audit/dimensions/alignment.py`
- [ ] Implement `AlignmentGridAuditor` class
- [ ] Check grid alignment (4px/8px grid)
- [ ] Detect pixel misalignments
- [ ] Verify layout precision
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 7: Components Dimension
- [ ] Create `src/audit/dimensions/components.py`
- [ ] Implement `ComponentsAuditor` class
- [ ] Compare same-type components
- [ ] Check interactive element visibility
- [ ] Detect styling inconsistencies
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 8: Density Dimension
- [ ] Create `src/audit/dimensions/density.py`
- [ ] Implement `DensityAuditor` class
- [ ] Calculate component density
- [ ] Detect information overload
- [ ] Find redundant elements
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 9: Integration & Testing
- [ ] Register all dimensions with orchestrator
- [ ] Create integration tests with validation dataset
- [ ] Test full audit flow with all 7 dimensions
- [ ] Verify finding quality against expected results
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] All 7 visual dimensions implemented and registered
- [ ] Each dimension produces findings when issues exist
- [ ] Findings include proper severity classification
- [ ] Findings link to relevant design standards
- [ ] Visual hierarchy scoring identifies prominence issues
- [ ] Spacing analysis detects rhythm breaks
- [ ] Typography analysis finds hierarchy problems
- [ ] Color analysis catches contrast issues
- [ ] Alignment analysis finds grid violations
- [ ] Components analysis detects inconsistencies
- [ ] Density analysis identifies information overload
- [ ] Unit test coverage > 90% for all dimensions
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Hierarchy scoring too subjective | Define clear scoring rules; use quantifiable metrics |
| Contrast detection misses edge cases | Use WCAG contrast formula; test with validation dataset |
| Alignment false positives | Allow configurable tolerance (1-2px threshold) |
| Density threshold arbitrary | Make configurable; provide sensible defaults |
| Component comparison across screens | Start with same-screen comparison; cross-screen in future |

---

## Validation

Run after completion:
```bash
# Run dimension tests
python -m pytest tests/unit/test_dimensions/ -v

# Test visual hierarchy auditor
python -c "
from src.audit.dimensions.visual_hierarchy import VisualHierarchyAuditor
from src.db.crud import get_components_by_screen

auditor = VisualHierarchyAuditor()
# ... test with sample screen
"

# Test full audit with all dimensions
python -c "
from src.audit.orchestrator import AuditOrchestrator
from src.audit.dimensions import register_all_dimensions

orchestrator = AuditOrchestrator()
register_all_dimensions(orchestrator)
print(f'Registered {len(orchestrator.dimensions)} dimensions')
"

# Validate against validation dataset
python -c "
from src.audit.orchestrator import AuditOrchestrator
from src.audit.dimensions import register_all_dimensions

orchestrator = AuditOrchestrator()
register_all_dimensions(orchestrator)
# Run on validation screenshots
# Compare findings to expected results
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- All M2 and M3-2 dependencies
- No new dependencies required

### System Dependencies
- M2 vision module (component detection, token extraction)
- M3-1 persistence layer
- M3-2 audit framework
- Design system files for standards references

---

*Created: 2026-03-02*
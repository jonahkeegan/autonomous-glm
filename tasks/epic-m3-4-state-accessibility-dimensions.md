# Epic M3-4: State & Accessibility Dimensions

> **Milestone:** 3 - Audit Engine  
> **Priority:** High  
> **Dependencies:** Epic M3-2  
> **Status:** 🔲 Not Started

---

## Objective

Implement the remaining audit dimensions focused on UI states (empty, loading, error, dark mode), iconography, and screenshot-detectable accessibility issues.

---

## Scope

### In Scope
- Iconography dimension (consistency, clarity, weight)
- Empty States dimension (blank screen handling)
- Loading States dimension (skeleton screens, spinners)
- Error States dimension (error message styling)
- Dark Mode / Theming dimension (contrast across themes)
- Accessibility dimension (contrast ratios, component type hints)
- Integration with M3-2 audit framework
- Unit tests for all dimensions

### Out of Scope
- Motion & Transitions (deferred to future milestone - requires video analysis)
- Responsiveness across viewports (deferred to future milestone - requires multi-viewport)
- Full ARIA/keyboard audit (requires DOM access)
- Agent communication (M5)
- Report generation (M6)

---

## Deferred Dimensions

The following dimensions are documented for future implementation:

### Motion & Transitions (Deferred)
- **Reason:** Requires video frame analysis to detect animation issues
- **Target Milestone:** Post-M7 (enhanced video analysis)
- **Expected Capabilities:**
  - Transition timing analysis
  - Animation purpose detection
  - Motion that exists for no reason
  - Responsive feel to touch/click

### Responsiveness (Deferred)
- **Reason:** Requires screenshots at multiple viewport sizes
- **Target Milestone:** Post-M6 (multi-viewport support)
- **Expected Capabilities:**
  - Mobile, tablet, desktop detection
  - Touch target sizing
  - Fluid layout adaptation
  - Breakpoint analysis

---

## Deliverables

### 1. Iconography Auditor (`src/audit/dimensions/iconography.py`)

Analyze icon consistency:
- `IconographyAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Icons consistent in style and weight
- Check: Icons from cohesive set (not mixed libraries)
- Check: Icons support meaning (not just decoration)
- Check: Icon sizes are consistent
- Use component type='icon' from M2 detection

### 2. Empty States Auditor (`src/audit/dimensions/empty_states.py`)

Analyze blank screen handling:
- `EmptyStatesAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Blank screens feel intentional (not broken)
- Check: User guided toward first action
- Check: Empty state messaging is helpful
- Detect low component count as potential empty state

### 3. Loading States Auditor (`src/audit/dimensions/loading_states.py`)

Analyze loading indicators:
- `LoadingStatesAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Skeleton screens/spinners consistent
- Check: App feels alive while waiting
- Detect loading-related components (spinners, progress bars)
- Note: Limited to visible loading states in screenshots

### 4. Error States Auditor (`src/audit/dimensions/error_states.py`)

Analyze error presentation:
- `ErrorStatesAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Error messages styled consistently
- Check: Errors feel helpful (not hostile)
- Check: Error text is clear and actionable
- Detect error-related components by type/content hints

### 5. Dark Mode / Theming Auditor (`src/audit/dimensions/theming.py`)

Analyze theme consistency:
- `ThemingAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: If dark mode present, is it designed (not just inverted)
- Check: All tokens/shadows hold up across themes
- Check: Contrast ratios maintained in dark mode
- Note: Requires dark mode screenshot for comparison

### 6. Accessibility Auditor (`src/audit/dimensions/accessibility.py`)

Analyze screenshot-detectable accessibility:
- `AccessibilityAuditor` — Main auditor class
- `audit(screen: Screen, components: list[Component]) -> list[AuditFinding]`
- Check: Color contrast ratios (WCAG AA - 4.5:1 text, 3:1 UI)
- Check: Component types suggest semantic elements
- Check: Interactive elements are distinguishable
- Check: Text is legible (minimum size)
- Note: Cannot check ARIA labels, keyboard nav, screen reader flow

---

## Technical Decisions

### Screenshot-Based Accessibility
- **Decision:** Focus on contrast ratios and visual accessibility only
- **Rationale:**
  - Screenshots don't expose DOM for ARIA/keyboard analysis
  - Contrast is the most common accessibility issue
  - Component types can hint at semantic requirements
  - Document limitation clearly for future DOM integration

### State Detection Strategy
- **Decision:** Heuristic detection based on component count and types
- **Rationale:**
  - Empty states have low component count
  - Loading states have spinners/progress indicators
  - Error states have specific text patterns or icons
  - Not perfect but catches common patterns

### Icon Consistency Analysis
- **Decision:** Compare detected icons by size and position patterns
- **Rationale:**
  - Cannot see actual icon SVG content
  - Size consistency is measurable from bounding boxes
  - Position patterns suggest icon usage (nav, actions, etc.)

### Theme Detection
- **Decision:** Analyze color palette for dark/light mode indicators
- **Rationale:**
  - Dark backgrounds suggest dark mode
  - Can compare contrast ratios against theme expectations
  - Single screenshot limits full theme comparison

---

## File Structure

```
src/
└── audit/
    └── dimensions/
        ├── iconography.py          # Iconography auditor
        ├── empty_states.py         # Empty states auditor
        ├── loading_states.py       # Loading states auditor
        ├── error_states.py         # Error states auditor
        ├── theming.py              # Dark mode/theming auditor
        └── accessibility.py        # Accessibility auditor
tests/
└── unit/
    └── test_dimensions/
        ├── test_iconography.py
        ├── test_empty_states.py
        ├── test_loading_states.py
        ├── test_error_states.py
        ├── test_theming.py
        └── test_accessibility.py
```

---

## Tasks

### Phase 1: Iconography Dimension
- [ ] Create `src/audit/dimensions/iconography.py`
- [ ] Implement `IconographyAuditor` class
- [ ] Detect icon components from M2 results
- [ ] Check size consistency across icons
- [ ] Check position patterns for icon usage
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 2: Empty States Dimension
- [ ] Create `src/audit/dimensions/empty_states.py`
- [ ] Implement `EmptyStatesAuditor` class
- [ ] Detect low component count screens
- [ ] Check for intentional empty state design
- [ ] Check for guidance toward first action
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 3: Loading States Dimension
- [ ] Create `src/audit/dimensions/loading_states.py`
- [ ] Implement `LoadingStatesAuditor` class
- [ ] Detect loading indicators (spinners, progress)
- [ ] Check loading state consistency
- [ ] Check for skeleton screen patterns
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 4: Error States Dimension
- [ ] Create `src/audit/dimensions/error_states.py`
- [ ] Implement `ErrorStatesAuditor` class
- [ ] Detect error-related components
- [ ] Check error message styling
- [ ] Check error text clarity
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 5: Dark Mode / Theming Dimension
- [ ] Create `src/audit/dimensions/theming.py`
- [ ] Implement `ThemingAuditor` class
- [ ] Detect dark/light mode from color palette
- [ ] Check contrast ratios for theme
- [ ] Check if theme is designed (not inverted)
- [ ] Generate findings with standards references
- [ ] Write unit tests

### Phase 6: Accessibility Dimension
- [ ] Create `src/audit/dimensions/accessibility.py`
- [ ] Implement `AccessibilityAuditor` class
- [ ] Calculate contrast ratios using M2 color data
- [ ] Check minimum text size requirements
- [ ] Check interactive element visibility
- [ ] Generate WCAG-linked findings
- [ ] Write unit tests

### Phase 7: Integration & Testing
- [ ] Register all 6 dimensions with orchestrator
- [ ] Create integration tests with validation dataset
- [ ] Test full audit with all 13 dimensions (7 from M3-3 + 6 from M3-4)
- [ ] Verify accessibility findings against WCAG criteria
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] All 6 state/accessibility dimensions implemented and registered
- [ ] Iconography analysis detects size inconsistencies
- [ ] Empty state analysis identifies potential issues
- [ ] Loading state analysis catches common patterns
- [ ] Error state analysis finds styling issues
- [ ] Theme analysis validates contrast across modes
- [ ] Accessibility analysis produces WCAG-linked findings
- [ ] All findings include proper severity classification
- [ ] Unit test coverage > 90% for all dimensions
- [ ] No regressions in existing test suite
- [ ] Full audit runs with all 13 dimensions

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| State detection unreliable | Use multiple heuristics; flag low-confidence findings |
| Accessibility incomplete | Document DOM limitation; focus on what's detectable |
| Theme detection false positives | Require explicit theme flag or comparison screenshot |
| Icon analysis limited | Focus on size/position; document content limitation |
| Motion/Responsiveness deferred | Document in milestones; schedule for future |

---

## Validation

Run after completion:
```bash
# Run dimension tests
python -m pytest tests/unit/test_dimensions/ -v

# Test accessibility auditor
python -c "
from src.audit.dimensions.accessibility import AccessibilityAuditor

auditor = AccessibilityAuditor()
# Test contrast calculation
# Test WCAG reference linking
"

# Test full audit with all 13 dimensions
python -c "
from src.audit.orchestrator import AuditOrchestrator
from src.audit.dimensions import register_all_dimensions

orchestrator = AuditOrchestrator()
register_all_dimensions(orchestrator)
print(f'Registered {len(orchestrator.dimensions)} dimensions')

# Should show 13: 7 visual + 6 state/accessibility
"

# Validate accessibility against known issues
python -c "
from src.audit.orchestrator import AuditOrchestrator
from src.audit.dimensions import register_all_dimensions

orchestrator = AuditOrchestrator()
register_all_dimensions(orchestrator)

# Run on screenshot with known contrast issue
# Verify finding is generated with WCAG reference
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
- M3-3 visual dimensions (for complete audit)
- Design system files for standards references
- WCAG criteria definitions

---

## Accessibility Limitations

This epic implements screenshot-based accessibility analysis. The following require DOM access and are out of scope:

| Capability | Requires | Future Integration |
|------------|----------|-------------------|
| ARIA label validation | DOM tree | Browser extension or DOM dump |
| Keyboard navigation | Focus state | Interactive session capture |
| Screen reader flow | Semantic HTML | DOM analysis |
| Tab order | Focusable elements | Interactive session |

Current accessibility scope focuses on:
- ✅ Color contrast ratios (WCAG 1.4.3)
- ✅ Minimum text size detection
- ✅ Interactive element visibility
- ✅ Component type semantic hints

---

*Created: 2026-03-02*
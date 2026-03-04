# Epic M4-3: Design System Proposals

> **Milestone:** 4 - Plan Generation  
> **Priority:** High  
> **Dependencies:** Epic M4-2 (Implementation Formatter)  
> **Status:** 🔲 Not Started

---

## Objective

Build the design system proposal generator that analyzes audit patterns to recommend token additions, component variants, and design system evolution opportunities.

---

## Scope

### In Scope
- Design system proposal Pydantic models
- Token proposal generation (new colors, spacing, typography)
- Component variant proposals (new sizes, states)
- Before/after text descriptions for proposals
- Proposal prioritization (impact vs. effort)
- Integration with existing design system files

### Out of Scope
- Report generation (M4-4)
- Plan persistence (M4-4)
- Visual before/after images
- Automatic design system file updates (human approval required)

---

## Deliverables

### 1. Proposal Models (`src/plan/proposal_models.py`)

Pydantic models for proposals:
- `ProposalType` — Enum (NEW_TOKEN, TOKEN_VARIANT, COMPONENT_VARIANT, STANDARD_UPDATE)
- `TokenProposal` — {token_name, token_type, proposed_value, rationale, usage_count}
- `ComponentProposal` — {component_type, variant_name, properties, rationale}
- `DesignSystemProposal` — {id, proposals, priority, impact_score, created_at}
- `BeforeAfterDescription` — {before_text, after_text, key_changes}

### 2. Token Analyzer (`src/plan/token_analyzer.py`)

Token pattern analysis:
- `TokenAnalyzer` — Analyzes token usage patterns
- `analyze_color_patterns(findings: list[AuditFinding]) -> list[TokenProposal]`
- `analyze_spacing_patterns(findings: list[AuditFinding]) -> list[TokenProposal]`
- `analyze_typography_patterns(findings: list[AuditFinding]) -> list[TokenProposal]`
- `detect_missing_tokens(detected_tokens: list, design_tokens: dict) -> list[str]`
- `calculate_usage_frequency(token_value: str, screens: list) -> int`

### 3. Proposal Generator (`src/plan/proposals.py`)

Main proposal generation:
- `ProposalGenerator` — Main generator class
- `generate_proposals(plan: Plan, audit_result: AuditResult) -> DesignSystemProposal`
- `create_token_proposal(pattern: dict) -> TokenProposal`
- `create_component_proposal(findings: list[AuditFinding]) -> ComponentProposal`
- `prioritize_proposals(proposals: list) -> list` — Sort by impact/effort
- `calculate_impact_score(proposal) -> float`

### 4. Before/After Generator (`src/plan/comparison.py`)

Text descriptions for changes:
- `BeforeAfterGenerator` — Generates before/after descriptions
- `generate_token_comparison(proposal: TokenProposal) -> BeforeAfterDescription`
- `generate_component_comparison(proposal: ComponentProposal) -> BeforeAfterDescription`
- `generate_summary_comparison(proposal: DesignSystemProposal) -> str`
- Format: "Currently: X. Proposed: Y. Benefit: Z."

---

## Technical Decisions

### Token Proposal Strategy
- **Decision:** Propose tokens when usage frequency > threshold (3+ occurrences)
- **Rationale:**
  - Avoids one-off tokens that bloat the system
  - Focuses on patterns that benefit from standardization
  - Aligns with design system best practices

**Token Naming Convention:**
- Colors: `--color-{semantic}-{variant}` (e.g., `--color-warning-light`)
- Spacing: `--spacing-{size}` (e.g., `--spacing-xs`, `--spacing-xl`)
- Typography: `--font-{property}-{size}` (e.g., `--font-size-caption`)

### Component Variant Detection
- **Decision:** Detect variants when same component type has inconsistent properties
- **Rationale:**
  - Inconsistency suggests missing variant definition
  - Variants formalize existing patterns
  - Reduces future drift

**Example Detection:**
- Multiple button sizes detected → propose `button-sm`, `button-lg` variants
- Multiple card styles detected → propose `card-elevated`, `card-outlined` variants

### Impact Scoring
- **Decision:** Score based on (affected_screens × severity_weight × consistency_gain)
- **Rationale:**
  - Quantifiable prioritization
  - Balances quick wins vs. systemic improvements
  - Explainable to stakeholders

**Formula:**
```
impact_score = (affected_screens / total_screens) * severity_weight * consistency_factor
```

---

## File Structure

```
src/
└── plan/
    ├── __init__.py           # Updated exports
    ├── proposal_models.py    # Proposal Pydantic models
    ├── token_analyzer.py     # Token pattern analysis
    ├── proposals.py          # Main proposal generator
    └── comparison.py         # Before/after descriptions
design_system/
├── tokens.md                 # Existing tokens (read-only)
├── components.md             # Existing components (read-only)
└── standards.md              # Existing standards (read-only)
tests/
└── unit/
    ├── test_proposal_models.py
    ├── test_token_analyzer.py
    ├── test_proposals.py
    └── test_comparison.py
```

---

## Tasks

### Phase 1: Proposal Models
- [ ] Create `src/plan/proposal_models.py`
- [ ] Define `ProposalType` enum
- [ ] Define `TokenProposal` model with all fields
- [ ] Define `ComponentProposal` model with all fields
- [ ] Define `DesignSystemProposal` aggregate model
- [ ] Define `BeforeAfterDescription` model
- [ ] Add `to_markdown()` method to proposals
- [ ] Write unit tests for models

### Phase 2: Token Analyzer
- [ ] Create `src/plan/token_analyzer.py`
- [ ] Implement `TokenAnalyzer` class
- [ ] Implement `analyze_color_patterns()` method
- [ ] Implement `analyze_spacing_patterns()` method
- [ ] Implement `analyze_typography_patterns()` method
- [ ] Implement `detect_missing_tokens()` method
- [ ] Implement `calculate_usage_frequency()` method
- [ ] Write unit tests for analyzer

### Phase 3: Proposal Generator
- [ ] Create `src/plan/proposals.py`
- [ ] Implement `ProposalGenerator` class
- [ ] Implement `create_token_proposal()` method
- [ ] Implement `create_component_proposal()` method
- [ ] Implement `prioritize_proposals()` method
- [ ] Implement `calculate_impact_score()` method
- [ ] Implement `generate_proposals()` main method
- [ ] Write unit tests for generator

### Phase 4: Before/After Generator
- [ ] Create `src/plan/comparison.py`
- [ ] Implement `BeforeAfterGenerator` class
- [ ] Implement `generate_token_comparison()` method
- [ ] Implement `generate_component_comparison()` method
- [ ] Implement `generate_summary_comparison()` method
- [ ] Add `to_markdown()` rendering
- [ ] Write unit tests for comparison generator

### Phase 5: Integration
- [ ] Update `src/plan/__init__.py` with new exports
- [ ] Load existing design tokens from `design_system/tokens.md`
- [ ] Create integration tests with M4-2 formatter
- [ ] Test with M3-1 validation dataset
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Proposal models validate correctly with all fields
- [ ] Token analyzer detects patterns across multiple screens
- [ ] Proposal generator creates actionable recommendations
- [ ] Before/after descriptions clearly communicate changes
- [ ] Proposals are prioritized by impact score
- [ ] Unit test coverage > 90% for proposal module
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Too many low-value proposals | Set usage frequency threshold; filter by impact |
| Token names conflict with existing | Check existing tokens before proposing |
| Proposals too vague | Require specific values in proposal model |
| Component variants proliferate | Limit variants per component type |

---

## Validation

Run after completion:
```bash
# Run proposal module tests
python -m pytest tests/unit/test_proposal*.py tests/unit/test_token*.py tests/unit/test_comparison*.py -v

# Test token analyzer
python -c "
from src.plan.token_analyzer import TokenAnalyzer

analyzer = TokenAnalyzer()
# Would analyze findings for patterns
print('Token analyzer ready')
"

# Test proposal generator
python -c "
from src.plan.proposals import ProposalGenerator

generator = ProposalGenerator()
# Would generate proposals from audit results
print('Proposal generator ready')
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- All M4-2 dependencies
- No new dependencies required

### System Dependencies
- Design system files (`design_system/*.md`)
- M3 audit findings with token data

---

*Created: 2026-03-04*
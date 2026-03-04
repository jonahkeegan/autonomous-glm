# Epic M4-2: Implementation Instruction Formatter

> **Milestone:** 4 - Plan Generation  
> **Priority:** Critical  
> **Dependencies:** Epic M4-1 (Phased Plan Synthesis)  
> **Status:** 🔲 Not Started

---

## Objective

Build the implementation instruction formatter that transforms audit findings into executable, unambiguous instructions in the format: "In file X, component Y, property Z: change from 'old' to 'new'".

---

## Scope

### In Scope
- Instruction Pydantic models (ImplementationInstruction, PropertyChange)
- Simple string template system for instruction formatting
- Template registry by issue type (spacing, color, typography, etc.)
- Instruction validator for completeness (no missing fields)
- File/component mapping using stored screen hierarchy data
- Rationale and standards reference inclusion

### Out of Scope
- Design system proposals (M4-3)
- Report generation (M4-4)
- Actual code implementation (Minimax's role)
- Visual before/after images

---

## Deliverables

### 1. Instruction Models (`src/plan/instruction_models.py`)

Pydantic models for instructions:
- `PropertyChange` — {property_name, old_value, new_value}
- `ImplementationInstruction` — {id, finding_id, file_path, component_id, component_type, changes, rationale, standards_refs}
- `InstructionTemplate` — Template with placeholders for instruction generation
- `InstructionResult` — {instruction, is_valid, validation_errors}

### 2. Template System (`src/plan/templates.py`)

Simple string templates:
- `InstructionTemplateRegistry` — Registry of templates by issue type
- `get_template(issue_type: str) -> InstructionTemplate`
- `render_template(template: InstructionTemplate, context: dict) -> str`
- Templates for common issue types:
  - `spacing_issue` — "Adjust {property} from {old} to {new}"
  - `color_contrast` — "Change {element} color from {old} to {new} for {ratio}:1 contrast"
  - `typography_issue` — "Update {property} from {old} to {new}"
  - `alignment_issue` — "Align {element} to {grid} grid"
  - `hierarchy_issue` — "Increase {element} visual weight"

### 3. Instruction Formatter (`src/plan/formatter.py`)

Main formatting logic:
- `InstructionFormatter` — Main formatter class
- `format_instruction(finding: AuditFinding, screen: Screen) -> ImplementationInstruction`
- `map_to_component(finding: AuditFinding, hierarchy: dict) -> ComponentInfo`
- `determine_file_path(screen: Screen) -> str`
- `generate_changes(finding: AuditFinding) -> list[PropertyChange]`
- `format_all(plan: Plan, screens: dict[str, Screen]) -> list[ImplementationInstruction]`

### 4. Instruction Validator (`src/plan/validator.py`)

Completeness validation:
- `InstructionValidator` — Validates instruction completeness
- `validate(instruction: ImplementationInstruction) -> ValidationResult`
- `check_required_fields(instruction: ImplementationInstruction) -> list[str]`
- `check_values_populated(instruction: ImplementationInstruction) -> list[str]`
- Required fields: file_path, component_id, at least one PropertyChange

---

## Technical Decisions

### Template Approach
- **Decision:** Simple string templates with `.format()` substitution
- **Rationale:**
  - Minimal dependency overhead (no Jinja2)
  - Sufficient for static instruction generation
  - Easy to validate and test
  - Clear placeholder syntax: `{property}`, `{old}`, `{new}`

### File/Component Mapping
- **Decision:** Use stored screen hierarchy + bounding boxes from M2
- **Rationale:**
  - Already have component detection data
  - Bounding boxes map to specific UI elements
  - Hierarchy provides component relationships

**Mapping Strategy:**
1. Finding includes entity_id pointing to Component
2. Component has bounding_box and type
3. Screen has hierarchy with component IDs
4. File path inferred from screen metadata (if available) or placeholder

### Instruction Format
- **Decision:** Structured Pydantic model with exact format requirements
- **Rationale:**
  - Enforces completeness at model level
  - Easy to render to any output format
  - Validation before persistence

**Required Format:**
```
In {file_path}, component {component_id} ({component_type}):
  - {property_1}: change from '{old_value}' to '{new_value}'
  - {property_2}: change from '{old_value}' to '{new_value}'
  
Rationale: {rationale}
Standards: {standards_refs}
```

---

## File Structure

```
src/
└── plan/
    ├── __init__.py           # Updated exports
    ├── instruction_models.py # Instruction Pydantic models
    ├── templates.py          # Template registry and rendering
    ├── formatter.py          # Main instruction formatter
    └── validator.py          # Instruction validation
tests/
└── unit/
    ├── test_instruction_models.py
    ├── test_templates.py
    ├── test_formatter.py
    └── test_validator.py
```

---

## Tasks

### Phase 1: Instruction Models
- [ ] Create `src/plan/instruction_models.py`
- [ ] Define `PropertyChange` model with old/new values
- [ ] Define `ImplementationInstruction` model with all fields
- [ ] Define `InstructionTemplate` model
- [ ] Define `InstructionResult` model
- [ ] Add `to_markdown()` method to ImplementationInstruction
- [ ] Add `to_json()` method to ImplementationInstruction
- [ ] Write unit tests for models

### Phase 2: Template System
- [ ] Create `src/plan/templates.py`
- [ ] Implement `InstructionTemplate` class with placeholders
- [ ] Implement `InstructionTemplateRegistry` class
- [ ] Create templates for spacing issues
- [ ] Create templates for color/contrast issues
- [ ] Create templates for typography issues
- [ ] Create templates for alignment issues
- [ ] Create templates for hierarchy issues
- [ ] Create templates for accessibility issues
- [ ] Implement `render_template()` with validation
- [ ] Write unit tests for templates

### Phase 3: Instruction Formatter
- [ ] Create `src/plan/formatter.py`
- [ ] Implement `InstructionFormatter` class
- [ ] Implement `map_to_component()` using hierarchy data
- [ ] Implement `determine_file_path()` with fallback
- [ ] Implement `generate_changes()` from finding metadata
- [ ] Implement `format_instruction()` main method
- [ ] Implement `format_all()` for batch processing
- [ ] Write unit tests with mock findings

### Phase 4: Instruction Validator
- [ ] Create `src/plan/validator.py`
- [ ] Implement `InstructionValidator` class
- [ ] Implement `check_required_fields()` validation
- [ ] Implement `check_values_populated()` validation
- [ ] Implement `validate()` main method
- [ ] Add validation to formatter pipeline
- [ ] Write unit tests for validator

### Phase 5: Integration
- [ ] Update `src/plan/__init__.py` with new exports
- [ ] Create integration tests with M4-1 plan synthesizer
- [ ] Test with M3-1 validation dataset
- [ ] Add `instruction_templates:` to `config/default.yaml`
- [ ] Run full test suite (ensure no regressions)

---

## Success Criteria

- [ ] Instruction models validate correctly with all fields
- [ ] Templates render correctly for all issue types
- [ ] Formatter produces valid instructions from findings
- [ ] Validator catches missing/incomplete fields
- [ ] Instructions include rationale and standards references
- [ ] Unit test coverage > 90% for formatter module
- [ ] No regressions in existing test suite

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| File path unknown | Use placeholder with clear annotation; require manual mapping |
| Component mapping ambiguous | Log warning; use best match by bounding box |
| Template doesn't fit issue | Fallback to generic template; flag for review |
| Old value unknown | Mark as "REQUIRES_INSPECTION"; don't guess |

---

## Validation

Run after completion:
```bash
# Run formatter module tests
python -m pytest tests/unit/test_instruction*.py tests/unit/test_formatter*.py tests/unit/test_templates*.py tests/unit/test_validator.py -v

# Test template rendering
python -c "
from src.plan.templates import InstructionTemplateRegistry

registry = InstructionTemplateRegistry()
template = registry.get_template('spacing_issue')
result = template.render(
    property='margin-top',
    old='12px',
    new='16px'
)
print(f'Rendered: {result}')
"

# Test instruction formatting
python -c "
from src.plan.formatter import InstructionFormatter
from src.audit.models import AuditFindingCreate, AuditDimension
from src.db.models import Severity, EntityType

formatter = InstructionFormatter()
# Mock finding would be created here
print('Formatter ready')
"

# Run full test suite
python -m pytest tests/ -v
```

---

## Dependencies

### Python Dependencies
- All M4-1 dependencies
- No new dependencies required

### System Dependencies
- M2 component detection data (hierarchy, bounding boxes)
- M3 audit findings

---

*Created: 2026-03-04*
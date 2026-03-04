# Task Completion Report: Epic M4-2 Implementation Instruction Formatter

**Date:** 2026-03-04
**Epic:** M4-2 Implementation Instruction Formatter
**Milestone:** M4 - Plan Generation
**Status:** ✅ Completed

---

## Summary

Successfully implemented the Implementation Instruction Formatter system that transforms audit findings into executable, unambiguous implementation instructions in the format: "In file X, component Y, property Z: change from 'old' to 'new'".

---

## Deliverables Completed

### 1. Instruction Models (`src/plan/instruction_models.py`)
- ✅ `PropertyChange` model with property_name, old_value, new_value, requires_inspection flag
- ✅ `ComponentInfo` model with component_id, component_type, bounding_box, selector
- ✅ `ImplementationInstruction` model with all required fields
- ✅ `InstructionTemplate` model with placeholder validation
- ✅ `ValidationResult` and `InstructionResult` models
- ✅ `BatchInstructionResult` for batch processing
- ✅ `IssueType` enum with dimension mapping
- ✅ `to_markdown()` and `to_json_dict()` output methods

### 2. Template System (`src/plan/templates.py`)
- ✅ `InstructionTemplateRegistry` class with built-in templates
- ✅ Templates for all issue types:
  - spacing, color_contrast, typography, alignment, hierarchy
  - accessibility, density, consistency, visual_balance, generic
- ✅ `render_for_issue()` method with context defaults
- ✅ `get_best_template()` with fallback logic
- ✅ Default registry singleton with reset capability

### 3. Instruction Formatter (`src/plan/formatter.py`)
- ✅ `InstructionFormatter` class with screen metadata and component registry
- ✅ `map_to_component()` using hierarchy/registry data
- ✅ `determine_file_path()` with screen_id and metadata fallbacks
- ✅ `generate_changes()` from finding metadata with issue-type-specific defaults
- ✅ `format_instruction()` main method
- ✅ `format_all()` for batch processing
- ✅ Convenience functions: `format_finding()`, `format_findings()`

### 4. Instruction Validator (`src/plan/validator.py`)
- ✅ `InstructionValidator` class with configurable options
- ✅ `validate()` method with error/warning collection
- ✅ Strict mode (converts warnings to errors)
- ✅ Confidence threshold validation
- ✅ Placeholder path handling
- ✅ Convenience functions: `validate_instruction()`, `is_valid_instruction()`, `get_validation_errors()`

---

## Test Results

**All 102 unit tests pass:**

| Test File | Tests | Status |
|-----------|-------|--------|
| test_instruction_models.py | 28 | ✅ Pass |
| test_templates.py | 24 | ✅ Pass |
| test_formatter.py | 24 | ✅ Pass |
| test_validator.py | 26 | ✅ Pass |
| **Total** | **102** | ✅ **Pass** |

```
============================= 102 passed in 0.09s ==============================
```

---

## Acceptance Criteria Status

| Criteria | Status |
|----------|--------|
| AC1: Instruction models with all required fields and output formats | ✅ Complete |
| AC2: Template registry with built-in templates for all issue types | ✅ Complete |
| AC3: Formatter that converts AuditFindings to ImplementationInstructions | ✅ Complete |
| AC4: Validator with strict mode and confidence thresholds | ✅ Complete |
| AC5: Output formats: Markdown and JSON | ✅ Complete |

---

## Exit Criteria Status

| Criteria | Status |
|----------|--------|
| EC1: All instruction models have comprehensive unit tests | ✅ Complete |
| EC2: Template registry has tests for all built-in templates | ✅ Complete |
| EC3: Formatter has tests for all conversion scenarios | ✅ Complete |
| EC4: Validator has tests for all validation modes | ✅ Complete |
| EC5: All tests pass | ✅ Complete (102/102) |

---

## Technical Decisions Made

1. **Pydantic Validation**: Models use Pydantic's `min_length=1` for required string fields, providing validation at model creation time before our validator runs.

2. **Template Approach**: Simple string templates with `.format()` substitution - no Jinja2 dependency needed.

3. **Issue Type Mapping**: `IssueType.from_dimension()` provides automatic mapping from audit dimensions to issue types.

4. **Placeholder Path Handling**: When file path is unknown, uses `UNKNOWN_FILE` with `is_placeholder_path=True` flag.

5. **REQUIRES_INSPECTION**: Special marker value for properties that need human review.

---

## Files Created

```
src/plan/
├── instruction_models.py   (new - 280+ lines)
├── templates.py            (new - 250+ lines)
├── formatter.py            (new - 200+ lines)
└── validator.py            (new - 180+ lines)

tests/unit/
├── test_instruction_models.py  (new - 28 tests)
├── test_templates.py           (new - 24 tests)
├── test_formatter.py           (new - 24 tests)
└── test_validator.py           (new - 26 tests)
```

---

## Integration Notes

- Updated `src/plan/__init__.py` with all new exports
- All new modules follow existing project patterns
- No breaking changes to existing code
- No new external dependencies required

---

## Risks Mitigated

| Risk | Mitigation Implemented |
|------|------------------------|
| File path unknown | Placeholder path with `is_placeholder_path=True` flag and warning |
| Component mapping ambiguous | Falls back to entity_type from finding |
| Template doesn't fit issue | Generic template fallback |
| Old value unknown | `REQUIRES_INSPECTION` marker with validator warning |

---

## Next Steps

1. **M4-3 Design System Proposals** - Use formatted instructions to propose design system updates
2. **M4-4 Reports Persistence** - Persist formatted instructions to database
3. **Integration with M4-1** - Full pipeline testing with phased plan synthesizer

---

## Validation Commands

```bash
# Run M4-2 specific tests
source .venv/bin/activate && python -m pytest tests/unit/test_instruction_models.py tests/unit/test_templates.py tests/unit/test_formatter.py tests/unit/test_validator.py -v

# Quick validation
python -c "
from src.plan.formatter import InstructionFormatter
from src.plan.templates import InstructionTemplateRegistry
from src.plan.validator import InstructionValidator

print('Formatter:', InstructionFormatter)
print('Registry:', InstructionTemplateRegistry)
print('Validator:', InstructionValidator)
print('All modules imported successfully!')
"
```

---

*Report generated: 2026-03-04*
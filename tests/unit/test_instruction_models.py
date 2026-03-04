"""
Unit tests for instruction models (M4-2).

Tests for PropertyChange, ComponentInfo, ImplementationInstruction,
InstructionTemplate, and related models.
"""

import pytest
from datetime import datetime

from src.plan.instruction_models import (
    IssueType,
    PropertyChange,
    ComponentInfo,
    ImplementationInstruction,
    InstructionTemplate,
    ValidationResult,
    InstructionResult,
    BatchInstructionResult,
)
from src.audit.models import AuditDimension, StandardsReference, WCAGReference
from src.db.models import Severity


# =============================================================================
# ISSUE TYPE TESTS
# =============================================================================

class TestIssueType:
    """Tests for IssueType enum."""
    
    def test_from_dimension_spacing(self):
        """Test mapping SPACING_RHYTHM dimension."""
        issue_type = IssueType.from_dimension(AuditDimension.SPACING_RHYTHM)
        assert issue_type == IssueType.SPACING
    
    def test_from_dimension_color(self):
        """Test mapping COLOR dimension."""
        issue_type = IssueType.from_dimension(AuditDimension.COLOR)
        assert issue_type == IssueType.COLOR_CONTRAST
    
    def test_from_dimension_accessibility(self):
        """Test mapping ACCESSIBILITY dimension."""
        issue_type = IssueType.from_dimension(AuditDimension.ACCESSIBILITY)
        assert issue_type == IssueType.ACCESSIBILITY
    
    def test_from_dimension_all_mapped(self):
        """Test all active dimensions have mappings."""
        for dimension in AuditDimension.all_active():
            issue_type = IssueType.from_dimension(dimension)
            assert isinstance(issue_type, IssueType)


# =============================================================================
# PROPERTY CHANGE TESTS
# =============================================================================

class TestPropertyChange:
    """Tests for PropertyChange model."""
    
    def test_create_basic(self):
        """Test creating a basic property change."""
        change = PropertyChange(
            property_name="margin-top",
            old_value="12px",
            new_value="16px",
        )
        assert change.property_name == "margin-top"
        assert change.old_value == "12px"
        assert change.new_value == "16px"
        assert change.confidence == 1.0
        assert not change.requires_inspection
    
    def test_create_with_inspection_required(self):
        """Test creating a change that requires inspection."""
        change = PropertyChange(
            property_name="color",
            old_value=None,
            new_value="var(--color-primary)",
            requires_inspection=True,
        )
        assert change.old_value is None
        assert change.requires_inspection
    
    def test_to_markdown_with_old_value(self):
        """Test markdown rendering with old value."""
        change = PropertyChange(
            property_name="font-size",
            old_value="14px",
            new_value="16px",
        )
        md = change.to_markdown()
        assert "font-size" in md
        assert "'14px'" in md
        assert "'16px'" in md
        assert "change from" in md
    
    def test_to_markdown_without_old_value(self):
        """Test markdown rendering without old value."""
        change = PropertyChange(
            property_name="color",
            old_value=None,
            new_value="#000000",
            requires_inspection=True,
        )
        md = change.to_markdown()
        assert "set to" in md
        assert "requires inspection" in md
    
    def test_to_json_dict(self):
        """Test JSON dict rendering."""
        change = PropertyChange(
            property_name="padding",
            old_value="8px",
            new_value="16px",
            confidence=0.9,
        )
        d = change.to_json_dict()
        assert d["property"] == "padding"
        assert d["old"] == "8px"
        assert d["new"] == "16px"
        assert d["confidence"] == 0.9


# =============================================================================
# COMPONENT INFO TESTS
# =============================================================================

class TestComponentInfo:
    """Tests for ComponentInfo model."""
    
    def test_create_basic(self):
        """Test creating basic component info."""
        info = ComponentInfo(
            component_id="btn-submit",
            component_type="button",
        )
        assert info.component_id == "btn-submit"
        assert info.component_type == "button"
        assert info.bounding_box is None
        assert info.selector is None
    
    def test_create_with_all_fields(self):
        """Test creating component info with all fields."""
        info = ComponentInfo(
            component_id="input-email",
            component_type="input",
            bounding_box=(0.1, 0.2, 0.5, 0.3),
            selector="#email-input",
        )
        assert info.bounding_box == (0.1, 0.2, 0.5, 0.3)
        assert info.selector == "#email-input"


# =============================================================================
# IMPLEMENTATION INSTRUCTION TESTS
# =============================================================================

class TestImplementationInstruction:
    """Tests for ImplementationInstruction model."""
    
    @pytest.fixture
    def sample_instruction(self):
        """Create a sample instruction for testing."""
        return ImplementationInstruction(
            finding_id="finding-123",
            file_path="components/Button.tsx",
            component=ComponentInfo(
                component_id="btn-primary",
                component_type="button",
            ),
            changes=[
                PropertyChange(
                    property_name="background-color",
                    old_value="#ff0000",
                    new_value="var(--color-primary)",
                ),
            ],
            rationale="Improve color consistency",
            dimension=AuditDimension.COLOR,
            severity=Severity.HIGH,
            issue_type=IssueType.COLOR_CONTRAST,
        )
    
    def test_create_basic(self, sample_instruction):
        """Test basic instruction creation."""
        assert sample_instruction.finding_id == "finding-123"
        assert sample_instruction.file_path == "components/Button.tsx"
        assert sample_instruction.change_count == 1
        assert sample_instruction.confidence == 1.0
    
    def test_change_count(self, sample_instruction):
        """Test change_count property."""
        assert sample_instruction.change_count == 1
        
        # Add another change
        instruction2 = ImplementationInstruction(
            **{
                **sample_instruction.model_dump(),
                "changes": [
                    PropertyChange(property_name="p1", new_value="v1"),
                    PropertyChange(property_name="p2", new_value="v2"),
                ]
            }
        )
        assert instruction2.change_count == 2
    
    def test_has_standards_refs_false(self, sample_instruction):
        """Test has_standards_refs when empty."""
        assert not sample_instruction.has_standards_refs
    
    def test_has_standards_refs_true(self, sample_instruction):
        """Test has_standards_refs when populated."""
        instruction = ImplementationInstruction(
            **{
                **sample_instruction.model_dump(),
                "standards_refs": [
                    StandardsReference(
                        wcag=WCAGReference(
                            criterion="1.4.3",
                            name="Contrast (Minimum)",
                            level="AA",
                        )
                    )
                ]
            }
        )
        assert instruction.has_standards_refs
    
    def test_to_markdown(self, sample_instruction):
        """Test markdown rendering."""
        md = sample_instruction.to_markdown()
        assert "components/Button.tsx" in md
        assert "btn-primary" in md
        assert "button" in md
        assert "background-color" in md
        assert "#ff0000" in md
        assert "var(--color-primary)" in md
        assert "Improve color consistency" in md
    
    def test_to_markdown_with_flags(self, sample_instruction):
        """Test markdown rendering with flags."""
        instruction = ImplementationInstruction(
            **{
                **sample_instruction.model_dump(),
                "requires_manual_review": True,
                "is_placeholder_path": True,
            }
        )
        md = instruction.to_markdown()
        assert "requires manual review" in md
        assert "placeholder path" in md
    
    def test_to_json_dict(self, sample_instruction):
        """Test JSON dict rendering."""
        d = sample_instruction.to_json_dict()
        assert d["finding_id"] == "finding-123"
        assert d["file_path"] == "components/Button.tsx"
        assert d["dimension"] == "color"
        assert d["severity"] == "high"
        assert len(d["changes"]) == 1
    
    def test_changes_validator_empty(self, sample_instruction):
        """Test that empty changes raises error."""
        with pytest.raises(ValueError):
            ImplementationInstruction(
                **{**sample_instruction.model_dump(), "changes": []}
            )


# =============================================================================
# INSTRUCTION TEMPLATE TESTS
# =============================================================================

class TestInstructionTemplate:
    """Tests for InstructionTemplate model."""
    
    def test_create_template(self):
        """Test creating a template."""
        template = InstructionTemplate(
            name="test_template",
            issue_type=IssueType.SPACING,
            template="Change {property} from {old} to {new}",
            placeholders=["property", "old", "new"],
        )
        assert template.name == "test_template"
        assert len(template.placeholders) == 3
    
    def test_render_success(self):
        """Test successful template rendering."""
        template = InstructionTemplate(
            name="test",
            issue_type=IssueType.GENERIC,
            template="{element}: {action}",
            placeholders=["element", "action"],
        )
        result = template.render(element="Button", action="increase size")
        assert result == "Button: increase size"
    
    def test_render_missing_placeholder(self):
        """Test rendering with missing placeholder."""
        template = InstructionTemplate(
            name="test",
            issue_type=IssueType.GENERIC,
            template="{a} and {b}",
            placeholders=["a", "b"],
        )
        with pytest.raises(ValueError) as exc_info:
            template.render(a="value")
        assert "b" in str(exc_info.value)
    
    def test_validate_context_valid(self):
        """Test context validation with all placeholders."""
        template = InstructionTemplate(
            name="test",
            issue_type=IssueType.GENERIC,
            template="{x} {y}",
            placeholders=["x", "y"],
        )
        missing = template.validate_context({"x": 1, "y": 2})
        assert missing == []
    
    def test_validate_context_missing(self):
        """Test context validation with missing placeholders."""
        template = InstructionTemplate(
            name="test",
            issue_type=IssueType.GENERIC,
            template="{x} {y} {z}",
            placeholders=["x", "y", "z"],
        )
        missing = template.validate_context({"x": 1})
        assert set(missing) == {"y", "z"}


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================

class TestValidationResult:
    """Tests for ValidationResult model."""
    
    def test_valid_result(self):
        """Test valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
    
    def test_invalid_result_with_errors(self):
        """Test invalid result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Missing field: file_path", "Empty changes"],
        )
        assert not result.is_valid
        assert len(result.errors) == 2


# =============================================================================
# INSTRUCTION RESULT TESTS
# =============================================================================

class TestInstructionResult:
    """Tests for InstructionResult model."""
    
    @pytest.fixture
    def valid_result(self):
        """Create a valid instruction result."""
        instruction = ImplementationInstruction(
            finding_id="f1",
            file_path="test.tsx",
            component=ComponentInfo(component_id="c1", component_type="button"),
            changes=[PropertyChange(property_name="color", new_value="red")],
            rationale="Test",
            dimension=AuditDimension.COLOR,
            issue_type=IssueType.COLOR_CONTRAST,
        )
        return InstructionResult(
            instruction=instruction,
            validation=ValidationResult(is_valid=True),
            original_finding_id="f1",
        )
    
    def test_is_valid_true(self, valid_result):
        """Test is_valid property when valid."""
        assert valid_result.is_valid
    
    def test_is_valid_false_no_instruction(self):
        """Test is_valid when instruction is None."""
        result = InstructionResult(
            instruction=None,
            validation=ValidationResult(is_valid=False, errors=["Error"]),
            original_finding_id="f1",
        )
        assert not result.is_valid
    
    def test_error_message(self):
        """Test error_message property."""
        result = InstructionResult(
            instruction=None,
            validation=ValidationResult(
                is_valid=False,
                errors=["Error 1", "Error 2"],
            ),
            original_finding_id="f1",
        )
        assert result.error_message == "Error 1; Error 2"
    
    def test_error_message_none_when_valid(self, valid_result):
        """Test error_message is None when valid."""
        assert valid_result.error_message is None


# =============================================================================
# BATCH RESULT TESTS
# =============================================================================

class TestBatchInstructionResult:
    """Tests for BatchInstructionResult model."""
    
    def test_empty_batch(self):
        """Test empty batch result."""
        batch = BatchInstructionResult()
        assert batch.total_findings == 0
        assert batch.valid_count == 0
        assert batch.invalid_count == 0
        assert batch.success_rate == 0.0
        assert batch.instructions == []
    
    def test_add_valid_result(self):
        """Test adding a valid result."""
        batch = BatchInstructionResult()
        instruction = ImplementationInstruction(
            finding_id="f1",
            file_path="test.tsx",
            component=ComponentInfo(component_id="c1", component_type="button"),
            changes=[PropertyChange(property_name="p", new_value="v")],
            rationale="Test",
            dimension=AuditDimension.COLOR,
            issue_type=IssueType.COLOR_CONTRAST,
        )
        result = InstructionResult(
            instruction=instruction,
            validation=ValidationResult(is_valid=True),
            original_finding_id="f1",
        )
        
        updated = batch.add_result(result)
        assert updated.total_findings == 1
        assert updated.valid_count == 1
        assert updated.invalid_count == 0
        assert updated.success_rate == 1.0
        assert len(updated.instructions) == 1
    
    def test_add_invalid_result(self):
        """Test adding an invalid result."""
        batch = BatchInstructionResult()
        result = InstructionResult(
            instruction=None,
            validation=ValidationResult(is_valid=False, errors=["Error"]),
            original_finding_id="f1",
        )
        
        updated = batch.add_result(result)
        assert updated.total_findings == 1
        assert updated.valid_count == 0
        assert updated.invalid_count == 1
        assert updated.success_rate == 0.0
        assert len(updated.instructions) == 0
    
    def test_mixed_batch(self):
        """Test batch with mixed results."""
        batch = BatchInstructionResult()
        
        # Add valid
        instruction = ImplementationInstruction(
            finding_id="f1",
            file_path="test.tsx",
            component=ComponentInfo(component_id="c1", component_type="button"),
            changes=[PropertyChange(property_name="p", new_value="v")],
            rationale="Test",
            dimension=AuditDimension.COLOR,
            issue_type=IssueType.COLOR_CONTRAST,
        )
        valid = InstructionResult(
            instruction=instruction,
            validation=ValidationResult(is_valid=True),
            original_finding_id="f1",
        )
        batch = batch.add_result(valid)
        
        # Add invalid
        invalid = InstructionResult(
            instruction=None,
            validation=ValidationResult(is_valid=False, errors=["Error"]),
            original_finding_id="f2",
        )
        batch = batch.add_result(invalid)
        
        assert batch.total_findings == 2
        assert batch.valid_count == 1
        assert batch.invalid_count == 1
        assert batch.success_rate == 0.5
"""
Unit tests for instruction validator (M4-2).

Tests for InstructionValidator and validation functions.
"""

import pytest

from src.plan.validator import (
    InstructionValidator,
    validate_instruction,
    is_valid_instruction,
    get_validation_errors,
)
from src.plan.instruction_models import (
    ImplementationInstruction,
    PropertyChange,
    ComponentInfo,
    IssueType,
)
from src.audit.models import AuditDimension
from src.db.models import Severity


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def valid_instruction():
    """Create a valid instruction for testing."""
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


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestInstructionValidator:
    """Tests for InstructionValidator class."""
    
    def test_validate_valid_instruction(self, valid_instruction):
        """Test validating a valid instruction."""
        validator = InstructionValidator()
        result = validator.validate(valid_instruction)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_with_warnings(self, valid_instruction):
        """Test validation produces warnings for placeholders."""
        validator = InstructionValidator()
        
        # Instruction with placeholder path
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "file_path": "UNKNOWN_FILE",
                "is_placeholder_path": True,
            }
        )
        
        result = validator.validate(instruction)
        
        assert result.is_valid  # Still valid
        assert len(result.warnings) > 0  # But has warnings
    
    def test_validate_empty_file_path(self, valid_instruction):
        """Test validation fails for empty file path."""
        validator = InstructionValidator()
        
        instruction = ImplementationInstruction(
            **{**valid_instruction.model_dump(), "file_path": ""}
        )
        
        result = validator.validate(instruction)
        
        assert not result.is_valid
        assert any("file_path" in e for e in result.errors)
    
    def test_validate_empty_rationale(self, valid_instruction):
        """Test validation fails for empty rationale - caught by Pydantic."""
        # Pydantic model enforces min_length=1, so ValidationError is raised
        # before our validator even sees it. This is correct behavior.
        with pytest.raises(Exception):  # Pydantic ValidationError
            ImplementationInstruction(
                **{**valid_instruction.model_dump(), "rationale": ""}
            )
    
    def test_validate_empty_changes(self, valid_instruction):
        """Test validation fails for empty changes."""
        validator = InstructionValidator()
        
        with pytest.raises(ValueError):
            # Empty changes not allowed by model
            ImplementationInstruction(
                **{**valid_instruction.model_dump(), "changes": []}
            )
    
    def test_validate_empty_component_id(self, valid_instruction):
        """Test validation fails for empty component_id."""
        validator = InstructionValidator()
        
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "component": ComponentInfo(component_id="", component_type="button"),
            }
        )
        
        result = validator.validate(instruction)
        
        assert not result.is_valid
        assert any("component_id" in e for e in result.errors)
    
    def test_validate_empty_property_name(self, valid_instruction):
        """Test validation fails for empty property name - caught by Pydantic."""
        # Pydantic model enforces min_length=1 on property_name
        with pytest.raises(Exception):  # Pydantic ValidationError
            PropertyChange(property_name="", new_value="red")
    
    def test_validate_empty_new_value(self, valid_instruction):
        """Test validation fails for empty new value - caught by Pydantic."""
        # Pydantic model enforces min_length=1 on new_value
        with pytest.raises(Exception):  # Pydantic ValidationError
            PropertyChange(property_name="color", new_value="")


# =============================================================================
# STRICT MODE TESTS
# =============================================================================

class TestStrictMode:
    """Tests for strict validation mode."""
    
    def test_strict_mode_converts_warnings_to_errors(self, valid_instruction):
        """Test strict mode converts warnings to errors."""
        validator = InstructionValidator(strict_mode=True)
        
        # Instruction with placeholder path (normally a warning)
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "file_path": "UNKNOWN_FILE",
                "is_placeholder_path": True,
            }
        )
        
        result = validator.validate(instruction)
        
        assert not result.is_valid  # Now invalid in strict mode
        assert len(result.errors) > 0


# =============================================================================
# PLACEHOLDER PATH TESTS
# =============================================================================

class TestPlaceholderPaths:
    """Tests for placeholder path handling."""
    
    def test_allow_placeholder_paths_true(self, valid_instruction):
        """Test placeholder paths allowed by default."""
        validator = InstructionValidator(allow_placeholder_paths=True)
        
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "file_path": "UNKNOWN_FILE",
                "is_placeholder_path": True,
            }
        )
        
        result = validator.validate(instruction)
        
        assert result.is_valid
        assert any("placeholder" in w for w in result.warnings)
    
    def test_allow_placeholder_paths_false(self, valid_instruction):
        """Test placeholder paths cause error when not allowed."""
        validator = InstructionValidator(allow_placeholder_paths=False)
        
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "file_path": "UNKNOWN_FILE",
                "is_placeholder_path": True,
            }
        )
        
        result = validator.validate(instruction)
        
        assert not result.is_valid
        assert any("placeholder" in e for e in result.errors)


# =============================================================================
# CONFIDENCE TESTS
# =============================================================================

class TestConfidenceValidation:
    """Tests for confidence validation."""
    
    def test_min_confidence_satisfied(self, valid_instruction):
        """Test confidence above minimum."""
        validator = InstructionValidator(min_confidence=0.5)
        
        instruction = ImplementationInstruction(
            **{**valid_instruction.model_dump(), "confidence": 0.8}
        )
        
        result = validator.validate(instruction)
        
        assert result.is_valid
    
    def test_min_confidence_not_satisfied(self, valid_instruction):
        """Test confidence below minimum."""
        validator = InstructionValidator(min_confidence=0.9)
        
        instruction = ImplementationInstruction(
            **{**valid_instruction.model_dump(), "confidence": 0.5}
        )
        
        result = validator.validate(instruction)
        
        assert not result.is_valid
        assert any("confidence" in e for e in result.errors)
    
    def test_low_confidence_warning(self, valid_instruction):
        """Test low confidence produces warning."""
        validator = InstructionValidator()
        
        instruction = ImplementationInstruction(
            **{**valid_instruction.model_dump(), "confidence": 0.3}
        )
        
        result = validator.validate(instruction)
        
        assert result.is_valid  # Still valid
        assert any("confidence" in w for w in result.warnings)


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_validate_instruction(self, valid_instruction):
        """Test validate_instruction function."""
        result = validate_instruction(valid_instruction)
        
        assert result.is_valid
        assert isinstance(result.errors, list)
    
    def test_validate_instruction_strict(self, valid_instruction):
        """Test validate_instruction with strict mode."""
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "is_placeholder_path": True,
            }
        )
        
        result = validate_instruction(instruction, strict=True)
        
        assert not result.is_valid
    
    def test_is_valid_instruction_true(self, valid_instruction):
        """Test is_valid_instruction returns True for valid."""
        assert is_valid_instruction(valid_instruction)
    
    def test_is_valid_instruction_false(self, valid_instruction):
        """Test is_valid_instruction returns False for invalid."""
        # Create instruction with invalid file_path (empty caught by validator, not Pydantic)
        instruction = ImplementationInstruction(
            **{**valid_instruction.model_dump(), "file_path": ""}
        )
        
        assert not is_valid_instruction(instruction)
    
    def test_get_validation_errors_empty(self, valid_instruction):
        """Test get_validation_errors returns empty for valid."""
        errors = get_validation_errors(valid_instruction)
        
        assert errors == []
    
    def test_get_validation_errors_with_errors(self, valid_instruction):
        """Test get_validation_errors returns errors."""
        # Create instruction with invalid file_path (caught by validator)
        instruction = ImplementationInstruction(
            **{**valid_instruction.model_dump(), "file_path": ""}
        )
        
        errors = get_validation_errors(instruction)
        
        assert len(errors) > 0
        assert any("file_path" in e for e in errors)


# =============================================================================
# INSPECTION FLAG TESTS
# =============================================================================

class TestInspectionFlags:
    """Tests for requires_inspection flag handling."""
    
    def test_requires_inspection_warning(self, valid_instruction):
        """Test requires_inspection produces warning."""
        validator = InstructionValidator()
        
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "changes": [
                    PropertyChange(
                        property_name="color",
                        old_value=None,
                        new_value="red",
                        requires_inspection=True,
                    )
                ],
            }
        )
        
        result = validator.validate(instruction)
        
        assert result.is_valid
        assert any("requires_inspection" in w for w in result.warnings)
    
    def test_requires_inspection_value_warning(self, valid_instruction):
        """Test REQUIRES_INSPECTION value produces warning."""
        validator = InstructionValidator()
        
        instruction = ImplementationInstruction(
            **{
                **valid_instruction.model_dump(),
                "changes": [
                    PropertyChange(
                        property_name="color",
                        new_value="REQUIRES_INSPECTION",
                    )
                ],
            }
        )
        
        result = validator.validate(instruction)
        
        assert result.is_valid
        assert any("REQUIRES_INSPECTION" in w for w in result.warnings)
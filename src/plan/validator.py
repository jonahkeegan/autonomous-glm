"""
Instruction validator for completeness validation.

Validates that instructions have all required fields populated
and meet quality standards before being persisted or transmitted.
"""

from typing import Optional

from src.plan.instruction_models import (
    ImplementationInstruction,
    InstructionResult,
    ValidationResult,
    PropertyChange,
)


# =============================================================================
# REQUIRED FIELDS
# =============================================================================

REQUIRED_INSTRUCTION_FIELDS = [
    "finding_id",
    "file_path",
    "component",
    "changes",
    "rationale",
    "dimension",
    "issue_type",
]

REQUIRED_COMPONENT_FIELDS = [
    "component_id",
    "component_type",
]

REQUIRED_CHANGE_FIELDS = [
    "property_name",
    "new_value",
]


# =============================================================================
# INSTRUCTION VALIDATOR
# =============================================================================

class InstructionValidator:
    """Validates instruction completeness and quality.
    
    Checks that instructions have:
    - All required fields populated
    - Non-empty values where required
    - At least one property change
    - Coherent metadata
    """
    
    def __init__(
        self,
        strict_mode: bool = False,
        allow_placeholder_paths: bool = True,
        min_confidence: float = 0.0,
    ):
        """Initialize validator.
        
        Args:
            strict_mode: If True, warnings become errors
            allow_placeholder_paths: If False, placeholder paths are errors
            min_confidence: Minimum required confidence (0.0-1.0)
        """
        self._strict_mode = strict_mode
        self._allow_placeholder_paths = allow_placeholder_paths
        self._min_confidence = min_confidence
    
    def validate(self, instruction: ImplementationInstruction) -> ValidationResult:
        """Validate an instruction completely.
        
        Args:
            instruction: Instruction to validate
            
        Returns:
            ValidationResult with is_valid, errors, and warnings
        """
        errors = []
        warnings = []
        
        # Check required fields
        field_errors = self.check_required_fields(instruction)
        errors.extend(field_errors)
        
        # Check values are populated
        value_errors, value_warnings = self.check_values_populated(instruction)
        errors.extend(value_errors)
        warnings.extend(value_warnings)
        
        # Check component info
        component_errors = self._validate_component(instruction)
        errors.extend(component_errors)
        
        # Check changes
        change_errors, change_warnings = self._validate_changes(instruction)
        errors.extend(change_errors)
        warnings.extend(change_warnings)
        
        # Check confidence
        confidence_errors, confidence_warnings = self._validate_confidence(instruction)
        errors.extend(confidence_errors)
        warnings.extend(confidence_warnings)
        
        # Check file path
        path_errors, path_warnings = self._validate_file_path(instruction)
        errors.extend(path_errors)
        warnings.extend(path_warnings)
        
        # Apply strict mode
        if self._strict_mode:
            errors.extend(warnings)
            warnings = []
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )
    
    def check_required_fields(
        self, 
        instruction: ImplementationInstruction
    ) -> list[str]:
        """Check that all required fields are present.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            List of error messages for missing fields
        """
        errors = []
        
        for field in REQUIRED_INSTRUCTION_FIELDS:
            value = getattr(instruction, field, None)
            if value is None:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def check_values_populated(
        self, 
        instruction: ImplementationInstruction
    ) -> tuple[list[str], list[str]]:
        """Check that required values are non-empty.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check file_path is not empty
        if not instruction.file_path or instruction.file_path.strip() == "":
            errors.append("file_path cannot be empty")
        
        # Check rationale is not empty
        if not instruction.rationale or instruction.rationale.strip() == "":
            errors.append("rationale cannot be empty")
        
        # Check component_id is not empty
        if not instruction.component.component_id:
            errors.append("component_id cannot be empty")
        
        # Check changes list is not empty
        if not instruction.changes:
            errors.append("changes list cannot be empty")
        
        # Warn on placeholder values
        if "UNKNOWN" in instruction.file_path:
            warnings.append("file_path contains placeholder value")
        
        if "REQUIRES_INSPECTION" in instruction.rationale:
            warnings.append("rationale contains placeholder text")
        
        return errors, warnings
    
    def _validate_component(
        self, 
        instruction: ImplementationInstruction
    ) -> list[str]:
        """Validate component information."""
        errors = []
        component = instruction.component
        
        if not component.component_id or component.component_id.strip() == "":
            errors.append("component.component_id cannot be empty")
        
        if not component.component_type or component.component_type.strip() == "":
            errors.append("component.component_type cannot be empty")
        
        return errors
    
    def _validate_changes(
        self, 
        instruction: ImplementationInstruction
    ) -> tuple[list[str], list[str]]:
        """Validate property changes."""
        errors = []
        warnings = []
        
        if not instruction.changes:
            errors.append("Instruction must have at least one PropertyChange")
            return errors, warnings
        
        for i, change in enumerate(instruction.changes):
            # Check property_name
            if not change.property_name or change.property_name.strip() == "":
                errors.append(f"changes[{i}].property_name cannot be empty")
            
            # Check new_value
            if not change.new_value or change.new_value.strip() == "":
                errors.append(f"changes[{i}].new_value cannot be empty")
            
            # Warn on inspection required
            if change.requires_inspection:
                warnings.append(
                    f"changes[{i}].requires_inspection=True for '{change.property_name}'"
                )
            
            # Warn on REQUIRES_INSPECTION value
            if change.new_value == "REQUIRES_INSPECTION":
                warnings.append(
                    f"changes[{i}].new_value is placeholder 'REQUIRES_INSPECTION'"
                )
        
        return errors, warnings
    
    def _validate_confidence(
        self, 
        instruction: ImplementationInstruction
    ) -> tuple[list[str], list[str]]:
        """Validate confidence level."""
        errors = []
        warnings = []
        
        if instruction.confidence < self._min_confidence:
            errors.append(
                f"confidence {instruction.confidence:.2f} below minimum {self._min_confidence}"
            )
        
        if instruction.confidence < 0.5:
            warnings.append(
                f"low confidence score: {instruction.confidence:.2f}"
            )
        
        return errors, warnings
    
    def _validate_file_path(
        self, 
        instruction: ImplementationInstruction
    ) -> tuple[list[str], list[str]]:
        """Validate file path."""
        errors = []
        warnings = []
        
        # Check for placeholder paths
        if instruction.is_placeholder_path:
            if not self._allow_placeholder_paths:
                errors.append("placeholder file paths not allowed")
            else:
                warnings.append("file_path is a placeholder and needs manual mapping")
        
        # Check for common issues
        if instruction.file_path == "UNKNOWN_FILE":
            warnings.append("file_path is UNKNOWN_FILE - screen metadata may be missing")
        
        return errors, warnings
    
    def validate_result(self, result: InstructionResult) -> InstructionResult:
        """Validate and potentially update an InstructionResult.
        
        Re-validates the instruction if present and updates the validation.
        
        Args:
            result: InstructionResult to validate
            
        Returns:
            Updated InstructionResult with fresh validation
        """
        if result.instruction is None:
            return result
        
        validation = self.validate(result.instruction)
        
        return InstructionResult(
            instruction=result.instruction if validation.is_valid else None,
            validation=validation,
            original_finding_id=result.original_finding_id,
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_instruction(
    instruction: ImplementationInstruction,
    strict: bool = False
) -> ValidationResult:
    """Validate an instruction with default settings.
    
    Args:
        instruction: Instruction to validate
        strict: If True, use strict validation mode
        
    Returns:
        ValidationResult
    """
    validator = InstructionValidator(strict_mode=strict)
    return validator.validate(instruction)


def is_valid_instruction(instruction: ImplementationInstruction) -> bool:
    """Quick check if instruction is valid.
    
    Args:
        instruction: Instruction to check
        
    Returns:
        True if valid, False otherwise
    """
    result = validate_instruction(instruction)
    return result.is_valid


def get_validation_errors(
    instruction: ImplementationInstruction
) -> list[str]:
    """Get list of validation errors for an instruction.
    
    Args:
        instruction: Instruction to validate
        
    Returns:
        List of error messages (empty if valid)
    """
    result = validate_instruction(instruction)
    return result.errors
"""
Plan Generation Module for Autonomous-GLM.

This module provides phased plan synthesis from audit findings, organizing
improvements into Critical → Refinement → Polish phases with proper
dependency resolution, and formatting them into implementation-ready
instructions.
"""

from src.plan.models import (
    PhaseType,
    PlanStatus,
    PlanActionCreate,
    PlanPhaseCreate as PlanPhaseData,
    Plan,
    PlanSummary,
)
from src.plan.phasing import PhaseClassifier, classify_finding
from src.plan.dependencies import DependencyResolver
from src.plan.synthesizer import PlanSynthesizer

# Instruction formatting (M4-2)
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
from src.plan.templates import (
    InstructionTemplateRegistry,
    get_default_registry,
    reset_registry,
)
from src.plan.formatter import (
    InstructionFormatter,
    format_finding,
    format_findings,
    map_to_component,
    determine_file_path,
    generate_changes,
    generate_rationale,
)
from src.plan.validator import (
    InstructionValidator,
    validate_instruction,
    is_valid_instruction,
    get_validation_errors,
)

__all__ = [
    # Models
    "PhaseType",
    "PlanStatus",
    "PlanActionCreate",
    "PlanPhaseData",
    "Plan",
    "PlanSummary",
    # Classification
    "PhaseClassifier",
    "classify_finding",
    # Dependencies
    "DependencyResolver",
    # Synthesis
    "PlanSynthesizer",
    # Instruction Models
    "IssueType",
    "PropertyChange",
    "ComponentInfo",
    "ImplementationInstruction",
    "InstructionTemplate",
    "ValidationResult",
    "InstructionResult",
    "BatchInstructionResult",
    # Templates
    "InstructionTemplateRegistry",
    "get_default_registry",
    "reset_registry",
    # Formatter
    "InstructionFormatter",
    "format_finding",
    "format_findings",
    "map_to_component",
    "determine_file_path",
    "generate_changes",
    "generate_rationale",
    # Validator
    "InstructionValidator",
    "validate_instruction",
    "is_valid_instruction",
    "get_validation_errors",
]

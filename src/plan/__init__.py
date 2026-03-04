"""
Plan Generation Module for Autonomous-GLM.

This module provides phased plan synthesis from audit findings, organizing
improvements into Critical → Refinement → Polish phases with proper
dependency resolution, and formatting them into implementation-ready
instructions.

Also provides design system proposal generation (M4-3) for recommending
token additions and component variants.
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

# Design System Proposals (M4-3)
from src.plan.proposal_models import (
    ProposalType,
    TokenType,
    Priority,
    TokenProposal,
    ComponentVariant,
    ComponentProposal,
    BeforeAfterDescription,
    DesignSystemProposal,
)
from src.plan.token_analyzer import (
    TokenAnalyzer,
    DEFAULT_DESIGN_TOKENS,
    generate_color_token_name,
    generate_spacing_token_name,
    generate_typography_token_name,
    analyze_all_token_patterns,
)
from src.plan.proposals import (
    ProposalGenerator,
    calculate_impact_score,
    determine_priority,
    generate_design_system_proposals,
)
from src.plan.comparison import (
    BeforeAfterGenerator,
    generate_token_comparison,
    generate_component_comparison,
    generate_summary_comparison,
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
    # Design System Proposals (M4-3)
    "ProposalType",
    "TokenType",
    "Priority",
    "TokenProposal",
    "ComponentVariant",
    "ComponentProposal",
    "BeforeAfterDescription",
    "DesignSystemProposal",
    "TokenAnalyzer",
    "DEFAULT_DESIGN_TOKENS",
    "generate_color_token_name",
    "generate_spacing_token_name",
    "generate_typography_token_name",
    "analyze_all_token_patterns",
    "ProposalGenerator",
    "calculate_impact_score",
    "determine_priority",
    "generate_design_system_proposals",
    "BeforeAfterGenerator",
    "generate_token_comparison",
    "generate_component_comparison",
    "generate_summary_comparison",
]

"""
Pydantic models for implementation instructions.

Defines data models for transforming audit findings into executable,
unambiguous instructions in the format:
"In file X, component Y, property Z: change from 'old' to 'new'"
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from src.audit.models import AuditDimension, StandardsReference
from src.db.models import Severity


# =============================================================================
# ISSUE TYPE ENUM
# =============================================================================

class IssueType(str, Enum):
    """Types of issues that can be formatted into instructions."""
    
    SPACING = "spacing"
    COLOR_CONTRAST = "color_contrast"
    TYPOGRAPHY = "typography"
    ALIGNMENT = "alignment"
    HIERARCHY = "hierarchy"
    ACCESSIBILITY = "accessibility"
    COMPONENTS = "components"
    DENSITY = "density"
    ICONOGRAPHY = "iconography"
    EMPTY_STATES = "empty_states"
    LOADING_STATES = "loading_states"
    ERROR_STATES = "error_states"
    THEMING = "theming"
    GENERIC = "generic"
    
    @classmethod
    def from_dimension(cls, dimension: AuditDimension) -> "IssueType":
        """Map audit dimension to issue type."""
        mapping = {
            AuditDimension.SPACING_RHYTHM: cls.SPACING,
            AuditDimension.COLOR: cls.COLOR_CONTRAST,
            AuditDimension.TYPOGRAPHY: cls.TYPOGRAPHY,
            AuditDimension.ALIGNMENT_GRID: cls.ALIGNMENT,
            AuditDimension.VISUAL_HIERARCHY: cls.HIERARCHY,
            AuditDimension.ACCESSIBILITY: cls.ACCESSIBILITY,
            AuditDimension.COMPONENTS: cls.COMPONENTS,
            AuditDimension.DENSITY: cls.DENSITY,
            AuditDimension.ICONOGRAPHY: cls.ICONOGRAPHY,
            AuditDimension.EMPTY_STATES: cls.EMPTY_STATES,
            AuditDimension.LOADING_STATES: cls.LOADING_STATES,
            AuditDimension.ERROR_STATES: cls.ERROR_STATES,
            AuditDimension.DARK_MODE_THEMING: cls.THEMING,
        }
        return mapping.get(dimension, cls.GENERIC)


# =============================================================================
# PROPERTY CHANGE
# =============================================================================

class PropertyChange(BaseModel):
    """A single property change within an instruction.
    
    Represents the core unit of change: property, old value, new value.
    """
    
    property_name: str = Field(
        ..., 
        min_length=1,
        description="CSS property or design attribute (e.g., 'margin-top', 'font-size')"
    )
    old_value: Optional[str] = Field(
        default=None,
        description="Current value (e.g., '12px', '#ff0000'). None if requires inspection."
    )
    new_value: str = Field(
        ...,
        min_length=1,
        description="Proposed value (e.g., '16px', 'var(--color-primary)')"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the change recommendation (0.0-1.0)"
    )
    requires_inspection: bool = Field(
        default=False,
        description="Whether old_value needs manual inspection"
    )
    
    model_config = {"frozen": True}
    
    def to_markdown(self) -> str:
        """Render as markdown list item."""
        if self.requires_inspection or self.old_value is None:
            return f"- {self.property_name}: set to '{self.new_value}' ⚠️ (requires inspection)"
        return f"- {self.property_name}: change from '{self.old_value}' to '{self.new_value}'"
    
    def to_json_dict(self) -> dict:
        """Render as JSON-compatible dict."""
        return {
            "property": self.property_name,
            "old": self.old_value,
            "new": self.new_value,
            "confidence": self.confidence,
            "requires_inspection": self.requires_inspection,
        }


# =============================================================================
# COMPONENT INFO
# =============================================================================

class ComponentInfo(BaseModel):
    """Information about a component targeted by an instruction."""
    
    component_id: str = Field(..., description="Component identifier")
    component_type: str = Field(..., description="Component type (e.g., 'button', 'input')")
    bounding_box: Optional[tuple[float, float, float, float]] = Field(
        default=None,
        description="Bounding box (x1, y1, x2, y2) normalized 0.0-1.0"
    )
    selector: Optional[str] = Field(
        default=None,
        description="CSS selector if determinable (e.g., '.btn-primary')"
    )
    
    model_config = {"frozen": True}


# =============================================================================
# IMPLEMENTATION INSTRUCTION
# =============================================================================

class ImplementationInstruction(BaseModel):
    """A complete implementation instruction derived from an audit finding.
    
    Contains all information needed to execute a fix:
    - Target location (file, component)
    - Specific changes (property: old → new)
    - Context (rationale, standards references)
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    finding_id: str = Field(..., description="ID of the source audit finding")
    
    # Target location
    file_path: str = Field(
        ...,
        description="File path or placeholder (e.g., 'components/Button.tsx', 'UNKNOWN_FILE')"
    )
    component: ComponentInfo = Field(..., description="Target component info")
    
    # Changes
    changes: list[PropertyChange] = Field(
        ...,
        min_length=1,
        description="Property changes to apply"
    )
    
    # Context
    rationale: str = Field(
        ...,
        min_length=1,
        description="Why this change is needed"
    )
    standards_refs: list[StandardsReference] = Field(
        default_factory=list,
        description="References to design standards or WCAG"
    )
    
    # Metadata
    dimension: AuditDimension = Field(..., description="Source audit dimension")
    severity: Severity = Field(default=Severity.MEDIUM, description="Issue severity")
    issue_type: IssueType = Field(..., description="Categorized issue type")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in instruction accuracy"
    )
    
    # Flags
    requires_manual_review: bool = Field(
        default=False,
        description="Whether this instruction needs human review before execution"
    )
    is_placeholder_path: bool = Field(
        default=False,
        description="Whether file_path is a placeholder (needs manual mapping)"
    )
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Additional metadata
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional instruction metadata"
    )
    
    @field_validator("changes", mode="before")
    @classmethod
    def validate_changes(cls, v):
        """Ensure changes is a non-empty list."""
        if v is None or len(v) == 0:
            raise ValueError("Instruction must have at least one PropertyChange")
        return list(v)
    
    @property
    def change_count(self) -> int:
        """Return number of property changes."""
        return len(self.changes)
    
    @property
    def has_standards_refs(self) -> bool:
        """Check if instruction has standards references."""
        return len(self.standards_refs) > 0
    
    def to_markdown(self) -> str:
        """Render as formatted markdown.
        
        Output format:
        ```
        In {file_path}, component {component_id} ({component_type}):
          - {property}: change from '{old}' to '{new}'
        
        Rationale: {rationale}
        Standards: {standards}
        ```
        """
        # Header line
        header = f"In `{self.file_path}`, component `{self.component.component_id}` ({self.component.component_type}):"
        
        # Changes
        changes_md = "\n".join(f"  {c.to_markdown()}" for c in self.changes)
        
        # Rationale
        rationale_md = f"\n**Rationale:** {self.rationale}"
        
        # Standards
        standards_md = ""
        if self.standards_refs:
            refs = []
            for ref in self.standards_refs:
                if ref.wcag:
                    refs.append(f"WCAG {ref.wcag.criterion} ({ref.wcag.level})")
                elif ref.design_token:
                    refs.append(f"Token: {ref.design_token.token_name}")
                elif ref.custom:
                    refs.append(ref.custom)
            standards_md = f"\n**Standards:** {', '.join(refs)}"
        
        # Flags
        flags_md = ""
        flags = []
        if self.requires_manual_review:
            flags.append("⚠️ requires manual review")
        if self.is_placeholder_path:
            flags.append("📍 placeholder path")
        if flags:
            flags_md = f"\n*{', '.join(flags)}*"
        
        return f"{header}\n{changes_md}{rationale_md}{standards_md}{flags_md}"
    
    def to_json_dict(self) -> dict:
        """Render as JSON-compatible dict."""
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "file_path": self.file_path,
            "component": {
                "id": self.component.component_id,
                "type": self.component.component_type,
                "selector": self.component.selector,
            },
            "changes": [c.to_json_dict() for c in self.changes],
            "rationale": self.rationale,
            "standards_refs": [
                {
                    "wcag": ref.wcag.model_dump() if ref.wcag else None,
                    "design_token": ref.design_token.model_dump() if ref.design_token else None,
                    "custom": ref.custom,
                }
                for ref in self.standards_refs
            ],
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "issue_type": self.issue_type.value,
            "confidence": self.confidence,
            "requires_manual_review": self.requires_manual_review,
            "is_placeholder_path": self.is_placeholder_path,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# INSTRUCTION TEMPLATE
# =============================================================================

class InstructionTemplate(BaseModel):
    """Template for generating instruction rationale.
    
    Uses simple string placeholders that can be filled with .format().
    """
    
    name: str = Field(..., description="Template name (e.g., 'spacing_issue')")
    issue_type: IssueType = Field(..., description="Associated issue type")
    template: str = Field(
        ...,
        min_length=1,
        description="Template string with {placeholders}"
    )
    placeholders: list[str] = Field(
        default_factory=list,
        description="List of expected placeholder names"
    )
    fallback: bool = Field(
        default=False,
        description="Whether this is a fallback/generic template"
    )
    
    model_config = {"frozen": True}
    
    def render(self, **kwargs) -> str:
        """Render template with provided values.
        
        Args:
            **kwargs: Values for template placeholders
            
        Returns:
            Rendered string
            
        Raises:
            ValueError: If required placeholders are missing
        """
        # Check for missing required placeholders
        missing = set(self.placeholders) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required placeholders: {missing}")
        
        return self.template.format(**kwargs)
    
    def validate_context(self, context: dict) -> list[str]:
        """Validate that context has all required placeholders.
        
        Returns:
            List of missing placeholder names (empty if valid)
        """
        return [p for p in self.placeholders if p not in context]


# =============================================================================
# INSTRUCTION RESULT
# =============================================================================

class ValidationResult(BaseModel):
    """Result of validating an instruction."""
    
    is_valid: bool = Field(..., description="Whether instruction is valid")
    errors: list[str] = Field(
        default_factory=list,
        description="Validation error messages"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal validation warnings"
    )
    
    model_config = {"frozen": True}


class InstructionResult(BaseModel):
    """Result of formatting an instruction.
    
    Contains either a valid instruction or validation errors.
    """
    
    instruction: Optional[ImplementationInstruction] = Field(
        default=None,
        description="Formatted instruction if valid"
    )
    validation: ValidationResult = Field(
        ...,
        description="Validation result"
    )
    original_finding_id: str = Field(
        ...,
        description="ID of the source finding"
    )
    
    @property
    def is_valid(self) -> bool:
        """Check if instruction is valid."""
        return self.validation.is_valid and self.instruction is not None
    
    @property
    def error_message(self) -> Optional[str]:
        """Get combined error message if invalid."""
        if self.is_valid:
            return None
        return "; ".join(self.validation.errors)


# =============================================================================
# BATCH RESULT
# =============================================================================

class BatchInstructionResult(BaseModel):
    """Result of batch formatting multiple findings."""
    
    results: list[InstructionResult] = Field(
        default_factory=list,
        description="Individual instruction results"
    )
    total_findings: int = Field(default=0, description="Total findings processed")
    valid_count: int = Field(default=0, description="Successfully formatted instructions")
    invalid_count: int = Field(default=0, description="Failed to format")
    
    @property
    def success_rate(self) -> float:
        """Calculate formatting success rate."""
        if self.total_findings == 0:
            return 0.0
        return self.valid_count / self.total_findings
    
    @property
    def instructions(self) -> list[ImplementationInstruction]:
        """Get all valid instructions."""
        return [r.instruction for r in self.results if r.instruction is not None]
    
    def add_result(self, result: InstructionResult) -> "BatchInstructionResult":
        """Add a result and update counts."""
        new_results = list(self.results) + [result]
        valid_count = self.valid_count + (1 if result.is_valid else 0)
        invalid_count = self.invalid_count + (0 if result.is_valid else 1)
        
        return BatchInstructionResult(
            results=new_results,
            total_findings=self.total_findings + 1,
            valid_count=valid_count,
            invalid_count=invalid_count,
        )
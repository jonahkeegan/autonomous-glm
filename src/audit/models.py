"""
Pydantic models for audit framework.

Defines data models for audit dimensions, sessions, results, and standards references.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

# Import existing Severity from db models
from src.db.models import Severity, EntityType


# =============================================================================
# AUDIT DIMENSION ENUM
# =============================================================================

class AuditDimension(str, Enum):
    """All audit dimensions per SOUL.md design audit protocol."""
    
    # Visual dimensions (M3-3)
    VISUAL_HIERARCHY = "visual_hierarchy"
    SPACING_RHYTHM = "spacing_rhythm"
    TYPOGRAPHY = "typography"
    COLOR = "color"
    ALIGNMENT_GRID = "alignment_grid"
    COMPONENTS = "components"
    DENSITY = "density"
    
    # State and accessibility dimensions (M3-4)
    ICONOGRAPHY = "iconography"
    EMPTY_STATES = "empty_states"
    LOADING_STATES = "loading_states"
    ERROR_STATES = "error_states"
    DARK_MODE_THEMING = "dark_mode_theming"
    ACCESSIBILITY = "accessibility"
    
    # Deferred dimensions (require additional capabilities)
    MOTION_TRANSITIONS = "motion_transitions"  # Requires video analysis
    RESPONSIVENESS = "responsiveness"  # Requires multi-viewport
    
    @classmethod
    def visual_dimensions(cls) -> list["AuditDimension"]:
        """Return visual audit dimensions (M3-3)."""
        return [
            cls.VISUAL_HIERARCHY,
            cls.SPACING_RHYTHM,
            cls.TYPOGRAPHY,
            cls.COLOR,
            cls.ALIGNMENT_GRID,
            cls.COMPONENTS,
            cls.DENSITY,
        ]
    
    @classmethod
    def state_dimensions(cls) -> list["AuditDimension"]:
        """Return state and accessibility dimensions (M3-4)."""
        return [
            cls.ICONOGRAPHY,
            cls.EMPTY_STATES,
            cls.LOADING_STATES,
            cls.ERROR_STATES,
            cls.DARK_MODE_THEMING,
            cls.ACCESSIBILITY,
        ]
    
    @classmethod
    def all_active(cls) -> list["AuditDimension"]:
        """Return all active (non-deferred) dimensions."""
        return cls.visual_dimensions() + cls.state_dimensions()


# =============================================================================
# AUDIT SESSION STATUS
# =============================================================================

class AuditSessionStatus(str, Enum):
    """Status of an audit session."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Completed with some dimension failures


# =============================================================================
# STANDARDS REFERENCES
# =============================================================================

class DesignTokenReference(BaseModel):
    """Reference to a design system token."""
    
    token_name: str = Field(..., description="Token name (e.g., --color-primary)")
    token_type: str = Field(..., description="Token type (color, spacing, typography)")
    expected_value: Optional[str] = Field(
        default=None,
        description="Expected value from design system"
    )
    actual_value: Optional[str] = Field(
        default=None,
        description="Actual value detected in screen"
    )
    
    model_config = {"frozen": True}


class WCAGReference(BaseModel):
    """Reference to a WCAG 2.1 criterion."""
    
    criterion: str = Field(..., description="WCAG criterion number (e.g., 1.4.3)")
    name: str = Field(..., description="Criterion name")
    level: str = Field(default="AA", description="Conformance level (A, AA, AAA)")
    url: Optional[str] = Field(default=None, description="Link to WCAG explanation")
    
    model_config = {"frozen": True}


class StandardsReference(BaseModel):
    """Reference to design standards (token or WCAG)."""
    
    design_token: Optional[DesignTokenReference] = Field(default=None)
    wcag: Optional[WCAGReference] = Field(default=None)
    custom: Optional[str] = Field(
        default=None,
        description="Custom standard reference (e.g., company guideline)"
    )
    
    def has_reference(self) -> bool:
        """Check if any reference is set."""
        return any([self.design_token, self.wcag, self.custom])
    
    model_config = {"frozen": True}


# =============================================================================
# AUDIT FINDING (EXTENDED)
# =============================================================================

class AuditFindingCreate(BaseModel):
    """Model for creating a new audit finding with audit session context."""
    
    entity_type: EntityType = Field(..., description="Type of entity with issue")
    entity_id: str = Field(..., description="ID of entity with issue")
    dimension: AuditDimension = Field(..., description="Audit dimension")
    issue: str = Field(..., min_length=1, description="Description of the issue")
    rationale: Optional[str] = Field(
        default=None,
        description="Why this is an issue"
    )
    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Issue severity level"
    )
    standards_refs: list[StandardsReference] = Field(
        default_factory=list,
        description="References to design standards or WCAG"
    )
    jobs_filtered: bool = Field(
        default=False,
        description="Whether this finding was flagged by Jobs filter"
    )
    jobs_filter_score: Optional[float] = Field(
        default=None,
        description="Jobs filter score (0.0-1.0)"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional finding metadata"
    )


# =============================================================================
# AUDIT SESSION
# =============================================================================

class AuditSession(BaseModel):
    """Audit session tracking model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    screen_id: str = Field(..., description="ID of the screen being audited")
    status: AuditSessionStatus = Field(
        default=AuditSessionStatus.PENDING,
        description="Current session status"
    )
    dimensions: list[AuditDimension] = Field(
        default_factory=list,
        description="Dimensions to audit"
    )
    completed_dimensions: list[AuditDimension] = Field(
        default_factory=list,
        description="Dimensions already completed"
    )
    finding_ids: list[str] = Field(
        default_factory=list,
        description="IDs of findings from this session"
    )
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator("dimensions", mode="before")
    @classmethod
    def validate_dimensions(cls, v):
        """Ensure dimensions is a list."""
        if v is None:
            return []
        return list(v)
    
    def mark_started(self) -> "AuditSession":
        """Mark session as started."""
        return AuditSession(
            **{**self.model_dump(), 
               "status": AuditSessionStatus.IN_PROGRESS,
               "started_at": datetime.now()}
        )
    
    def mark_completed(self, success: bool = True) -> "AuditSession":
        """Mark session as completed."""
        if success:
            status = AuditSessionStatus.COMPLETED
        elif self.completed_dimensions:
            status = AuditSessionStatus.PARTIAL
        else:
            status = AuditSessionStatus.FAILED
        
        return AuditSession(
            **{**self.model_dump(),
               "status": status,
               "completed_at": datetime.now()}
        )
    
    def add_dimension_result(
        self, 
        dimension: AuditDimension, 
        finding_ids: list[str]
    ) -> "AuditSession":
        """Add results from a dimension audit."""
        completed = list(self.completed_dimensions)
        if dimension not in completed:
            completed.append(dimension)
        
        all_findings = list(self.finding_ids) + finding_ids
        
        return AuditSession(
            **{**self.model_dump(),
               "completed_dimensions": completed,
               "finding_ids": all_findings}
        )


# =============================================================================
# AUDIT RESULT
# =============================================================================

class DimensionStats(BaseModel):
    """Statistics for a single dimension."""
    
    dimension: AuditDimension
    total_findings: int = Field(default=0)
    by_severity: dict[str, int] = Field(default_factory=dict)
    jobs_filtered_count: int = Field(default=0)
    
    def add_finding(self, severity: Severity, jobs_filtered: bool = False) -> None:
        """Add a finding to stats."""
        self.total_findings += 1
        sev_key = severity.value
        self.by_severity[sev_key] = self.by_severity.get(sev_key, 0) + 1
        if jobs_filtered:
            self.jobs_filtered_count += 1


class AuditResult(BaseModel):
    """Aggregated audit result with findings and statistics."""
    
    session: AuditSession
    findings_by_dimension: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Finding IDs grouped by dimension"
    )
    summary_stats: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics"
    )
    
    def add_dimension_findings(
        self, 
        dimension: AuditDimension, 
        finding_ids: list[str],
        stats: DimensionStats
    ) -> None:
        """Add findings from a dimension."""
        dim_key = dimension.value
        self.findings_by_dimension[dim_key] = finding_ids
        self.summary_stats[dim_key] = stats.model_dump()
    
    def compute_summary(self) -> dict[str, Any]:
        """Compute overall summary statistics."""
        total_findings = 0
        total_by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        total_filtered = 0
        
        for dim_key, stats in self.summary_stats.items():
            if isinstance(stats, dict):
                total_findings += stats.get("total_findings", 0)
                total_filtered += stats.get("jobs_filtered_count", 0)
                for sev, count in stats.get("by_severity", {}).items():
                    total_by_severity[sev] = total_by_severity.get(sev, 0) + count
        
        return {
            "total_findings": total_findings,
            "total_by_severity": total_by_severity,
            "total_jobs_filtered": total_filtered,
            "dimensions_completed": len(self.findings_by_dimension),
            "dimensions_total": len(self.session.dimensions),
        }


# =============================================================================
# DIMENSION AUDITOR TYPE
# =============================================================================

DimensionAuditor = Callable[[Any], list[AuditFindingCreate]]
"""Type alias for dimension auditor functions.

A dimension auditor takes a screen (or screen data) and returns a list of findings.
"""
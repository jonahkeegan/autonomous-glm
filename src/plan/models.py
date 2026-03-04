"""
Pydantic models for plan generation.

Defines data models for phased improvement plans, including phase types,
plan actions, and plan summaries.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from src.audit.models import AuditDimension
from src.db.models import Severity, PhaseName, PhaseStatus


# =============================================================================
# PHASE TYPE ENUM
# =============================================================================

class PhaseType(str, Enum):
    """Types of plan phases for prioritization.
    
    Maps to PhaseName in db.models but provides ordering semantics.
    """
    
    CRITICAL = "critical"      # Usability, hierarchy, accessibility issues
    REFINEMENT = "refinement"  # Spacing, typography, color, alignment
    POLISH = "polish"          # States, theming, micro-interactions
    
    @classmethod
    def from_phase_name(cls, name: PhaseName) -> "PhaseType":
        """Convert from db.models.PhaseName to PhaseType."""
        mapping = {
            PhaseName.CRITICAL: cls.CRITICAL,
            PhaseName.REFINEMENT: cls.REFINEMENT,
            PhaseName.POLISH: cls.POLISH,
        }
        return mapping[name]
    
    def to_phase_name(self) -> PhaseName:
        """Convert to db.models.PhaseName."""
        mapping = {
            PhaseType.CRITICAL: PhaseName.CRITICAL,
            PhaseType.REFINEMENT: PhaseName.REFINEMENT,
            PhaseType.POLISH: PhaseName.POLISH,
        }
        return mapping[self]
    
    def order(self) -> int:
        """Return the execution order (1 = first)."""
        ordering = {
            PhaseType.CRITICAL: 1,
            PhaseType.REFINEMENT: 2,
            PhaseType.POLISH: 3,
        }
        return ordering[self]


# =============================================================================
# PLAN STATUS ENUM
# =============================================================================

class PlanStatus(str, Enum):
    """Status of a plan."""
    
    PENDING = "pending"              # Plan created, not started
    IN_PROGRESS = "in_progress"      # Some phases started
    COMPLETED = "completed"          # All phases complete
    FAILED = "failed"                # Plan execution failed


# =============================================================================
# PLAN ACTION
# =============================================================================

class PlanActionCreate(BaseModel):
    """Model for creating a plan action from an audit finding.
    
    This extends the db.models.PlanAction with additional metadata
    for plan synthesis.
    """
    
    finding_id: str = Field(..., description="ID of the source audit finding")
    description: str = Field(..., min_length=1, description="What to do")
    target_entity: str = Field(..., description="Entity to modify (e.g., 'Button#submit')")
    target_property: Optional[str] = Field(
        default=None,
        description="Property to modify (e.g., 'background-color')"
    )
    current_value: Optional[str] = Field(
        default=None,
        description="Current value (e.g., '#ff0000')"
    )
    proposed_value: Optional[str] = Field(
        default=None,
        description="Proposed value (e.g., '--color-primary')"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Why this change is needed"
    )
    dimension: AuditDimension = Field(
        ..., 
        description="Audit dimension this action addresses"
    )
    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Severity of the underlying issue"
    )
    sequence: int = Field(
        default=0,
        ge=0,
        description="Order within phase (0 = not yet sequenced)"
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs of actions that must complete first"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional action metadata"
    )
    
    model_config = {"frozen": False}
    
    def with_sequence(self, seq: int) -> "PlanActionCreate":
        """Return a copy with updated sequence."""
        return PlanActionCreate(
            **{**self.model_dump(), "sequence": seq}
        )
    
    def with_dependencies(self, deps: list[str]) -> "PlanActionCreate":
        """Return a copy with updated dependencies."""
        return PlanActionCreate(
            **{**self.model_dump(), "dependencies": deps}
        )


# =============================================================================
# PLAN PHASE (for synthesis)
# =============================================================================

class PlanPhaseCreate(BaseModel):
    """Model for creating a plan phase during synthesis.
    
    This is the synthesis-time representation that groups actions by phase type.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    phase_type: PhaseType = Field(..., description="Type of phase")
    actions: list[PlanActionCreate] = Field(
        default_factory=list,
        description="Actions in this phase, sequenced by dependencies"
    )
    status: PhaseStatus = Field(
        default=PhaseStatus.PROPOSED,
        description="Current status"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator("actions", mode="before")
    @classmethod
    def validate_actions(cls, v):
        """Ensure actions is a list."""
        if v is None:
            return []
        return list(v)
    
    @property
    def action_count(self) -> int:
        """Return the number of actions in this phase."""
        return len(self.actions)
    
    @property
    def findings_by_severity(self) -> dict[str, int]:
        """Return count of actions by severity."""
        counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for action in self.actions:
            key = action.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def to_db_phase(self, audit_id: Optional[str] = None) -> dict:
        """Convert to a dict suitable for PlanPhase database model."""
        from src.db.models import PlanAction
        
        db_actions = []
        for action in self.actions:
            db_actions.append(PlanAction(
                description=action.description,
                target_entity=action.target_entity,
                fix=action.proposed_value or action.description,
                rationale=action.rationale,
            ).model_dump())
        
        return {
            "audit_id": audit_id,
            "phase_name": self.phase_type.to_phase_name(),
            "sequence": self.phase_type.order(),
            "actions": db_actions,
            "status": self.status,
        }


# =============================================================================
# PLAN
# =============================================================================

class Plan(BaseModel):
    """A complete phased improvement plan generated from an audit.
    
    Contains all phases (Critical, Refinement, Polish) with their
    sequenced actions.
    """
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    audit_session_id: str = Field(..., description="ID of the source audit session")
    screen_id: str = Field(..., description="ID of the audited screen")
    phases: list[PlanPhaseCreate] = Field(
        default_factory=list,
        description="Phases in execution order"
    )
    status: PlanStatus = Field(
        default=PlanStatus.PENDING,
        description="Overall plan status"
    )
    summary: Optional["PlanSummary"] = Field(
        default=None,
        description="Plan summary statistics"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator("phases", mode="before")
    @classmethod
    def sort_phases(cls, v):
        """Ensure phases are sorted by execution order."""
        if v is None:
            return []
        phases = list(v)
        return sorted(phases, key=lambda p: p.phase_type.order())
    
    def get_phase(self, phase_type: PhaseType) -> Optional[PlanPhaseCreate]:
        """Get a specific phase by type."""
        for phase in self.phases:
            if phase.phase_type == phase_type:
                return phase
        return None
    
    @property
    def total_actions(self) -> int:
        """Return total number of actions across all phases."""
        return sum(phase.action_count for phase in self.phases)
    
    @property
    def phase_count(self) -> int:
        """Return number of phases with actions."""
        return len([p for p in self.phases if p.action_count > 0])
    
    def compute_summary(self) -> "Plan":
        """Compute and attach summary statistics."""
        summary = PlanSummary.from_plan(self)
        # Update summary in place to avoid re-validation issues
        self.summary = summary
        return self


# =============================================================================
# PLAN SUMMARY
# =============================================================================

class PlanSummary(BaseModel):
    """Summary statistics for a plan."""
    
    total_actions: int = Field(default=0, description="Total actions across all phases")
    total_phases: int = Field(default=0, description="Number of phases with actions")
    by_phase: dict[str, int] = Field(
        default_factory=dict,
        description="Action count by phase type"
    )
    by_severity: dict[str, int] = Field(
        default_factory=dict,
        description="Action count by severity"
    )
    by_dimension: dict[str, int] = Field(
        default_factory=dict,
        description="Action count by audit dimension"
    )
    critical_count: int = Field(
        default=0,
        description="Number of critical severity actions"
    )
    high_count: int = Field(
        default=0,
        description="Number of high severity actions"
    )
    has_accessibility_issues: bool = Field(
        default=False,
        description="Whether any accessibility issues exist"
    )
    has_hierarchy_issues: bool = Field(
        default=False,
        description="Whether any hierarchy issues exist"
    )
    
    @classmethod
    def from_plan(cls, plan: Plan) -> "PlanSummary":
        """Create summary from a plan."""
        by_phase: dict[str, int] = {}
        by_severity: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        by_dimension: dict[str, int] = {}
        critical_count = 0
        high_count = 0
        has_accessibility_issues = False
        has_hierarchy_issues = False
        
        for phase in plan.phases:
            phase_key = phase.phase_type.value
            by_phase[phase_key] = phase.action_count
            
            for action in phase.actions:
                # Count by severity
                sev_key = action.severity.value
                by_severity[sev_key] = by_severity.get(sev_key, 0) + 1
                
                # Track critical/high
                if action.severity == Severity.CRITICAL:
                    critical_count += 1
                elif action.severity == Severity.HIGH:
                    high_count += 1
                
                # Count by dimension
                dim_key = action.dimension.value
                by_dimension[dim_key] = by_dimension.get(dim_key, 0) + 1
                
                # Track special dimensions
                if action.dimension == AuditDimension.ACCESSIBILITY:
                    has_accessibility_issues = True
                elif action.dimension == AuditDimension.VISUAL_HIERARCHY:
                    has_hierarchy_issues = True
        
        return cls(
            total_actions=plan.total_actions,
            total_phases=plan.phase_count,
            by_phase=by_phase,
            by_severity=by_severity,
            by_dimension=by_dimension,
            critical_count=critical_count,
            high_count=high_count,
            has_accessibility_issues=has_accessibility_issues,
            has_hierarchy_issues=has_hierarchy_issues,
        )
    
    @property
    def priority_score(self) -> float:
        """Calculate a priority score for this plan.
        
        Higher score = more urgent plan.
        Weights: critical=10, high=5, accessibility=3, hierarchy=2
        """
        score = 0.0
        score += self.critical_count * 10
        score += self.high_count * 5
        if self.has_accessibility_issues:
            score += 3
        if self.has_hierarchy_issues:
            score += 2
        return score
    
    @property
    def estimated_effort(self) -> str:
        """Estimate effort level based on action count.
        
        Returns: 'low', 'medium', 'high', or 'very_high'
        """
        total = self.total_actions
        if total <= 5:
            return "low"
        elif total <= 15:
            return "medium"
        elif total <= 30:
            return "high"
        else:
            return "very_high"


# Update forward reference
Plan.model_rebuild()
"""
Pydantic models for design system proposals.

Defines models for token proposals, component proposals, and design system
evolution recommendations derived from audit findings.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


from pydantic import BaseModel, Field, field_validator, model_validator


class ProposalType(str, Enum):
    """Types of design system proposals."""
    
    NEW_TOKEN = "new_token"
    TOKEN_VARIANT = "token_variant"
    COMPONENT_VARIANT = "component_variant"
    STANDARD_UPDATE = "standard_update"


class TokenType(str, Enum):
    """Token type categories."""
    
    COLOR = "color"
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    RADIUS = "radius"
    SHADOW = "shadow"
    MOTION = "motion"


class Priority(str, Enum):
    """Proposal priority levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# TOKEN PROPOSAL
# =============================================================================

class TokenProposal(BaseModel):
    """Proposal for a new or variant design token."""
    
    token_name: str = Field(
        ...,
        min_length=1,
        description="Proposed token name (e.g., --color-warning-light)"
    )
    token_type: TokenType = Field(
        ...,
        description="Category of token (color, spacing, typography, etc.)"
    )
    proposed_value: str = Field(
        ...,
        min_length=1,
        description="Suggested value for the token"
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Why this token should be added"
    )
    usage_count: int = Field(
        default=1,
        ge=1,
        description="Number of times this pattern was detected"
    )
    affected_screens: list[str] = Field(
        default_factory=list,
        description="Screen IDs where this pattern was found"
    )
    existing_token_conflict: Optional[str] = Field(
        default=None,
        description="Name of existing token this might conflict with"
    )
    
    model_config = {"frozen": True}
    
    def to_markdown(self) -> str:
        """Generate markdown representation of the token proposal."""
        lines = [
            f"### Token Proposal: `{self.token_name}`",
            "",
            f"**Type:** {self.token_type.value}",
            f"**Proposed Value:** `{self.proposed_value}`",
            f"**Usage Count:** {self.usage_count}",
            "",
            f"**Rationale:** {self.rationale}",
        ]
        
        if self.affected_screens:
            lines.extend([
                "",
                f"**Affected Screens:** {len(self.affected_screens)} screens"
            ])
        
        if self.existing_token_conflict:
            lines.extend([
                "",
                f"⚠️ **Potential Conflict:** May conflict with `{self.existing_token_conflict}`"
            ])
        
        return "\n".join(lines)


# =============================================================================
# COMPONENT PROPOSAL
# =============================================================================

class ComponentVariant(BaseModel):
    """A specific variant for a component."""
    
    variant_name: str = Field(
        ...,
        min_length=1,
        description="Name of the variant (e.g., 'elevated', 'outlined')"
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="CSS properties that define this variant"
    )
    description: str = Field(
        default="",
        description="Human-readable description of the variant"
    )
    
    model_config = {"frozen": True}


class ComponentProposal(BaseModel):
    """Proposal for a new component variant."""
    
    component_type: str = Field(
        ...,
        min_length=1,
        description="Base component type (e.g., 'button', 'card')"
    )
    variant_name: str = Field(
        ...,
        min_length=1,
        description="Name of the proposed variant"
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="CSS properties that define this variant"
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Why this variant should be added"
    )
    detected_instances: int = Field(
        default=1,
        ge=1,
        description="Number of instances detected with this pattern"
    )
    affected_screens: list[str] = Field(
        default_factory=list,
        description="Screen IDs where this pattern was found"
    )
    example_components: list[str] = Field(
        default_factory=list,
        description="Component IDs that exemplify this variant"
    )
    
    model_config = {"frozen": True}
    
    def to_markdown(self) -> str:
        """Generate markdown representation of the component proposal."""
        lines = [
            f"### Component Variant Proposal: `{self.component_type}-{self.variant_name}`",
            "",
            f"**Detected Instances:** {self.detected_instances}",
            "",
            f"**Rationale:** {self.rationale}",
            "",
            "**Properties:**",
            ""
        ]
        
        for prop, value in self.properties.items():
            lines.append(f"- `{prop}: {value}`")
        
        if self.affected_screens:
            lines.extend([
                "",
                f"**Affected Screens:** {len(self.affected_screens)} screens"
            ])
        
        return "\n".join(lines)


# =============================================================================
# BEFORE/AFTER DESCRIPTION
# =============================================================================

class BeforeAfterDescription(BaseModel):
    """Text description of before/after state for a proposal."""
    
    before_text: str = Field(
        ...,
        min_length=1,
        description="Description of current state"
    )
    after_text: str = Field(
        ...,
        min_length=1,
        description="Description of proposed state"
    )
    key_changes: list[str] = Field(
        default_factory=list,
        description="List of key changes between before and after"
    )
    benefit: str = Field(
        default="",
        description="Primary benefit of making this change"
    )
    
    model_config = {"frozen": True}
    
    def to_markdown(self) -> str:
        """Generate markdown representation."""
        lines = [
            "#### Before/After Comparison",
            "",
            f"**Currently:** {self.before_text}",
            "",
            f"**Proposed:** {self.after_text}",
        ]
        
        if self.benefit:
            lines.extend(["", f"**Benefit:** {self.benefit}"])
        
        if self.key_changes:
            lines.extend(["", "**Key Changes:**", ""])
            for change in self.key_changes:
                lines.append(f"- {change}")
        
        return "\n".join(lines)
    
    def to_summary(self) -> str:
        """Generate a one-line summary."""
        return f"Currently: {self.before_text}. Proposed: {self.after_text}. Benefit: {self.benefit}"


# =============================================================================
# DESIGN SYSTEM PROPOSAL (AGGREGATE)
# =============================================================================

class DesignSystemProposal(BaseModel):
    """Aggregate design system proposal with multiple recommendations."""
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this proposal"
    )
    token_proposals: list[TokenProposal] = Field(
        default_factory=list,
        description="Token proposals"
    )
    component_proposals: list[ComponentProposal] = Field(
        default_factory=list,
        description="Component variant proposals"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Overall priority of this proposal set"
    )
    impact_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Impact score (0.0-1.0)"
    )
    total_affected_screens: int = Field(
        default=0,
        ge=0,
        description="Total number of unique screens affected"
    )
    audit_session_id: Optional[str] = Field(
        default=None,
        description="ID of the audit session that generated this proposal"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this proposal was created"
    )
    before_after_summaries: dict[str, BeforeAfterDescription] = Field(
        default_factory=dict,
        description="Before/after descriptions keyed by proposal identifier"
    )
    
    def total_proposals(self) -> int:
        """Return total number of proposals."""
        return len(self.token_proposals) + len(self.component_proposals)
    
    def proposals_by_type(self) -> dict[str, int]:
        """Return count of proposals by type."""
        return {
            "token": len(self.token_proposals),
            "component": len(self.component_proposals),
            "total": self.total_proposals(),
        }
    
    def get_highest_impact_proposal(self) -> Optional[TokenProposal | ComponentProposal]:
        """Get the proposal with highest usage count."""
        all_proposals: list[TokenProposal | ComponentProposal] = [
            *self.token_proposals,
            *self.component_proposals
        ]
        
        if not all_proposals:
            return None
        
        return max(
            all_proposals,
            key=lambda p: p.usage_count if isinstance(p, TokenProposal) else p.detected_instances
        )
    
    def to_markdown(self) -> str:
        """Generate markdown representation of the full proposal."""
        lines = [
            "# Design System Proposal",
            "",
            f"**ID:** {self.id}",
            f"**Priority:** {self.priority.value.upper()}",
            f"**Impact Score:** {self.impact_score:.2f}",
            f"**Created:** {self.created_at.isoformat()}",
            "",
            "## Summary",
            "",
            f"- **Token Proposals:** {len(self.token_proposals)}",
            f"- **Component Proposals:** {len(self.component_proposals)}",
            f"- **Total Affected Screens:** {self.total_affected_screens}",
            "",
        ]
        
        if self.token_proposals:
            lines.extend([
                "## Token Proposals",
                ""
            ])
            for proposal in self.token_proposals:
                lines.extend([proposal.to_markdown(), ""])
        
        if self.component_proposals:
            lines.extend([
                "## Component Proposals",
                ""
            ])
            for proposal in self.component_proposals:
                lines.extend([proposal.to_markdown(), ""])
        
        if self.before_after_summaries:
            lines.extend([
                "## Before/After Summaries",
                ""
            ])
            for key, desc in self.before_after_summaries.items():
                lines.extend([f"### {key}", "", desc.to_markdown(), ""])
        
        return "\n".join(lines)
    
    def to_json_dict(self) -> dict[str, Any]:
        """Export to JSON-serializable dict."""
        return {
            "id": self.id,
            "priority": self.priority.value,
            "impact_score": self.impact_score,
            "total_affected_screens": self.total_affected_screens,
            "audit_session_id": self.audit_session_id,
            "created_at": self.created_at.isoformat(),
            "proposals_by_type": self.proposals_by_type(),
            "token_proposals": [p.model_dump() for p in self.token_proposals],
            "component_proposals": [p.model_dump() for p in self.component_proposals],
            "before_after_summaries": {
                k: v.model_dump() for k, v in self.before_after_summaries.items()
            }
        }
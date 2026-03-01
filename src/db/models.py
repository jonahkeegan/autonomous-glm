"""
Pydantic models for Autonomous-GLM database entities.

Provides data validation, serialization, and type safety for all entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS
# =============================================================================

class Severity(str, Enum):
    """Severity levels for audit findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PhaseStatus(str, Enum):
    """Status options for plan phases."""
    PROPOSED = "proposed"
    IN_PROGRESS = "in-progress"
    COMPLETE = "complete"


class TokenType(str, Enum):
    """Types of design system tokens."""
    COLOR = "color"
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    BORDER = "border"
    SHADOW = "shadow"
    ANIMATION = "animation"


class PhaseName(str, Enum):
    """Names for plan phases."""
    CRITICAL = "Critical"
    REFINEMENT = "Refinement"
    POLISH = "Polish"


class EntityType(str, Enum):
    """Entity types that can have audit findings."""
    SCREEN = "Screen"
    FLOW = "Flow"
    COMPONENT = "Component"


# =============================================================================
# BASE MODEL
# =============================================================================

class BaseEntity(BaseModel):
    """Base model with common fields for all entities."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


# =============================================================================
# BOUNDING BOX
# =============================================================================

class BoundingBox(BaseModel):
    """Bounding box for component positioning."""
    x: float
    y: float
    width: float
    height: float
    
    def to_json(self) -> str:
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> "BoundingBox":
        return cls.model_validate_json(json_str)


# =============================================================================
# SCREEN
# =============================================================================

class Screen(BaseEntity):
    """Captured screen with hierarchy and layout data."""
    
    name: str = Field(..., min_length=1, description="Screen name")
    image_path: str = Field(..., min_length=1, description="Path to screenshot file")
    hierarchy: Optional[dict[str, Any]] = Field(
        default=None, 
        description="Nested structure of components"
    )
    
    @field_validator("image_path")
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("image_path cannot be empty")
        return v


class ScreenCreate(BaseModel):
    """Model for creating a new screen."""
    name: str
    image_path: str
    hierarchy: Optional[dict[str, Any]] = None


class ScreenUpdate(BaseModel):
    """Model for updating an existing screen."""
    name: Optional[str] = None
    image_path: Optional[str] = None
    hierarchy: Optional[dict[str, Any]] = None


# =============================================================================
# FLOW
# =============================================================================

class Flow(BaseEntity):
    """Sequence of screens representing an activity."""
    
    name: str = Field(..., min_length=1, description="Flow name")
    video_path: Optional[str] = Field(
        default=None,
        description="Path to source video file"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional flow metadata"
    )
    screen_ids: list[str] = Field(
        default_factory=list,
        description="Ordered list of screen IDs in this flow"
    )


class FlowCreate(BaseModel):
    """Model for creating a new flow."""
    name: str
    video_path: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    screen_ids: list[str] = Field(default_factory=list)


class FlowUpdate(BaseModel):
    """Model for updating an existing flow."""
    name: Optional[str] = None
    video_path: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    screen_ids: Optional[list[str]] = None


# =============================================================================
# COMPONENT
# =============================================================================

class Component(BaseEntity):
    """Parsed UI element with bounding box and properties."""
    
    screen_id: str = Field(..., description="ID of parent screen")
    type: str = Field(..., min_length=1, description="Component type (button, input, etc.)")
    bounding_box: BoundingBox = Field(..., description="Component position and size")
    properties: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional component properties"
    )
    token_ids: list[str] = Field(
        default_factory=list,
        description="IDs of system tokens used by this component"
    )


class ComponentCreate(BaseModel):
    """Model for creating a new component."""
    screen_id: str
    type: str
    bounding_box: BoundingBox
    properties: Optional[dict[str, Any]] = None
    token_ids: list[str] = Field(default_factory=list)


class ComponentUpdate(BaseModel):
    """Model for updating an existing component."""
    type: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None
    properties: Optional[dict[str, Any]] = None
    token_ids: Optional[list[str]] = None


# =============================================================================
# SYSTEM TOKEN
# =============================================================================

class SystemToken(BaseEntity):
    """Design system variable (color, spacing, typography, etc.)."""
    
    name: str = Field(..., min_length=1, description="Token name")
    type: TokenType = Field(..., description="Token type")
    value: str = Field(..., min_length=1, description="Token value")
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("name cannot be empty")
        return v.strip()


class SystemTokenCreate(BaseModel):
    """Model for creating a new system token."""
    name: str
    type: TokenType
    value: str
    description: Optional[str] = None


class SystemTokenUpdate(BaseModel):
    """Model for updating an existing system token."""
    name: Optional[str] = None
    type: Optional[TokenType] = None
    value: Optional[str] = None
    description: Optional[str] = None


# =============================================================================
# AUDIT FINDING
# =============================================================================

class AuditFinding(BaseEntity):
    """Issue detected during UI/UX audit."""
    
    entity_type: EntityType = Field(..., description="Type of entity with issue")
    entity_id: str = Field(..., description="ID of entity with issue")
    issue: str = Field(..., min_length=1, description="Description of the issue")
    rationale: Optional[str] = Field(
        default=None,
        description="Why this is an issue"
    )
    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Issue severity level"
    )
    related_standard: Optional[str] = Field(
        default=None,
        description="Reference to design system or WCAG criterion"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional finding metadata"
    )


class AuditFindingCreate(BaseModel):
    """Model for creating a new audit finding."""
    entity_type: EntityType
    entity_id: str
    issue: str
    rationale: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    related_standard: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class AuditFindingUpdate(BaseModel):
    """Model for updating an existing audit finding."""
    issue: Optional[str] = None
    rationale: Optional[str] = None
    severity: Optional[Severity] = None
    related_standard: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


# =============================================================================
# PLAN PHASE
# =============================================================================

class PlanAction(BaseModel):
    """A single action within a plan phase."""
    description: str = Field(..., description="What to do")
    target_entity: str = Field(..., description="Entity to modify")
    fix: str = Field(..., description="How to fix the issue")
    rationale: Optional[str] = Field(default=None, description="Why this fix")


class PlanPhase(BaseEntity):
    """A phase of a phased improvement plan."""
    
    audit_id: Optional[str] = Field(
        default=None,
        description="ID of related audit finding"
    )
    phase_name: PhaseName = Field(..., description="Phase name")
    sequence: int = Field(..., ge=1, description="Order in plan")
    actions: list[PlanAction] = Field(
        default_factory=list,
        description="List of actions in this phase"
    )
    status: PhaseStatus = Field(
        default=PhaseStatus.PROPOSED,
        description="Current status"
    )
    updated_at: Optional[datetime] = Field(default=None)


class PlanPhaseCreate(BaseModel):
    """Model for creating a new plan phase."""
    audit_id: Optional[str] = None
    phase_name: PhaseName
    sequence: int
    actions: list[PlanAction] = Field(default_factory=list)
    status: PhaseStatus = PhaseStatus.PROPOSED


class PlanPhaseUpdate(BaseModel):
    """Model for updating an existing plan phase."""
    phase_name: Optional[PhaseName] = None
    sequence: Optional[int] = None
    actions: Optional[list[PlanAction]] = None
    status: Optional[PhaseStatus] = None


# =============================================================================
# DATABASE ROW CONVERSION
# =============================================================================

def row_to_screen(row: dict) -> Screen:
    """Convert a database row to a Screen model."""
    import json
    
    return Screen(
        id=row["id"],
        name=row["name"],
        image_path=row["image_path"],
        hierarchy=json.loads(row["hierarchy"]) if row.get("hierarchy") else None,
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
    )


def row_to_flow(row: dict, screen_ids: list[str] | None = None) -> Flow:
    """Convert a database row to a Flow model."""
    import json
    
    return Flow(
        id=row["id"],
        name=row["name"],
        video_path=row.get("video_path"),
        metadata=json.loads(row["metadata"]) if row.get("metadata") else None,
        screen_ids=screen_ids or [],
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
    )


def row_to_component(row: dict, token_ids: list[str] | None = None) -> Component:
    """Convert a database row to a Component model."""
    import json
    
    bbox_data = json.loads(row["bounding_box"])
    
    return Component(
        id=row["id"],
        screen_id=row["screen_id"],
        type=row["type"],
        bounding_box=BoundingBox(**bbox_data),
        properties=json.loads(row["properties"]) if row.get("properties") else None,
        token_ids=token_ids or [],
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
    )


def row_to_system_token(row: dict) -> SystemToken:
    """Convert a database row to a SystemToken model."""
    type_map = {
        1: TokenType.COLOR,
        2: TokenType.SPACING,
        3: TokenType.TYPOGRAPHY,
        4: TokenType.BORDER,
        5: TokenType.SHADOW,
        6: TokenType.ANIMATION,
    }
    
    return SystemToken(
        id=row["id"],
        name=row["name"],
        type=type_map.get(row["type_id"], TokenType.COLOR),
        value=row["value"],
        description=row.get("description"),
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
    )


def row_to_audit_finding(row: dict) -> AuditFinding:
    """Convert a database row to an AuditFinding model."""
    import json
    
    severity_map = {
        1: Severity.LOW,
        2: Severity.MEDIUM,
        3: Severity.HIGH,
        4: Severity.CRITICAL,
    }
    
    return AuditFinding(
        id=row["id"],
        entity_type=EntityType(row["entity_type"]),
        entity_id=row["entity_id"],
        issue=row["issue"],
        rationale=row.get("rationale"),
        severity=severity_map.get(row["severity_id"], Severity.MEDIUM),
        related_standard=row.get("related_standard"),
        metadata=json.loads(row["metadata"]) if row.get("metadata") else None,
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"]
    )


def row_to_plan_phase(row: dict) -> PlanPhase:
    """Convert a database row to a PlanPhase model."""
    import json
    
    status_map = {
        1: PhaseStatus.PROPOSED,
        2: PhaseStatus.IN_PROGRESS,
        3: PhaseStatus.COMPLETE,
    }
    
    actions_data = json.loads(row["actions"]) if row.get("actions") else []
    actions = [PlanAction(**a) for a in actions_data]
    
    return PlanPhase(
        id=row["id"],
        audit_id=row.get("audit_id"),
        phase_name=PhaseName(row["phase_name"]),
        sequence=row["sequence"],
        actions=actions,
        status=status_map.get(row["status_id"], PhaseStatus.PROPOSED),
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None
    )
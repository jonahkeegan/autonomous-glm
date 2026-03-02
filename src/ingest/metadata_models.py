"""
Metadata models for Autonomous-GLM artifacts.

Pydantic models for context metadata associated with screenshots, videos, and flows.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class MetadataSource(str, Enum):
    """Origin of metadata."""
    FILE = "file"
    API = "api"
    AGENT = "agent"
    MANUAL = "manual"


class ArtifactType(str, Enum):
    """Type of artifact metadata applies to."""
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    FLOW = "flow"


# =============================================================================
# BASE METADATA
# =============================================================================

class ArtifactMetadata(BaseModel):
    """
    User-provided context metadata for artifacts.
    
    Contains project, feature, and tagging information that helps
    organize and contextualize ingested artifacts.
    """
    project: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Project name or identifier"
    )
    feature: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Feature or module name"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags for categorization and search"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Free-form notes about the artifact"
    )
    source: MetadataSource = Field(
        default=MetadataSource.API,
        description="Origin of the metadata"
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata"
    )
    
    # Timestamps
    captured_at: Optional[datetime] = Field(
        default=None,
        description="When the artifact was captured"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this metadata was created"
    )


# =============================================================================
# SCREENSHOT METADATA
# =============================================================================

class ScreenMetadata(ArtifactMetadata):
    """
    Screenshot-specific metadata.
    
    Extends base metadata with screenshot-specific fields.
    """
    artifact_type: ArtifactType = Field(
        default=ArtifactType.SCREENSHOT,
        description="Type of artifact"
    )
    screen_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable screen name"
    )
    url: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="URL where screenshot was captured"
    )
    viewport_width: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Viewport width in pixels"
    )
    viewport_height: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Viewport height in pixels"
    )
    device_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Device type (desktop, mobile, tablet)"
    )
    browser: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Browser name and version"
    )
    os: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Operating system"
    )


# =============================================================================
# FLOW/VIDEO METADATA
# =============================================================================

class FlowMetadata(ArtifactMetadata):
    """
    Video/flow-specific metadata.
    
    Extends base metadata with video and flow-specific fields.
    """
    artifact_type: ArtifactType = Field(
        default=ArtifactType.VIDEO,
        description="Type of artifact"
    )
    flow_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable flow name"
    )
    user_journey: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Description of user journey being recorded"
    )
    start_url: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Starting URL for the flow"
    )
    end_url: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Ending URL for the flow"
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="Duration of the video in seconds"
    )
    interaction_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of user interactions in the flow"
    )
    device_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Device type (desktop, mobile, tablet)"
    )
    browser: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Browser name and version"
    )


# =============================================================================
# METADATA VALIDATION RESULT
# =============================================================================

class MetadataValidationResult(BaseModel):
    """Result of metadata validation."""
    valid: bool = Field(..., description="Whether metadata is valid")
    errors: list[str] = Field(
        default_factory=list,
        description="Validation errors if any"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings if any"
    )
    metadata: Optional[ArtifactMetadata] = Field(
        default=None,
        description="Parsed metadata if valid"
    )
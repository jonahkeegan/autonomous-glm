"""
Request and response models for Autonomous-GLM API.

Pydantic models for API input validation and output serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class IngestStatus(str, Enum):
    """Status of an ingestion operation."""
    SUCCESS = "success"
    PROCESSING = "processing"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CheckStatus(str, Enum):
    """Individual health check status."""
    OK = "ok"
    ERROR = "error"
    WARNING = "warning"


# =============================================================================
# ERROR RESPONSE (RFC 7807)
# =============================================================================

class ErrorResponse(BaseModel):
    """
    RFC 7807 Problem Details error response.
    
    Standardized error format for API errors.
    """
    type: str = Field(..., description="URI reference identifying the error type")
    title: str = Field(..., description="Short human-readable summary")
    status: int = Field(..., description="HTTP status code")
    detail: Optional[str] = Field(default=None, description="Detailed error message")
    instance: Optional[str] = Field(default=None, description="URI to specific occurrence")


# =============================================================================
# SCREENSHOT INGEST
# =============================================================================

class ScreenshotIngestResponse(BaseModel):
    """Response for screenshot ingestion."""
    ingest_id: str = Field(..., description="Unique ingestion ID")
    screen_id: str = Field(..., description="ID of the created screen entity")
    status: IngestStatus = Field(..., description="Ingestion status")
    storage_path: str = Field(..., description="Path where screenshot is stored")
    duplicate: bool = Field(default=False, description="Whether this was a duplicate")
    message: Optional[str] = Field(default=None, description="Additional status message")


# =============================================================================
# VIDEO INGEST
# =============================================================================

class VideoIngestResponse(BaseModel):
    """Response for video ingestion."""
    ingest_id: str = Field(..., description="Unique ingestion ID")
    flow_id: str = Field(..., description="ID of the created flow entity")
    status: IngestStatus = Field(..., description="Ingestion status")
    frame_count: int = Field(..., ge=0, description="Number of frames extracted")
    storage_path: str = Field(..., description="Path where video/frames are stored")
    message: Optional[str] = Field(default=None, description="Additional status message")


# =============================================================================
# INGEST STATUS
# =============================================================================

class IngestStatusResponse(BaseModel):
    """Response for querying ingestion status."""
    ingest_id: str = Field(..., description="Unique ingestion ID")
    artifact_type: str = Field(..., description="Type of artifact (screenshot/video)")
    status: IngestStatus = Field(..., description="Current ingestion status")
    created_at: datetime = Field(..., description="When ingestion was initiated")
    artifact_id: str = Field(..., description="ID of the created artifact")
    message: Optional[str] = Field(default=None, description="Status message or error")


# =============================================================================
# HEALTH CHECK
# =============================================================================

class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""
    status: HealthStatus = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    checks: dict[str, str] = Field(
        default_factory=dict,
        description="Individual check statuses"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the health check was performed"
    )
"""
Pydantic models for screenshot ingestion.

Defines data models for validation results, ingestion results, and configuration.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ImageFormat(str, Enum):
    """Supported image formats for ingestion."""
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


class IngestStatus(str, Enum):
    """Status of an ingestion operation."""
    SUCCESS = "success"
    FAILURE = "failure"
    DUPLICATE = "duplicate"


class ValidationErrorCode(str, Enum):
    """Error codes for validation failures."""
    FILE_NOT_FOUND = "file_not_found"
    INVALID_MAGIC_BYTES = "invalid_magic_bytes"
    UNSUPPORTED_FORMAT = "unsupported_format"
    FILE_TOO_LARGE = "file_too_large"
    FILE_EMPTY = "file_empty"
    DIMENSIONS_TOO_SMALL = "dimensions_too_small"
    DIMENSIONS_TOO_LARGE = "dimensions_too_large"
    CORRUPTED_IMAGE = "corrupted_image"
    PERMISSION_DENIED = "permission_denied"


class ValidationError(BaseModel):
    """A single validation error."""
    code: ValidationErrorCode
    message: str
    detail: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of screenshot validation."""
    valid: bool = Field(..., description="Whether the file passed validation")
    errors: list[ValidationError] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
    format: Optional[ImageFormat] = Field(
        default=None,
        description="Detected image format if valid"
    )
    dimensions: Optional[tuple[int, int]] = Field(
        default=None,
        description="Image dimensions (width, height) if valid"
    )
    file_size: Optional[int] = Field(
        default=None,
        description="File size in bytes if valid"
    )
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class IngestResult(BaseModel):
    """Result of a screenshot ingestion operation."""
    success: bool = Field(..., description="Whether ingestion succeeded")
    status: IngestStatus = Field(..., description="Detailed status of ingestion")
    ingest_id: Optional[str] = Field(
        default=None,
        description="Unique ingest ID (content hash based)"
    )
    screen_id: Optional[str] = Field(
        default=None,
        description="Database screen entity ID"
    )
    storage_path: Optional[str] = Field(
        default=None,
        description="Path where file is stored"
    )
    original_path: Optional[str] = Field(
        default=None,
        description="Original file path that was ingested"
    )
    errors: list[ValidationError] = Field(
        default_factory=list,
        description="List of errors if ingestion failed"
    )
    is_duplicate: bool = Field(
        default=False,
        description="Whether this was a duplicate of an existing file"
    )
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0


class IngestConfig(BaseModel):
    """Configuration for screenshot ingestion."""
    max_file_size_mb: float = Field(
        default=50.0,
        ge=0.1,
        le=1000.0,
        description="Maximum file size in megabytes"
    )
    min_width: int = Field(
        default=100,
        ge=1,
        description="Minimum image width in pixels"
    )
    min_height: int = Field(
        default=100,
        ge=1,
        description="Minimum image height in pixels"
    )
    max_width: int = Field(
        default=10000,
        ge=100,
        description="Maximum image width in pixels"
    )
    max_height: int = Field(
        default=10000,
        ge=100,
        description="Maximum image height in pixels"
    )
    allowed_formats: list[ImageFormat] = Field(
        default=[ImageFormat.PNG, ImageFormat.JPEG, ImageFormat.JPG],
        description="List of allowed image formats"
    )
    screenshots_dir: str = Field(
        default="./data/artifacts/screenshots",
        description="Base directory for screenshot storage"
    )
    
    @field_validator("max_width")
    @classmethod
    def validate_max_width(cls, v: int, info) -> int:
        """Ensure max_width > min_width."""
        min_width = info.data.get("min_width", 100)
        if v <= min_width:
            raise ValueError("max_width must be greater than min_width")
        return v
    
    @field_validator("max_height")
    @classmethod
    def validate_max_height(cls, v: int, info) -> int:
        """Ensure max_height > min_height."""
        min_height = info.data.get("min_height", 100)
        if v <= min_height:
            raise ValueError("max_height must be greater than min_height")
        return v
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return int(self.max_file_size_mb * 1024 * 1024)
    
    @property
    def min_dimensions(self) -> tuple[int, int]:
        """Get minimum dimensions as tuple."""
        return (self.min_width, self.min_height)
    
    @property
    def max_dimensions(self) -> tuple[int, int]:
        """Get maximum dimensions as tuple."""
        return (self.max_width, self.max_height)
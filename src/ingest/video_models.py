"""
Pydantic models for video ingestion.

Defines data models for video validation results, frame extraction, and ingestion results.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VideoContainer(str, Enum):
    """Supported video container formats."""
    MP4 = "mp4"
    MOV = "mov"


class VideoCodec(str, Enum):
    """Supported video codecs."""
    H264 = "h264"
    H265 = "h265"
    HEVC = "hevc"
    VP8 = "vp8"
    VP9 = "vp9"


class VideoValidationErrorCode(str, Enum):
    """Error codes for video validation failures."""
    FILE_NOT_FOUND = "file_not_found"
    INVALID_CONTAINER = "invalid_container"
    UNSUPPORTED_CONTAINER = "unsupported_container"
    UNSUPPORTED_CODEC = "unsupported_codec"
    FILE_TOO_LARGE = "file_too_large"
    FILE_EMPTY = "file_empty"
    DURATION_TOO_LONG = "duration_too_long"
    RESOLUTION_TOO_LARGE = "resolution_too_large"
    CORRUPTED_VIDEO = "corrupted_video"
    PERMISSION_DENIED = "permission_denied"
    FFMPEG_NOT_AVAILABLE = "ffmpeg_not_available"
    EXTRACTION_FAILED = "extraction_failed"


class VideoValidationError(BaseModel):
    """A single video validation error."""
    code: VideoValidationErrorCode
    message: str
    detail: Optional[str] = None


class VideoValidationResult(BaseModel):
    """Result of video file validation."""
    valid: bool = Field(..., description="Whether the file passed validation")
    errors: list[VideoValidationError] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
    container: Optional[VideoContainer] = Field(
        default=None,
        description="Detected container format if valid"
    )
    codec: Optional[VideoCodec] = Field(
        default=None,
        description="Detected video codec if valid"
    )
    duration: Optional[float] = Field(
        default=None,
        description="Video duration in seconds if valid"
    )
    resolution: Optional[tuple[int, int]] = Field(
        default=None,
        description="Video resolution (width, height) if valid"
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


class FrameInfo(BaseModel):
    """Information about an extracted video frame."""
    frame_number: int = Field(..., ge=0, description="Frame sequence number")
    timestamp: float = Field(..., ge=0.0, description="Timestamp in seconds")
    temp_path: Optional[Path] = Field(
        default=None,
        description="Temporary path to extracted frame"
    )
    content_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 hash of frame content"
    )
    width: Optional[int] = Field(default=None, description="Frame width")
    height: Optional[int] = Field(default=None, description="Frame height")
    
    model_config = {
        "arbitrary_types_allowed": True
    }


class VideoIngestConfig(BaseModel):
    """Configuration for video ingestion."""
    max_file_size_mb: float = Field(
        default=500.0,
        ge=0.1,
        le=10000.0,
        description="Maximum video file size in megabytes"
    )
    max_duration_seconds: float = Field(
        default=1800.0,  # 30 minutes
        ge=1.0,
        le=7200.0,
        description="Maximum video duration in seconds"
    )
    max_width: int = Field(
        default=10000,
        ge=100,
        description="Maximum video width in pixels"
    )
    max_height: int = Field(
        default=10000,
        ge=100,
        description="Maximum video height in pixels"
    )
    allowed_containers: list[VideoContainer] = Field(
        default=[VideoContainer.MP4, VideoContainer.MOV],
        description="List of allowed container formats"
    )
    allowed_codecs: list[VideoCodec] = Field(
        default=[VideoCodec.H264, VideoCodec.H265, VideoCodec.HEVC, VideoCodec.VP8, VideoCodec.VP9],
        description="List of allowed video codecs"
    )
    extraction_interval: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Frame extraction interval in seconds (inverse of fps)"
    )
    max_frames: int = Field(
        default=500,
        ge=1,
        le=5000,
        description="Maximum number of frames to extract per video"
    )
    screenshots_dir: str = Field(
        default="./data/artifacts/screenshots",
        description="Base directory for extracted frame storage"
    )
    videos_dir: str = Field(
        default="./data/artifacts/videos",
        description="Base directory for video storage"
    )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return int(self.max_file_size_mb * 1024 * 1024)
    
    @property
    def max_resolution(self) -> tuple[int, int]:
        """Get maximum resolution as tuple."""
        return (self.max_width, self.max_height)
    
    @property
    def extraction_fps(self) -> float:
        """Get extraction FPS (inverse of interval)."""
        return 1.0 / self.extraction_interval


class VideoIngestStatus(str, Enum):
    """Status of a video ingestion operation."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"  # Some frames extracted, but not all


class VideoIngestResult(BaseModel):
    """Result of a video ingestion operation."""
    success: bool = Field(..., description="Whether ingestion succeeded")
    status: VideoIngestStatus = Field(..., description="Detailed status of ingestion")
    ingest_id: Optional[str] = Field(
        default=None,
        description="Unique ingest ID for the video"
    )
    flow_id: Optional[str] = Field(
        default=None,
        description="Database flow entity ID linking frames"
    )
    video_storage_path: Optional[str] = Field(
        default=None,
        description="Path where video file is stored (if stored)"
    )
    original_path: Optional[str] = Field(
        default=None,
        description="Original video file path that was ingested"
    )
    frame_count: int = Field(
        default=0,
        ge=0,
        description="Number of frames extracted"
    )
    screen_ids: list[str] = Field(
        default_factory=list,
        description="List of screen entity IDs for extracted frames"
    )
    extraction_metadata: Optional[dict] = Field(
        default=None,
        description="Metadata about the extraction process"
    )
    errors: list[VideoValidationError] = Field(
        default_factory=list,
        description="List of errors if ingestion failed"
    )
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0


class ExtractionMetadata(BaseModel):
    """Metadata about frame extraction from a video."""
    source_duration: float = Field(..., description="Original video duration in seconds")
    source_resolution: tuple[int, int] = Field(..., description="Original video resolution")
    source_codec: str = Field(..., description="Original video codec")
    source_container: str = Field(..., description="Original container format")
    extraction_interval: float = Field(..., description="Frame extraction interval used")
    total_frames_extracted: int = Field(..., description="Number of frames extracted")
    frames_skipped: int = Field(default=0, description="Frames skipped (duplicates, errors)")
    extraction_time_seconds: Optional[float] = Field(default=None, description="Time taken for extraction")
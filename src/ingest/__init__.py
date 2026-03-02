"""
Screenshot and video ingestion module for Autonomous-GLM.

Provides file validation, storage management, and database integration
for screenshot artifacts (PNG, JPEG) and video files (MP4, MOV).
"""

from .models import IngestConfig, IngestResult, ValidationResult
from .screenshot import ingest_screenshot, validate_screenshot, generate_ingest_id
from .storage import StorageManager
from .validators import ScreenshotValidator

# Video ingestion
from .video_models import (
    VideoIngestConfig,
    VideoIngestResult,
    VideoValidationResult,
    VideoValidationErrorCode,
    VideoValidationError,
    VideoContainer,
    VideoCodec,
    FrameInfo,
    ExtractionMetadata,
)
from .video_validators import VideoValidator, validate_video, check_ffmpeg_available
from .frames import FrameExtractor, extract_frames
from .video import (
    ingest_video,
    ingest_video_quick,
    get_video_ingest_config,
)

__all__ = [
    # Screenshot ingestion
    "IngestConfig",
    "IngestResult",
    "ValidationResult",
    "ingest_screenshot",
    "validate_screenshot",
    "generate_ingest_id",
    "StorageManager",
    "ScreenshotValidator",
    # Video ingestion
    "VideoIngestConfig",
    "VideoIngestResult",
    "VideoValidationResult",
    "VideoValidationErrorCode",
    "VideoValidationError",
    "VideoContainer",
    "VideoCodec",
    "FrameInfo",
    "ExtractionMetadata",
    "VideoValidator",
    "validate_video",
    "check_ffmpeg_available",
    "FrameExtractor",
    "extract_frames",
    "ingest_video",
    "ingest_video_quick",
    "get_video_ingest_config",
]

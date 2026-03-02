"""
Video ingestion handler for Autonomous-GLM.

Provides the main entry point for video ingestion, integrating
validation, frame extraction, storage, and database operations.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import get_config
from src.db.crud import create_flow, create_screen, get_flow
from src.db.models import FlowCreate, ScreenCreate

from .frames import FrameExtractor
from .models import ImageFormat, IngestConfig
from .storage import StorageManager
from .video_models import (
    ExtractionMetadata,
    FrameInfo,
    VideoContainer,
    VideoIngestConfig,
    VideoIngestResult,
    VideoIngestStatus,
    VideoValidationResult,
)
from .video_validators import VideoValidator


def get_video_ingest_config() -> VideoIngestConfig:
    """
    Get video ingestion configuration from application config.
    
    Returns:
        VideoIngestConfig with settings from config files
    """
    config = get_config()
    
    return VideoIngestConfig(
        max_file_size_mb=config.video_ingestion.max_file_size_mb,
        max_duration_seconds=config.video_ingestion.max_duration_seconds,
        max_width=config.video_ingestion.max_width,
        max_height=config.video_ingestion.max_height,
        allowed_containers=[
            VideoContainer(c) for c in config.video_ingestion.allowed_containers
        ],
        extraction_interval=config.video_ingestion.extraction_interval,
        max_frames=config.video_ingestion.max_frames,
        screenshots_dir=config.paths.screenshots_dir,
        videos_dir=config.paths.videos_dir,
    )


def generate_video_ingest_id() -> str:
    """
    Generate a unique ingest ID for a video.
    
    Returns:
        UUID string for the video
    """
    return str(uuid.uuid4())


def validate_video(
    file_path: str | Path,
    config: Optional[VideoIngestConfig] = None
) -> VideoValidationResult:
    """
    Validate a video file.
    
    Args:
        file_path: Path to the file to validate
        config: Optional configuration (uses app config if not provided)
        
    Returns:
        VideoValidationResult with validity status and any errors
    """
    config = config or get_video_ingest_config()
    validator = VideoValidator(config)
    return validator.validate(file_path)


def ingest_video(
    file_path: str | Path,
    config: Optional[VideoIngestConfig] = None,
    db_path: Optional[Path] = None,
    deduplicate: bool = True,
) -> VideoIngestResult:
    """
    Ingest a video file.
    
    This is the main entry point for video ingestion. It:
    1. Validates the file (container, codec, size, duration)
    2. Extracts frames at configured intervals
    3. Optionally deduplicates frames by content hash
    4. Stores frames using the screenshot storage pattern
    5. Creates Screen entities for each frame
    6. Creates a Flow entity linking all frames
    
    Args:
        file_path: Path to the video file to ingest
        config: Optional configuration (uses app config if not provided)
        db_path: Optional database path (uses default if not provided)
        deduplicate: Whether to remove duplicate frames (default True)
        
    Returns:
        VideoIngestResult with success status, flow ID, and frame count
    """
    path = Path(file_path)
    start_time = time.time()
    
    # Get configuration
    ingest_config = config or get_video_ingest_config()
    
    # Generate ingest ID
    ingest_id = generate_video_ingest_id()
    
    # Initialize components
    validator = VideoValidator(ingest_config)
    
    # Step 1: Validate the video file
    validation_result = validator.validate(path)
    
    if not validation_result.valid:
        return VideoIngestResult(
            success=False,
            status=VideoIngestStatus.FAILURE,
            ingest_id=ingest_id,
            original_path=str(path),
            errors=validation_result.errors,
        )
    
    # Step 2: Extract frames using FrameExtractor
    frames: list[FrameInfo] = []
    extractor = FrameExtractor(ingest_config)
    
    try:
        frames = extractor.extract_frames(path)
        
        # Step 3: Deduplicate frames if requested
        if deduplicate:
            frames = extractor.deduplicate_frames(frames)
        
        if not frames:
            return VideoIngestResult(
                success=False,
                status=VideoIngestStatus.FAILURE,
                ingest_id=ingest_id,
                original_path=str(path),
                errors=[{
                    "code": "extraction_failed",
                    "message": "No frames were extracted from the video",
                }],
            )
            
    except RuntimeError as e:
        return VideoIngestResult(
            success=False,
            status=VideoIngestStatus.FAILURE,
            ingest_id=ingest_id,
            original_path=str(path),
            errors=[{
                "code": "extraction_failed",
                "message": str(e),
            }],
        )
    finally:
        # Always cleanup temp files
        extractor.cleanup()
    
    # Step 4: Store frames and create Screen entities
    screen_ids: list[str] = []
    storage = StorageManager(IngestConfig(
        screenshots_dir=ingest_config.screenshots_dir,
    ))
    
    frames_skipped = 0
    
    for frame in frames:
        if frame.temp_path is None or not frame.temp_path.exists():
            frames_skipped += 1
            continue
        
        try:
            # Generate storage path for frame
            frame_ingest_id = storage.generate_ingest_id(frame.temp_path)
            storage_path = storage.get_storage_path(
                ingest_id=frame_ingest_id,
                format=ImageFormat.PNG,
            )
            
            # Check for duplicate
            if storage.file_exists(storage_path):
                frames_skipped += 1
                continue
            
            # Store frame
            storage.store_file(frame.temp_path, storage_path)
            
            # Create Screen entity
            screen = create_screen(
                ScreenCreate(
                    name=f"{path.stem}_frame_{frame.frame_number:06d}",
                    image_path=str(storage_path),
                ),
                db_path=db_path,
            )
            
            screen_ids.append(screen.id)
            
        except Exception:
            frames_skipped += 1
            continue
    
    # Step 5: Create Flow entity linking all frames
    extraction_time = time.time() - start_time
    
    extraction_metadata = ExtractionMetadata(
        source_duration=validation_result.duration or 0.0,
        source_resolution=validation_result.resolution or (0, 0),
        source_codec=validation_result.codec.value if validation_result.codec else "unknown",
        source_container=validation_result.container.value if validation_result.container else "unknown",
        extraction_interval=ingest_config.extraction_interval,
        total_frames_extracted=len(screen_ids),
        frames_skipped=frames_skipped,
        extraction_time_seconds=extraction_time,
    )
    
    try:
        flow = create_flow(
            FlowCreate(
                name=f"{path.stem}_flow",
                video_path=str(path),
                metadata=extraction_metadata.model_dump(),
                screen_ids=screen_ids,
            ),
            db_path=db_path,
        )
    except Exception as e:
        return VideoIngestResult(
            success=False,
            status=VideoIngestStatus.FAILURE,
            ingest_id=ingest_id,
            original_path=str(path),
            frame_count=len(screen_ids),
            screen_ids=screen_ids,
            errors=[{
                "code": "database_error",
                "message": f"Failed to create Flow entity: {str(e)}",
            }],
        )
    
    # Success!
    return VideoIngestResult(
        success=True,
        status=VideoIngestStatus.SUCCESS if len(screen_ids) == len(frames) else VideoIngestStatus.PARTIAL,
        ingest_id=ingest_id,
        flow_id=flow.id,
        original_path=str(path),
        frame_count=len(screen_ids),
        screen_ids=screen_ids,
        extraction_metadata=extraction_metadata.model_dump(),
    )


def ingest_video_quick(
    file_path: str | Path,
    config: Optional[VideoIngestConfig] = None,
    db_path: Optional[Path] = None,
) -> VideoIngestResult:
    """
    Quick video ingestion without deduplication.
    
    Faster ingestion that skips frame deduplication step.
    
    Args:
        file_path: Path to the video file
        config: Optional configuration
        db_path: Optional database path
        
    Returns:
        VideoIngestResult
    """
    return ingest_video(file_path, config, db_path, deduplicate=False)
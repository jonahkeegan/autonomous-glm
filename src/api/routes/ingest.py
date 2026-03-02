"""
Ingestion endpoints for Autonomous-GLM API.

Provides REST endpoints for uploading and ingesting screenshots and videos.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ..models import (
    ScreenshotIngestResponse,
    VideoIngestResponse,
    IngestStatusResponse,
    IngestStatus,
)
from ..config import default_api_config
from ..exceptions import (
    ValidationError,
    UnsupportedMediaTypeError,
    FileTooLargeError,
    IngestionError,
)
from ...ingest.metadata_models import ArtifactType

router = APIRouter(prefix="/ingest", tags=["ingestion"])

# In-memory store for ingest status (would be database in production)
_ingest_store: dict[str, dict] = {}


def _validate_file_size(file: UploadFile, max_size_mb: int) -> None:
    """Validate file size by reading content length."""
    # FastAPI's UploadFile doesn't expose content-length reliably
    # We'll check after reading into temp file


def _get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


@router.post(
    "/screenshot",
    response_model=ScreenshotIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Screenshot",
    description="Upload and ingest a screenshot (PNG or JPEG)",
    responses={
        201: {"description": "Screenshot ingested successfully"},
        200: {"description": "Duplicate screenshot (already exists)"},
        400: {"description": "Validation error"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported media type"},
        422: {"description": "Ingestion error"},
    },
)
async def ingest_screenshot(
    file: UploadFile = File(..., description="Screenshot file (PNG or JPEG)"),
    metadata: Optional[str] = Form(
        default=None,
        description="Optional metadata as JSON string"
    ),
) -> ScreenshotIngestResponse:
    """
    Upload and ingest a screenshot.
    
    Accepts multipart/form-data with:
    - file: The screenshot file (PNG or JPEG)
    - metadata: Optional JSON string with artifact metadata
    
    Returns:
    - 201: New screenshot ingested successfully
    - 200: Duplicate screenshot (content hash matches existing)
    """
    from ...ingest.screenshot import ingest_screenshot as do_ingest_screenshot
    from ...ingest.metadata import validate_metadata
    from ...ingest.metadata_models import ArtifactMetadata
    import uuid
    
    # Generate ingest ID
    ingest_id = str(uuid.uuid4())
    
    # Validate file extension
    ext = _get_file_extension(file.filename or "unknown")
    if ext not in ("png", "jpg", "jpeg"):
        raise UnsupportedMediaTypeError(
            detail=f"Unsupported file format: {ext}. Expected PNG or JPEG.",
            supported_types=["image/png", "image/jpeg"]
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    max_bytes = default_api_config.max_screenshot_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileTooLargeError(
            detail=f"File size ({len(content) / 1024 / 1024:.1f}MB) exceeds limit ({default_api_config.max_screenshot_size_mb}MB)",
            max_size_mb=default_api_config.max_screenshot_size_mb
        )
    
    # Parse metadata if provided
    parsed_metadata: Optional[ArtifactMetadata] = None
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            result = validate_metadata(metadata_dict)
            if not result.valid:
                raise ValidationError(
                    detail=f"Invalid metadata: {', '.join(result.errors)}",
                    field="metadata"
                )
            parsed_metadata = result.metadata
        except json.JSONDecodeError as e:
            raise ValidationError(
                detail=f"Invalid JSON in metadata: {e}",
                field="metadata"
            )
    
    # Write to temp file and ingest
    suffix = f".{ext}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Perform ingestion
        result = do_ingest_screenshot(tmp_path)
        
        # Store ingest status
        _ingest_store[ingest_id] = {
            "artifact_type": "screenshot",
            "status": IngestStatus.SUCCESS if result.success else IngestStatus.FAILED,
            "created_at": datetime.now().isoformat(),
            "artifact_id": result.screen_id,
            "message": None,
        }
        
        # Associate metadata if provided
        if parsed_metadata and result.screen_id:
            try:
                from ...ingest.metadata import associate_metadata
                associate_metadata(
                    result.screen_id,
                    parsed_metadata,
                    ArtifactType.SCREENSHOT
                )
            except Exception as e:
                # Log but don't fail - metadata is optional
                pass
        
        # Determine response status
        is_duplicate = result.is_duplicate
        response_status = IngestStatus.DUPLICATE if is_duplicate else IngestStatus.SUCCESS
        
        return ScreenshotIngestResponse(
            ingest_id=ingest_id,
            screen_id=result.screen_id or "",
            status=response_status,
            storage_path=result.storage_path or "",
            duplicate=is_duplicate,
            message=None,
        )
    except Exception as e:
        _ingest_store[ingest_id] = {
            "artifact_type": "screenshot",
            "status": IngestStatus.FAILED,
            "created_at": datetime.now().isoformat(),
            "artifact_id": "",
            "message": str(e),
        }
        raise IngestionError(
            detail=f"Screenshot ingestion failed: {e}",
            reason=str(e)
        )
    finally:
        # Cleanup temp file
        Path(tmp_path).unlink(missing_ok=True)


@router.post(
    "/video",
    response_model=VideoIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Video",
    description="Upload and ingest a video (MP4 or MOV) with frame extraction",
    responses={
        201: {"description": "Video ingested successfully"},
        400: {"description": "Validation error"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported media type"},
        422: {"description": "Ingestion error"},
        503: {"description": "ffmpeg not available"},
    },
)
async def ingest_video(
    file: UploadFile = File(..., description="Video file (MP4 or MOV)"),
    metadata: Optional[str] = Form(
        default=None,
        description="Optional metadata as JSON string"
    ),
    extraction_interval: Optional[float] = Form(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Frame extraction interval in seconds"
    ),
) -> VideoIngestResponse:
    """
    Upload and ingest a video.
    
    Accepts multipart/form-data with:
    - file: The video file (MP4 or MOV)
    - metadata: Optional JSON string with artifact metadata
    - extraction_interval: Seconds between frame extractions (default 1.0)
    
    Returns:
    - 201: Video ingested successfully with frame extraction
    """
    from ...ingest.video import ingest_video as do_ingest_video
    from ...ingest.video import generate_video_ingest_id
    from ...ingest.metadata import validate_metadata
    from ...ingest.metadata_models import ArtifactMetadata
    from ...ingest.video_validators import check_ffmpeg_available
    
    # Generate ingest ID
    ingest_id = generate_video_ingest_id()
    
    # Check ffmpeg availability
    if not check_ffmpeg_available():
        from ..exceptions import ServiceUnavailableError
        raise ServiceUnavailableError(
            detail="Video processing unavailable: ffmpeg not installed",
            service="ffmpeg"
        )
    
    # Validate file extension
    ext = _get_file_extension(file.filename or "unknown")
    if ext not in ("mp4", "mov"):
        raise UnsupportedMediaTypeError(
            detail=f"Unsupported file format: {ext}. Expected MP4 or MOV.",
            supported_types=["video/mp4", "video/quicktime"]
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    max_bytes = default_api_config.max_video_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileTooLargeError(
            detail=f"File size ({len(content) / 1024 / 1024:.1f}MB) exceeds limit ({default_api_config.max_video_size_mb}MB)",
            max_size_mb=default_api_config.max_video_size_mb
        )
    
    # Parse metadata if provided
    parsed_metadata: Optional[ArtifactMetadata] = None
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
            result = validate_metadata(metadata_dict)
            if not result.valid:
                raise ValidationError(
                    detail=f"Invalid metadata: {', '.join(result.errors)}",
                    field="metadata"
                )
            parsed_metadata = result.metadata
        except json.JSONDecodeError as e:
            raise ValidationError(
                detail=f"Invalid JSON in metadata: {e}",
                field="metadata"
            )
    
    # Write to temp file and ingest
    suffix = f".{ext}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Perform ingestion
        result = do_ingest_video(
            tmp_path,
            extraction_interval=extraction_interval
        )
        
        # Store ingest status
        _ingest_store[ingest_id] = {
            "artifact_type": "video",
            "status": IngestStatus.SUCCESS if result.success else IngestStatus.FAILED,
            "created_at": datetime.now().isoformat(),
            "artifact_id": result.flow_id,
            "message": None,
        }
        
        # Associate metadata if provided
        if parsed_metadata and result.flow_id:
            try:
                from ...ingest.metadata import associate_metadata
                associate_metadata(
                    result.flow_id,
                    parsed_metadata,
                    ArtifactType.VIDEO
                )
            except Exception as e:
                # Log but don't fail - metadata is optional
                pass
        
        return VideoIngestResponse(
            ingest_id=ingest_id,
            flow_id=result.flow_id or "",
            status=IngestStatus.SUCCESS,
            frame_count=result.frame_count,
            storage_path=result.video_storage_path or "",
            message=None,
        )
    except Exception as e:
        _ingest_store[ingest_id] = {
            "artifact_type": "video",
            "status": IngestStatus.FAILED,
            "created_at": datetime.now().isoformat(),
            "artifact_id": "",
            "message": str(e),
        }
        raise IngestionError(
            detail=f"Video ingestion failed: {e}",
            reason=str(e)
        )
    finally:
        # Cleanup temp file
        Path(tmp_path).unlink(missing_ok=True)


@router.get(
    "/{ingest_id}",
    response_model=IngestStatusResponse,
    summary="Get Ingest Status",
    description="Query the status of an ingestion operation",
    responses={
        200: {"description": "Ingest status found"},
        404: {"description": "Ingest ID not found"},
    },
)
async def get_ingest_status(ingest_id: str) -> IngestStatusResponse:
    """
    Get the status of an ingestion operation.
    
    Returns the current status and details of a previously
    initiated screenshot or video ingestion.
    """
    if ingest_id not in _ingest_store:
        from ..exceptions import FileNotFoundError
        raise FileNotFoundError(
            detail=f"Ingest ID not found: {ingest_id}",
            instance=f"/ingest/{ingest_id}"
        )
    
    data = _ingest_store[ingest_id]
    
    return IngestStatusResponse(
        ingest_id=ingest_id,
        artifact_type=data["artifact_type"],
        status=data["status"],
        created_at=datetime.fromisoformat(data["created_at"]),
        artifact_id=data["artifact_id"],
        message=data.get("message"),
    )
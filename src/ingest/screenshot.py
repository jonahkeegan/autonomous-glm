"""
Screenshot ingestion handler for Autonomous-GLM.

Provides the main entry point for screenshot ingestion, integrating
validation, storage, and database operations.
"""

from pathlib import Path
from typing import Optional

from src.config import get_config
from src.db.crud import create_screen, get_screen
from src.db.models import ScreenCreate

from .models import (
    ImageFormat,
    IngestConfig,
    IngestResult,
    IngestStatus,
    ValidationError,
    ValidationResult,
)
from .storage import StorageManager
from .validators import ScreenshotValidator


def get_ingest_config() -> IngestConfig:
    """
    Get ingestion configuration from application config.
    
    Returns:
        IngestConfig with settings from config files
    """
    config = get_config()
    
    return IngestConfig(
        max_file_size_mb=config.ingestion.max_file_size_mb,
        min_width=config.ingestion.min_width,
        min_height=config.ingestion.min_height,
        max_width=config.ingestion.max_width,
        max_height=config.ingestion.max_height,
        allowed_formats=[
            ImageFormat(f) for f in config.ingestion.allowed_formats
        ],
        screenshots_dir=config.paths.screenshots_dir,
    )


def generate_ingest_id(file_path: str | Path, config: Optional[IngestConfig] = None) -> str:
    """
    Generate a deterministic ingest ID from file content.
    
    Args:
        file_path: Path to the file
        config: Optional configuration (uses app config if not provided)
        
    Returns:
        UUID string based on content hash
    """
    config = config or get_ingest_config()
    storage = StorageManager(config)
    return storage.generate_ingest_id(Path(file_path))


def validate_screenshot(
    file_path: str | Path,
    config: Optional[IngestConfig] = None
) -> ValidationResult:
    """
    Validate a screenshot file.
    
    Args:
        file_path: Path to the file to validate
        config: Optional configuration (uses app config if not provided)
        
    Returns:
        ValidationResult with validity status and any errors
    """
    config = config or get_ingest_config()
    validator = ScreenshotValidator(config)
    return validator.validate(file_path)


def ingest_screenshot(
    file_path: str | Path,
    config: Optional[IngestConfig] = None,
    db_path: Optional[Path] = None,
) -> IngestResult:
    """
    Ingest a screenshot file.
    
    This is the main entry point for screenshot ingestion. It:
    1. Validates the file (format, size, dimensions, corruption)
    2. Generates a deterministic ingest ID from content hash
    3. Checks for duplicates
    4. Stores the file in the organized directory structure
    5. Creates a database record
    
    Args:
        file_path: Path to the screenshot file to ingest
        config: Optional configuration (uses app config if not provided)
        db_path: Optional database path (uses default if not provided)
        
    Returns:
        IngestResult with success status, ingest ID, and storage path
    """
    path = Path(file_path)
    
    # Get configuration
    ingest_config = config or get_ingest_config()
    
    # Initialize components
    validator = ScreenshotValidator(ingest_config)
    storage = StorageManager(ingest_config)
    
    # Step 1: Validate the file
    validation_result = validator.validate(path)
    
    if not validation_result.valid:
        return IngestResult(
            success=False,
            status=IngestStatus.FAILURE,
            original_path=str(path),
            errors=validation_result.errors,
        )
    
    # Step 2: Generate ingest ID (deterministic from content hash)
    ingest_id = storage.generate_ingest_id(path)
    
    # Step 3: Determine storage path
    assert validation_result.format is not None  # Valid file has format
    storage_path = storage.get_storage_path(
        ingest_id=ingest_id,
        format=validation_result.format,
    )
    
    # Step 4: Check for duplicate
    if storage.file_exists(storage_path):
        # File already exists - find existing screen record
        relative_path = storage.get_relative_path(storage_path)
        
        # Try to find existing screen by image_path
        from src.db.crud import list_screens
        
        existing_screens = list_screens(limit=1000, db_path=db_path)
        for screen in existing_screens:
            if screen.image_path == str(storage_path) or screen.image_path == relative_path:
                return IngestResult(
                    success=True,
                    status=IngestStatus.DUPLICATE,
                    ingest_id=ingest_id,
                    screen_id=screen.id,
                    storage_path=str(storage_path),
                    original_path=str(path),
                    is_duplicate=True,
                )
        
        # File exists but no DB record - create one
        screen = create_screen(
            ScreenCreate(
                name=path.stem,
                image_path=str(storage_path),
            ),
            db_path=db_path,
        )
        
        return IngestResult(
            success=True,
            status=IngestStatus.DUPLICATE,
            ingest_id=ingest_id,
            screen_id=screen.id,
            storage_path=str(storage_path),
            original_path=str(path),
            is_duplicate=True,
        )
    
    # Step 5: Store the file
    try:
        storage.store_file(path, storage_path)
    except Exception as e:
        return IngestResult(
            success=False,
            status=IngestStatus.FAILURE,
            ingest_id=ingest_id,
            original_path=str(path),
            errors=[
                ValidationError(
                    code="storage_error",
                    message=f"Failed to store file: {str(e)}",
                )
            ],
        )
    
    # Step 6: Create database record
    try:
        screen = create_screen(
            ScreenCreate(
                name=path.stem,
                image_path=str(storage_path),
            ),
            db_path=db_path,
        )
    except Exception as e:
        # Clean up stored file on DB failure
        try:
            storage_path.unlink()
        except Exception:
            pass
        
        return IngestResult(
            success=False,
            status=IngestStatus.FAILURE,
            ingest_id=ingest_id,
            storage_path=str(storage_path),
            original_path=str(path),
            errors=[
                ValidationError(
                    code="database_error",
                    message=f"Failed to create database record: {str(e)}",
                )
            ],
        )
    
    # Success!
    return IngestResult(
        success=True,
        status=IngestStatus.SUCCESS,
        ingest_id=ingest_id,
        screen_id=screen.id,
        storage_path=str(storage_path),
        original_path=str(path),
        is_duplicate=False,
    )
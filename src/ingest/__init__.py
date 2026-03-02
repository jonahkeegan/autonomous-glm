"""
Screenshot ingestion module for Autonomous-GLM.

Provides file validation, storage management, and database integration
for screenshot artifacts (PNG, JPEG).
"""

from .models import IngestConfig, IngestResult, ValidationResult
from .screenshot import ingest_screenshot, validate_screenshot, generate_ingest_id
from .storage import StorageManager
from .validators import ScreenshotValidator

__all__ = [
    "IngestConfig",
    "IngestResult",
    "ValidationResult",
    "ingest_screenshot",
    "validate_screenshot",
    "generate_ingest_id",
    "StorageManager",
    "ScreenshotValidator",
]
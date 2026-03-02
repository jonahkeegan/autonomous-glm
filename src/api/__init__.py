"""
REST API module for Autonomous-GLM.

Provides FastAPI-based endpoints for screenshot and video ingestion,
health checks, and metadata handling.
"""

from .app import create_app, app
from .config import APIConfig
from .models import (
    ScreenshotIngestResponse,
    VideoIngestResponse,
    IngestStatusResponse,
    HealthCheckResponse,
    ErrorResponse,
)

__all__ = [
    "create_app",
    "app",
    "APIConfig",
    "ScreenshotIngestResponse",
    "VideoIngestResponse",
    "IngestStatusResponse",
    "HealthCheckResponse",
    "ErrorResponse",
]
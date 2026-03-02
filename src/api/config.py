"""
API configuration for Autonomous-GLM.

Defines API-specific settings including server configuration,
CORS settings, and upload limits.
"""

from typing import Optional

from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    """Configuration for the FastAPI application."""
    
    # Server settings
    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # API metadata
    title: str = Field(default="Autonomous-GLM API", description="API title")
    description: str = Field(
        default="UI/UX Design Agent API for screenshot and video ingestion",
        description="API description"
    )
    version: str = Field(default="0.1.0", description="API version")
    
    # Upload settings
    max_upload_size_mb: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum upload file size in MB"
    )
    max_screenshot_size_mb: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum screenshot file size in MB"
    )
    max_video_size_mb: int = Field(
        default=500,
        ge=1,
        le=2000,
        description="Maximum video file size in MB"
    )
    
    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])
    
    # API prefix
    api_prefix: str = Field(default="/api/v1", description="API route prefix")


# Default configuration instance
default_api_config = APIConfig()
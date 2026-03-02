"""
Pydantic models for vision detection results.

Defines models for component detection, bounding boxes, and detection results.
"""

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ComponentType(str, Enum):
    """Supported UI component types for detection."""
    BUTTON = "button"
    INPUT = "input"
    MODAL = "modal"
    LABEL = "label"
    ICON = "icon"
    IMAGE = "image"
    TEXT = "text"
    CONTAINER = "container"
    CARD = "card"
    NAVIGATION = "navigation"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    SLIDER = "slider"
    SWITCH = "switch"
    TAB = "tab"
    TABLE = "table"
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    UNKNOWN = "unknown"


class DetectedComponent(BaseModel):
    """A single detected UI component with bounding box and metadata."""
    
    type: ComponentType = Field(..., description="Component type classification")
    label: Optional[str] = Field(
        default=None,
        description="Human-readable label or text content"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence score (0.0-1.0)"
    )
    # Normalized bounding box coordinates (0.0-1.0)
    bbox_x: float = Field(..., ge=0.0, le=1.0, description="X position (normalized)")
    bbox_y: float = Field(..., ge=0.0, le=1.0, description="Y position (normalized)")
    bbox_width: float = Field(..., gt=0.0, le=1.0, description="Width (normalized)")
    bbox_height: float = Field(..., gt=0.0, le=1.0, description="Height (normalized)")
    properties: Optional[dict] = Field(
        default=None,
        description="Additional component properties (color, font, etc.)"
    )
    
    @field_validator("bbox_x", "bbox_y", "bbox_width", "bbox_height")
    @classmethod
    def validate_normalized_coords(cls, v: float) -> float:
        """Ensure coordinates are within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Normalized coordinate must be between 0.0 and 1.0, got {v}")
        return v
    
    def to_absolute(self, image_width: int, image_height: int) -> tuple[int, int, int, int]:
        """Convert normalized bounding box to absolute pixel coordinates.
        
        Returns:
            Tuple of (x, y, width, height) in pixels
        """
        x = int(self.bbox_x * image_width)
        y = int(self.bbox_y * image_height)
        width = int(self.bbox_width * image_width)
        height = int(self.bbox_height * image_height)
        return (x, y, width, height)


class DetectionResult(BaseModel):
    """Complete detection result for a single image."""
    
    components: list[DetectedComponent] = Field(
        default_factory=list,
        description="List of detected components"
    )
    image_id: Optional[str] = Field(
        default=None,
        description="Identifier for the source image"
    )
    image_width: Optional[int] = Field(
        default=None,
        ge=1,
        description="Original image width in pixels"
    )
    image_height: Optional[int] = Field(
        default=None,
        ge=1,
        description="Original image height in pixels"
    )
    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Time taken for detection in milliseconds"
    )
    model_version: Optional[str] = Field(
        default=None,
        description="Model version used for detection"
    )
    detected_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when detection was performed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if detection failed"
    )
    
    @property
    def component_count(self) -> int:
        """Return the number of detected components."""
        return len(self.components)
    
    @property
    def is_success(self) -> bool:
        """Return True if detection was successful."""
        return self.error is None
    
    def get_components_by_type(self, component_type: ComponentType) -> list[DetectedComponent]:
        """Filter components by type."""
        return [c for c in self.components if c.type == component_type]
    
    def get_high_confidence_components(self, threshold: float = 0.9) -> list[DetectedComponent]:
        """Filter components by confidence threshold."""
        return [c for c in self.components if c.confidence >= threshold]


class DetectionConfig(BaseModel):
    """Configuration for vision detection."""
    
    model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use for detection"
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=16384,
        description="Maximum tokens in API response"
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (lower = more deterministic)"
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to include in results"
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Maximum API requests per minute"
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts on failure"
    )
    retry_base_delay_ms: int = Field(
        default=1000,
        ge=100,
        description="Base delay for retries in milliseconds"
    )
    retry_max_delay_ms: int = Field(
        default=30000,
        ge=1000,
        description="Maximum delay for retries in milliseconds"
    )
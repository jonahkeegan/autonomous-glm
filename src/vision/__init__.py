"""
Vision module for Autonomous-GLM.

Provides GPT-4 Vision API integration for UI component detection.
"""

from .models import (
    ComponentType,
    DetectedComponent,
    DetectionResult,
    DetectionConfig,
)
from .client import VisionClient
from .prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    build_detection_prompt,
)

__all__ = [
    # Models
    "ComponentType",
    "DetectedComponent",
    "DetectionResult",
    "DetectionConfig",
    # Client
    "VisionClient",
    # Prompts
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
    "build_detection_prompt",
]
"""
Watch mode for automatic artifact detection and processing.

Provides directory watching capability that automatically detects new
artifacts (screenshots, videos) and triggers the audit pipeline.
"""

from .models import (
    ArtifactType,
    WatchStatus,
    WatchState,
    QueueStatus,
    WatchEvent,
    WatchEventType,
    WatchConfig,
)
from .debouncer import EventDebouncer
from .handler import ArtifactEventHandler
from .logger import WatchEventLogger
from .processor import AutoProcessor
from .manager import WatchManager

__all__ = [
    # Models
    "ArtifactType",
    "WatchStatus",
    "WatchState",
    "QueueStatus",
    "WatchEvent",
    "WatchEventType",
    "WatchConfig",
    # Components
    "EventDebouncer",
    "ArtifactEventHandler",
    "WatchEventLogger",
    "AutoProcessor",
    "WatchManager",
]
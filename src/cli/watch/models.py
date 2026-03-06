"""
Pydantic models for watch mode.

Defines models for artifact types, watch status, queue status, and events.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ArtifactType(str, Enum):
    """Types of artifacts that can be detected."""
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_extension(cls, extension: str) -> "ArtifactType":
        """Determine artifact type from file extension.
        
        Args:
            extension: File extension (with or without leading dot)
            
        Returns:
            ArtifactType enum value
        """
        ext = extension.lower().lstrip(".")
        
        screenshot_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
        video_extensions = {"mp4", "mov", "avi", "mkv", "webm"}
        
        if ext in screenshot_extensions:
            return cls.SCREENSHOT
        elif ext in video_extensions:
            return cls.VIDEO
        else:
            return cls.UNKNOWN


class WatchState(str, Enum):
    """States for watch session."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class WatchEventType(str, Enum):
    """Types of watch events."""
    DETECTED = "detected"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class WatchStatus(BaseModel):
    """Current status of watch session."""
    state: WatchState = Field(default=WatchState.IDLE, description="Current watch state")
    directories: list[str] = Field(default_factory=list, description="Watched directories")
    recursive: bool = Field(default=False, description="Watching subdirectories")
    started_at: Optional[datetime] = Field(default=None, description="When watch started")
    uptime_seconds: float = Field(default=0.0, description="Seconds since watch started")
    total_detected: int = Field(default=0, description="Total artifacts detected")
    total_processed: int = Field(default=0, description="Total artifacts processed")
    total_failed: int = Field(default=0, description="Total processing failures")
    
    def to_display_dict(self) -> dict:
        """Convert to display-friendly dictionary."""
        return {
            "State": self.state.value,
            "Directories": ", ".join(self.directories) if self.directories else "None",
            "Recursive": "Yes" if self.recursive else "No",
            "Uptime": f"{self.uptime_seconds:.1f}s" if self.uptime_seconds else "N/A",
            "Detected": self.total_detected,
            "Processed": self.total_processed,
            "Failed": self.total_failed,
        }


class QueueStatus(BaseModel):
    """Status of the processing queue."""
    pending: int = Field(default=0, ge=0, description="Items waiting to process")
    processing: int = Field(default=0, ge=0, description="Items currently processing")
    completed: int = Field(default=0, ge=0, description="Items completed")
    failed: int = Field(default=0, ge=0, description="Items that failed")
    max_size: int = Field(default=100, ge=1, description="Maximum queue size")
    
    @property
    def is_full(self) -> bool:
        """Check if queue is at capacity."""
        return self.pending >= self.max_size
    
    @property
    def total(self) -> int:
        """Total items through queue."""
        return self.pending + self.processing + self.completed + self.failed
    
    def to_display_dict(self) -> dict:
        """Convert to display-friendly dictionary."""
        return {
            "Pending": self.pending,
            "Processing": self.processing,
            "Completed": self.completed,
            "Failed": self.failed,
            "Max Size": self.max_size,
            "Utilization": f"{(self.pending / self.max_size) * 100:.0f}%" if self.max_size > 0 else "N/A",
        }


class WatchEvent(BaseModel):
    """A watch event for logging."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    event_type: WatchEventType = Field(..., description="Type of event")
    path: Optional[str] = Field(default=None, description="File path (if applicable)")
    artifact_type: Optional[ArtifactType] = Field(default=None, description="Artifact type (if applicable)")
    message: str = Field(default="", description="Event message")
    audit_id: Optional[str] = Field(default=None, description="Audit ID (if applicable)")
    report_path: Optional[str] = Field(default=None, description="Report path (if applicable)")
    error: Optional[str] = Field(default=None, description="Error message (if applicable)")
    
    def to_ndjson(self) -> str:
        """Convert to NDJSON line for logging."""
        data = self.model_dump(mode="json")
        # Ensure timestamp is ISO format
        if isinstance(data["timestamp"], datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        import json
        return json.dumps(data)


class WatchConfig(BaseModel):
    """Configuration for watch mode."""
    debounce_window_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=60.0,
        description="Seconds to wait before processing duplicate events"
    )
    max_queue_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum items in processing queue"
    )
    processing_interval_seconds: float = Field(
        default=0.5,
        ge=0.1,
        le=10.0,
        description="Interval between queue processing cycles"
    )
    event_log_path: str = Field(
        default="logs/watch-log.ndjson",
        description="Path to event log file"
    )
    screenshot_extensions: list[str] = Field(
        default=["png", "jpg", "jpeg", "gif", "webp"],
        description="Screenshot file extensions to detect"
    )
    video_extensions: list[str] = Field(
        default=["mp4", "mov", "avi", "mkv", "webm"],
        description="Video file extensions to detect"
    )
    
    @field_validator("screenshot_extensions", "video_extensions")
    @classmethod
    def lowercase_extensions(cls, v: list[str]) -> list[str]:
        """Ensure all extensions are lowercase."""
        return [ext.lower().lstrip(".") for ext in v]
    
    def is_screenshot(self, path: Path) -> bool:
        """Check if path is a screenshot based on extension."""
        return path.suffix.lower().lstrip(".") in self.screenshot_extensions
    
    def is_video(self, path: Path) -> bool:
        """Check if path is a video based on extension."""
        return path.suffix.lower().lstrip(".") in self.video_extensions
    
    def is_artifact(self, path: Path) -> bool:
        """Check if path is any valid artifact type."""
        return self.is_screenshot(path) or self.is_video(path)
    
    def get_artifact_type(self, path: Path) -> ArtifactType:
        """Get artifact type for path."""
        if self.is_screenshot(path):
            return ArtifactType.SCREENSHOT
        elif self.is_video(path):
            return ArtifactType.VIDEO
        else:
            return ArtifactType.UNKNOWN
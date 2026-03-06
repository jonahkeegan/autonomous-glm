"""
Event logger for watch mode.

Logs watch events to NDJSON for persistent tracking.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import WatchEvent, WatchEventType, ArtifactType

logger = logging.getLogger(__name__)


class WatchEventLogger:
    """Logs watch events to NDJSON file.
    
    Provides persistent event logging for audit trails and debugging.
    
    Example:
        >>> event_logger = WatchEventLogger("./logs/watch-log.ndjson")
        >>> event_logger.log_detected(Path("/data/test.png"), ArtifactType.SCREENSHOT)
        >>> event_logger.log_completed(Path("/data/test.png"), "audit-123", "./reports/test.md")
    """
    
    def __init__(self, log_path: str):
        """Initialize event logger.
        
        Args:
            log_path: Path to NDJSON log file
        """
        self.log_path = Path(log_path)
        self._ensure_log_dir()
    
    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        log_dir = self.log_path.parent
        if log_dir and not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
    
    def _write_event(self, event: WatchEvent) -> None:
        """Write event to log file.
        
        Args:
            event: WatchEvent to log
        """
        try:
            with open(self.log_path, "a") as f:
                f.write(event.to_ndjson() + "\n")
        except Exception as e:
            logger.error(f"Failed to write watch event log: {e}")
    
    def log_detected(
        self,
        path: Path,
        artifact_type: ArtifactType,
        message: str = "",
    ) -> None:
        """Log artifact detection event.
        
        Args:
            path: Path to detected artifact
            artifact_type: Type of artifact
            message: Optional message
        """
        event = WatchEvent(
            timestamp=datetime.utcnow(),
            event_type=WatchEventType.DETECTED,
            path=str(path),
            artifact_type=artifact_type,
            message=message or f"Detected {artifact_type.value}: {path}",
        )
        self._write_event(event)
    
    def log_processing_started(
        self,
        path: Path,
        artifact_type: ArtifactType,
        message: str = "",
    ) -> None:
        """Log processing started event.
        
        Args:
            path: Path to artifact
            artifact_type: Type of artifact
            message: Optional message
        """
        event = WatchEvent(
            timestamp=datetime.utcnow(),
            event_type=WatchEventType.PROCESSING_STARTED,
            path=str(path),
            artifact_type=artifact_type,
            message=message or f"Started processing: {path}",
        )
        self._write_event(event)
    
    def log_processing_completed(
        self,
        path: Path,
        artifact_type: ArtifactType,
        audit_id: str,
        report_path: str,
        message: str = "",
    ) -> None:
        """Log processing completed event.
        
        Args:
            path: Path to artifact
            artifact_type: Type of artifact
            audit_id: Audit ID generated
            report_path: Path to report file
            message: Optional message
        """
        event = WatchEvent(
            timestamp=datetime.utcnow(),
            event_type=WatchEventType.PROCESSING_COMPLETED,
            path=str(path),
            artifact_type=artifact_type,
            audit_id=audit_id,
            report_path=report_path,
            message=message or f"Completed processing: {path}",
        )
        self._write_event(event)
    
    def log_processing_failed(
        self,
        path: Path,
        artifact_type: ArtifactType,
        error: str,
        message: str = "",
    ) -> None:
        """Log processing failed event.
        
        Args:
            path: Path to artifact
            artifact_type: Type of artifact
            error: Error message
            message: Optional additional message
        """
        event = WatchEvent(
            timestamp=datetime.utcnow(),
            event_type=WatchEventType.PROCESSING_FAILED,
            path=str(path),
            artifact_type=artifact_type,
            error=error,
            message=message or f"Failed processing: {path}",
        )
        self._write_event(event)
    
    def log_error(
        self,
        error: str,
        path: Optional[Path] = None,
        message: str = "",
    ) -> None:
        """Log general error event.
        
        Args:
            error: Error message
            path: Optional related path
            message: Optional additional message
        """
        event = WatchEvent(
            timestamp=datetime.utcnow(),
            event_type=WatchEventType.ERROR,
            path=str(path) if path else None,
            error=error,
            message=message or "Watch error occurred",
        )
        self._write_event(event)
    
    def log_shutdown(self, message: str = "Watch mode shutting down") -> None:
        """Log shutdown event.
        
        Args:
            message: Shutdown message
        """
        event = WatchEvent(
            timestamp=datetime.utcnow(),
            event_type=WatchEventType.SHUTDOWN,
            message=message,
        )
        self._write_event(event)
    
    def read_recent_events(self, count: int = 100) -> list[WatchEvent]:
        """Read recent events from log.
        
        Args:
            count: Maximum number of events to read
            
        Returns:
            List of WatchEvent objects (most recent last)
        """
        events = []
        
        if not self.log_path.exists():
            return events
        
        try:
            with open(self.log_path, "r") as f:
                # Read last N lines
                lines = f.readlines()[-count:]
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        event = WatchEvent(**data)
                        events.append(event)
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"Failed to parse log line: {e}")
                        continue
        except Exception as e:
            logger.error(f"Failed to read watch event log: {e}")
        
        return events
"""
File system event handler for watch mode.

Handles file system events and detects valid artifacts.
"""

import logging
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .models import ArtifactType, WatchConfig
from .debouncer import EventDebouncer

logger = logging.getLogger(__name__)

# Type for artifact callback
ArtifactCallback = Callable[[Path, ArtifactType], None]


class ArtifactEventHandler(FileSystemEventHandler):
    """Watchdog event handler for detecting artifacts.
    
    Handles file system events (created, modified, moved) and triggers
    callbacks for valid artifacts after debouncing.
    
    Example:
        >>> def on_artifact(path: Path, artifact_type: ArtifactType):
        ...     print(f"Detected {artifact_type}: {path}")
        >>> 
        >>> handler = ArtifactEventHandler(
        ...     config=WatchConfig(),
        ...     on_artifact_detected=on_artifact,
        ... )
        >>> 
        >>> # Use with watchdog Observer
        >>> from watchdog.observers import Observer
        >>> observer = Observer()
        >>> observer.schedule(handler, "/data/artifacts/screenshots", recursive=True)
        >>> observer.start()
    """
    
    def __init__(
        self,
        config: Optional[WatchConfig] = None,
        debouncer: Optional[EventDebouncer] = None,
        on_artifact_detected: Optional[ArtifactCallback] = None,
        dry_run: bool = False,
    ):
        """Initialize event handler.
        
        Args:
            config: Watch configuration (uses defaults if None)
            debouncer: Event debouncer (creates new one if None)
            on_artifact_detected: Callback for detected artifacts
            dry_run: If True, only log detections without calling callback
        """
        super().__init__()
        
        self.config = config or WatchConfig()
        self.debouncer = debouncer or EventDebouncer(config=self.config)
        self.on_artifact_detected = on_artifact_detected
        self.dry_run = dry_run
        
        # Track processed files for status
        self._processed_count = 0
        self._skipped_count = 0
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event.
        
        Args:
            event: File system event from watchdog
        """
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        self._handle_event(path, "created")
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event.
        
        Args:
            event: File system event from watchdog
        """
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        self._handle_event(path, "modified")
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move event.
        
        Args:
            event: File system event from watchdog
        """
        if event.is_directory:
            return
        
        # Only process destination of move
        path = Path(event.dest_path)
        self._handle_event(path, "moved")
    
    def _handle_event(self, path: Path, event_type: str) -> None:
        """Handle a file system event.
        
        Args:
            path: File path that triggered event
            event_type: Type of event (created, modified, moved)
        """
        # Check if this is a valid artifact
        if not self.is_artifact(path):
            logger.debug(f"Ignoring non-artifact: {path}")
            return
        
        # Get artifact type
        artifact_type = self.get_artifact_type(path)
        if artifact_type == ArtifactType.UNKNOWN:
            logger.debug(f"Ignoring unknown artifact type: {path}")
            return
        
        # Check debouncer
        if not self.debouncer.should_process(path, event_type):
            logger.debug(f"Debounced {event_type} event for: {path}")
            self._skipped_count += 1
            return
        
        # Check if file still exists (may have been deleted)
        if not path.exists():
            logger.debug(f"File no longer exists: {path}")
            return
        
        logger.info(f"Detected {artifact_type.value}: {path}")
        self._processed_count += 1
        
        # Call callback if set
        if self.on_artifact_detected and not self.dry_run:
            try:
                self.on_artifact_detected(path, artifact_type)
            except Exception as e:
                logger.error(f"Error processing artifact {path}: {e}")
        elif self.dry_run:
            logger.info(f"[DRY RUN] Would process {artifact_type.value}: {path}")
    
    def is_artifact(self, path: Path) -> bool:
        """Check if file is a valid artifact.
        
        Args:
            path: File path to check
            
        Returns:
            True if file is a valid artifact type
        """
        return self.config.is_artifact(path)
    
    def get_artifact_type(self, path: Path) -> ArtifactType:
        """Determine artifact type for file.
        
        Args:
            path: File path to check
            
        Returns:
            ArtifactType enum value
        """
        return self.config.get_artifact_type(path)
    
    @property
    def processed_count(self) -> int:
        """Number of artifacts processed."""
        return self._processed_count
    
    @property
    def skipped_count(self) -> int:
        """Number of events skipped due to debouncing."""
        return self._skipped_count
    
    def reset_counts(self) -> None:
        """Reset processed and skipped counters."""
        self._processed_count = 0
        self._skipped_count = 0
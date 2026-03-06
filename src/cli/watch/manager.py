"""
Watch manager for coordinating watch mode.

Orchestrates file watching, debouncing, and processing.
"""

import logging
import signal
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from watchdog.observers import Observer

from .models import (
    ArtifactType,
    WatchConfig,
    WatchState,
    WatchStatus,
    QueueStatus,
)
from .debouncer import EventDebouncer
from .handler import ArtifactEventHandler
from .logger import WatchEventLogger
from .processor import AutoProcessor

logger = logging.getLogger(__name__)

# Type for process callback
ProcessCallback = Callable[[Path, ArtifactType], tuple[str, str]]


class WatchManager:
    """Manages the watch mode lifecycle.
    
    Coordinates file system watching, event debouncing, and
    automatic processing of detected artifacts.
    
    Example:
        >>> def process_artifact(path: Path, artifact_type: ArtifactType):
        ...     return ("audit-123", "./reports/audit-123.md")
        >>> 
        >>> manager = WatchManager(
        ...     config=WatchConfig(),
        ...     process_callback=process_artifact,
        ... )
        >>> 
        >>> manager.add_directory(Path("/data/artifacts/screenshots"))
        >>> manager.add_directory(Path("/data/artifacts/videos"))
        >>> 
        >>> manager.start()  # Blocking
        >>> # Or use manager.start_async() for non-blocking
    """
    
    def __init__(
        self,
        config: Optional[WatchConfig] = None,
        process_callback: Optional[ProcessCallback] = None,
        dry_run: bool = False,
    ):
        """Initialize watch manager.
        
        Args:
            config: Watch configuration (uses defaults if None)
            process_callback: Function to process detected artifacts
            dry_run: If True, only log detections without processing
        """
        self.config = config or WatchConfig()
        self.dry_run = dry_run
        
        # Initialize components
        self.debouncer = EventDebouncer(config=self.config)
        self.event_logger = WatchEventLogger(self.config.event_log_path)
        self.processor = AutoProcessor(
            config=self.config,
            event_logger=self.event_logger,
            process_callback=process_callback if not dry_run else None,
        )
        
        # File system observer
        self._observer: Optional[Observer] = None
        
        # Status tracking
        self._status = WatchStatus()
        self._status_lock = threading.Lock()
        
        # Control
        self._stop_event = threading.Event()
        self._watch_thread: Optional[threading.Thread] = None
        
        # Directories to watch
        self._directories: list[Path] = []
        self._recursive = True
    
    @property
    def status(self) -> WatchStatus:
        """Get current watch status."""
        with self._status_lock:
            # Update uptime if running
            if self._status.started_at:
                self._status.uptime_seconds = (
                    datetime.utcnow() - self._status.started_at
                ).total_seconds()
            return self._status
    
    @property
    def queue_status(self) -> QueueStatus:
        """Get current queue status."""
        return self.processor.status
    
    @property
    def is_running(self) -> bool:
        """Check if watch is running."""
        with self._status_lock:
            return self._status.state == WatchState.RUNNING
    
    def add_directory(
        self,
        directory: Path,
        recursive: bool = True,
    ) -> bool:
        """Add directory to watch.
        
        Args:
            directory: Directory path to watch
            recursive: Watch subdirectories
            
        Returns:
            True if directory added successfully
        """
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return False
        
        if not directory.is_dir():
            logger.warning(f"Path is not a directory: {directory}")
            return False
        
        if directory in self._directories:
            logger.debug(f"Directory already registered: {directory}")
            return True
        
        self._directories.append(directory)
        self._recursive = self._recursive and recursive
        
        logger.info(f"Added watch directory: {directory} (recursive={recursive})")
        return True
    
    def start(self) -> None:
        """Start watching (blocking).
        
        Blocks until interrupted by signal or stop() call.
        """
        if self.is_running:
            logger.warning("Watch already running")
            return
        
        if not self._directories:
            logger.error("No directories to watch")
            return
        
        # Update status
        with self._status_lock:
            self._status.state = WatchState.STARTING
            self._status.directories = [str(d) for d in self._directories]
            self._status.recursive = self._recursive
            self._status.started_at = datetime.utcnow()
        
        # Start processor
        self.processor.start()
        
        # Create handler with callback
        def on_artifact(path: Path, artifact_type: ArtifactType) -> None:
            # Log detection
            self.event_logger.log_detected(path, artifact_type)
            
            with self._status_lock:
                self._status.total_detected += 1
            
            # Enqueue for processing
            self.processor.enqueue(path, artifact_type)
        
        handler = ArtifactEventHandler(
            config=self.config,
            debouncer=self.debouncer,
            on_artifact_detected=on_artifact,
            dry_run=self.dry_run,
        )
        
        # Create and start observer
        self._observer = Observer()
        
        for directory in self._directories:
            self._observer.schedule(
                handler,
                str(directory),
                recursive=self._recursive,
            )
        
        # Update status
        with self._status_lock:
            self._status.state = WatchState.RUNNING
        
        # Start observer
        self._observer.start()
        logger.info(
            f"Watch started on {len(self._directories)} directorie(s) "
            f"(recursive={self._recursive}, dry_run={self.dry_run})"
        )
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Block until stopped
        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self._do_stop()
    
    def start_async(self) -> None:
        """Start watching in background thread.
        
        Non-blocking - returns immediately.
        """
        if self.is_running:
            logger.warning("Watch already running")
            return
        
        self._stop_event.clear()
        self._watch_thread = threading.Thread(
            target=self.start,
            name="WatchManager",
            daemon=True,
        )
        self._watch_thread.start()
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop watching.
        
        Args:
            timeout: Seconds to wait for shutdown
        """
        self._stop_event.set()
        
        if self._watch_thread and self._watch_thread.is_alive():
            self._watch_thread.join(timeout=timeout)
        
        self._do_stop()
    
    def _do_stop(self) -> None:
        """Internal stop implementation."""
        with self._status_lock:
            if self._status.state == WatchState.STOPPED:
                return
            self._status.state = WatchState.STOPPING
        
        # Stop observer
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None
        
        # Stop processor
        self.processor.stop(timeout=2.0)
        
        # Log shutdown
        self.event_logger.log_shutdown()
        
        # Update status
        with self._status_lock:
            self._status.state = WatchState.STOPPED
        
        logger.info("Watch stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, stopping...")
            self._stop_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def process_existing(self) -> int:
        """Process all existing artifacts in watched directories.
        
        Returns:
            Number of artifacts queued for processing
        """
        if not self._directories:
            logger.warning("No directories configured")
            return 0
        
        queued = 0
        
        for directory in self._directories:
            if self._recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for path in directory.glob(pattern):
                if not path.is_file():
                    continue
                
                if self.config.is_artifact(path):
                    artifact_type = self.config.get_artifact_type(path)
                    
                    if artifact_type != ArtifactType.UNKNOWN:
                        # Log detection
                        self.event_logger.log_detected(path, artifact_type)
                        
                        # Enqueue
                        if self.processor.enqueue(path, artifact_type):
                            queued += 1
        
        logger.info(f"Queued {queued} existing artifact(s) for processing")
        return queued
    
    def get_status_display(self) -> dict:
        """Get status formatted for display.
        
        Returns:
            Dictionary with display-friendly status
        """
        status = self.status
        queue = self.queue_status
        
        return {
            "Watch State": status.state.value,
            "Directories": ", ".join(status.directories) if status.directories else "None",
            "Recursive": "Yes" if status.recursive else "No",
            "Uptime": f"{status.uptime_seconds:.1f}s" if status.uptime_seconds else "N/A",
            "Detected": status.total_detected,
            "Processed": status.total_processed,
            "Failed": status.total_failed,
            "---": "---",
            "Queue Pending": queue.pending,
            "Queue Processing": queue.processing,
            "Queue Completed": queue.completed,
            "Queue Failed": queue.failed,
        }
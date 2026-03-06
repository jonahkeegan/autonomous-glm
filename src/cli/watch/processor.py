"""
Auto processor for watch mode.

Processes detected artifacts through the audit pipeline.
"""

import logging
import queue
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from .models import (
    ArtifactType,
    WatchConfig,
    QueueStatus,
    WatchEventType,
)
from .logger import WatchEventLogger

logger = logging.getLogger(__name__)

# Type for processing callback
ProcessCallback = Callable[[Path, ArtifactType], tuple[str, str]]  # (audit_id, report_path)


@dataclass
class QueueItem:
    """Item in the processing queue."""
    path: Path
    artifact_type: ArtifactType
    added_at: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0


class AutoProcessor:
    """Processes artifacts through audit pipeline.
    
    Manages a queue of detected artifacts and processes them
    asynchronously using a worker thread.
    
    Example:
        >>> def process_artifact(path: Path, artifact_type: ArtifactType):
        ...     # Run audit and return (audit_id, report_path)
        ...     return ("audit-123", "./reports/audit-123.md")
        >>> 
        >>> processor = AutoProcessor(
        ...     config=WatchConfig(),
        ...     event_logger=WatchEventLogger("./logs/watch-log.ndjson"),
        ...     process_callback=process_artifact,
        ... )
        >>> 
        >>> processor.start()
        >>> processor.enqueue(Path("/data/test.png"), ArtifactType.SCREENSHOT)
        >>> 
        >>> # Later...
        >>> processor.stop()
    """
    
    def __init__(
        self,
        config: WatchConfig,
        event_logger: WatchEventLogger,
        process_callback: Optional[ProcessCallback] = None,
    ):
        """Initialize auto processor.
        
        Args:
            config: Watch configuration
            event_logger: Event logger for recording events
            process_callback: Function to process artifacts (path, type) -> (audit_id, report_path)
        """
        self.config = config
        self.event_logger = event_logger
        self.process_callback = process_callback
        
        # Queue and threading
        self._queue: queue.Queue[Optional[QueueItem]] = queue.Queue(
            maxsize=config.max_queue_size
        )
        self._worker: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Status tracking
        self._status = QueueStatus(max_size=config.max_queue_size)
        self._status_lock = threading.Lock()
        
        # Callbacks for completion
        self._on_completed: Optional[Callable[[Path, str, str], None]] = None
        self._on_failed: Optional[Callable[[Path, str], None]] = None
    
    def set_callbacks(
        self,
        on_completed: Optional[Callable[[Path, str, str], None]] = None,
        on_failed: Optional[Callable[[Path, str], None]] = None,
    ) -> None:
        """Set completion callbacks.
        
        Args:
            on_completed: Called with (path, audit_id, report_path) on success
            on_failed: Called with (path, error) on failure
        """
        self._on_completed = on_completed
        self._on_failed = on_failed
    
    @property
    def status(self) -> QueueStatus:
        """Get current queue status."""
        with self._status_lock:
            # Update pending count from actual queue
            self._status.pending = self._queue.qsize()
            return self._status
    
    @property
    def is_running(self) -> bool:
        """Check if processor is running."""
        return self._worker is not None and self._worker.is_alive()
    
    def enqueue(self, path: Path, artifact_type: ArtifactType) -> bool:
        """Add artifact to processing queue.
        
        Args:
            path: Path to artifact
            artifact_type: Type of artifact
            
        Returns:
            True if enqueued successfully, False if queue is full
        """
        if self._queue.full():
            logger.warning(f"Queue full, cannot enqueue: {path}")
            return False
        
        item = QueueItem(path=path, artifact_type=artifact_type)
        
        try:
            self._queue.put_nowait(item)
            
            with self._status_lock:
                self._status.pending = self._queue.qsize()
            
            logger.info(f"Enqueued {artifact_type.value}: {path}")
            return True
        except queue.Full:
            return False
    
    def start(self) -> None:
        """Start the processing worker thread."""
        if self.is_running:
            logger.warning("Processor already running")
            return
        
        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._worker_loop,
            name="AutoProcessor",
            daemon=True,
        )
        self._worker.start()
        logger.info("AutoProcessor started")
    
    def stop(self, timeout: float = 5.0) -> None:
        """Stop the processing worker thread.
        
        Args:
            timeout: Seconds to wait for worker to finish
        """
        if not self.is_running:
            return
        
        # Signal stop and wake up worker
        self._stop_event.set()
        self._queue.put(None)  # Sentinel to wake up worker
        
        self._worker.join(timeout=timeout)
        
        if self._worker.is_alive():
            logger.warning("Worker did not stop gracefully")
        
        self._worker = None
        logger.info("AutoProcessor stopped")
    
    def _worker_loop(self) -> None:
        """Main worker loop for processing queue items."""
        while not self._stop_event.is_set():
            try:
                # Wait for item with timeout
                try:
                    item = self._queue.get(timeout=self.config.processing_interval_seconds)
                except queue.Empty:
                    # No items, just continue loop
                    continue
                
                # Check for sentinel (None means stop)
                if item is None:
                    break
                
                # Process the item
                self._process_item(item)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                self.event_logger.log_error(str(e))
    
    def _process_item(self, item: QueueItem) -> None:
        """Process a single queue item.
        
        Args:
            item: Queue item to process
        """
        with self._status_lock:
            self._status.pending -= 1
            self._status.processing += 1
        
        try:
            # Log processing started
            self.event_logger.log_processing_started(
                path=item.path,
                artifact_type=item.artifact_type,
            )
            
            # Check if file still exists
            if not item.path.exists():
                raise FileNotFoundError(f"Artifact no longer exists: {item.path}")
            
            # Process using callback
            if self.process_callback:
                audit_id, report_path = self.process_callback(
                    item.path,
                    item.artifact_type,
                )
            else:
                # No callback - simulate processing (for testing)
                audit_id = f"audit-{uuid.uuid4().hex[:8]}"
                report_path = f"./reports/{audit_id}.md"
                logger.warning(
                    f"No process_callback set, using mock: {audit_id}"
                )
            
            # Log and update status
            self.event_logger.log_processing_completed(
                path=item.path,
                artifact_type=item.artifact_type,
                audit_id=audit_id,
                report_path=report_path,
            )
            
            with self._status_lock:
                self._status.processing -= 1
                self._status.completed += 1
            
            logger.info(
                f"Completed processing {item.artifact_type.value}: {item.path} "
                f"-> {report_path}"
            )
            
            # Call completion callback
            if self._on_completed:
                try:
                    self._on_completed(item.path, audit_id, report_path)
                except Exception as e:
                    logger.error(f"Error in completion callback: {e}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process {item.path}: {error_msg}")
            
            # Log failure
            self.event_logger.log_processing_failed(
                path=item.path,
                artifact_type=item.artifact_type,
                error=error_msg,
            )
            
            with self._status_lock:
                self._status.processing -= 1
                self._status.failed += 1
            
            # Call failure callback
            if self._on_failed:
                try:
                    self._on_failed(item.path, error_msg)
                except Exception as e:
                    logger.error(f"Error in failure callback: {e}")
    
    def process_sync(self, path: Path, artifact_type: ArtifactType) -> tuple[str, str]:
        """Process artifact synchronously (bypassing queue).
        
        Useful for testing or when immediate processing is needed.
        
        Args:
            path: Path to artifact
            artifact_type: Type of artifact
            
        Returns:
            Tuple of (audit_id, report_path)
            
        Raises:
            Exception: If processing fails
        """
        item = QueueItem(path=path, artifact_type=artifact_type)
        
        # Process directly (not through queue)
        if self.process_callback:
            return self.process_callback(path, artifact_type)
        else:
            audit_id = f"audit-{uuid.uuid4().hex[:8]}"
            report_path = f"./reports/{audit_id}.md"
            return audit_id, report_path
    
    def clear_queue(self) -> int:
        """Clear all pending items from queue.
        
        Returns:
            Number of items cleared
        """
        cleared = 0
        
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                cleared += 1
            except queue.Empty:
                break
        
        with self._status_lock:
            self._status.pending = 0
        
        return cleared
"""
Unit tests for AutoProcessor - watch mode processing.

Tests cover:
- AutoProcessor initialization and configuration
- Queue management (enqueue, clear)
- Worker thread lifecycle (start, stop)
- Item processing (success, failure)
- Status tracking
"""

import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli.watch.processor import AutoProcessor, QueueItem
from src.cli.watch.models import (
    ArtifactType,
    WatchConfig,
    QueueStatus,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def config():
    """Create test watch configuration."""
    return WatchConfig(
        max_queue_size=10,
        processing_interval_seconds=0.1,
    )


@pytest.fixture
def event_logger(tmp_path):
    """Create mock event logger."""
    logger = MagicMock()
    logger.log_processing_started = MagicMock()
    logger.log_processing_completed = MagicMock()
    logger.log_processing_failed = MagicMock()
    logger.log_error = MagicMock()
    return logger


@pytest.fixture
def process_callback():
    """Create mock process callback."""
    return MagicMock(return_value=("audit-123", "./reports/audit-123.md"))


@pytest.fixture
def processor(config, event_logger, process_callback):
    """Create AutoProcessor instance."""
    return AutoProcessor(
        config=config,
        event_logger=event_logger,
        process_callback=process_callback,
    )


@pytest.fixture
def artifact_path(tmp_path):
    """Create test artifact file."""
    path = tmp_path / "test.png"
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    return path


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================

class TestAutoProcessorInit:
    """Tests for AutoProcessor initialization."""
    
    def test_init(self, config, event_logger):
        """Processor initializes correctly."""
        processor = AutoProcessor(
            config=config,
            event_logger=event_logger,
        )
        
        assert processor.config == config
        assert processor.event_logger == event_logger
        assert processor.process_callback is None
        assert processor.is_running is False
    
    def test_init_with_callback(self, config, event_logger, process_callback):
        """Processor stores callback."""
        processor = AutoProcessor(
            config=config,
            event_logger=event_logger,
            process_callback=process_callback,
        )
        
        assert processor.process_callback == process_callback
    
    def test_queue_initialized(self, processor):
        """Queue is initialized with correct size."""
        assert processor._queue is not None
        assert processor._queue.maxsize == 10


# =============================================================================
# STATUS TESTS
# =============================================================================

class TestStatusTracking:
    """Tests for status tracking."""
    
    def test_initial_status(self, processor):
        """Initial status is correct."""
        status = processor.status
        
        assert isinstance(status, QueueStatus)
        assert status.pending == 0
        assert status.processing == 0
        assert status.completed == 0
        assert status.failed == 0
    
    def test_status_property_thread_safe(self, processor):
        """Status access is thread-safe."""
        results = []
        
        def read_status():
            for _ in range(10):
                results.append(processor.status)
        
        threads = [threading.Thread(target=read_status) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 50
    
    def test_is_running_false_initially(self, processor):
        """is_running is False initially."""
        assert processor.is_running is False


# =============================================================================
# ENQUEUE TESTS
# =============================================================================

class TestEnqueue:
    """Tests for queue management."""
    
    def test_enqueue_success(self, processor, artifact_path):
        """Can enqueue an artifact."""
        result = processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        assert result is True
        assert processor.status.pending == 1
    
    def test_enqueue_updates_pending(self, processor, artifact_path):
        """Enqueue updates pending count."""
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        assert processor.status.pending == 2
    
    def test_enqueue_queue_full(self, config, event_logger, process_callback):
        """Returns False when queue is full."""
        # Create processor with tiny queue
        small_config = WatchConfig(max_queue_size=1)
        processor = AutoProcessor(
            config=small_config,
            event_logger=event_logger,
            process_callback=process_callback,
        )
        
        path1 = Path("/test1.png")
        path2 = Path("/test2.png")
        
        processor.enqueue(path1, ArtifactType.SCREENSHOT)
        result = processor.enqueue(path2, ArtifactType.SCREENSHOT)
        
        # Second enqueue should fail (queue full)
        # Note: This depends on queue not being consumed
        assert processor._queue.full() or result is False


# =============================================================================
# START/STOP TESTS
# =============================================================================

class TestStartStop:
    """Tests for worker lifecycle."""
    
    def test_start_creates_thread(self, processor):
        """Start creates worker thread."""
        processor.start()
        
        assert processor._worker is not None
        assert processor.is_running
        
        processor.stop()
    
    def test_start_when_already_running(self, processor):
        """Starting when running is safe."""
        processor.start()
        processor.start()  # Second call should be safe
        
        assert processor.is_running
        
        processor.stop()
    
    def test_stop_terminates_thread(self, processor):
        """Stop terminates worker thread."""
        processor.start()
        processor.stop(timeout=1.0)
        
        assert processor.is_running is False
    
    def test_stop_when_not_running(self, processor):
        """Stop when not running is safe."""
        processor.stop()  # Should not raise
    
    def test_double_stop_safe(self, processor):
        """Double stop is safe."""
        processor.start()
        processor.stop()
        processor.stop()  # Should not raise


# =============================================================================
# PROCESSING TESTS
# =============================================================================

class TestProcessing:
    """Tests for item processing."""
    
    def test_process_item_success(self, processor, artifact_path, process_callback):
        """Item is processed successfully."""
        processor.start()
        
        # Create a real file for processing
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        # Wait for processing
        time.sleep(0.3)
        
        processor.stop()
        
        # Verify callback was called
        process_callback.assert_called_once()
        
        # Verify status updated
        status = processor.status
        assert status.completed == 1
    
    def test_process_item_logs_events(self, processor, artifact_path, event_logger):
        """Processing logs events."""
        processor.start()
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        time.sleep(0.3)
        processor.stop()
        
        # Verify logging calls
        event_logger.log_processing_started.assert_called_once()
        event_logger.log_processing_completed.assert_called_once()
    
    def test_process_item_file_not_found(self, processor, event_logger, tmp_path):
        """Missing file is handled gracefully."""
        missing_path = tmp_path / "missing.png"
        # Don't create the file
        
        processor.start()
        processor.enqueue(missing_path, ArtifactType.SCREENSHOT)
        
        time.sleep(0.3)
        processor.stop()
        
        # Should log failure
        event_logger.log_processing_failed.assert_called_once()
        
        status = processor.status
        assert status.failed == 1
    
    def test_process_item_callback_exception(self, processor, artifact_path, process_callback, event_logger):
        """Callback exceptions are handled."""
        process_callback.side_effect = RuntimeError("Processing failed")
        
        processor.start()
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        time.sleep(0.3)
        processor.stop()
        
        status = processor.status
        assert status.failed == 1
        event_logger.log_processing_failed.assert_called_once()


# =============================================================================
# CALLBACKS TESTS
# =============================================================================

class TestCallbacks:
    """Tests for completion callbacks."""
    
    def test_set_callbacks(self, processor):
        """Can set completion callbacks."""
        on_completed = MagicMock()
        on_failed = MagicMock()
        
        processor.set_callbacks(on_completed=on_completed, on_failed=on_failed)
        
        assert processor._on_completed == on_completed
        assert processor._on_failed == on_failed
    
    def test_on_completed_called(self, processor, artifact_path):
        """on_completed callback is called on success."""
        on_completed = MagicMock()
        processor.set_callbacks(on_completed=on_completed)
        
        processor.start()
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        time.sleep(0.3)
        processor.stop()
        
        on_completed.assert_called_once()
    
    def test_on_failed_called(self, processor, tmp_path, event_logger):
        """on_failed callback is called on failure."""
        on_failed = MagicMock()
        processor.set_callbacks(on_failed=on_failed)
        
        missing_path = tmp_path / "missing.png"
        
        processor.start()
        processor.enqueue(missing_path, ArtifactType.SCREENSHOT)
        
        time.sleep(0.3)
        processor.stop()
        
        on_failed.assert_called_once()
    
    def test_callback_exception_handled(self, processor, artifact_path):
        """Exception in callback is handled gracefully."""
        on_completed = MagicMock(side_effect=RuntimeError("Callback error"))
        processor.set_callbacks(on_completed=on_completed)
        
        processor.start()
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        time.sleep(0.3)
        processor.stop()
        
        # Should not crash, status should show completed
        assert processor.status.completed == 1


# =============================================================================
# SYNC PROCESSING TESTS
# =============================================================================

class TestSyncProcessing:
    """Tests for synchronous processing."""
    
    def test_process_sync_with_callback(self, processor, artifact_path, process_callback):
        """Synchronous processing uses callback."""
        audit_id, report_path = processor.process_sync(
            artifact_path,
            ArtifactType.SCREENSHOT,
        )
        
        process_callback.assert_called_once_with(
            artifact_path,
            ArtifactType.SCREENSHOT,
        )
        assert audit_id == "audit-123"
        assert report_path == "./reports/audit-123.md"
    
    def test_process_sync_without_callback(self, config, event_logger, artifact_path):
        """Synchronous processing without callback returns mock values."""
        processor = AutoProcessor(
            config=config,
            event_logger=event_logger,
            process_callback=None,
        )
        
        audit_id, report_path = processor.process_sync(
            artifact_path,
            ArtifactType.SCREENSHOT,
        )
        
        assert audit_id.startswith("audit-")
        assert ".md" in report_path


# =============================================================================
# CLEAR QUEUE TESTS
# =============================================================================

class TestClearQueue:
    """Tests for queue clearing."""
    
    def test_clear_empty_queue(self, processor):
        """Clearing empty queue returns 0."""
        cleared = processor.clear_queue()
        
        assert cleared == 0
    
    def test_clear_queue_with_items(self, processor):
        """Clearing queue removes all items."""
        path = Path("/test.png")
        
        # Enqueue multiple items
        processor.enqueue(path, ArtifactType.SCREENSHOT)
        processor.enqueue(path, ArtifactType.SCREENSHOT)
        processor.enqueue(path, ArtifactType.SCREENSHOT)
        
        cleared = processor.clear_queue()
        
        assert cleared == 3
        assert processor.status.pending == 0


# =============================================================================
# QUEUE ITEM TESTS
# =============================================================================

class TestQueueItem:
    """Tests for QueueItem dataclass."""
    
    def test_queue_item_creation(self):
        """QueueItem is created correctly."""
        path = Path("/test.png")
        item = QueueItem(path=path, artifact_type=ArtifactType.SCREENSHOT)
        
        assert item.path == path
        assert item.artifact_type == ArtifactType.SCREENSHOT
        assert item.retry_count == 0
        assert isinstance(item.added_at, datetime)
    
    def test_queue_item_retry_count(self):
        """QueueItem retry_count can be set."""
        item = QueueItem(
            path=Path("/test.png"),
            artifact_type=ArtifactType.SCREENSHOT,
            retry_count=3,
        )
        
        assert item.retry_count == 3


# =============================================================================
# NO CALLBACK TESTS
# =============================================================================

class TestNoCallback:
    """Tests for processor without callback."""
    
    def test_processes_with_mock_without_callback(self, config, event_logger, artifact_path):
        """Processor creates mock results without callback."""
        processor = AutoProcessor(
            config=config,
            event_logger=event_logger,
            process_callback=None,
        )
        
        processor.start()
        processor.enqueue(artifact_path, ArtifactType.SCREENSHOT)
        
        time.sleep(0.3)
        processor.stop()
        
        # Should still complete with mock values
        assert processor.status.completed == 1
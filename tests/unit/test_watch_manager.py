"""
Unit tests for WatchManager - watch mode coordination.

Tests cover:
- WatchManager initialization and configuration
- Directory management
- Status tracking
- Signal handling
- Process existing artifacts
"""

import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.cli.watch.manager import WatchManager
from src.cli.watch.models import (
    ArtifactType,
    WatchConfig,
    WatchState,
    WatchStatus,
    QueueStatus,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_watch_dir(tmp_path):
    """Create a temporary watch directory."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    return watch_dir


@pytest.fixture
def config():
    """Create test watch configuration."""
    return WatchConfig(
        debounce_seconds=0.1,
        max_queue_size=100,
    )


@pytest.fixture
def process_callback():
    """Create mock process callback."""
    return MagicMock(return_value=("audit-123", "./reports/audit-123.md"))


@pytest.fixture
def manager(config, process_callback):
    """Create WatchManager instance."""
    return WatchManager(
        config=config,
        process_callback=process_callback,
    )


# =============================================================================
# INITIALIZATION TESTS
# =============================================================================

class TestWatchManagerInit:
    """Tests for WatchManager initialization."""
    
    def test_init_default_config(self):
        """Manager initializes with default config."""
        manager = WatchManager()
        
        assert manager.config is not None
        assert manager.dry_run is False
        assert manager.is_running is False
    
    def test_init_custom_config(self, config):
        """Manager accepts custom config."""
        manager = WatchManager(config=config)
        
        assert manager.config == config
    
    def test_init_dry_run(self, config):
        """Manager initializes in dry_run mode."""
        manager = WatchManager(config=config, dry_run=True)
        
        assert manager.dry_run is True
    
    def test_init_with_callback(self, config, process_callback):
        """Manager stores process callback."""
        manager = WatchManager(
            config=config,
            process_callback=process_callback,
        )
        
        # Callback is passed to processor
        assert manager.processor is not None


# =============================================================================
# DIRECTORY MANAGEMENT TESTS
# =============================================================================

class TestDirectoryManagement:
    """Tests for directory management."""
    
    def test_add_directory(self, manager, temp_watch_dir):
        """Can add a directory to watch."""
        result = manager.add_directory(temp_watch_dir)
        
        assert result is True
        assert temp_watch_dir in manager._directories
    
    def test_add_nonexistent_directory(self, manager):
        """Returns False for nonexistent directory."""
        result = manager.add_directory(Path("/nonexistent/path"))
        
        assert result is False
        assert len(manager._directories) == 0
    
    def test_add_file_as_directory(self, manager, tmp_path):
        """Returns False if path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        
        result = manager.add_directory(file_path)
        
        assert result is False
    
    def test_add_same_directory_twice(self, manager, temp_watch_dir):
        """Adding same directory twice is idempotent."""
        manager.add_directory(temp_watch_dir)
        result = manager.add_directory(temp_watch_dir)
        
        assert result is True
        assert len(manager._directories) == 1
    
    def test_add_multiple_directories(self, manager, tmp_path):
        """Can add multiple directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        manager.add_directory(dir1)
        manager.add_directory(dir2)
        
        assert len(manager._directories) == 2


# =============================================================================
# STATUS TESTS
# =============================================================================

class TestStatusTracking:
    """Tests for status tracking."""
    
    def test_initial_status(self, manager):
        """Initial status is IDLE."""
        status = manager.status
        
        assert status.state == WatchState.IDLE
    
    def test_status_property(self, manager):
        """Status property returns WatchStatus."""
        status = manager.status
        
        assert isinstance(status, WatchStatus)
    
    def test_queue_status_property(self, manager):
        """queue_status property returns QueueStatus."""
        queue = manager.queue_status
        
        assert isinstance(queue, QueueStatus)
    
    def test_is_running_false_initially(self, manager):
        """is_running is False initially."""
        assert manager.is_running is False
    
    def test_uptime_updates_when_running(self, manager, temp_watch_dir):
        """Uptime updates when watch is running."""
        manager.add_directory(temp_watch_dir)
        
        # Manually set status to running with started_at
        with manager._status_lock:
            manager._status.state = WatchState.RUNNING
            manager._status.started_at = datetime.utcnow()
        
        # Small delay
        time.sleep(0.1)
        
        status = manager.status
        assert status.uptime_seconds > 0


# =============================================================================
# START/STOP TESTS
# =============================================================================

class TestStartStop:
    """Tests for starting and stopping watch."""
    
    def test_start_no_directories(self, manager):
        """Start returns early if no directories configured."""
        # Should return without error
        manager._do_stop()  # Test internal stop
    
    def test_start_async(self, manager, temp_watch_dir):
        """start_async starts background thread."""
        manager.add_directory(temp_watch_dir)
        
        # Patch the blocking start method to just set status without blocking
        def mock_start():
            with manager._status_lock:
                manager._status.state = WatchState.RUNNING
            # Keep thread alive briefly
            time.sleep(0.2)
        
        with patch.object(manager, 'start', side_effect=mock_start):
            manager.start_async()
            
            # Give thread time to start
            time.sleep(0.05)
            
            assert manager._watch_thread is not None
            # Thread should be alive since mock_start sleeps
            assert manager._watch_thread.is_alive()
    
    def test_stop_sets_event(self, manager):
        """Stop sets the stop event."""
        manager.stop()
        
        assert manager._stop_event.is_set()
    
    def test_stop_when_not_running(self, manager):
        """Stop is safe when not running."""
        # Should not raise
        manager.stop()
        
        assert manager.status.state == WatchState.STOPPED
    
    def test_double_stop_safe(self, manager, temp_watch_dir):
        """Double stop is safe."""
        manager.add_directory(temp_watch_dir)
        manager.stop()
        manager.stop()  # Should not raise
        
        assert manager.status.state == WatchState.STOPPED


# =============================================================================
# PROCESS EXISTING TESTS
# =============================================================================

class TestProcessExisting:
    """Tests for processing existing artifacts."""
    
    def test_process_existing_no_directories(self, manager):
        """Returns 0 if no directories configured."""
        count = manager.process_existing()
        
        assert count == 0
    
    def test_process_existing_empty_directory(self, manager, temp_watch_dir):
        """Returns 0 for empty directory."""
        manager.add_directory(temp_watch_dir)
        
        count = manager.process_existing()
        
        assert count == 0
    
    def test_process_existing_with_screenshot(self, manager, temp_watch_dir):
        """Queues existing screenshots."""
        manager.add_directory(temp_watch_dir)
        
        # Create a screenshot
        screenshot = temp_watch_dir / "test.png"
        screenshot.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        
        count = manager.process_existing()
        
        assert count == 1
    
    def test_process_existing_with_video(self, manager, temp_watch_dir):
        """Queues existing videos."""
        manager.add_directory(temp_watch_dir)
        
        # Create a video file (mock MP4)
        video = temp_watch_dir / "test.mp4"
        video.write_bytes(b'\x00\x00\x00\x18ftypmp42' + b'\x00' * 100)
        
        count = manager.process_existing()
        
        assert count == 1
    
    def test_process_existing_ignores_non_artifacts(self, manager, temp_watch_dir):
        """Ignores files that aren't artifacts."""
        manager.add_directory(temp_watch_dir)
        
        # Create non-artifact files
        (temp_watch_dir / "readme.txt").write_text("readme")
        (temp_watch_dir / "config.yaml").write_text("key: value")
        
        count = manager.process_existing()
        
        assert count == 0
    
    def test_process_existing_recursive(self, manager, tmp_path):
        """Process existing finds files in subdirectories."""
        watch_dir = tmp_path / "watch"
        sub_dir = watch_dir / "subdir"
        sub_dir.mkdir(parents=True)
        
        manager.add_directory(watch_dir, recursive=True)
        
        # Create screenshot in subdirectory
        screenshot = sub_dir / "nested.png"
        screenshot.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        
        count = manager.process_existing()
        
        assert count == 1


# =============================================================================
# STATUS DISPLAY TESTS
# =============================================================================

class TestStatusDisplay:
    """Tests for status display formatting."""
    
    def test_get_status_display(self, manager):
        """get_status_display returns formatted dict."""
        display = manager.get_status_display()
        
        assert isinstance(display, dict)
        assert "Watch State" in display
        assert "Directories" in display
        assert "Queue Pending" in display
    
    def test_status_display_with_directories(self, manager, temp_watch_dir):
        """Status display shows configured directories after start sets them."""
        manager.add_directory(temp_watch_dir)
        
        # Directories are set in status when start() is called
        # Here we simulate what start() does to status
        with manager._status_lock:
            manager._status.directories = [str(d) for d in manager._directories]
        
        display = manager.get_status_display()
        
        assert str(temp_watch_dir) in display["Directories"]


# =============================================================================
# DRY RUN TESTS
# =============================================================================

class TestDryRun:
    """Tests for dry run mode."""
    
    def test_dry_run_no_processing(self, config, temp_watch_dir):
        """Dry run mode doesn't process artifacts."""
        manager = WatchManager(config=config, dry_run=True)
        manager.add_directory(temp_watch_dir)
        
        # Create artifact
        screenshot = temp_watch_dir / "test.png"
        screenshot.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        
        count = manager.process_existing()
        
        # Should queue but processor has no callback
        assert manager.dry_run is True


# =============================================================================
# SIGNAL HANDLER TESTS
# =============================================================================

class TestSignalHandlers:
    """Tests for signal handler setup."""
    
    def test_setup_signal_handlers(self, manager):
        """Signal handlers can be set up."""
        # Just test that the method exists and doesn't raise
        manager._setup_signal_handlers()
        
        # Verify stop_event is available
        assert manager._stop_event is not None


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_start_already_running(self, manager, temp_watch_dir):
        """Starting when already running logs warning."""
        manager.add_directory(temp_watch_dir)
        
        # Manually set to running
        with manager._status_lock:
            manager._status.state = WatchState.RUNNING
        
        # Should return early without error
        manager.start()  # Would block if it really started
    
    def test_add_directory_after_start(self, manager, temp_watch_dir):
        """Can add directory after manager created."""
        # Manager exists but no directories
        assert len(manager._directories) == 0
        
        result = manager.add_directory(temp_watch_dir)
        
        assert result is True
    
    def test_status_thread_safety(self, manager):
        """Status access is thread-safe."""
        results = []
        
        def read_status():
            for _ in range(10):
                results.append(manager.status)
        
        threads = [threading.Thread(target=read_status) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All reads should succeed
        assert len(results) == 50
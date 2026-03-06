"""Unit tests for watch mode models."""

import pytest
from datetime import datetime
from pathlib import Path
import time

from src.cli.watch.models import (
    ArtifactType,
    WatchState,
    WatchEventType,
    WatchStatus,
    QueueStatus,
    WatchEvent,
    WatchConfig,
)


class TestArtifactType:
    """Tests for ArtifactType enum."""
    
    def test_from_extension_screenshot(self):
        """Test detecting screenshot types."""
        assert ArtifactType.from_extension("png") == ArtifactType.SCREENSHOT
        assert ArtifactType.from_extension(".jpg") == ArtifactType.SCREENSHOT
        assert ArtifactType.from_extension("JPEG") == ArtifactType.SCREENSHOT
        assert ArtifactType.from_extension(".gif") == ArtifactType.SCREENSHOT
        assert ArtifactType.from_extension("webp") == ArtifactType.SCREENSHOT
    
    def test_from_extension_video(self):
        """Test detecting video types."""
        assert ArtifactType.from_extension("mp4") == ArtifactType.VIDEO
        assert ArtifactType.from_extension(".mov") == ArtifactType.VIDEO
        assert ArtifactType.from_extension("avi") == ArtifactType.VIDEO
        assert ArtifactType.from_extension("mkv") == ArtifactType.VIDEO
        assert ArtifactType.from_extension("webm") == ArtifactType.VIDEO
    
    def test_from_extension_unknown(self):
        """Test unknown file types."""
        assert ArtifactType.from_extension("txt") == ArtifactType.UNKNOWN
        assert ArtifactType.from_extension(".pdf") == ArtifactType.UNKNOWN
        assert ArtifactType.from_extension("docx") == ArtifactType.UNKNOWN


class TestWatchStatus:
    """Tests for WatchStatus model."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        status = WatchStatus()
        assert status.state == WatchState.IDLE
        assert status.directories == []
        assert status.recursive is False
        assert status.started_at is None
        assert status.uptime_seconds == 0.0
        assert status.total_detected == 0
        assert status.total_processed == 0
        assert status.total_failed == 0
    
    def test_to_display_dict(self):
        """Test display dictionary conversion."""
        status = WatchStatus(
            state=WatchState.RUNNING,
            directories=["/data/screenshots"],
            recursive=True,
            total_detected=5,
        )
        display = status.to_display_dict()
        
        assert display["State"] == "running"
        assert display["Directories"] == "/data/screenshots"
        assert display["Recursive"] == "Yes"
        assert display["Detected"] == 5


class TestQueueStatus:
    """Tests for QueueStatus model."""
    
    def test_default_values(self):
        """Test default values."""
        status = QueueStatus()
        assert status.pending == 0
        assert status.processing == 0
        assert status.completed == 0
        assert status.failed == 0
        assert status.max_size == 100
    
    def test_is_full(self):
        """Test queue full detection."""
        status = QueueStatus(pending=50, max_size=100)
        assert not status.is_full
        
        status = QueueStatus(pending=100, max_size=100)
        assert status.is_full
    
    def test_total(self):
        """Test total calculation."""
        status = QueueStatus(
            pending=5,
            processing=2,
            completed=10,
            failed=1,
        )
        assert status.total == 18


class TestWatchEvent:
    """Tests for WatchEvent model."""
    
    def test_to_ndjson(self):
        """Test NDJSON serialization."""
        event = WatchEvent(
            event_type=WatchEventType.DETECTED,
            path="/data/test.png",
            artifact_type=ArtifactType.SCREENSHOT,
            message="Detected screenshot",
        )
        
        json_str = event.to_ndjson()
        
        # Should be valid JSON
        import json
        data = json.loads(json_str)
        
        assert data["event_type"] == "detected"
        assert data["path"] == "/data/test.png"
        assert data["artifact_type"] == "screenshot"
        assert data["message"] == "Detected screenshot"
        assert "timestamp" in data


class TestWatchConfig:
    """Tests for WatchConfig model."""
    
    def test_default_values(self):
        """Test default configuration."""
        config = WatchConfig()
        
        assert config.debounce_window_seconds == 2.0
        assert config.max_queue_size == 100
        assert config.processing_interval_seconds == 0.5
        assert "png" in config.screenshot_extensions
        assert "mp4" in config.video_extensions
    
    def test_lowercase_extensions(self):
        """Test extensions are normalized to lowercase."""
        config = WatchConfig(
            screenshot_extensions=["PNG", ".JPG", "jpeg"],
            video_extensions=["MP4", ".MOV"],
        )
        
        assert "png" in config.screenshot_extensions
        assert "jpg" in config.screenshot_extensions
        assert "mp4" in config.video_extensions
        assert "mov" in config.video_extensions
    
    def test_is_screenshot(self, tmp_path):
        """Test screenshot detection."""
        config = WatchConfig()
        
        assert config.is_screenshot(Path("test.png"))
        assert config.is_screenshot(Path("test.jpg"))
        assert config.is_screenshot(Path("test.jpeg"))
        assert not config.is_screenshot(Path("test.mp4"))
        assert not config.is_screenshot(Path("test.txt"))
    
    def test_is_video(self, tmp_path):
        """Test video detection."""
        config = WatchConfig()
        
        assert config.is_video(Path("test.mp4"))
        assert config.is_video(Path("test.mov"))
        assert not config.is_video(Path("test.png"))
        assert not config.is_video(Path("test.txt"))
    
    def test_is_artifact(self):
        """Test general artifact detection."""
        config = WatchConfig()
        
        assert config.is_artifact(Path("test.png"))
        assert config.is_artifact(Path("test.mp4"))
        assert not config.is_artifact(Path("test.txt"))
    
    def test_get_artifact_type(self):
        """Test artifact type resolution."""
        config = WatchConfig()
        
        assert config.get_artifact_type(Path("test.png")) == ArtifactType.SCREENSHOT
        assert config.get_artifact_type(Path("test.mp4")) == ArtifactType.VIDEO
        assert config.get_artifact_type(Path("test.txt")) == ArtifactType.UNKNOWN
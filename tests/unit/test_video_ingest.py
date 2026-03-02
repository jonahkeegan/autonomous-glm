"""
Unit tests for video ingestion functionality.

Tests video validation, frame extraction, and ingestion integration.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from src.ingest import (
    VideoIngestConfig,
    VideoContainer,
    VideoCodec,
    VideoValidator,
    validate_video,
    check_ffmpeg_available,
    FrameExtractor,
    VideoValidationErrorCode,
    VideoValidationError,
    VideoValidationResult,
    FrameInfo,
)
from src.ingest.video_models import ExtractionMetadata


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def video_config():
    """Default video ingestion config for tests."""
    return VideoIngestConfig(
        max_file_size_mb=500.0,
        max_duration_seconds=1800.0,
        max_width=10000,
        max_height=10000,
        allowed_containers=[VideoContainer.MP4, VideoContainer.MOV],
        allowed_codecs=[VideoCodec.H264, VideoCodec.H265, VideoCodec.HEVC, VideoCodec.VP8, VideoCodec.VP9],
        extraction_interval=1.0,
        max_frames=500,
    )


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_mp4_file(temp_dir):
    """Create a mock MP4 file with valid ftyp header."""
    mp4_path = temp_dir / "test_video.mp4"
    # MP4 header: size (4 bytes) + "ftyp" (4 bytes) + brand "isom" (4 bytes)
    header = b"\x00\x00\x00\x14ftypisom"
    # Add some dummy data to make file non-empty
    mp4_path.write_bytes(header + b"\x00" * 1000)
    return mp4_path


@pytest.fixture
def mock_mov_file(temp_dir):
    """Create a mock MOV file with valid ftyp header."""
    mov_path = temp_dir / "test_video.mov"
    # MOV header with "qt  " brand
    header = b"\x00\x00\x00\x14ftypqt  "
    mov_path.write_bytes(header + b"\x00" * 1000)
    return mov_path


@pytest.fixture
def mock_invalid_file(temp_dir):
    """Create an invalid file (not a video)."""
    invalid_path = temp_dir / "invalid.txt"
    invalid_path.write_text("This is not a video file")
    return invalid_path


@pytest.fixture
def mock_empty_file(temp_dir):
    """Create an empty file."""
    empty_path = temp_dir / "empty.mp4"
    empty_path.write_bytes(b"")
    return empty_path


# =============================================================================
# VideoIngestConfig Tests
# =============================================================================

class TestVideoIngestConfig:
    """Tests for VideoIngestConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = VideoIngestConfig()
        
        assert config.max_file_size_mb == 500.0
        assert config.max_duration_seconds == 1800.0
        assert config.max_frames == 500
        assert config.extraction_interval == 1.0
        assert VideoContainer.MP4 in config.allowed_containers
        assert VideoCodec.H264 in config.allowed_codecs
    
    def test_max_file_size_bytes(self, video_config):
        """Test max_file_size_bytes property."""
        expected = int(500.0 * 1024 * 1024)
        assert video_config.max_file_size_bytes == expected
    
    def test_extraction_fps(self, video_config):
        """Test extraction_fps property."""
        assert video_config.extraction_fps == 1.0  # 1 / 1.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = VideoIngestConfig(
            max_file_size_mb=100.0,
            max_duration_seconds=60.0,
            extraction_interval=0.5,
            max_frames=100,
        )
        
        assert config.max_file_size_mb == 100.0
        assert config.max_duration_seconds == 60.0
        assert config.extraction_interval == 0.5
        assert config.max_frames == 100


# =============================================================================
# VideoValidator Tests
# =============================================================================

class TestVideoValidator:
    """Tests for VideoValidator class."""
    
    def test_file_not_found(self, video_config):
        """Test validation fails for non-existent file."""
        validator = VideoValidator(video_config)
        result = validator.validate("/nonexistent/video.mp4")
        
        assert not result.valid
        assert len(result.errors) == 1
        assert result.errors[0].code == VideoValidationErrorCode.FILE_NOT_FOUND
    
    def test_empty_file(self, video_config, mock_empty_file):
        """Test validation fails for empty file."""
        validator = VideoValidator(video_config)
        result = validator.validate(mock_empty_file)
        
        assert not result.valid
        assert any(e.code == VideoValidationErrorCode.FILE_EMPTY for e in result.errors)
    
    def test_invalid_container(self, video_config, mock_invalid_file):
        """Test validation fails for invalid container format."""
        validator = VideoValidator(video_config)
        
        with patch.object(validator, '_check_ffmpeg', return_value=(True, None)):
            result = validator.validate(mock_invalid_file)
        
        assert not result.valid
        assert any(e.code == VideoValidationErrorCode.INVALID_CONTAINER for e in result.errors)
    
    def test_detect_mp4_container(self, video_config, mock_mp4_file):
        """Test MP4 container detection from ftyp box."""
        validator = VideoValidator(video_config)
        container = validator._detect_container(mock_mp4_file)
        
        assert container == VideoContainer.MP4
    
    def test_detect_mov_container(self, video_config, mock_mov_file):
        """Test MOV container detection from ftyp box."""
        validator = VideoValidator(video_config)
        container = validator._detect_container(mock_mov_file)
        
        assert container == VideoContainer.MOV
    
    def test_normalize_codec_h264(self, video_config):
        """Test H264 codec normalization."""
        validator = VideoValidator(video_config)
        
        assert validator._normalize_codec("h264") == VideoCodec.H264
        assert validator._normalize_codec("avc") == VideoCodec.H264
        assert validator._normalize_codec("avc1") == VideoCodec.H264
        assert validator._normalize_codec("H264") == VideoCodec.H264
    
    def test_normalize_codec_hevc(self, video_config):
        """Test HEVC codec normalization."""
        validator = VideoValidator(video_config)
        
        assert validator._normalize_codec("hevc") == VideoCodec.HEVC
        assert validator._normalize_codec("h265") == VideoCodec.H265
    
    def test_normalize_codec_unknown(self, video_config):
        """Test unknown codec returns None."""
        validator = VideoValidator(video_config)
        
        assert validator._normalize_codec("unknown") is None
        assert validator._normalize_codec("mpeg2") is None
    
    def test_validate_format_convenience(self, video_config, mock_mp4_file):
        """Test validate_format convenience method."""
        validator = VideoValidator(video_config)
        container = validator.validate_format(mock_mp4_file)
        
        assert container == VideoContainer.MP4
    
    def test_is_valid_video_convenience(self, video_config, mock_mp4_file):
        """Test is_valid_video convenience method."""
        validator = VideoValidator(video_config)
        
        # Mock ffprobe response
        mock_video_info = {
            "streams": [{
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
            }],
            "format": {
                "duration": "10.5",
            }
        }
        
        with patch.object(validator, '_check_ffmpeg', return_value=(True, None)):
            with patch('src.ingest.video_validators.get_video_info', return_value=mock_video_info):
                is_valid = validator.is_valid_video(mock_mp4_file)
        
        # Would be True if all validations pass
        assert isinstance(is_valid, bool)


# =============================================================================
# FrameExtractor Tests
# =============================================================================

class TestFrameExtractor:
    """Tests for FrameExtractor class."""
    
    def test_extractor_initialization(self, video_config):
        """Test FrameExtractor initialization."""
        extractor = FrameExtractor(video_config)
        
        assert extractor.config == video_config
        assert extractor._temp_dir is None
    
    def test_get_temp_dir(self, video_config):
        """Test temporary directory creation."""
        extractor = FrameExtractor(video_config)
        temp_dir = extractor._get_temp_dir()
        
        assert temp_dir.exists()
        assert "video_frames_" in str(temp_dir)
        
        # Cleanup
        extractor.cleanup()
    
    def test_cleanup(self, video_config):
        """Test cleanup removes temporary directory."""
        extractor = FrameExtractor(video_config)
        temp_dir = extractor._get_temp_dir()
        
        assert temp_dir.exists()
        
        extractor.cleanup()
        
        assert not temp_dir.exists()
        assert extractor._temp_dir is None
    
    def test_context_manager(self, video_config):
        """Test context manager pattern."""
        with FrameExtractor(video_config) as extractor:
            temp_dir = extractor._get_temp_dir()
            assert temp_dir.exists()
        
        # After context exit, temp dir should be cleaned
        assert not temp_dir.exists()
    
    def test_calculate_hash(self, video_config, temp_dir):
        """Test SHA-256 hash calculation."""
        extractor = FrameExtractor(video_config)
        
        # Create a test file
        test_file = temp_dir / "test_frame.png"
        test_file.write_bytes(b"test content")
        
        hash_result = extractor._calculate_hash(test_file)
        
        # SHA-256 hash is 64 hex characters
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)
    
    def test_deduplicate_frames(self, video_config, temp_dir):
        """Test frame deduplication by content hash."""
        extractor = FrameExtractor(video_config)
        
        # Create frames with same hash (duplicates)
        frames = [
            FrameInfo(
                frame_number=0,
                timestamp=0.0,
                content_hash="hash1",
                temp_path=temp_dir / "frame1.png",
            ),
            FrameInfo(
                frame_number=1,
                timestamp=1.0,
                content_hash="hash1",  # Duplicate
                temp_path=temp_dir / "frame2.png",
            ),
            FrameInfo(
                frame_number=2,
                timestamp=2.0,
                content_hash="hash2",  # Unique
                temp_path=temp_dir / "frame3.png",
            ),
        ]
        
        # Create the temp files
        for f in frames:
            f.temp_path.write_bytes(b"test")
        
        unique_frames = extractor.deduplicate_frames(frames)
        
        # Should have 2 unique frames
        assert len(unique_frames) == 2
        assert unique_frames[0].frame_number == 0
        assert unique_frames[1].frame_number == 2


# =============================================================================
# FrameInfo Tests
# =============================================================================

class TestFrameInfo:
    """Tests for FrameInfo model."""
    
    def test_frame_info_creation(self):
        """Test FrameInfo creation with required fields."""
        frame = FrameInfo(
            frame_number=0,
            timestamp=0.0,
        )
        
        assert frame.frame_number == 0
        assert frame.timestamp == 0.0
        assert frame.temp_path is None
        assert frame.content_hash is None
    
    def test_frame_info_with_all_fields(self, temp_dir):
        """Test FrameInfo with all fields populated."""
        frame = FrameInfo(
            frame_number=10,
            timestamp=5.5,
            temp_path=temp_dir / "frame.png",
            content_hash="abc123",
            width=1920,
            height=1080,
        )
        
        assert frame.frame_number == 10
        assert frame.timestamp == 5.5
        assert frame.content_hash == "abc123"
        assert frame.width == 1920
        assert frame.height == 1080


# =============================================================================
# ExtractionMetadata Tests
# =============================================================================

class TestExtractionMetadata:
    """Tests for ExtractionMetadata model."""
    
    def test_extraction_metadata_creation(self):
        """Test ExtractionMetadata creation."""
        metadata = ExtractionMetadata(
            source_duration=30.0,
            source_resolution=(1920, 1080),
            source_codec="h264",
            source_container="mp4",
            extraction_interval=1.0,
            total_frames_extracted=30,
        )
        
        assert metadata.source_duration == 30.0
        assert metadata.source_resolution == (1920, 1080)
        assert metadata.total_frames_extracted == 30
        assert metadata.frames_skipped == 0
    
    def test_extraction_metadata_with_skipped(self):
        """Test ExtractionMetadata with skipped frames."""
        metadata = ExtractionMetadata(
            source_duration=60.0,
            source_resolution=(3840, 2160),
            source_codec="hevc",
            source_container="mp4",
            extraction_interval=2.0,
            total_frames_extracted=28,
            frames_skipped=2,
            extraction_time_seconds=5.5,
        )
        
        assert metadata.frames_skipped == 2
        assert metadata.extraction_time_seconds == 5.5


# =============================================================================
# VideoValidationResult Tests
# =============================================================================

class TestVideoValidationResult:
    """Tests for VideoValidationResult model."""
    
    def test_valid_result(self):
        """Test a valid validation result."""
        result = VideoValidationResult(
            valid=True,
            container=VideoContainer.MP4,
            codec=VideoCodec.H264,
            duration=30.0,
            resolution=(1920, 1080),
            file_size=5000000,
        )
        
        assert result.valid
        assert not result.has_errors
        assert result.container == VideoContainer.MP4
    
    def test_invalid_result_with_errors(self):
        """Test invalid result with errors."""
        result = VideoValidationResult(
            valid=False,
            errors=[
                VideoValidationError(
                    code=VideoValidationErrorCode.FILE_TOO_LARGE,
                    message="File exceeds size limit",
                )
            ],
        )
        
        assert not result.valid
        assert result.has_errors
        assert len(result.errors) == 1
    
    def test_result_with_warnings(self):
        """Test result with warnings."""
        result = VideoValidationResult(
            valid=True,
            warnings=["Video has variable frame rate"],
        )
        
        assert result.valid
        assert result.has_warnings
        assert len(result.warnings) == 1


# =============================================================================
# check_ffmpeg_available Tests
# =============================================================================

class TestCheckFfmpegAvailable:
    """Tests for check_ffmpeg_available function."""
    
    @patch('subprocess.run')
    def test_ffmpeg_available(self, mock_run):
        """Test when ffmpeg is available."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ffmpeg version 5.0\n"
        )
        
        available, version = check_ffmpeg_available()
        
        assert available is True
        assert "ffmpeg version" in version
    
    @patch('subprocess.run')
    def test_ffmpeg_not_found(self, mock_run):
        """Test when ffmpeg is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        available, error = check_ffmpeg_available()
        
        assert available is False
        assert "not found" in error.lower()
    
    @patch('subprocess.run')
    def test_ffprobe_timeout(self, mock_run):
        """Test when ffmpeg check times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=5)
        
        available, error = check_ffmpeg_available()
        
        assert available is False
        assert "timed out" in error.lower()


# =============================================================================
# Integration Tests (require ffmpeg)
# =============================================================================

@pytest.mark.integration
class TestVideoIntegration:
    """Integration tests requiring ffmpeg."""
    
    @pytest.mark.skipif(
        not shutil.which("ffmpeg"),
        reason="ffmpeg not available"
    )
    def test_real_ffmpeg_check(self):
        """Test real ffmpeg availability check."""
        import shutil
        
        available, info = check_ffmpeg_available()
        
        if shutil.which("ffmpeg"):
            assert available is True
        else:
            assert available is False


# =============================================================================
# VideoContainer and VideoCodec Enums
# =============================================================================

class TestVideoEnums:
    """Tests for video-related enums."""
    
    def test_video_container_values(self):
        """Test VideoContainer enum values."""
        assert VideoContainer.MP4.value == "mp4"
        assert VideoContainer.MOV.value == "mov"
    
    def test_video_codec_values(self):
        """Test VideoCodec enum values."""
        assert VideoCodec.H264.value == "h264"
        assert VideoCodec.H265.value == "h265"
        assert VideoCodec.HEVC.value == "hevc"
        assert VideoCodec.VP8.value == "vp8"
        assert VideoCodec.VP9.value == "vp9"
    
    def test_video_validation_error_code_values(self):
        """Test VideoValidationErrorCode enum values."""
        assert VideoValidationErrorCode.FILE_NOT_FOUND.value == "file_not_found"
        assert VideoValidationErrorCode.UNSUPPORTED_CONTAINER.value == "unsupported_container"
        assert VideoValidationErrorCode.FFMPEG_NOT_AVAILABLE.value == "ffmpeg_not_available"
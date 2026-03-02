"""
Video validation utilities for Autonomous-GLM.

Provides video file validation including container format detection,
codec verification, duration limits, and resolution checks.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .video_models import (
    VideoContainer,
    VideoCodec,
    VideoIngestConfig,
    VideoValidationErrorCode,
    VideoValidationError,
    VideoValidationResult,
)


# Magic byte signatures for video containers
# MP4/MOV: ftyp box starts at offset 4, followed by brand
CONTAINER_SIGNATURES = {
    # MP4 brands
    b"mp41": VideoContainer.MP4,
    b"mp42": VideoContainer.MP4,
    b"isom": VideoContainer.MP4,
    b"iso2": VideoContainer.MP4,
    b"avc1": VideoContainer.MP4,
    b"msnv": VideoContainer.MP4,
    b"M4V ": VideoContainer.MP4,
    b"M4A ": VideoContainer.MP4,
    b"fmp4": VideoContainer.MP4,
    # MOV brands (QuickTime)
    b"qt  ": VideoContainer.MOV,
}

# Length of ftyp brand to read (4 bytes after "ftyp" marker)
BRAND_LENGTH = 4


def check_ffmpeg_available() -> tuple[bool, Optional[str]]:
    """
    Check if ffmpeg is available on the system.
    
    Returns:
        Tuple of (available, version_string or error_message)
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split("\n")[0] if result.stdout else "ffmpeg"
            return True, first_line
        return False, "ffmpeg returned non-zero exit code"
    except FileNotFoundError:
        return False, "ffmpeg not found in PATH. Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
    except subprocess.TimeoutExpired:
        return False, "ffmpeg version check timed out"
    except Exception as e:
        return False, f"Error checking ffmpeg: {str(e)}"


def get_video_info(file_path: Path) -> Optional[dict]:
    """
    Get video metadata using ffprobe.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Dictionary with video info or None if failed
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return None
            
        import json
        return json.loads(result.stdout)
        
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


class VideoValidator:
    """Validator for video files."""
    
    def __init__(self, config: Optional[VideoIngestConfig] = None):
        """Initialize validator with optional configuration."""
        self.config = config or VideoIngestConfig()
        self._ffmpeg_checked = False
        self._ffmpeg_available = False
    
    def _check_ffmpeg(self) -> tuple[bool, Optional[str]]:
        """Check ffmpeg availability (cached)."""
        if not self._ffmpeg_checked:
            self._ffmpeg_available, _ = check_ffmpeg_available()
            self._ffmpeg_checked = True
        return self._ffmpeg_available, None
    
    def validate(self, file_path: str | Path) -> VideoValidationResult:
        """
        Validate a video file.
        
        Performs all validation checks and returns a comprehensive result.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            VideoValidationResult with validity status, errors, and metadata
        """
        path = Path(file_path)
        errors: list[VideoValidationError] = []
        warnings: list[str] = []
        
        # Track detected values
        detected_container: Optional[VideoContainer] = None
        detected_codec: Optional[VideoCodec] = None
        duration: Optional[float] = None
        resolution: Optional[tuple[int, int]] = None
        file_size: Optional[int] = None
        
        # Step 1: Check file exists
        if not path.exists():
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.FILE_NOT_FOUND,
                message=f"File not found: {file_path}",
                detail=str(path.absolute())
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Step 2: Check file is readable
        if not os.access(path, os.R_OK):
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.PERMISSION_DENIED,
                message=f"Permission denied: cannot read file",
                detail=str(path.absolute())
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Step 3: Get file size
        file_size = path.stat().st_size
        
        # Step 4: Check file is not empty
        if file_size == 0:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.FILE_EMPTY,
                message="File is empty (0 bytes)",
                detail=str(path)
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size
            )
        
        # Step 5: Check file size limit
        if file_size > self.config.max_file_size_bytes:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.FILE_TOO_LARGE,
                message=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds limit ({self.config.max_file_size_mb} MB)",
                detail=f"Size: {file_size} bytes, Limit: {self.config.max_file_size_bytes} bytes"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size
            )
        
        # Step 6: Check ffmpeg availability
        ffmpeg_available, ffmpeg_error = self._check_ffmpeg()
        if not ffmpeg_available:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.FFMPEG_NOT_AVAILABLE,
                message="ffmpeg is not available",
                detail=ffmpeg_error or "Install ffmpeg to enable video validation"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size
            )
        
        # Step 7: Detect container from magic bytes (ftyp box)
        detected_container = self._detect_container(path)
        if detected_container is None:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.INVALID_CONTAINER,
                message="File does not appear to be a valid MP4 or MOV video",
                detail="Could not detect ftyp box with recognized brand"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size
            )
        
        # Step 8: Check container is allowed
        if detected_container not in self.config.allowed_containers:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.UNSUPPORTED_CONTAINER,
                message=f"Container format '{detected_container.value}' is not allowed",
                detail=f"Allowed containers: {[c.value for c in self.config.allowed_containers]}"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size,
                container=detected_container
            )
        
        # Step 9: Get video info using ffprobe
        video_info = get_video_info(path)
        if video_info is None:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.CORRUPTED_VIDEO,
                message="Could not read video metadata",
                detail="ffprobe failed to extract video information"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size,
                container=detected_container
            )
        
        # Step 10: Extract video stream info
        video_stream = None
        for stream in video_info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break
        
        if video_stream is None:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.CORRUPTED_VIDEO,
                message="No video stream found in file",
                detail="File may be audio-only or corrupted"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size,
                container=detected_container
            )
        
        # Step 11: Extract codec
        codec_name = video_stream.get("codec_name", "").lower()
        detected_codec = self._normalize_codec(codec_name)
        
        if detected_codec is None:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.UNSUPPORTED_CODEC,
                message=f"Video codec '{codec_name}' is not supported",
                detail=f"Allowed codecs: {[c.value for c in self.config.allowed_codecs]}"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size,
                container=detected_container
            )
        
        # Step 12: Check codec is allowed
        if detected_codec not in self.config.allowed_codecs:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.UNSUPPORTED_CODEC,
                message=f"Codec '{detected_codec.value}' is not allowed",
                detail=f"Allowed codecs: {[c.value for c in self.config.allowed_codecs]}"
            ))
            return VideoValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size,
                container=detected_container,
                codec=detected_codec
            )
        
        # Step 13: Extract duration
        format_info = video_info.get("format", {})
        duration_str = format_info.get("duration")
        if duration_str:
            try:
                duration = float(duration_str)
            except ValueError:
                duration = None
        
        if duration is None:
            # Try from video stream
            duration_str = video_stream.get("duration")
            if duration_str:
                try:
                    duration = float(duration_str)
                except ValueError:
                    pass
        
        # Step 14: Check duration limit
        if duration is not None and duration > self.config.max_duration_seconds:
            errors.append(VideoValidationError(
                code=VideoValidationErrorCode.DURATION_TOO_LONG,
                message=f"Video duration ({duration:.1f}s) exceeds limit ({self.config.max_duration_seconds}s)",
                detail=f"Duration: {duration} seconds, Limit: {self.config.max_duration_seconds} seconds"
            ))
        
        # Step 15: Extract resolution
        width = video_stream.get("width")
        height = video_stream.get("height")
        if width and height:
            resolution = (width, height)
        
        # Step 16: Check resolution limits
        if resolution:
            if resolution[0] > self.config.max_width or resolution[1] > self.config.max_height:
                errors.append(VideoValidationError(
                    code=VideoValidationErrorCode.RESOLUTION_TOO_LARGE,
                    message=f"Video resolution ({resolution[0]}x{resolution[1]}) exceeds maximum ({self.config.max_width}x{self.config.max_height})",
                    detail=f"Width: {resolution[0]}, Height: {resolution[1]}"
                ))
        
        # Return result
        return VideoValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            container=detected_container,
            codec=detected_codec,
            duration=duration,
            resolution=resolution,
            file_size=file_size
        )
    
    def _detect_container(self, path: Path) -> Optional[VideoContainer]:
        """
        Detect video container format from ftyp box.
        
        MP4 and MOV files start with:
        - Bytes 0-3: File size (big-endian)
        - Bytes 4-7: "ftyp" marker
        - Bytes 8-11: Brand (e.g., "mp42", "qt  ", "isom")
        
        Args:
            path: Path to the file
            
        Returns:
            Detected VideoContainer or None if not recognized
        """
        try:
            with open(path, "rb") as f:
                # Read first 12 bytes (size + ftyp + brand)
                header = f.read(12)
                
                if len(header) < 12:
                    return None
                
                # Check for ftyp marker at offset 4
                ftyp_marker = header[4:8]
                if ftyp_marker != b"ftyp":
                    return None
                
                # Get brand at offset 8
                brand = header[8:12]
                
                return CONTAINER_SIGNATURES.get(brand)
                
        except (IOError, OSError):
            return None
    
    def _normalize_codec(self, codec_name: str) -> Optional[VideoCodec]:
        """
        Normalize codec name to VideoCodec enum.
        
        Args:
            codec_name: Raw codec name from ffprobe
            
        Returns:
            VideoCodec enum value or None
        """
        codec_map = {
            "h264": VideoCodec.H264,
            "avc": VideoCodec.H264,
            "avc1": VideoCodec.H264,
            "h265": VideoCodec.H265,
            "hevc": VideoCodec.HEVC,
            "vp8": VideoCodec.VP8,
            "vp9": VideoCodec.VP9,
        }
        return codec_map.get(codec_name.lower())
    
    def validate_format(self, file_path: str | Path) -> Optional[VideoContainer]:
        """
        Quick container detection without full validation.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected VideoContainer or None
        """
        return self._detect_container(Path(file_path))
    
    def is_valid_video(self, file_path: str | Path) -> bool:
        """
        Quick check if file is a valid video.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid, False otherwise
        """
        result = self.validate(file_path)
        return result.valid


def validate_video(file_path: str | Path, config: Optional[VideoIngestConfig] = None) -> VideoValidationResult:
    """
    Convenience function to validate a video file.
    
    Args:
        file_path: Path to the file to validate
        config: Optional configuration (uses defaults if not provided)
        
    Returns:
        VideoValidationResult with validity status and any errors
    """
    validator = VideoValidator(config)
    return validator.validate(file_path)
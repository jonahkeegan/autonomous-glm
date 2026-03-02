"""
Frame extraction utilities for video ingestion.

Provides time-based frame extraction using ffmpeg, frame metadata capture,
and temporary file management.
"""

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from .video_models import FrameInfo, VideoIngestConfig


class FrameExtractor:
    """Extracts frames from video files using ffmpeg."""
    
    def __init__(self, config: Optional[VideoIngestConfig] = None):
        """Initialize frame extractor with optional configuration."""
        self.config = config or VideoIngestConfig()
        self._temp_dir: Optional[Path] = None
    
    def _get_temp_dir(self) -> Path:
        """Get or create temporary directory for frame extraction."""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="video_frames_"))
        return self._temp_dir
    
    def cleanup(self) -> None:
        """Clean up temporary files created during extraction."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
            except OSError:
                pass
            self._temp_dir = None
    
    def extract_frames(
        self,
        video_path: Path,
        interval: Optional[float] = None,
        max_frames: Optional[int] = None,
    ) -> list[FrameInfo]:
        """
        Extract frames from a video at specified time intervals.
        
        Args:
            video_path: Path to the video file
            interval: Time interval between frames in seconds (default from config)
            max_frames: Maximum number of frames to extract (default from config)
            
        Returns:
            List of FrameInfo objects with metadata and temp paths
            
        Raises:
            RuntimeError: If frame extraction fails
        """
        interval = interval or self.config.extraction_interval
        max_frames = max_frames or self.config.max_frames
        
        # Calculate extraction FPS (inverse of interval)
        fps = 1.0 / interval
        
        # Create output directory
        temp_dir = self._get_temp_dir()
        output_pattern = temp_dir / "frame_%06d.png"
        
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"fps={fps}",
            "-vsync", "vfr",  # Variable frame rate to match timestamps
            "-frame_preview", "false",
            "-y",  # Overwrite existing files
            str(output_pattern),
        ]
        
        # Run ffmpeg
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for extraction
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg frame extraction failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Frame extraction timed out after 5 minutes")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
        
        extraction_time = time.time() - start_time
        
        # Collect extracted frames
        frames: list[FrameInfo] = []
        frame_files = sorted(temp_dir.glob("frame_*.png"))
        
        for i, frame_path in enumerate(frame_files):
            if i >= max_frames:
                # Remove excess frames
                try:
                    frame_path.unlink()
                except OSError:
                    pass
                continue
            
            # Calculate frame metadata
            frame_number = i
            timestamp = i * interval
            
            # Calculate content hash
            content_hash = self._calculate_hash(frame_path)
            
            # Get frame dimensions
            width, height = self._get_image_dimensions(frame_path)
            
            frames.append(FrameInfo(
                frame_number=frame_number,
                timestamp=round(timestamp, 3),
                temp_path=frame_path,
                content_hash=content_hash,
                width=width,
                height=height,
            ))
        
        return frames
    
    def extract_single_frame(
        self,
        video_path: Path,
        timestamp: float,
    ) -> Optional[FrameInfo]:
        """
        Extract a single frame at a specific timestamp.
        
        Args:
            video_path: Path to the video file
            timestamp: Time in seconds to extract frame from
            
        Returns:
            FrameInfo if successful, None otherwise
        """
        temp_dir = self._get_temp_dir()
        output_path = temp_dir / f"frame_{timestamp:.3f}.png"
        
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),  # Seek to timestamp
            "-i", str(video_path),
            "-vframes", "1",  # Extract only 1 frame
            "-y",
            str(output_path),
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0 or not output_path.exists():
                return None
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
        
        # Get frame dimensions
        width, height = self._get_image_dimensions(output_path)
        
        return FrameInfo(
            frame_number=0,
            timestamp=timestamp,
            temp_path=output_path,
            content_hash=self._calculate_hash(output_path),
            width=width,
            height=height,
        )
    
    def _calculate_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _get_image_dimensions(self, file_path: Path) -> tuple[Optional[int], Optional[int]]:
        """
        Get image dimensions using ffprobe.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (width, height) or (None, None) if failed
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode != 0:
                return (None, None)
            
            import json
            data = json.loads(result.stdout)
            
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    return (stream.get("width"), stream.get("height"))
            
            return (None, None)
            
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return (None, None)
    
    def deduplicate_frames(
        self,
        frames: list[FrameInfo],
    ) -> list[FrameInfo]:
        """
        Remove duplicate frames based on content hash.
        
        Args:
            frames: List of FrameInfo objects
            
        Returns:
            Deduplicated list of FrameInfo objects
        """
        seen_hashes: set[str] = set()
        unique_frames: list[FrameInfo] = []
        
        for frame in frames:
            if frame.content_hash and frame.content_hash not in seen_hashes:
                seen_hashes.add(frame.content_hash)
                unique_frames.append(frame)
            elif frame.temp_path:
                # Remove duplicate frame file
                try:
                    frame.temp_path.unlink()
                except OSError:
                    pass
        
        return unique_frames
    
    def __enter__(self) -> "FrameExtractor":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup temp files."""
        self.cleanup()


def extract_frames(
    video_path: Path,
    config: Optional[VideoIngestConfig] = None,
) -> list[FrameInfo]:
    """
    Convenience function to extract frames from a video.
    
    Args:
        video_path: Path to the video file
        config: Optional configuration
        
    Returns:
        List of FrameInfo objects
    """
    with FrameExtractor(config) as extractor:
        return extractor.extract_frames(video_path)
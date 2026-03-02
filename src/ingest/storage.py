"""
Storage management for screenshot ingestion.

Provides organized file storage with date-based directory structure,
atomic file operations, content hashing, and duplicate detection.
"""

import hashlib
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ImageFormat, IngestConfig


class StorageManager:
    """Manages screenshot file storage."""
    
    # UUID namespace for deterministic ingest IDs (DNS namespace as base)
    UUID_NAMESPACE = uuid.NAMESPACE_DNS
    
    def __init__(self, config: Optional[IngestConfig] = None):
        """Initialize storage manager with optional configuration."""
        self.config = config or IngestConfig()
        self._base_dir: Optional[Path] = None
    
    @property
    def base_dir(self) -> Path:
        """Get the base storage directory, creating it if needed."""
        if self._base_dir is None:
            self._base_dir = Path(self.config.screenshots_dir).resolve()
            self._base_dir.mkdir(parents=True, exist_ok=True)
        return self._base_dir
    
    def calculate_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks for memory efficiency with large files
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def generate_ingest_id(self, file_path: Path) -> str:
        """
        Generate a deterministic ingest ID from file content.
        
        Uses SHA-256 hash to create a UUID v5 for consistent identification.
        Same file content always produces the same ingest ID.
        
        Args:
            file_path: Path to the file
            
        Returns:
            UUID string based on content hash
        """
        content_hash = self.calculate_hash(file_path)
        
        # Create deterministic UUID v5 from content hash
        ingest_uuid = uuid.uuid5(self.UUID_NAMESPACE, content_hash)
        
        return str(ingest_uuid)
    
    def get_storage_path(
        self,
        ingest_id: str,
        format: ImageFormat,
        date: Optional[datetime] = None
    ) -> Path:
        """
        Get the storage path for a file.
        
        Structure: {base_dir}/{YYYY}/{MM}/{ingest_id}.{ext}
        
        Args:
            ingest_id: Unique ingest identifier
            format: Image format (determines extension)
            date: Optional date (uses current date if not provided)
            
        Returns:
            Full path where the file should be stored
        """
        date = date or datetime.now()
        
        # Create date-based directory structure
        year = date.strftime("%Y")
        month = date.strftime("%m")
        
        directory = self.base_dir / year / month
        directory.mkdir(parents=True, exist_ok=True)
        
        # Determine extension
        ext = format.value.lower()
        if ext == "jpeg":
            ext = "jpg"
        
        filename = f"{ingest_id}.{ext}"
        return directory / filename
    
    def store_file(
        self,
        source_path: Path,
        dest_path: Path
    ) -> Path:
        """
        Store a file with atomic write operation.
        
        Writes to a temporary file first, then renames to final destination.
        This ensures no partial files exist if the operation is interrupted.
        
        Args:
            source_path: Path to source file
            dest_path: Destination path (from get_storage_path)
            
        Returns:
            Path to the stored file
            
        Raises:
            IOError: If file operation fails
        """
        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temp file in same directory for atomic rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dest_path.parent,
            prefix=".tmp_"
        )
        
        try:
            # Copy file content
            with open(source_path, "rb") as src:
                with os.fdopen(temp_fd, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            
            # Atomic rename
            os.rename(temp_path, dest_path)
            
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
        
        return dest_path
    
    def file_exists(self, storage_path: Path) -> bool:
        """
        Check if a file already exists at the storage path.
        
        Args:
            storage_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return storage_path.exists()
    
    def find_by_hash(self, content_hash: str) -> Optional[Path]:
        """
        Find an existing file by its content hash.
        
        This is a simple implementation that scans for files matching
        the ingest ID pattern. For production, consider a database index.
        
        Args:
            content_hash: SHA-256 hash to search for
            
        Returns:
            Path to existing file or None
        """
        ingest_id = str(uuid.uuid5(self.UUID_NAMESPACE, content_hash))
        
        # Search for files matching the ingest ID
        for year_dir in self.base_dir.iterdir():
            if not year_dir.is_dir():
                continue
            
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                
                for file_path in month_dir.iterdir():
                    if file_path.stem == ingest_id:
                        return file_path
        
        return None
    
    def get_relative_path(self, full_path: Path) -> str:
        """
        Get path relative to base directory.
        
        Args:
            full_path: Full path to file
            
        Returns:
            Relative path as string
        """
        try:
            return str(full_path.relative_to(self.base_dir))
        except ValueError:
            return str(full_path)
    
    def cleanup_empty_directories(self) -> int:
        """
        Remove empty month directories.
        
        Returns:
            Number of directories removed
        """
        removed = 0
        
        for year_dir in self.base_dir.iterdir():
            if not year_dir.is_dir():
                continue
            
            for month_dir in list(year_dir.iterdir()):
                if not month_dir.is_dir():
                    continue
                
                try:
                    month_dir.rmdir()
                    removed += 1
                except OSError:
                    # Directory not empty
                    pass
            
            # Try to remove empty year directory
            try:
                year_dir.rmdir()
            except OSError:
                pass
        
        return removed
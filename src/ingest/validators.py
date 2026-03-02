"""
Screenshot validation utilities for Autonomous-GLM.

Provides file validation including magic byte verification, size limits,
dimension checking, and corruption detection.
"""

import os
from pathlib import Path
from typing import Optional

from PIL import Image

from .models import (
    ImageFormat,
    IngestConfig,
    ValidationError,
    ValidationErrorCode,
    ValidationResult,
)


# Magic byte signatures for supported formats
MAGIC_BYTES = {
    ImageFormat.PNG: b"\x89PNG\r\n\x1a\n",
    ImageFormat.JPEG: b"\xff\xd8\xff",
}

# Length of magic bytes to read for detection
MAGIC_BYTE_LENGTH = 8


class ScreenshotValidator:
    """Validator for screenshot files."""
    
    def __init__(self, config: Optional[IngestConfig] = None):
        """Initialize validator with optional configuration."""
        self.config = config or IngestConfig()
    
    def validate(self, file_path: str | Path) -> ValidationResult:
        """
        Validate a screenshot file.
        
        Performs all validation checks and returns a comprehensive result.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            ValidationResult with validity status, errors, and metadata
        """
        path = Path(file_path)
        errors: list[ValidationError] = []
        warnings: list[str] = []
        
        # Track detected values
        detected_format: Optional[ImageFormat] = None
        dimensions: Optional[tuple[int, int]] = None
        file_size: Optional[int] = None
        
        # Check file exists
        if not path.exists():
            errors.append(ValidationError(
                code=ValidationErrorCode.FILE_NOT_FOUND,
                message=f"File not found: {file_path}",
                detail=str(path.absolute())
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Check file is readable
        if not os.access(path, os.R_OK):
            errors.append(ValidationError(
                code=ValidationErrorCode.PERMISSION_DENIED,
                message=f"Permission denied: cannot read file",
                detail=str(path.absolute())
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Get file size
        file_size = path.stat().st_size
        
        # Check file is not empty
        if file_size == 0:
            errors.append(ValidationError(
                code=ValidationErrorCode.FILE_EMPTY,
                message="File is empty (0 bytes)",
                detail=str(path)
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size
            )
        
        # Check file size limit
        if file_size > self.config.max_file_size_bytes:
            errors.append(ValidationError(
                code=ValidationErrorCode.FILE_TOO_LARGE,
                message=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds limit ({self.config.max_file_size_mb} MB)",
                detail=f"Size: {file_size} bytes, Limit: {self.config.max_file_size_bytes} bytes"
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size
            )
        
        # Check magic bytes and detect format
        detected_format = self._detect_format(path)
        if detected_format is None:
            errors.append(ValidationError(
                code=ValidationErrorCode.INVALID_MAGIC_BYTES,
                message="File does not appear to be a valid PNG or JPEG image",
                detail="Magic bytes do not match PNG or JPEG signatures"
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                file_size=file_size
            )
        
        # Check format is allowed
        if detected_format not in self.config.allowed_formats:
            errors.append(ValidationError(
                code=ValidationErrorCode.UNSUPPORTED_FORMAT,
                message=f"Format '{detected_format.value}' is not allowed",
                detail=f"Allowed formats: {[f.value for f in self.config.allowed_formats]}"
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                format=detected_format,
                file_size=file_size
            )
        
        # Validate image can be opened (corruption check) and get dimensions
        try:
            with Image.open(path) as img:
                img.verify()  # Verify image integrity
        except Exception as e:
            errors.append(ValidationError(
                code=ValidationErrorCode.CORRUPTED_IMAGE,
                message="Image file is corrupted or cannot be read",
                detail=str(e)
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                format=detected_format,
                file_size=file_size
            )
        
        # Re-open to get dimensions (verify() can only be called once)
        try:
            with Image.open(path) as img:
                dimensions = img.size  # (width, height)
        except Exception as e:
            errors.append(ValidationError(
                code=ValidationErrorCode.CORRUPTED_IMAGE,
                message="Failed to read image dimensions",
                detail=str(e)
            ))
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                format=detected_format,
                file_size=file_size
            )
        
        # Check minimum dimensions
        if dimensions[0] < self.config.min_width or dimensions[1] < self.config.min_height:
            errors.append(ValidationError(
                code=ValidationErrorCode.DIMENSIONS_TOO_SMALL,
                message=f"Image dimensions ({dimensions[0]}x{dimensions[1]}) are below minimum ({self.config.min_width}x{self.config.min_height})",
                detail=f"Width: {dimensions[0]}, Height: {dimensions[1]}, Min: {self.config.min_width}x{self.config.min_height}"
            ))
        
        # Check maximum dimensions
        if dimensions[0] > self.config.max_width or dimensions[1] > self.config.max_height:
            errors.append(ValidationError(
                code=ValidationErrorCode.DIMENSIONS_TOO_LARGE,
                message=f"Image dimensions ({dimensions[0]}x{dimensions[1]}) exceed maximum ({self.config.max_width}x{self.config.max_height})",
                detail=f"Width: {dimensions[0]}, Height: {dimensions[1]}, Max: {self.config.max_width}x{self.config.max_height}"
            ))
        
        # Return result
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            format=detected_format,
            dimensions=dimensions,
            file_size=file_size
        )
    
    def _detect_format(self, path: Path) -> Optional[ImageFormat]:
        """
        Detect image format from magic bytes.
        
        Args:
            path: Path to the file
            
        Returns:
            Detected ImageFormat or None if not recognized
        """
        try:
            with open(path, "rb") as f:
                header = f.read(MAGIC_BYTE_LENGTH)
        except (IOError, OSError):
            return None
        
        # Check PNG (8 bytes)
        if header[:8] == MAGIC_BYTES[ImageFormat.PNG]:
            return ImageFormat.PNG
        
        # Check JPEG (3 bytes)
        if header[:3] == MAGIC_BYTES[ImageFormat.JPEG]:
            return ImageFormat.JPEG
        
        return None
    
    def validate_format(self, file_path: str | Path) -> Optional[ImageFormat]:
        """
        Quick format detection without full validation.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected ImageFormat or None
        """
        return self._detect_format(Path(file_path))
    
    def is_valid_screenshot(self, file_path: str | Path) -> bool:
        """
        Quick check if file is a valid screenshot.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid, False otherwise
        """
        result = self.validate(file_path)
        return result.valid


def validate_screenshot(file_path: str | Path, config: Optional[IngestConfig] = None) -> ValidationResult:
    """
    Convenience function to validate a screenshot.
    
    Args:
        file_path: Path to the file to validate
        config: Optional configuration (uses defaults if not provided)
        
    Returns:
        ValidationResult with validity status and any errors
    """
    validator = ScreenshotValidator(config)
    return validator.validate(file_path)
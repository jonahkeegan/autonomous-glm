"""
Unit tests for screenshot ingestion module.

Tests cover models, validators, storage, and integration with database.
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.ingest.models import (
    ImageFormat,
    IngestConfig,
    IngestResult,
    IngestStatus,
    ValidationError,
    ValidationErrorCode,
    ValidationResult,
)
from src.ingest.storage import StorageManager
from src.ingest.validators import ScreenshotValidator, MAGIC_BYTES, validate_screenshot
from src.ingest.screenshot import (
    ingest_screenshot,
    validate_screenshot as validate_screenshot_fn,
    generate_ingest_id,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def fixtures_dir() -> Path:
    """Get the test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sample_png(fixtures_dir: Path) -> Path:
    """Path to sample PNG file."""
    return fixtures_dir / "sample.png"


@pytest.fixture
def sample_jpg(fixtures_dir: Path) -> Path:
    """Path to sample JPEG file."""
    return fixtures_dir / "sample.jpg"


@pytest.fixture
def too_small_png(fixtures_dir: Path) -> Path:
    """Path to image that's too small."""
    return fixtures_dir / "too_small.png"


@pytest.fixture
def min_size_png(fixtures_dir: Path) -> Path:
    """Path to image at minimum size."""
    return fixtures_dir / "min_size.png"


@pytest.fixture
def corrupted_png(fixtures_dir: Path) -> Path:
    """Path to corrupted file."""
    return fixtures_dir / "corrupted.png"


@pytest.fixture
def empty_file(fixtures_dir: Path) -> Path:
    """Path to empty file."""
    return fixtures_dir / "empty.png"


@pytest.fixture
def fake_image(fixtures_dir: Path) -> Path:
    """Path to text file with image extension."""
    return fixtures_dir / "fake_image.png"


@pytest.fixture
def temp_storage_dir(temp_directory: Path) -> Path:
    """Create a temporary storage directory."""
    storage_dir = temp_directory / "screenshots"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def ingest_config(temp_storage_dir: Path) -> IngestConfig:
    """Create a test ingestion config."""
    return IngestConfig(
        max_file_size_mb=50.0,
        min_width=100,
        min_height=100,
        max_width=10000,
        max_height=10000,
        allowed_formats=[ImageFormat.PNG, ImageFormat.JPEG, ImageFormat.JPG],
        screenshots_dir=str(temp_storage_dir),
    )


# =============================================================================
# MODEL TESTS
# =============================================================================

class TestIngestConfig:
    """Tests for IngestConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = IngestConfig()
        
        assert config.max_file_size_mb == 50.0
        assert config.min_width == 100
        assert config.min_height == 100
        assert config.max_width == 10000
        assert config.max_height == 10000
        assert ImageFormat.PNG in config.allowed_formats
    
    def test_max_file_size_bytes(self):
        """Test max_file_size_bytes property."""
        config = IngestConfig(max_file_size_mb=1.0)
        
        assert config.max_file_size_bytes == 1024 * 1024
    
    def test_min_dimensions(self):
        """Test min_dimensions property."""
        config = IngestConfig(min_width=200, min_height=150)
        
        assert config.min_dimensions == (200, 150)
    
    def test_max_dimensions(self):
        """Test max_dimensions property."""
        config = IngestConfig(max_width=5000, max_height=4000)
        
        assert config.max_dimensions == (5000, 4000)
    
    def test_invalid_width_validation(self):
        """Test that max_width must be greater than min_width."""
        with pytest.raises(ValueError, match="max_width must be greater than min_width"):
            IngestConfig(min_width=100, max_width=100)
        
        # This triggers Pydantic's ge=100 constraint first
        with pytest.raises(ValueError):  # Either constraint can fire
            IngestConfig(min_width=100, max_width=50)
    
    def test_invalid_height_validation(self):
        """Test that max_height must be greater than min_height."""
        with pytest.raises(ValueError, match="max_height must be greater than min_height"):
            IngestConfig(min_height=100, max_height=100)


class TestValidationResult:
    """Tests for ValidationResult model."""
    
    def test_valid_result(self):
        """Test a valid validation result."""
        result = ValidationResult(
            valid=True,
            format=ImageFormat.PNG,
            dimensions=(800, 600),
            file_size=1024,
        )
        
        assert result.valid is True
        assert result.has_errors is False
        assert result.format == ImageFormat.PNG
    
    def test_invalid_result(self):
        """Test an invalid validation result."""
        result = ValidationResult(
            valid=False,
            errors=[
                ValidationError(
                    code=ValidationErrorCode.FILE_NOT_FOUND,
                    message="File not found",
                )
            ],
        )
        
        assert result.valid is False
        assert result.has_errors is True
        assert len(result.errors) == 1
    
    def test_has_warnings(self):
        """Test has_warnings property."""
        result = ValidationResult(valid=True, warnings=["Test warning"])
        
        assert result.has_warnings is True


class TestIngestResult:
    """Tests for IngestResult model."""
    
    def test_success_result(self):
        """Test a successful ingest result."""
        result = IngestResult(
            success=True,
            status=IngestStatus.SUCCESS,
            ingest_id="test-uuid",
            screen_id="screen-uuid",
            storage_path="/path/to/file.png",
        )
        
        assert result.success is True
        assert result.status == IngestStatus.SUCCESS
        assert result.is_duplicate is False
        assert result.has_errors is False
    
    def test_failure_result(self):
        """Test a failed ingest result."""
        result = IngestResult(
            success=False,
            status=IngestStatus.FAILURE,
            errors=[
                ValidationError(
                    code=ValidationErrorCode.FILE_TOO_LARGE,
                    message="File too large",
                )
            ],
        )
        
        assert result.success is False
        assert result.has_errors is True
    
    def test_duplicate_result(self):
        """Test a duplicate ingest result."""
        result = IngestResult(
            success=True,
            status=IngestStatus.DUPLICATE,
            is_duplicate=True,
        )
        
        assert result.is_duplicate is True


# =============================================================================
# VALIDATOR TESTS
# =============================================================================

class TestScreenshotValidator:
    """Tests for ScreenshotValidator class."""
    
    def test_validate_valid_png(self, sample_png: Path, ingest_config: IngestConfig):
        """Test validation of a valid PNG file."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate(sample_png)
        
        assert result.valid is True
        assert result.format == ImageFormat.PNG
        assert result.dimensions == (800, 600)
        assert result.file_size > 0
        assert len(result.errors) == 0
    
    def test_validate_valid_jpeg(self, sample_jpg: Path, ingest_config: IngestConfig):
        """Test validation of a valid JPEG file."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate(sample_jpg)
        
        assert result.valid is True
        assert result.format == ImageFormat.JPEG
        assert result.dimensions == (800, 600)
        assert result.file_size > 0
    
    def test_validate_file_not_found(self, ingest_config: IngestConfig):
        """Test validation of non-existent file."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate("/nonexistent/path/file.png")
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == ValidationErrorCode.FILE_NOT_FOUND
    
    def test_validate_empty_file(self, empty_file: Path, ingest_config: IngestConfig):
        """Test validation of empty file."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate(empty_file)
        
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == ValidationErrorCode.FILE_EMPTY
    
    def test_validate_invalid_magic_bytes(self, fake_image: Path, ingest_config: IngestConfig):
        """Test validation of file with wrong magic bytes."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate(fake_image)
        
        assert result.valid is False
        assert any(e.code == ValidationErrorCode.INVALID_MAGIC_BYTES for e in result.errors)
    
    def test_validate_corrupted_image(self, corrupted_png: Path, ingest_config: IngestConfig):
        """Test validation of corrupted image file."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate(corrupted_png)
        
        assert result.valid is False
        # Corrupted file triggers either CORRUPTED_IMAGE or INVALID_MAGIC_BYTES
        assert result.has_errors is True
    
    def test_validate_too_small_dimensions(self, too_small_png: Path, ingest_config: IngestConfig):
        """Test validation of image below minimum dimensions."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate(too_small_png)
        
        assert result.valid is False
        assert any(e.code == ValidationErrorCode.DIMENSIONS_TOO_SMALL for e in result.errors)
    
    def test_validate_min_size_image(self, min_size_png: Path, ingest_config: IngestConfig):
        """Test validation of image at exact minimum dimensions."""
        validator = ScreenshotValidator(ingest_config)
        result = validator.validate(min_size_png)
        
        assert result.valid is True
        assert result.dimensions == (100, 100)
    
    def test_validate_format_method(self, sample_png: Path, ingest_config: IngestConfig):
        """Test the validate_format method."""
        validator = ScreenshotValidator(ingest_config)
        format = validator.validate_format(sample_png)
        
        assert format == ImageFormat.PNG
    
    def test_is_valid_screenshot(self, sample_png: Path, ingest_config: IngestConfig):
        """Test the is_valid_screenshot method."""
        validator = ScreenshotValidator(ingest_config)
        
        assert validator.is_valid_screenshot(sample_png) is True
        assert validator.is_valid_screenshot("/nonexistent.png") is False
    
    def test_convenience_function(self, sample_png: Path, ingest_config: IngestConfig):
        """Test the validate_screenshot convenience function."""
        result = validate_screenshot(sample_png, ingest_config)
        
        assert result.valid is True


class TestMagicBytes:
    """Tests for magic byte detection."""
    
    def test_png_magic_bytes(self):
        """Test PNG magic bytes are correct."""
        assert MAGIC_BYTES[ImageFormat.PNG] == b"\x89PNG\r\n\x1a\n"
    
    def test_jpeg_magic_bytes(self):
        """Test JPEG magic bytes are correct."""
        assert MAGIC_BYTES[ImageFormat.JPEG] == b"\xff\xd8\xff"


# =============================================================================
# STORAGE MANAGER TESTS
# =============================================================================

class TestStorageManager:
    """Tests for StorageManager class."""
    
    def test_base_dir_creation(self, temp_storage_dir: Path):
        """Test that base directory is created."""
        config = IngestConfig(screenshots_dir=str(temp_storage_dir / "new_dir"))
        storage = StorageManager(config)
        
        # Directory should be created on access
        assert storage.base_dir.exists()
    
    def test_calculate_hash(self, sample_png: Path, ingest_config: IngestConfig):
        """Test content hash calculation."""
        storage = StorageManager(ingest_config)
        hash1 = storage.calculate_hash(sample_png)
        hash2 = storage.calculate_hash(sample_png)
        
        # Same file should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
    
    def test_generate_ingest_id(self, sample_png: Path, ingest_config: IngestConfig):
        """Test ingest ID generation."""
        storage = StorageManager(ingest_config)
        id1 = storage.generate_ingest_id(sample_png)
        id2 = storage.generate_ingest_id(sample_png)
        
        # Same file should produce same ID
        assert id1 == id2
        
        # Should be valid UUID
        uuid.UUID(id1)  # Will raise if invalid
    
    def test_generate_ingest_id_deterministic(self, sample_png: Path, sample_jpg: Path, ingest_config: IngestConfig):
        """Test that different files produce different IDs."""
        storage = StorageManager(ingest_config)
        id_png = storage.generate_ingest_id(sample_png)
        id_jpg = storage.generate_ingest_id(sample_jpg)
        
        assert id_png != id_jpg
    
    def test_get_storage_path(self, ingest_config: IngestConfig):
        """Test storage path generation."""
        storage = StorageManager(ingest_config)
        ingest_id = "test-id-123"
        test_date = datetime(2026, 3, 1)
        
        path = storage.get_storage_path(ingest_id, ImageFormat.PNG, test_date)
        
        assert "2026" in str(path)
        assert "03" in str(path)
        assert path.name == "test-id-123.png"
    
    def test_get_storage_path_jpeg_extension(self, ingest_config: IngestConfig):
        """Test that JPEG format gets .jpg extension."""
        storage = StorageManager(ingest_config)
        path = storage.get_storage_path("test-id", ImageFormat.JPEG)
        
        assert path.suffix == ".jpg"
    
    def test_store_file(self, sample_png: Path, ingest_config: IngestConfig):
        """Test file storage with atomic write."""
        storage = StorageManager(ingest_config)
        dest_path = storage.base_dir / "2026" / "03" / "test-store.png"
        
        result_path = storage.store_file(sample_png, dest_path)
        
        assert result_path.exists()
        assert result_path == dest_path
        
        # Content should match
        original_hash = storage.calculate_hash(sample_png)
        stored_hash = storage.calculate_hash(dest_path)
        assert original_hash == stored_hash
    
    def test_file_exists(self, sample_png: Path, ingest_config: IngestConfig):
        """Test file existence check."""
        storage = StorageManager(ingest_config)
        dest_path = storage.base_dir / "test.png"
        
        assert storage.file_exists(dest_path) is False
        
        storage.store_file(sample_png, dest_path)
        
        assert storage.file_exists(dest_path) is True
    
    def test_get_relative_path(self, ingest_config: IngestConfig):
        """Test relative path generation."""
        storage = StorageManager(ingest_config)
        full_path = storage.base_dir / "2026" / "03" / "test.png"
        
        relative = storage.get_relative_path(full_path)
        
        assert relative == "2026/03/test.png"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIngestScreenshot:
    """Integration tests for ingest_screenshot function."""
    
    def test_ingest_valid_png(
        self,
        sample_png: Path,
        ingest_config: IngestConfig,
        temp_db: Path,
    ):
        """Test ingesting a valid PNG file."""
        result = ingest_screenshot(sample_png, ingest_config, temp_db)
        
        assert result.success is True
        assert result.status == IngestStatus.SUCCESS
        assert result.ingest_id is not None
        assert result.screen_id is not None
        assert result.storage_path is not None
        assert result.is_duplicate is False
        
        # Verify file was stored
        assert Path(result.storage_path).exists()
    
    def test_ingest_valid_jpeg(
        self,
        sample_jpg: Path,
        ingest_config: IngestConfig,
        temp_db: Path,
    ):
        """Test ingesting a valid JPEG file."""
        result = ingest_screenshot(sample_jpg, ingest_config, temp_db)
        
        assert result.success is True
        assert result.status == IngestStatus.SUCCESS
        assert result.storage_path.endswith(".jpg")
    
    def test_ingest_duplicate_file(
        self,
        sample_png: Path,
        ingest_config: IngestConfig,
        temp_db: Path,
    ):
        """Test that duplicate files are detected."""
        # First ingest
        result1 = ingest_screenshot(sample_png, ingest_config, temp_db)
        assert result1.success is True
        assert result1.is_duplicate is False
        
        # Second ingest of same file
        result2 = ingest_screenshot(sample_png, ingest_config, temp_db)
        assert result2.success is True
        assert result2.is_duplicate is True
        assert result2.status == IngestStatus.DUPLICATE
        assert result2.ingest_id == result1.ingest_id
    
    def test_ingest_invalid_file(
        self,
        too_small_png: Path,
        ingest_config: IngestConfig,
        temp_db: Path,
    ):
        """Test ingesting an invalid file."""
        result = ingest_screenshot(too_small_png, ingest_config, temp_db)
        
        assert result.success is False
        assert result.status == IngestStatus.FAILURE
        assert result.has_errors is True
        assert any(e.code == ValidationErrorCode.DIMENSIONS_TOO_SMALL for e in result.errors)
    
    def test_ingest_nonexistent_file(
        self,
        ingest_config: IngestConfig,
        temp_db: Path,
    ):
        """Test ingesting a non-existent file."""
        result = ingest_screenshot("/nonexistent/file.png", ingest_config, temp_db)
        
        assert result.success is False
        assert any(e.code == ValidationErrorCode.FILE_NOT_FOUND for e in result.errors)
    
    def test_generate_ingest_id_function(self, sample_png: Path, ingest_config: IngestConfig):
        """Test the generate_ingest_id convenience function."""
        id1 = generate_ingest_id(sample_png, ingest_config)
        id2 = generate_ingest_id(sample_png, ingest_config)
        
        assert id1 == id2
        uuid.UUID(id1)  # Validate UUID format
    
    def test_validate_screenshot_function(self, sample_png: Path, ingest_config: IngestConfig):
        """Test the validate_screenshot convenience function."""
        result = validate_screenshot_fn(sample_png, ingest_config)
        
        assert result.valid is True
        assert result.format == ImageFormat.PNG


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_config_with_zero_size(self):
        """Test that zero file size is rejected."""
        with pytest.raises(ValueError):
            IngestConfig(max_file_size_mb=0)
    
    def test_config_with_negative_dimensions(self):
        """Test that negative dimensions are rejected."""
        with pytest.raises(ValueError):
            IngestConfig(min_width=-1)
    
    def test_dimensions_at_boundary(self, temp_directory: Path):
        """Test images at exact dimension boundaries."""
        from PIL import Image
        
        config = IngestConfig(
            min_width=100,
            min_height=100,
            max_width=1000,
            max_height=1000,
        )
        
        # Create image at max dimensions
        max_img_path = temp_directory / "max_size.png"
        img = Image.new("RGB", (1000, 1000), color="blue")
        img.save(max_img_path)
        
        validator = ScreenshotValidator(config)
        result = validator.validate(max_img_path)
        
        assert result.valid is True
    
    def test_dimensions_exceed_max(self, temp_directory: Path):
        """Test image exceeding max dimensions."""
        from PIL import Image
        
        # Set min low enough that max can be valid
        config = IngestConfig(
            min_width=10,
            min_height=10,
            max_width=100,
            max_height=100,
        )
        
        # Create oversized image
        large_img_path = temp_directory / "large.png"
        img = Image.new("RGB", (200, 200), color="red")
        img.save(large_img_path)
        
        validator = ScreenshotValidator(config)
        result = validator.validate(large_img_path)
        
        assert result.valid is False
        assert any(e.code == ValidationErrorCode.DIMENSIONS_TOO_LARGE for e in result.errors)

"""E2E tests for edge cases and boundary conditions.

Tests handling of:
- Corrupted or malformed images
- Unusual aspect ratios
- Empty/minimal screens
- Very large or dense images
- Special characters in metadata
"""
from pathlib import Path

import pytest
from PIL import Image


@pytest.mark.e2e
class TestCorruptedImagesE2E:
    """E2E tests for corrupted or malformed images."""

    def test_corrupted_png_file(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of corrupted PNG file."""
        from src.ingest.validators import validate_screenshot
        
        # Create a file with PNG magic bytes but corrupted content
        corrupted_path = e2e_temp_dir / "corrupted.png"
        with open(corrupted_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")  # PNG header
            f.write(b"GARBAGE_DATA_NOT_VALID_PNG")

        # Should fail validation
        result = validate_screenshot(str(corrupted_path))
        assert result.valid is False

    def test_wrong_extension_png(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test file with .png extension but JPEG content."""
        from src.ingest.validators import validate_screenshot
        
        # Create JPEG file with .png extension
        jpeg_path = e2e_temp_dir / "fake.png"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(jpeg_path, "JPEG")  # Save as JPEG

        # Should fail magic byte validation
        result = validate_screenshot(str(jpeg_path))
        assert result.valid is False

    def test_truncated_image(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of truncated image file."""
        from src.ingest.validators import validate_screenshot
        
        # Create valid PNG then truncate it
        valid_path = e2e_temp_dir / "valid.png"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(valid_path, "PNG")

        # Read and truncate
        with open(valid_path, "rb") as f:
            data = f.read()

        truncated_path = e2e_temp_dir / "truncated.png"
        with open(truncated_path, "wb") as f:
            f.write(data[: len(data) // 2])  # Half the file

        # Should fail validation
        result = validate_screenshot(str(truncated_path))
        assert result.valid is False


@pytest.mark.e2e
class TestUnusualAspectRatiosE2E:
    """E2E tests for unusual aspect ratios."""

    def test_very_wide_image(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of very wide image (panorama)."""
        from src.ingest.validators import validate_screenshot
        
        wide_path = e2e_temp_dir / "wide.png"
        img = Image.new("RGB", (2000, 100), color="green")
        img.save(wide_path, "PNG")

        # Should validate successfully
        result = validate_screenshot(str(wide_path))
        assert result.valid is True

    def test_very_tall_image(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of very tall image (scroll capture)."""
        from src.ingest.validators import validate_screenshot
        
        tall_path = e2e_temp_dir / "tall.png"
        img = Image.new("RGB", (100, 5000), color="yellow")
        img.save(tall_path, "PNG")

        # Should validate successfully
        result = validate_screenshot(str(tall_path))
        assert result.valid is True

    def test_square_image(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of square image."""
        from src.ingest.validators import validate_screenshot
        
        square_path = e2e_temp_dir / "square.png"
        img = Image.new("RGB", (500, 500), color="purple")
        img.save(square_path, "PNG")

        # Should validate successfully
        result = validate_screenshot(str(square_path))
        assert result.valid is True


@pytest.mark.e2e
class TestEmptyScreensE2E:
    """E2E tests for empty or minimal screens."""

    def test_blank_white_screen(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of blank white screen."""
        from src.ingest.screenshot import ingest_screenshot
        
        blank_path = e2e_temp_dir / "blank_white.png"
        img = Image.new("RGB", (390, 844), color="white")
        img.save(blank_path, "PNG")

        # Should ingest successfully
        result = ingest_screenshot(
            str(blank_path),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )
        assert result is not None

    def test_blank_black_screen(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of blank black screen."""
        from src.ingest.screenshot import ingest_screenshot
        
        blank_path = e2e_temp_dir / "blank_black.png"
        img = Image.new("RGB", (390, 844), color="black")
        img.save(blank_path, "PNG")

        # Should ingest successfully
        result = ingest_screenshot(
            str(blank_path),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )
        assert result is not None

    def test_single_pixel_image(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of single pixel image."""
        from src.ingest.validators import validate_screenshot
        
        pixel_path = e2e_temp_dir / "pixel.png"
        img = Image.new("RGB", (1, 1), color="red")
        img.save(pixel_path, "PNG")

        # Should fail validation (too small)
        result = validate_screenshot(str(pixel_path))
        assert result.valid is False


@pytest.mark.e2e
class TestSpecialCharactersE2E:
    """E2E tests for special characters in metadata."""

    def test_unicode_in_metadata(
        self, e2e_temp_dir: Path, e2e_db_path: Path, e2e_screenshot: Path
    ) -> None:
        """Test handling of Unicode characters in metadata."""
        from src.ingest.screenshot import ingest_screenshot
        
        metadata = {
            "app_name": "测试应用",  # Chinese
            "screen_name": "Écran Principal",  # French with accents
            "description": "日本語テスト",  # Japanese
        }

        result = ingest_screenshot(
            str(e2e_screenshot),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
            metadata=metadata,
        )

        assert result is not None

    def test_special_chars_in_path(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of special characters in file path."""
        from src.ingest.screenshot import ingest_screenshot
        
        # Create directory with spaces
        special_dir = e2e_temp_dir / "my screenshots" / "2024"
        special_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = special_dir / "test screenshot.png"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(screenshot_path, "PNG")

        result = ingest_screenshot(
            str(screenshot_path),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )

        assert result is not None


@pytest.mark.e2e
class TestColorVariationsE2E:
    """E2E tests for various color formats."""

    def test_grayscale_image(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of grayscale image."""
        from src.ingest.screenshot import ingest_screenshot
        
        gray_path = e2e_temp_dir / "grayscale.png"
        img = Image.new("L", (390, 844), color=128)  # L mode = grayscale
        img.save(gray_path, "PNG")

        # Should ingest successfully
        result = ingest_screenshot(
            str(gray_path),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )
        assert result is not None

    def test_rgba_image_with_transparency(
        self, e2e_temp_dir: Path, e2e_db_path: Path
    ) -> None:
        """Test handling of RGBA image with transparency."""
        from src.ingest.screenshot import ingest_screenshot
        
        rgba_path = e2e_temp_dir / "rgba.png"
        img = Image.new("RGBA", (390, 844), color=(255, 0, 0, 128))  # Semi-transparent red
        img.save(rgba_path, "PNG")

        # Should ingest successfully
        result = ingest_screenshot(
            str(rgba_path),
            db_path=e2e_db_path,
            storage_dir=str(e2e_temp_dir / "storage"),
        )
        assert result is not None
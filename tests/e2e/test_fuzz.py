"""Fuzz tests for robustness validation.

Uses hypothesis for property-based testing to ensure the system
handles random/malformed inputs gracefully without crashing.

Key property: "No crash, clear error message"
"""
import json
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, settings, assume
from PIL import Image


@pytest.mark.e2e
class TestFuzzScreenshotValidation:
    """Fuzz tests for screenshot validation."""

    @given(st.binary(min_size=100, max_size=10000))
    @settings(max_examples=20, deadline=None)
    def test_random_bytes_as_screenshot(
        self, e2e_temp_dir: Path, random_bytes: bytes
    ) -> None:
        """Property: Random bytes should not crash screenshot validation."""
        from src.ingest.validators import validate_screenshot
        
        # Create file with random bytes
        random_path = e2e_temp_dir / "random.png"
        with open(random_path, "wb") as f:
            f.write(random_bytes)

        # Should not raise exception
        try:
            result = validate_screenshot(str(random_path))
            # Result should be valid or have clear error
            assert isinstance(result.valid, bool)
        except Exception as e:
            # Should not crash with unhandled exception
            pytest.fail(f"Unhandled exception: {e}")


@pytest.mark.e2e
class TestFuzzConfigValues:
    """Fuzz tests for configuration handling."""

    @given(st.integers(min_value=1, max_value=10000))
    @settings(max_examples=10, deadline=None)
    def test_random_dimension_config(
        self, dimension: int
    ) -> None:
        """Property: Random dimension values should not crash config."""
        try:
            from src.ingest.models import IngestConfig
            
            config = IngestConfig(
                min_width=dimension,
                min_height=dimension,
                max_width=dimension * 10,
                max_height=dimension * 10,
            )
            # Config should be created or raise validation error
            assert config.min_width >= 1
        except Exception as e:
            # Should be a validation error, not a crash
            assert "validation" in str(e).lower() or "invalid" in str(e).lower() or "value" in str(e).lower()


@pytest.mark.e2e
class TestFuzzEdgeCases:
    """Fuzz tests for specific edge cases."""

    @given(st.lists(st.integers(min_value=0, max_value=255), min_size=3, max_size=4))
    @settings(max_examples=10, deadline=None)
    def test_random_color_values(
        self, e2e_temp_dir: Path, e2e_db_path: Path, color_values: list
    ) -> None:
        """Property: Random color values should create valid images."""
        from src.ingest.validators import validate_screenshot
        
        try:
            # Create image with random color
            color = tuple(color_values[:3])  # RGB
            img = Image.new("RGB", (100, 100), color=color)

            color_path = e2e_temp_dir / "color_test.png"
            img.save(color_path, "PNG")

            # Should validate successfully
            result = validate_screenshot(str(color_path))
            assert result.valid is True
        except Exception as e:
            pytest.fail(f"Failed with color {color_values}: {e}")

    @given(
        st.integers(min_value=100, max_value=500),
        st.integers(min_value=100, max_value=500),
    )
    @settings(max_examples=10, deadline=None)
    def test_random_image_sizes(
        self, e2e_temp_dir: Path, e2e_db_path: Path, width: int, height: int
    ) -> None:
        """Property: Random image sizes should handle gracefully."""
        from src.ingest.validators import validate_screenshot
        
        try:
            img = Image.new("RGB", (width, height), color="white")

            size_path = e2e_temp_dir / f"size_{width}x{height}.png"
            img.save(size_path, "PNG")

            result = validate_screenshot(str(size_path))
            assert result.valid is True
        except Exception as e:
            pytest.fail(f"Failed with size {width}x{height}: {e}")


@pytest.mark.e2e
class TestFuzzNegativeCases:
    """Fuzz tests for negative/error cases."""

    @given(st.one_of(
        st.none(),
        st.just(""),
        st.just("   "),
        st.just("nonexistent.png"),
        st.just("/invalid/path/to/file.png"),
    ))
    @settings(max_examples=10, deadline=None)
    def test_invalid_file_paths(
        self, invalid_path
    ) -> None:
        """Property: Invalid paths should return clear errors."""
        from src.ingest.validators import validate_screenshot
        
        try:
            result = validate_screenshot(invalid_path)
            assert result.valid is False
            assert result.error is not None
        except (FileNotFoundError, TypeError, ValueError, AttributeError):
            # Expected errors
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")
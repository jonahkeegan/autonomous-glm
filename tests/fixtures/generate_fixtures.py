#!/usr/bin/env python3
"""
Generate test fixtures for screenshot ingestion tests.

Creates sample PNG and JPEG images with known properties for testing.
"""

from PIL import Image
from pathlib import Path


def create_sample_png(output_path: Path, width: int = 800, height: int = 600) -> None:
    """Create a sample PNG image."""
    img = Image.new("RGB", (width, height), color=(73, 109, 137))
    
    # Add some visual variation
    for x in range(0, width, 50):
        for y in range(0, height, 50):
            color = ((x + y) % 256, (x * 2) % 256, (y * 2) % 256)
            img.putpixel((x, y), color)
    
    img.save(output_path, "PNG")


def create_sample_jpeg(output_path: Path, width: int = 800, height: int = 600) -> None:
    """Create a sample JPEG image."""
    img = Image.new("RGB", (width, height), color=(137, 109, 73))
    
    # Add some visual variation
    for x in range(0, width, 50):
        for y in range(0, height, 50):
            color = ((y * 2) % 256, (x * 2) % 256, (x + y) % 256)
            img.putpixel((x, y), color)
    
    img.save(output_path, "JPEG", quality=85)


def create_small_image(output_path: Path, width: int = 50, height: int = 50) -> None:
    """Create a small image (below min dimensions)."""
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    img.save(output_path, "PNG")


def create_corrupted_file(output_path: Path) -> None:
    """Create a file with PNG extension but invalid content."""
    output_path.write_bytes(b"Not a real image file, just some random data")


def create_empty_file(output_path: Path) -> None:
    """Create an empty file."""
    output_path.write_bytes(b"")


def main():
    """Generate all test fixtures."""
    fixtures_dir = Path(__file__).parent
    
    # Create sample valid images
    create_sample_png(fixtures_dir / "sample.png")
    create_sample_jpeg(fixtures_dir / "sample.jpg")
    create_sample_png(fixtures_dir / "sample_large.png", width=2000, height=1500)
    
    # Create edge case images
    create_small_image(fixtures_dir / "too_small.png", width=50, height=50)
    create_small_image(fixtures_dir / "min_size.png", width=100, height=100)
    
    # Create invalid files
    create_corrupted_file(fixtures_dir / "corrupted.png")
    create_empty_file(fixtures_dir / "empty.png")
    
    # Create a text file with image extension
    (fixtures_dir / "fake_image.png").write_text("This is not an image")
    
    print(f"Generated test fixtures in {fixtures_dir}")


if __name__ == "__main__":
    main()
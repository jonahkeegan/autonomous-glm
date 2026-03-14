"""E2E test fixtures and configuration.

Provides fixtures for:
- Temporary directories for artifact storage
- Test database setup
- Sample screenshots and videos
- CLI runner for command testing
"""
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from src.db.database import init_database, get_connection


@pytest.fixture
def e2e_temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for E2E tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="glm_e2e_"))
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def e2e_db_path(e2e_temp_dir: Path) -> Generator[Path, None, None]:
    """Create a test database in temporary directory."""
    db_path = e2e_temp_dir / "test.db"
    init_database(db_path)
    yield db_path
    # Cleanup handled by e2e_temp_dir


@pytest.fixture
def e2e_db_connection(e2e_db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Create a test database connection."""
    conn = get_connection(e2e_db_path)
    yield conn
    conn.close()


@pytest.fixture
def e2e_paths(e2e_temp_dir: Path) -> dict:
    """Create path configuration pointing to temp directories."""
    return {
        "data_dir": e2e_temp_dir / "data",
        "artifacts_dir": e2e_temp_dir / "data" / "artifacts",
        "screenshots_dir": e2e_temp_dir / "data" / "artifacts" / "screenshots",
        "videos_dir": e2e_temp_dir / "data" / "artifacts" / "videos",
        "output_dir": e2e_temp_dir / "output",
        "reports_dir": e2e_temp_dir / "output" / "reports",
        "logs_dir": e2e_temp_dir / "logs",
    }


@pytest.fixture
def e2e_screenshot(e2e_temp_dir: Path) -> Path:
    """Create a simple test screenshot (valid PNG)."""
    from PIL import Image
    
    screenshots_dir = e2e_temp_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple 100x100 white image
    img = Image.new("RGB", (100, 100), color="white")
    screenshot_path = screenshots_dir / "test_screenshot.png"
    img.save(screenshot_path, "PNG")
    
    return screenshot_path


@pytest.fixture
def e2e_screenshot_with_ui(e2e_temp_dir: Path) -> Path:
    """Create a test screenshot with UI elements (button-like shape)."""
    from PIL import Image, ImageDraw
    
    screenshots_dir = e2e_temp_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a 390x844 mobile viewport with a button
    img = Image.new("RGB", (390, 844), color="white")
    draw = ImageDraw.Draw(img)
    
    # Draw a button-like rectangle
    draw.rectangle([50, 200, 340, 260], fill="#007AFF", outline="#0056CC", width=2)
    
    # Draw some text area
    draw.rectangle([50, 100, 340, 180], fill="#F5F5F5", outline="#E0E0E0", width=1)
    
    screenshot_path = screenshots_dir / "test_ui_screenshot.png"
    img.save(screenshot_path, "PNG")
    
    return screenshot_path


@pytest.fixture
def e2e_cli_runner() -> CliRunner:
    """Create a Click CLI runner for testing."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def e2e_watch_dir(e2e_temp_dir: Path) -> Path:
    """Create a directory for watch mode testing."""
    watch_dir = e2e_temp_dir / "watch"
    watch_dir.mkdir(parents=True, exist_ok=True)
    return watch_dir


@pytest.fixture
def e2e_output_dir(e2e_temp_dir: Path) -> Path:
    """Create an output directory for reports."""
    output_dir = e2e_temp_dir / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture(autouse=True)
def e2e_env_setup(e2e_temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up environment variables for E2E tests."""
    monkeypatch.setenv("AUTONOMOUS_GLM_DATA_DIR", str(e2e_temp_dir / "data"))
    monkeypatch.setenv("AUTONOMOUS_GLM_OUTPUT_DIR", str(e2e_temp_dir / "output"))
    monkeypatch.setenv("AUTONOMOUS_GLM_LOGS_DIR", str(e2e_temp_dir / "logs"))
    monkeypatch.setenv("AUTONOMOUS_GLM_ENV", "test")
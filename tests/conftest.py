"""
Shared pytest fixtures for Autonomous-GLM tests.

Provides common fixtures for temporary directories, test databases,
and configuration overrides.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import clear_config


# =============================================================================
# AUTO-USE FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def reset_config_cache():
    """Clear config cache before and after each test."""
    clear_config()
    yield
    clear_config()


# =============================================================================
# DIRECTORY FIXTURES
# =============================================================================

@pytest.fixture
def temp_directory():
    """Create a temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config_dir(temp_directory):
    """Create a temporary config directory with test files."""
    config_dir = temp_directory / "config"
    config_dir.mkdir()
    
    # Create default.yaml with minimal valid config
    default_yaml = config_dir / "default.yaml"
    default_yaml.write_text("""
app:
  name: test-app
  version: "1.0.0"
  environment: development
  debug: false

paths:
  data_dir: "./data"
  database_path: "./data/test.db"

database:
  pool_size: 5
  timeout: 30

agent_protocol:
  message_timeout: 5000
  retry_attempts: 3
  retry_base_delay: 1000
  retry_max_delay: 1800000

logging:
  level: INFO
  format: "%(message)s"
  file_rotation: "10 MB"
  file_count: 5
""")
    
    # Create development.yaml
    dev_yaml = config_dir / "development.yaml"
    dev_yaml.write_text("""
app:
  debug: true

logging:
  level: DEBUG
""")
    
    # Create production.yaml
    prod_yaml = config_dir / "production.yaml"
    prod_yaml.write_text("""
app:
  environment: production
  debug: false

logging:
  level: WARNING
""")
    
    # Create staging.yaml
    staging_yaml = config_dir / "staging.yaml"
    staging_yaml.write_text("""
app:
  environment: staging
  debug: false
""")
    
    return config_dir


@pytest.fixture
def temp_data_dir(temp_directory):
    """Create a temporary data directory structure."""
    data_dir = temp_directory / "data"
    data_dir.mkdir()
    
    # Create subdirectories
    (data_dir / "artifacts" / "screenshots").mkdir(parents=True)
    (data_dir / "artifacts" / "videos").mkdir(parents=True)
    (data_dir / "artifacts" / "context").mkdir(parents=True)
    
    return data_dir


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture
def temp_db(temp_directory):
    """Create a temporary database for testing."""
    from src.db import init_database
    
    db_path = temp_directory / "test.db"
    init_database(db_path)
    yield db_path


# =============================================================================
# PROJECT ROOT FIXTURE
# =============================================================================

@pytest.fixture
def project_root():
    """Get the project root directory."""
    from src.config.paths import get_project_root
    return get_project_root()


# =============================================================================
# SCHEMA FIXTURES
# =============================================================================

@pytest.fixture
def interfaces_dir(project_root):
    """Get the interfaces directory."""
    return project_root / "interfaces"


@pytest.fixture
def design_system_dir(project_root):
    """Get the design system directory."""
    return project_root / "design_system"


@pytest.fixture
def memory_bank_dir(project_root):
    """Get the memory bank directory."""
    return project_root / "memory-bank"


# =============================================================================
# MARKERS
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, external deps)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (skip in quick runs)"
    )
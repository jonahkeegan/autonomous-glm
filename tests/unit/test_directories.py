"""
Unit tests for Autonomous-GLM directory structure validation.

Tests verify that all required directories exist and are properly configured.
"""

from pathlib import Path

import pytest


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def project_root():
    """Get the project root directory."""
    from src.config.paths import get_project_root
    return get_project_root()


# =============================================================================
# ROOT DIRECTORY TESTS
# =============================================================================

class TestRootDirectory:
    """Tests for root directory structure."""
    
    def test_project_root_exists(self, project_root):
        """Project root directory exists."""
        assert project_root.exists()
        assert project_root.is_dir()
    
    def test_config_directory_exists(self, project_root):
        """Config directory exists."""
        config_dir = project_root / "config"
        assert config_dir.exists()
        assert config_dir.is_dir()
    
    def test_data_directory_exists(self, project_root):
        """Data directory exists."""
        data_dir = project_root / "data"
        assert data_dir.exists()
        assert data_dir.is_dir()
    
    def test_src_directory_exists(self, project_root):
        """Source directory exists."""
        src_dir = project_root / "src"
        assert src_dir.exists()
        assert src_dir.is_dir()
    
    def test_tests_directory_exists(self, project_root):
        """Tests directory exists."""
        tests_dir = project_root / "tests"
        assert tests_dir.exists()
        assert tests_dir.is_dir()
    
    def test_design_system_directory_exists(self, project_root):
        """Design system directory exists."""
        ds_dir = project_root / "design_system"
        assert ds_dir.exists()
        assert ds_dir.is_dir()
    
    def test_memory_bank_directory_exists(self, project_root):
        """Memory bank directory exists."""
        mb_dir = project_root / "memory-bank"
        assert mb_dir.exists()
        assert mb_dir.is_dir()
    
    def test_interfaces_directory_exists(self, project_root):
        """Interfaces directory exists."""
        interfaces_dir = project_root / "interfaces"
        assert interfaces_dir.exists()
        assert interfaces_dir.is_dir()
    
    def test_output_directory_exists(self, project_root):
        """Output directory exists."""
        output_dir = project_root / "output"
        assert output_dir.exists()
        assert output_dir.is_dir()
    
    def test_logs_directory_exists(self, project_root):
        """Logs directory exists."""
        logs_dir = project_root / "logs"
        assert logs_dir.exists()
        assert logs_dir.is_dir()


# =============================================================================
# DATA SUBDIRECTORY TESTS
# =============================================================================

class TestDataSubdirectories:
    """Tests for data subdirectory structure."""
    
    def test_artifacts_directory_exists(self, project_root):
        """Artifacts directory exists."""
        artifacts_dir = project_root / "data" / "artifacts"
        assert artifacts_dir.exists()
        assert artifacts_dir.is_dir()
    
    def test_screenshots_directory_exists(self, project_root):
        """Screenshots directory exists."""
        screenshots_dir = project_root / "data" / "artifacts" / "screenshots"
        assert screenshots_dir.exists()
        assert screenshots_dir.is_dir()
    
    def test_videos_directory_exists(self, project_root):
        """Videos directory exists."""
        videos_dir = project_root / "data" / "artifacts" / "videos"
        assert videos_dir.exists()
        assert videos_dir.is_dir()
    
    def test_context_directory_exists(self, project_root):
        """Context directory exists."""
        context_dir = project_root / "data" / "artifacts" / "context"
        assert context_dir.exists()
        assert context_dir.is_dir()


# =============================================================================
# OUTPUT SUBDIRECTORY TESTS
# =============================================================================

class TestOutputSubdirectories:
    """Tests for output subdirectory structure."""
    
    def test_reports_directory_exists(self, project_root):
        """Reports directory exists."""
        reports_dir = project_root / "output" / "reports"
        assert reports_dir.exists()
        assert reports_dir.is_dir()


# =============================================================================
# TESTS SUBDIRECTORY TESTS
# =============================================================================

class TestTestsSubdirectories:
    """Tests for tests subdirectory structure."""
    
    def test_unit_directory_exists(self, project_root):
        """Unit tests directory exists."""
        unit_dir = project_root / "tests" / "unit"
        assert unit_dir.exists()
        assert unit_dir.is_dir()
    
    def test_integration_directory_exists(self, project_root):
        """Integration tests directory exists."""
        integration_dir = project_root / "tests" / "integration"
        assert integration_dir.exists()
        assert integration_dir.is_dir()
    
    def test_e2e_directory_exists(self, project_root):
        """E2E tests directory exists."""
        e2e_dir = project_root / "tests" / "e2e"
        assert e2e_dir.exists()
        assert e2e_dir.is_dir()
    
    def test_golden_dataset_directory_exists(self, project_root):
        """Golden dataset directory exists."""
        golden_dir = project_root / "tests" / "golden-dataset"
        assert golden_dir.exists()
        assert golden_dir.is_dir()


# =============================================================================
# SRC SUBDIRECTORY TESTS
# =============================================================================

class TestSrcSubdirectories:
    """Tests for src subdirectory structure."""
    
    def test_db_directory_exists(self, project_root):
        """Database module directory exists."""
        db_dir = project_root / "src" / "db"
        assert db_dir.exists()
        assert db_dir.is_dir()
    
    def test_config_directory_exists(self, project_root):
        """Config module directory exists."""
        config_dir = project_root / "src" / "config"
        assert config_dir.exists()
        assert config_dir.is_dir()


# =============================================================================
# GITKEEP TESTS
# =============================================================================

class TestGitkeepFiles:
    """Tests for .gitkeep files in empty directories."""
    
    @pytest.mark.parametrize("subdir", [
        "data/artifacts/screenshots",
        "data/artifacts/videos",
        "data/artifacts/context",
        "output/reports",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "tests/golden-dataset",
        "logs",
    ])
    def test_gitkeep_exists(self, project_root, subdir):
        """Empty directories have .gitkeep files."""
        gitkeep = project_root / subdir / ".gitkeep"
        assert gitkeep.exists(), f"Missing .gitkeep in {subdir}"


# =============================================================================
# DIRECTORY WRITABILITY TESTS
# =============================================================================

class TestDirectoryWritability:
    """Tests for directory writability."""
    
    @pytest.mark.parametrize("subdir", [
        "data",
        "data/artifacts",
        "data/artifacts/screenshots",
        "data/artifacts/videos",
        "data/artifacts/context",
        "output",
        "output/reports",
        "logs",
    ])
    def test_directory_is_writable(self, project_root, subdir):
        """Required directories are writable."""
        dir_path = project_root / subdir
        assert dir_path.exists()
        # Test writability by checking mode
        # Note: This is a basic check; actual write test would require temp file creation
        import os
        assert os.access(dir_path, os.W_OK), f"Directory {subdir} is not writable"


# =============================================================================
# CONFIG FILE TESTS
# =============================================================================

class TestConfigFiles:
    """Tests for config directory files."""
    
    def test_default_config_exists(self, project_root):
        """Default config file exists."""
        config_file = project_root / "config" / "default.yaml"
        assert config_file.exists()
        assert config_file.is_file()
    
    def test_development_config_exists(self, project_root):
        """Development config file exists."""
        config_file = project_root / "config" / "development.yaml"
        assert config_file.exists()
        assert config_file.is_file()
    
    def test_staging_config_exists(self, project_root):
        """Staging config file exists."""
        config_file = project_root / "config" / "staging.yaml"
        assert config_file.exists()
        assert config_file.is_file()
    
    def test_production_config_exists(self, project_root):
        """Production config file exists."""
        config_file = project_root / "config" / "production.yaml"
        assert config_file.exists()
        assert config_file.is_file()


# =============================================================================
# REQUIRED ROOT FILES
# =============================================================================

class TestRequiredRootFiles:
    """Tests for required root-level files."""
    
    def test_agents_md_exists(self, project_root):
        """AGENTS.md exists."""
        agents_file = project_root / "AGENTS.md"
        assert agents_file.exists()
    
    def test_soul_md_exists(self, project_root):
        """SOUL.md exists."""
        soul_file = project_root / "SOUL.md"
        assert soul_file.exists()
    
    def test_prd_exists(self, project_root):
        """PRD exists."""
        prd_file = project_root / "autonomous-glm-prd.md"
        assert prd_file.exists()
    
    def test_requirements_exists(self, project_root):
        """requirements.txt exists."""
        req_file = project_root / "requirements.txt"
        assert req_file.exists()
    
    def test_gitignore_exists(self, project_root):
        """.gitignore exists."""
        gitignore = project_root / ".gitignore"
        assert gitignore.exists()
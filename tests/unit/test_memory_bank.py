"""
Unit tests for Autonomous-GLM memory bank file validation.

Tests verify that memory bank files exist, are valid, and have correct structure.
"""

import json
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


@pytest.fixture
def memory_bank_dir(project_root):
    """Get the memory bank directory."""
    return project_root / "memory-bank"


@pytest.fixture
def active_context_file(memory_bank_dir):
    """Get the active-context.md file path."""
    return memory_bank_dir / "active-context.md"


@pytest.fixture
def skill_matrix_file(memory_bank_dir):
    """Get the skill-matrix.json file path."""
    return memory_bank_dir / "skill-matrix.json"


@pytest.fixture
def audit_patterns_file(memory_bank_dir):
    """Get the audit-patterns.md file path."""
    return memory_bank_dir / "audit-patterns.md"


@pytest.fixture
def mistakes_file(memory_bank_dir):
    """Get the mistakes.md file path."""
    return memory_bank_dir / "mistakes.md"


@pytest.fixture
def agent_feedback_file(memory_bank_dir):
    """Get the agent-feedback.md file path."""
    return memory_bank_dir / "agent-feedback.md"


@pytest.fixture
def consolidated_learnings_file(memory_bank_dir):
    """Get the consolidated-learnings.md file path."""
    return memory_bank_dir / "consolidated-learnings.md"


@pytest.fixture
def readme_file(memory_bank_dir):
    """Get the README.md file path."""
    return memory_bank_dir / "README.md"


@pytest.fixture
def skill_matrix_data(skill_matrix_file):
    """Load skill matrix JSON data."""
    with open(skill_matrix_file) as f:
        return json.load(f)


# =============================================================================
# DIRECTORY TESTS
# =============================================================================

class TestMemoryBankDirectory:
    """Tests for memory bank directory."""
    
    def test_memory_bank_directory_exists(self, memory_bank_dir):
        """Memory bank directory exists."""
        assert memory_bank_dir.exists()
        assert memory_bank_dir.is_dir()


# =============================================================================
# FILE EXISTENCE TESTS
# =============================================================================

class TestMemoryBankFilesExist:
    """Tests for memory bank file existence."""
    
    def test_active_context_exists(self, active_context_file):
        """Active context file exists."""
        assert active_context_file.exists()
        assert active_context_file.is_file()
    
    def test_skill_matrix_exists(self, skill_matrix_file):
        """Skill matrix file exists."""
        assert skill_matrix_file.exists()
        assert skill_matrix_file.is_file()
    
    def test_audit_patterns_exists(self, audit_patterns_file):
        """Audit patterns file exists."""
        assert audit_patterns_file.exists()
        assert audit_patterns_file.is_file()
    
    def test_mistakes_exists(self, mistakes_file):
        """Mistakes file exists."""
        assert mistakes_file.exists()
        assert mistakes_file.is_file()
    
    def test_agent_feedback_exists(self, agent_feedback_file):
        """Agent feedback file exists."""
        assert agent_feedback_file.exists()
        assert agent_feedback_file.is_file()
    
    def test_consolidated_learnings_exists(self, consolidated_learnings_file):
        """Consolidated learnings file exists."""
        assert consolidated_learnings_file.exists()
        assert consolidated_learnings_file.is_file()
    
    def test_readme_exists(self, readme_file):
        """README file exists."""
        assert readme_file.exists()
        assert readme_file.is_file()


# =============================================================================
# JSON VALIDATION TESTS
# =============================================================================

class TestSkillMatrixJson:
    """Tests for skill-matrix.json validity."""
    
    def test_skill_matrix_is_valid_json(self, skill_matrix_file):
        """Skill matrix is valid JSON."""
        with open(skill_matrix_file) as f:
            data = json.load(f)
        
        assert isinstance(data, dict)
    
    def test_skill_matrix_has_cv_detection(self, skill_matrix_data):
        """Skill matrix has cv_detection capability."""
        assert "cv_detection" in skill_matrix_data
        assert "confidence" in skill_matrix_data["cv_detection"]
    
    def test_skill_matrix_has_hierarchy_analysis(self, skill_matrix_data):
        """Skill matrix has hierarchy_analysis capability."""
        assert "hierarchy_analysis" in skill_matrix_data
        assert "confidence" in skill_matrix_data["hierarchy_analysis"]
    
    def test_skill_matrix_has_accessibility_audit(self, skill_matrix_data):
        """Skill matrix has accessibility_audit capability."""
        assert "accessibility_audit" in skill_matrix_data
        assert "confidence" in skill_matrix_data["accessibility_audit"]
    
    def test_skill_matrix_has_color_typography(self, skill_matrix_data):
        """Skill matrix has color_typography capability."""
        assert "color_typography" in skill_matrix_data
        assert "confidence" in skill_matrix_data["color_typography"]
    
    def test_skill_matrix_has_motion_transitions(self, skill_matrix_data):
        """Skill matrix has motion_transitions capability."""
        assert "motion_transitions" in skill_matrix_data
        assert "confidence" in skill_matrix_data["motion_transitions"]
    
    def test_skill_matrix_confidence_values_valid(self, skill_matrix_data):
        """All confidence values are between 0.0 and 1.0."""
        for capability, data in skill_matrix_data.items():
            confidence = data.get("confidence")
            assert confidence is not None, f"Missing confidence for {capability}"
            assert 0.0 <= confidence <= 1.0, f"Invalid confidence {confidence} for {capability}"
    
    def test_skill_matrix_has_last_updated_field(self, skill_matrix_data):
        """Each capability has last_updated field."""
        for capability, data in skill_matrix_data.items():
            assert "last_updated" in data, f"Missing last_updated for {capability}"


# =============================================================================
# MARKDOWN STRUCTURE TESTS
# =============================================================================

class TestMarkdownStructure:
    """Tests for markdown file structure."""
    
    def test_active_context_has_title(self, active_context_file):
        """Active context has proper title."""
        content = active_context_file.read_text()
        assert content.strip().startswith("#")
    
    def test_audit_patterns_has_title(self, audit_patterns_file):
        """Audit patterns has proper title."""
        content = audit_patterns_file.read_text()
        assert content.strip().startswith("#")
    
    def test_mistakes_has_title(self, mistakes_file):
        """Mistakes has proper title."""
        content = mistakes_file.read_text()
        assert content.strip().startswith("#")
    
    def test_agent_feedback_has_title(self, agent_feedback_file):
        """Agent feedback has proper title."""
        content = agent_feedback_file.read_text()
        assert content.strip().startswith("#")
    
    def test_consolidated_learnings_has_title(self, consolidated_learnings_file):
        """Consolidated learnings has proper title."""
        content = consolidated_learnings_file.read_text()
        assert content.strip().startswith("#")
    
    def test_readme_has_title(self, readme_file):
        """README has proper title."""
        content = readme_file.read_text()
        assert content.strip().startswith("#")


# =============================================================================
# ACTIVE CONTEXT CONTENT TESTS
# =============================================================================

class TestActiveContextContent:
    """Tests for active-context.md content."""
    
    def test_active_context_has_current_state(self, active_context_file):
        """Active context has Current State section."""
        content = active_context_file.read_text()
        assert "Current State" in content or "current state" in content.lower()
    
    def test_active_context_has_milestone_progress(self, active_context_file):
        """Active context has milestone progress tracking."""
        content = active_context_file.read_text().lower()
        assert "milestone" in content or "progress" in content
    
    def test_active_context_has_agent_status(self, active_context_file):
        """Active context has agent handshake status."""
        content = active_context_file.read_text().lower()
        assert "agent" in content or "handshake" in content


# =============================================================================
# README CONTENT TESTS
# =============================================================================

class TestReadmeContent:
    """Tests for memory bank README content."""
    
    def test_readme_describes_purpose(self, readme_file):
        """README describes memory bank purpose."""
        content = readme_file.read_text().lower()
        assert "purpose" in content or "memory" in content
    
    def test_readme_lists_files(self, readme_file):
        """README lists memory bank files."""
        content = readme_file.read_text().lower()
        # Should mention the key files
        assert "skill-matrix" in content or "skill matrix" in content
    
    def test_readme_describes_update_protocol(self, readme_file):
        """README describes update protocol."""
        content = readme_file.read_text().lower()
        assert "update" in content or "protocol" in content


# =============================================================================
# FILE NOT EMPTY TESTS
# =============================================================================

class TestFilesNotEmpty:
    """Tests that files have meaningful content."""
    
    def test_active_context_not_empty(self, active_context_file):
        """Active context is not empty."""
        content = active_context_file.read_text()
        assert len(content.strip()) > 50
    
    def test_skill_matrix_not_empty(self, skill_matrix_data):
        """Skill matrix has capabilities defined."""
        assert len(skill_matrix_data) >= 5
    
    def test_readme_not_empty(self, readme_file):
        """README has meaningful content."""
        content = readme_file.read_text()
        assert len(content.strip()) > 200
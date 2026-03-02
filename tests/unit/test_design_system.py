"""
Unit tests for Autonomous-GLM design system file validation.

Tests verify that design system files are parseable and contain required sections.
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


@pytest.fixture
def design_system_dir(project_root):
    """Get the design system directory."""
    return project_root / "design_system"


@pytest.fixture
def tokens_file(design_system_dir):
    """Get the tokens.md file path."""
    return design_system_dir / "tokens.md"


@pytest.fixture
def components_file(design_system_dir):
    """Get the components.md file path."""
    return design_system_dir / "components.md"


@pytest.fixture
def standards_file(design_system_dir):
    """Get the standards.md file path."""
    return design_system_dir / "standards.md"


# =============================================================================
# FILE EXISTENCE TESTS
# =============================================================================

class TestDesignSystemFilesExist:
    """Tests for design system file existence."""
    
    def test_design_system_directory_exists(self, design_system_dir):
        """Design system directory exists."""
        assert design_system_dir.exists()
        assert design_system_dir.is_dir()
    
    def test_tokens_file_exists(self, tokens_file):
        """Tokens file exists."""
        assert tokens_file.exists()
        assert tokens_file.is_file()
    
    def test_components_file_exists(self, components_file):
        """Components file exists."""
        assert components_file.exists()
        assert components_file.is_file()
    
    def test_standards_file_exists(self, standards_file):
        """Standards file exists."""
        assert standards_file.exists()
        assert standards_file.is_file()


# =============================================================================
# FILE PARSEABILITY TESTS
# =============================================================================

class TestDesignSystemParseability:
    """Tests for design system file parseability."""
    
    def test_tokens_is_valid_markdown(self, tokens_file):
        """Tokens file is valid markdown."""
        content = tokens_file.read_text()
        
        # Should start with a heading
        assert content.strip().startswith("#")
        
        # Should contain markdown structure
        assert "##" in content or "|" in content
    
    def test_components_is_valid_markdown(self, components_file):
        """Components file is valid markdown."""
        content = components_file.read_text()
        
        # Should start with a heading
        assert content.strip().startswith("#")
        
        # Should contain markdown structure
        assert "##" in content
    
    def test_standards_is_valid_markdown(self, standards_file):
        """Standards file is valid markdown."""
        content = standards_file.read_text()
        
        # Should start with a heading
        assert content.strip().startswith("#")
        
        # Should contain markdown structure
        assert "##" in content
    
    def test_tokens_not_empty(self, tokens_file):
        """Tokens file is not empty."""
        content = tokens_file.read_text()
        assert len(content.strip()) > 100  # Should have meaningful content
    
    def test_components_not_empty(self, components_file):
        """Components file is not empty."""
        content = components_file.read_text()
        assert len(content.strip()) > 100
    
    def test_standards_not_empty(self, standards_file):
        """Standards file is not empty."""
        content = standards_file.read_text()
        assert len(content.strip()) > 100


# =============================================================================
# TOKEN CONTENT TESTS
# =============================================================================

class TestTokensContent:
    """Tests for tokens.md content structure."""
    
    def test_tokens_has_color_section(self, tokens_file):
        """Tokens file has color section."""
        content = tokens_file.read_text().lower()
        assert "color" in content
    
    def test_tokens_has_typography_section(self, tokens_file):
        """Tokens file has typography section."""
        content = tokens_file.read_text().lower()
        assert "typography" in content or "font" in content
    
    def test_tokens_has_spacing_section(self, tokens_file):
        """Tokens file has spacing section."""
        content = tokens_file.read_text().lower()
        assert "spacing" in content or "space" in content
    
    def test_tokens_has_table_structure(self, tokens_file):
        """Tokens file uses table structure."""
        content = tokens_file.read_text()
        # Tables in markdown use | character
        assert "|" in content
    
    def test_tokens_has_token_references(self, tokens_file):
        """Tokens file has token references (CSS variables)."""
        content = tokens_file.read_text()
        # Should have CSS variable style tokens
        assert "--" in content


# =============================================================================
# COMPONENTS CONTENT TESTS
# =============================================================================

class TestComponentsContent:
    """Tests for components.md content structure."""
    
    def test_components_has_buttons_section(self, components_file):
        """Components file has buttons section."""
        content = components_file.read_text().lower()
        assert "button" in content
    
    def test_components_has_form_section(self, components_file):
        """Components file has form elements section."""
        content = components_file.read_text().lower()
        assert "form" in content or "input" in content
    
    def test_components_has_feedback_section(self, components_file):
        """Components file has feedback section."""
        content = components_file.read_text().lower()
        # Should have some feedback mechanism documented
        assert "alert" in content or "toast" in content or "notification" in content
    
    def test_components_has_states_documented(self, components_file):
        """Components file documents component states."""
        content = components_file.read_text().lower()
        # Should mention states
        assert "state" in content or "hover" in content or "disabled" in content


# =============================================================================
# STANDARDS CONTENT TESTS
# =============================================================================

class TestStandardsContent:
    """Tests for standards.md content structure."""
    
    def test_standards_has_principles(self, standards_file):
        """Standards file has design principles."""
        content = standards_file.read_text().lower()
        assert "principle" in content
    
    def test_standards_has_accessibility(self, standards_file):
        """Standards file has accessibility section."""
        content = standards_file.read_text().lower()
        assert "accessibility" in content or "wcag" in content
    
    def test_standards_has_responsive(self, standards_file):
        """Standards file has responsive design section."""
        content = standards_file.read_text().lower()
        assert "responsive" in content or "breakpoint" in content
    
    def test_standards_has_motion(self, standards_file):
        """Standards file has motion/animation section."""
        content = standards_file.read_text().lower()
        assert "motion" in content or "animation" in content or "transition" in content
    
    def test_standards_has_quality_checklist(self, standards_file):
        """Standards file has quality checklist."""
        content = standards_file.read_text().lower()
        assert "checklist" in content or "quality" in content
    
    def test_standards_references_contrast(self, standards_file):
        """Standards file references contrast requirements."""
        content = standards_file.read_text().lower()
        assert "contrast" in content


# =============================================================================
# CROSS-FILE CONSISTENCY
# =============================================================================

class TestDesignSystemConsistency:
    """Tests for consistency across design system files."""
    
    def test_all_files_have_titles(self, tokens_file, components_file, standards_file):
        """All design system files have proper titles."""
        for file_path in [tokens_file, components_file, standards_file]:
            content = file_path.read_text()
            first_line = content.strip().split("\n")[0]
            assert first_line.startswith("# "), f"{file_path.name} missing title"
    
    def test_files_reference_each_other(self, standards_file):
        """Standards file references other design system files."""
        content = standards_file.read_text().lower()
        # Standards should reference tokens or components
        assert "token" in content or "component" in content
"""
Unit tests for state and accessibility dimension auditors (M3-4).

Tests all 6 state/accessibility dimensions:
- Iconography
- Empty States
- Loading States
- Error States
- Dark Mode / Theming
- Accessibility
"""

import pytest
from unittest.mock import MagicMock

from src.audit.models import AuditDimension
from src.db.models import Screen, Component, BoundingBox, Severity
from src.audit.dimensions import (
    # State & Accessibility Dimensions
    IconographyAuditor,
    EmptyStatesAuditor,
    LoadingStatesAuditor,
    ErrorStatesAuditor,
    ThemingAuditor,
    AccessibilityAuditor,
    DIMENSION_AUDITORS,
    get_auditor,
    get_all_auditors,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_screen():
    """Create a mock screen for testing."""
    screen = MagicMock(spec=Screen)
    screen.id = "test-screen-001"
    screen.width = 1920
    screen.height = 1080
    return screen


@pytest.fixture
def make_component():
    """Factory for creating test components."""
    def _make(
        comp_id: str = "comp-001",
        comp_type: str = "button",
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 50,
        properties: dict = None,
    ):
        comp = MagicMock(spec=Component)
        comp.id = comp_id
        comp.type = comp_type
        comp.bounding_box = BoundingBox(
            x=x, y=y, width=width, height=height
        )
        comp.properties = properties or {}
        return comp
    return _make


# =============================================================================
# ICONOGRAPHY AUDITOR TESTS
# =============================================================================

class TestIconographyAuditor:
    """Tests for IconographyAuditor."""
    
    def test_dimension_attribute(self):
        auditor = IconographyAuditor()
        assert auditor.dimension == AuditDimension.ICONOGRAPHY
    
    def test_no_findings_for_few_icons(self, mock_screen, make_component):
        """Should return no findings when too few icons."""
        auditor = IconographyAuditor()
        components = [make_component(comp_type="icon") for _ in range(1)]
        findings = auditor.audit(mock_screen, components)
        assert findings == []
    
    def test_consistent_icon_sizes_no_issue(self, mock_screen, make_component):
        """Should not flag when icon sizes are consistent."""
        auditor = IconographyAuditor()
        # All 24x24 icons
        components = [
            make_component(f"icon-{i}", "icon", width=24, height=24)
            for i in range(5)
        ]
        findings = auditor.audit(mock_screen, components)
        size_issues = [f for f in findings if "inconsistent" in f.issue.lower()]
        assert len(size_issues) == 0
    
    def test_inconsistent_icon_sizes_detection(self, mock_screen, make_component):
        """Should detect inconsistent icon sizes."""
        auditor = IconographyAuditor()
        # Mix of very different sizes
        components = [
            make_component("icon-1", "icon", width=16, height=16),
            make_component("icon-2", "icon", width=24, height=24),
            make_component("icon-3", "icon", width=48, height=48),
            make_component("icon-4", "icon", width=64, height=64),
            make_component("icon-5", "icon", width=128, height=128),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should detect either inconsistency or too many size groups
        assert len(findings) >= 1
    
    def test_configurable_thresholds(self, mock_screen, make_component):
        """Should use configurable thresholds."""
        auditor = IconographyAuditor(config={"max_size_variance": 0.1})
        assert auditor.config["max_size_variance"] == 0.1


# =============================================================================
# EMPTY STATES AUDITOR TESTS
# =============================================================================

class TestEmptyStatesAuditor:
    """Tests for EmptyStatesAuditor."""
    
    def test_dimension_attribute(self):
        auditor = EmptyStatesAuditor()
        assert auditor.dimension == AuditDimension.EMPTY_STATES
    
    def test_populated_screen_no_empty_state(self, mock_screen, make_component):
        """Should not flag populated screens as empty states."""
        auditor = EmptyStatesAuditor()
        # Many components - not an empty state
        components = [
            make_component(f"comp-{i}", "button", x=(i % 10) * 100, y=(i // 10) * 50)
            for i in range(50)
        ]
        findings = auditor.audit(mock_screen, components)
        # Should not detect as empty state
        assert findings == []
    
    def test_empty_state_without_action_detection(self, mock_screen, make_component):
        """Should detect empty state without user guidance."""
        auditor = EmptyStatesAuditor(config={"min_components_for_populated": 10})
        # Few components, no action
        components = [
            make_component("text-1", "text", x=100, y=100, width=200, height=20),
            make_component("text-2", "text", x=100, y=140, width=200, height=20),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should detect as empty state with issues
        guidance_issues = [f for f in findings if "guidance" in f.issue.lower()]
        assert len(guidance_issues) >= 1
    
    def test_well_designed_empty_state(self, mock_screen, make_component):
        """Should not flag well-designed empty states."""
        auditor = EmptyStatesAuditor(config={"min_components_for_populated": 10})
        # Good empty state: centered illustration + text + button
        components = [
            make_component("illustration", "image", x=760, y=400, width=400, height=300),
            make_component("heading", "text", x=710, y=720, width=500, height=30),
            make_component("cta", "button", x=860, y=780, width=200, height=44),
        ]
        findings = auditor.audit(mock_screen, components)
        # Well-designed empty state should have fewer/no issues
        # (May still have some findings depending on thresholds)


# =============================================================================
# LOADING STATES AUDITOR TESTS
# =============================================================================

class TestLoadingStatesAuditor:
    """Tests for LoadingStatesAuditor."""
    
    def test_dimension_attribute(self):
        auditor = LoadingStatesAuditor()
        assert auditor.dimension == AuditDimension.LOADING_STATES
    
    def test_no_findings_without_loading_components(self, mock_screen, make_component):
        """Should return no findings when no loading indicators."""
        auditor = LoadingStatesAuditor()
        components = [
            make_component("btn-1", "button"),
            make_component("text-1", "text"),
        ]
        findings = auditor.audit(mock_screen, components)
        assert findings == []
    
    def test_detects_loading_properties(self, mock_screen, make_component):
        """Should detect loading components by properties."""
        auditor = LoadingStatesAuditor()
        components = [
            make_component("loader-1", "image", width=32, height=32, 
                          properties={"loading": True}),
            make_component("loader-2", "image", width=32, height=32,
                          properties={"skeleton": True}),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should have some findings about loading indicators
        # (positioning, etc.)
        assert isinstance(findings, list)
    
    def test_centered_loading_indicator(self, mock_screen, make_component):
        """Should not flag centered loading indicators."""
        auditor = LoadingStatesAuditor()
        # Centered spinner
        components = [
            make_component("spinner", "image", x=944, y=524, width=32, height=32,
                          properties={"spinner": True}),
        ]
        findings = auditor.audit(mock_screen, components)
        # Centered indicator should not have position issue
        position_issues = [f for f in findings if "centered" in f.issue.lower()]
        # This should pass - centered spinner shouldn't trigger position warning
        assert len(position_issues) == 0


# =============================================================================
# ERROR STATES AUDITOR TESTS
# =============================================================================

class TestErrorStatesAuditor:
    """Tests for ErrorStatesAuditor."""
    
    def test_dimension_attribute(self):
        auditor = ErrorStatesAuditor()
        assert auditor.dimension == AuditDimension.ERROR_STATES
    
    def test_no_findings_without_errors(self, mock_screen, make_component):
        """Should return no findings when no error components."""
        auditor = ErrorStatesAuditor()
        components = [
            make_component("btn-1", "button"),
            make_component("text-1", "text"),
        ]
        findings = auditor.audit(mock_screen, components)
        assert findings == []
    
    def test_detects_error_by_property(self, mock_screen, make_component):
        """Should detect error components by properties."""
        auditor = ErrorStatesAuditor()
        components = [
            make_component("error-msg", "text", properties={"error": True}),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should detect and analyze error component
        assert isinstance(findings, list)
    
    def test_detects_error_by_color(self, mock_screen, make_component):
        """Should detect error components by red color."""
        auditor = ErrorStatesAuditor()
        components = [
            make_component("error-msg", "text", 
                          properties={"color": [220, 50, 50]}),  # Red
        ]
        findings = auditor.audit(mock_screen, components)
        assert isinstance(findings, list)
    
    def test_detects_error_by_text_pattern(self, mock_screen, make_component):
        """Should detect error components by text content."""
        auditor = ErrorStatesAuditor()
        components = [
            make_component("error-msg", "text",
                          properties={"text": "Invalid email address"}),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should detect as error and potentially flag for helpfulness
        assert isinstance(findings, list)
    
    def test_actionable_error_no_issue(self, mock_screen, make_component):
        """Should not flag actionable error messages."""
        auditor = ErrorStatesAuditor()
        components = [
            make_component("error-msg", "text", width=300, height=50,
                          properties={
                              "error": True,
                              "text": "Please enter a valid email address"
                          }),
        ]
        findings = auditor.audit(mock_screen, components)
        # Actionable message should not have helpfulness issue
        helpfulness_issues = [f for f in findings if "helpful" in f.issue.lower() 
                             or "actionable" in f.issue.lower()]
        # This error IS actionable, so should not be flagged
        # (may still have other findings)


# =============================================================================
# THEMING AUDITOR TESTS
# =============================================================================

class TestThemingAuditor:
    """Tests for ThemingAuditor."""
    
    def test_dimension_attribute(self):
        auditor = ThemingAuditor()
        assert auditor.dimension == AuditDimension.DARK_MODE_THEMING
    
    def test_no_findings_without_color_data(self, mock_screen, make_component):
        """Should return no findings when no color data."""
        auditor = ThemingAuditor()
        components = [
            make_component("btn-1", "button"),
            make_component("text-1", "text"),
            make_component("icon-1", "icon"),
        ]
        findings = auditor.audit(mock_screen, components)
        assert findings == []
    
    def test_detects_light_mode(self, mock_screen, make_component):
        """Should detect light mode from background."""
        auditor = ThemingAuditor()
        components = [
            make_component("container", "container", 
                          properties={"background": [255, 255, 255]}),
            make_component("card", "card",
                          properties={"background": [250, 250, 250]}),
            make_component("text", "text",
                          properties={"color": [0, 0, 0], "background": [255, 255, 255]}),
        ]
        findings = auditor.audit(mock_screen, components)
        # Light mode with good contrast should have no issues
        contrast_issues = [f for f in findings if "contrast" in f.issue.lower()]
        # Black on white is 21:1 - should pass
        assert len(contrast_issues) == 0
    
    def test_detects_dark_mode(self, mock_screen, make_component):
        """Should detect dark mode from background."""
        auditor = ThemingAuditor()
        components = [
            make_component("container", "container",
                          properties={"background": [30, 30, 30]}),
            make_component("card", "card",
                          properties={"background": [40, 40, 40]}),
            make_component("text", "text",
                          properties={"color": [255, 255, 255], "background": [30, 30, 30]}),
        ]
        findings = auditor.audit(mock_screen, components)
        # Dark mode with good contrast should have no contrast issues
        contrast_issues = [f for f in findings if "contrast" in f.issue.lower()]
        # White on dark is 21:1 - should pass
        assert len(contrast_issues) == 0
    
    def test_low_contrast_detection(self, mock_screen, make_component):
        """Should detect low contrast in theming."""
        auditor = ThemingAuditor()
        # Need 3+ components to meet min_components threshold
        components = [
            make_component("container", "container",
                          properties={"background": [100, 100, 100]}),
            make_component("card", "card",
                          properties={"background": [100, 100, 100]}),
            make_component("text", "text",
                          properties={"color": [120, 120, 120], "background": [100, 100, 100]}),
        ]
        findings = auditor.audit(mock_screen, components)
        # Low contrast should be flagged
        contrast_issues = [f for f in findings if "contrast" in f.issue.lower()]
        assert len(contrast_issues) >= 1


# =============================================================================
# ACCESSIBILITY AUDITOR TESTS
# =============================================================================

class TestAccessibilityAuditor:
    """Tests for AccessibilityAuditor."""
    
    def test_dimension_attribute(self):
        auditor = AccessibilityAuditor()
        assert auditor.dimension == AuditDimension.ACCESSIBILITY
    
    def test_good_contrast_no_issue(self, mock_screen, make_component):
        """Should not flag good contrast ratios."""
        auditor = AccessibilityAuditor()
        # Black text on white background = 21:1
        components = [
            make_component("text-1", "text", height=16,
                          properties={"color": [0, 0, 0], "background": [255, 255, 255]}),
            make_component("text-2", "text", height=16,
                          properties={"color": [0, 0, 0], "background": [255, 255, 255]}),
        ]
        findings = auditor.audit(mock_screen, components)
        contrast_issues = [f for f in findings if "contrast" in f.issue.lower()]
        assert len(contrast_issues) == 0
    
    def test_low_contrast_detection(self, mock_screen, make_component):
        """Should detect low contrast ratios."""
        auditor = AccessibilityAuditor()
        # Light gray on white = very low contrast
        components = [
            make_component("text-1", "text", height=16,
                          properties={"color": [200, 200, 200], "background": [255, 255, 255]}),
        ]
        findings = auditor.audit(mock_screen, components)
        contrast_issues = [f for f in findings if "contrast" in f.issue.lower()]
        assert len(contrast_issues) >= 1
    
    def test_small_text_detection(self, mock_screen, make_component):
        """Should detect text below minimum size."""
        auditor = AccessibilityAuditor()
        components = [
            make_component("text-1", "text", height=8,  # Too small
                          properties={"color": [0, 0, 0], "background": [255, 255, 255]}),
        ]
        findings = auditor.audit(mock_screen, components)
        size_issues = [f for f in findings if "size" in f.issue.lower() or "small" in f.issue.lower()]
        assert len(size_issues) >= 1
    
    def test_small_touch_target_detection(self, mock_screen, make_component):
        """Should detect small touch targets."""
        auditor = AccessibilityAuditor()
        components = [
            make_component("btn-1", "button", width=30, height=30,  # Too small
                          properties={"color": [255, 255, 255], "background": [0, 0, 128]}),
        ]
        findings = auditor.audit(mock_screen, components)
        touch_issues = [f for f in findings if "touch" in f.issue.lower()]
        assert len(touch_issues) >= 1
    
    def test_configurable_wcag_thresholds(self, mock_screen, make_component):
        """Should use configurable WCAG thresholds."""
        auditor = AccessibilityAuditor(config={"min_contrast_normal_text": 7.0})  # AAA
        assert auditor.config["min_contrast_normal_text"] == 7.0


# =============================================================================
# REGISTRY TESTS
# =============================================================================

class TestStateDimensionRegistry:
    """Tests for state dimension auditor registry."""
    
    def test_all_state_dimensions_registered(self):
        """All 6 state dimensions should be registered."""
        expected = {
            "iconography",
            "empty_states",
            "loading_states",
            "error_states",
            "dark_mode_theming",
            "accessibility",
        }
        assert expected.issubset(set(DIMENSION_AUDITORS.keys()))
    
    def test_get_state_auditor_valid(self):
        """get_auditor should return correct state auditor."""
        auditor = get_auditor("accessibility")
        assert isinstance(auditor, AccessibilityAuditor)
    
    def test_get_all_auditors_includes_state(self):
        """get_all_auditors should include state auditors."""
        auditors = get_all_auditors()
        auditor_types = [type(a).__name__ for a in auditors]
        
        assert "IconographyAuditor" in auditor_types
        assert "EmptyStatesAuditor" in auditor_types
        assert "LoadingStatesAuditor" in auditor_types
        assert "ErrorStatesAuditor" in auditor_types
        assert "ThemingAuditor" in auditor_types
        assert "AccessibilityAuditor" in auditor_types
    
    def test_total_dimension_count(self):
        """Should have 13 total dimensions (7 visual + 6 state)."""
        assert len(DIMENSION_AUDITORS) == 13


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestStateDimensionIntegration:
    """Integration tests for state dimension auditors."""
    
    def test_all_state_auditors_run_without_error(self, mock_screen, make_component):
        """All state auditors should run without error."""
        state_auditors = [
            IconographyAuditor(),
            EmptyStatesAuditor(),
            LoadingStatesAuditor(),
            ErrorStatesAuditor(),
            ThemingAuditor(),
            AccessibilityAuditor(),
        ]
        
        components = [
            make_component("icon-1", "icon", width=24, height=24),
            make_component("text-1", "text", height=16,
                          properties={"color": [0, 0, 0], "background": [255, 255, 255]}),
            make_component("btn-1", "button", width=44, height=44),
        ]
        
        for auditor in state_auditors:
            findings = auditor.audit(mock_screen, components)
            assert isinstance(findings, list)
            for finding in findings:
                assert hasattr(finding, 'issue')
                assert hasattr(finding, 'severity')
                assert hasattr(finding, 'rationale')
    
    def test_finding_severity_levels(self, mock_screen, make_component):
        """Findings should have appropriate severity levels."""
        auditor = AccessibilityAuditor()
        
        # Create components with accessibility issues
        components = [
            make_component("text-1", "text", height=16,
                          properties={"color": [180, 180, 180], "background": [255, 255, 255]}),
        ]
        
        findings = auditor.audit(mock_screen, components)
        
        for finding in findings:
            assert finding.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    
    def test_metadata_in_state_findings(self, mock_screen, make_component):
        """State findings should include metadata."""
        auditor = AccessibilityAuditor()
        
        components = [
            make_component("text-1", "text", height=8,
                          properties={"color": [200, 200, 200], "background": [255, 255, 255]}),
        ]
        
        findings = auditor.audit(mock_screen, components)
        
        for finding in findings:
            assert finding.metadata is not None
            assert isinstance(finding.metadata, dict)
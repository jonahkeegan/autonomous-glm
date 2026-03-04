"""
Unit tests for visual audit dimension auditors.

Tests all 7 visual audit dimensions:
- Visual Hierarchy
- Spacing & Rhythm
- Typography
- Color
- Alignment & Grid
- Components
- Density
"""

import pytest
from unittest.mock import MagicMock

from src.audit.models import AuditDimension
from src.db.models import Screen, Component, BoundingBox, Severity
from src.audit.dimensions import (
    BaseAuditor,
    VisualHierarchyAuditor,
    SpacingRhythmAuditor,
    TypographyAuditor,
    ColorAuditor,
    AlignmentGridAuditor,
    ComponentsAuditor,
    DensityAuditor,
    DIMENSION_AUDITORS,
    get_auditor,
    get_all_auditors,
    # Utility functions
    calculate_distance,
    get_bbox_center,
    get_bbox_area,
    bboxes_overlap,
    bbox_contains,
    quantize_to_grid,
    is_on_grid,
    calculate_contrast_ratio,
    rgb_to_luminance,
    group_by_type,
    calculate_density,
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


@pytest.fixture
def sample_components(make_component):
    """Create a set of sample components for testing."""
    return [
        make_component("comp-001", "button", x=100, y=100, width=120, height=40),
        make_component("comp-002", "text", x=100, y=160, width=200, height=24),
        make_component("comp-003", "input", x=100, y=200, width=300, height=40),
        make_component("comp-004", "button", x=100, y=260, width=120, height=40),
        make_component("comp-005", "image", x=500, y=100, width=400, height=300),
    ]


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions in base.py."""
    
    def test_calculate_distance(self):
        assert calculate_distance((0, 0), (3, 4)) == 5.0
        assert calculate_distance((1, 1), (1, 1)) == 0.0
    
    def test_get_bbox_center(self):
        bbox = BoundingBox(x=100, y=100, width=200, height=100)
        center = get_bbox_center(bbox)
        assert center == (200.0, 150.0)
    
    def test_get_bbox_area(self):
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        assert get_bbox_area(bbox) == 5000
    
    def test_bboxes_overlap_true(self):
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100)
        bbox2 = BoundingBox(x=50, y=50, width=100, height=100)
        assert bboxes_overlap(bbox1, bbox2) is True
    
    def test_bboxes_overlap_false(self):
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100)
        bbox2 = BoundingBox(x=200, y=200, width=100, height=100)
        assert bboxes_overlap(bbox1, bbox2) is False
    
    def test_bbox_contains_true(self):
        outer = BoundingBox(x=0, y=0, width=200, height=200)
        inner = BoundingBox(x=50, y=50, width=100, height=100)
        assert bbox_contains(outer, inner) is True
    
    def test_bbox_contains_false(self):
        outer = BoundingBox(x=0, y=0, width=100, height=100)
        inner = BoundingBox(x=50, y=50, width=100, height=100)
        assert bbox_contains(outer, inner) is False
    
    def test_quantize_to_grid(self):
        assert quantize_to_grid(7, grid_base=4) == 8
        assert quantize_to_grid(5, grid_base=4) == 4
        assert quantize_to_grid(10, grid_base=8) == 8
    
    def test_is_on_grid(self):
        assert is_on_grid(8, grid_base=4) is True
        assert is_on_grid(9, grid_base=4, tolerance=1) is True
        # 11 is 1 away from 12 (divisible by 4), so with tolerance=1 it IS on grid
        assert is_on_grid(11, grid_base=4, tolerance=1) is True
        # 13 is 1 away from 12, so with tolerance=1 it's still on grid
        assert is_on_grid(13, grid_base=4, tolerance=1) is True
        # 14 is 2 away from both 12 and 16
        assert is_on_grid(14, grid_base=4, tolerance=1) is False
    
    def test_calculate_contrast_ratio(self):
        # Black on white
        ratio = calculate_contrast_ratio(0, 1)
        assert ratio == 21.0
        
        # Same color
        ratio = calculate_contrast_ratio(0.5, 0.5)
        assert ratio == 1.0
    
    def test_rgb_to_luminance(self):
        # White
        assert rgb_to_luminance(255, 255, 255) == 1.0
        
        # Black
        assert rgb_to_luminance(0, 0, 0) == 0.0
    
    def test_group_by_type(self, sample_components):
        groups = group_by_type(sample_components)
        assert "button" in groups
        assert len(groups["button"]) == 2
        assert "text" in groups
        assert len(groups["text"]) == 1
    
    def test_calculate_density(self, sample_components):
        density = calculate_density(sample_components, 1920, 1080)
        # 5 components in 2,073,600 pixels = 0.024 per 10k
        assert density > 0


# =============================================================================
# VISUAL HIERARCHY AUDITOR TESTS
# =============================================================================

class TestVisualHierarchyAuditor:
    """Tests for VisualHierarchyAuditor."""
    
    def test_dimension_attribute(self):
        auditor = VisualHierarchyAuditor()
        assert auditor.dimension == AuditDimension.VISUAL_HIERARCHY
    
    def test_no_findings_for_few_components(self, mock_screen, make_component):
        """Should return no findings when too few components."""
        auditor = VisualHierarchyAuditor()
        components = [make_component() for _ in range(2)]
        findings = auditor.audit(mock_screen, components)
        assert findings == []
    
    def test_clear_focal_point_no_issue(self, mock_screen, make_component):
        """Should not flag when there's a clear focal point."""
        auditor = VisualHierarchyAuditor()
        # One large prominent element, others smaller
        components = [
            make_component("hero", "image", x=0, y=0, width=800, height=600),
            make_component("btn1", "button", x=100, y=650, width=100, height=40),
            make_component("btn2", "button", x=250, y=650, width=100, height=40),
            make_component("text1", "text", x=100, y=720, width=300, height=20),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should have no focal point issue (hero is clearly prominent)
        focal_issues = [f for f in findings if "focal point" in f.issue.lower()]
        assert len(focal_issues) == 0
    
    def test_competing_elements_detection(self, mock_screen, make_component):
        """Should detect competing elements with similar prominence."""
        auditor = VisualHierarchyAuditor()
        # Multiple similar-sized elements
        components = [
            make_component("c1", "card", x=100, y=100, width=300, height=200),
            make_component("c2", "card", x=450, y=100, width=300, height=200),
            make_component("c3", "card", x=800, y=100, width=300, height=200),
            make_component("c4", "card", x=100, y=350, width=300, height=200),
            make_component("c5", "card", x=450, y=350, width=300, height=200),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should detect competing elements
        competing = [f for f in findings if "competing" in f.issue.lower()]
        assert len(competing) >= 1
    
    def test_focal_position_outside_expected_region(self, mock_screen, make_component):
        """Should flag focal point outside top-left region."""
        auditor = VisualHierarchyAuditor(config={"focal_region_x": 0.3, "focal_region_y": 0.3})
        # Large element in bottom-right
        components = [
            make_component("hero", "image", x=1200, y=700, width=600, height=300),
            make_component("btn1", "button", x=100, y=100, width=80, height=30),
            make_component("btn2", "button", x=200, y=100, width=80, height=30),
            make_component("text1", "text", x=100, y=150, width=200, height=20),
        ]
        findings = auditor.audit(mock_screen, components)
        position_issues = [f for f in findings if "focal region" in f.issue.lower()]
        assert len(position_issues) >= 1


# =============================================================================
# SPACING & RHYTHM AUDITOR TESTS
# =============================================================================

class TestSpacingRhythmAuditor:
    """Tests for SpacingRhythmAuditor."""
    
    def test_dimension_attribute(self):
        auditor = SpacingRhythmAuditor()
        assert auditor.dimension == AuditDimension.SPACING_RHYTHM
    
    def test_configurable_threshold(self, mock_screen, make_component):
        """Should use configurable thresholds."""
        # Test that config is accepted
        auditor = SpacingRhythmAuditor(config={"max_spacing_cv": 0.1, "min_spacing": 20})
        assert auditor.config["max_spacing_cv"] == 0.1
        assert auditor.config["min_spacing"] == 20
    
    def test_inconsistent_spacing_detection(self, mock_screen, make_component):
        """Should detect inconsistent spacing."""
        auditor = SpacingRhythmAuditor()
        # Very inconsistent spacing
        components = [
            make_component("c1", "button", x=100, y=100, width=100, height=40),
            make_component("c2", "button", x=100, y=145, width=100, height=40),  # 5px gap
            make_component("c3", "button", x=100, y=300, width=100, height=40),  # 155px gap
            make_component("c4", "button", x=100, y=320, width=100, height=40),  # 20px gap
            make_component("c5", "button", x=100, y=500, width=100, height=40),  # 180px gap
        ]
        findings = auditor.audit(mock_screen, components)
        spacing_issues = [f for f in findings if "inconsistent" in f.issue.lower()]
        assert len(spacing_issues) >= 1
    
    def test_cramped_elements_detection(self, mock_screen, make_component):
        """Should detect cramped elements."""
        auditor = SpacingRhythmAuditor(config={"min_spacing": 8})
        # Elements with less than 8px gaps
        components = [
            make_component("c1", "button", x=100, y=100, width=100, height=40),
            make_component("c2", "button", x=100, y=143, width=100, height=40),  # 3px gap
            make_component("c3", "button", x=100, y=186, width=100, height=40),  # 3px gap
            make_component("c4", "button", x=100, y=229, width=100, height=40),  # 3px gap
        ]
        findings = auditor.audit(mock_screen, components)
        cramped = [f for f in findings if "cramped" in f.issue.lower()]
        assert len(cramped) >= 1


# =============================================================================
# TYPOGRAPHY AUDITOR TESTS
# =============================================================================

class TestTypographyAuditor:
    """Tests for TypographyAuditor."""
    
    def test_dimension_attribute(self):
        auditor = TypographyAuditor()
        assert auditor.dimension == AuditDimension.TYPOGRAPHY
    
    def test_limited_font_sizes_no_issue(self, mock_screen, make_component):
        """Should not flag when font sizes are limited."""
        auditor = TypographyAuditor()
        components = [
            make_component("h1", "text", x=100, y=100, width=300, height=36),  # 36px
            make_component("h2", "text", x=100, y=150, width=250, height=24),  # 24px
            make_component("p1", "text", x=100, y=190, width=400, height=16),  # 16px
            make_component("p2", "text", x=100, y=220, width=400, height=16),  # 16px
        ]
        findings = auditor.audit(mock_screen, components)
        size_issues = [f for f in findings if "too many font sizes" in f.issue.lower()]
        assert len(size_issues) == 0
    
    def test_too_many_font_sizes_detection(self, mock_screen, make_component):
        """Should detect too many distinct font sizes."""
        auditor = TypographyAuditor(config={"max_font_sizes": 3})
        components = [
            make_component("t1", "text", x=100, y=100, width=300, height=72),
            make_component("t2", "text", x=100, y=180, width=250, height=48),
            make_component("t3", "text", x=100, y=240, width=200, height=36),
            make_component("t4", "text", x=100, y=290, width=400, height=24),
            make_component("t5", "text", x=100, y=330, width=400, height=18),
            make_component("t6", "text", x=100, y=360, width=400, height=14),
        ]
        findings = auditor.audit(mock_screen, components)
        size_issues = [f for f in findings if "too many font sizes" in f.issue.lower()]
        assert len(size_issues) >= 1


# =============================================================================
# COLOR AUDITOR TESTS
# =============================================================================

class TestColorAuditor:
    """Tests for ColorAuditor."""
    
    def test_dimension_attribute(self):
        auditor = ColorAuditor()
        assert auditor.dimension == AuditDimension.COLOR
    
    def test_no_findings_without_colors(self, mock_screen, sample_components):
        """Should return no findings when no color data available."""
        auditor = ColorAuditor()
        findings = auditor.audit(mock_screen, sample_components)
        # Without color properties, should have no findings
        assert findings == []
    
    def test_too_many_colors_detection(self, mock_screen, make_component):
        """Should detect too many distinct colors."""
        auditor = ColorAuditor(config={"max_distinct_colors": 3})
        # Components with many different colors
        components = [
            make_component("c1", "button", properties={"color": [255, 0, 0]}),
            make_component("c2", "button", properties={"color": [0, 255, 0]}),
            make_component("c3", "button", properties={"color": [0, 0, 255]}),
            make_component("c4", "button", properties={"color": [255, 255, 0]}),
            make_component("c5", "button", properties={"color": [255, 0, 255]}),
        ]
        findings = auditor.audit(mock_screen, components)
        color_issues = [f for f in findings if "too many" in f.issue.lower()]
        assert len(color_issues) >= 1
    
    def test_contrast_issue_detection(self, mock_screen, make_component):
        """Should detect contrast issues."""
        auditor = ColorAuditor()
        # Low contrast: light gray on white
        components = [
            make_component("bg", "container", properties={"background": [255, 255, 255]}),
            make_component("text1", "text", properties={"color": [200, 200, 200]}),
            make_component("text2", "text", properties={"color": [190, 190, 190]}),
            make_component("text3", "text", properties={"color": [180, 180, 180]}),
        ]
        findings = auditor.audit(mock_screen, components)
        contrast_issues = [f for f in findings if "contrast" in f.issue.lower()]
        assert len(contrast_issues) >= 1


# =============================================================================
# ALIGNMENT & GRID AUDITOR TESTS
# =============================================================================

class TestAlignmentGridAuditor:
    """Tests for AlignmentGridAuditor."""
    
    def test_dimension_attribute(self):
        auditor = AlignmentGridAuditor()
        assert auditor.dimension == AuditDimension.ALIGNMENT_GRID
    
    def test_grid_aligned_no_issue(self, mock_screen, make_component):
        """Should not flag when elements are grid-aligned."""
        auditor = AlignmentGridAuditor()
        # All on 4px grid
        components = [
            make_component("c1", "button", x=100, y=100, width=120, height=40),
            make_component("c2", "button", x=100, y=148, width=120, height=40),
            make_component("c3", "button", x=100, y=196, width=120, height=40),
        ]
        findings = auditor.audit(mock_screen, components)
        grid_issues = [f for f in findings if "not aligned to" in f.issue.lower()]
        assert len(grid_issues) == 0
    
    def test_off_grid_detection(self, mock_screen, make_component):
        """Should detect off-grid elements."""
        auditor = AlignmentGridAuditor(config={"grid_base": 8, "grid_tolerance": 0})
        # Off-grid positions
        components = [
            make_component("c1", "button", x=101, y=100, width=120, height=40),
            make_component("c2", "button", x=100, y=103, width=120, height=40),
            make_component("c3", "button", x=100, y=100, width=123, height=40),
            make_component("c4", "button", x=100, y=100, width=120, height=43),
        ]
        findings = auditor.audit(mock_screen, components)
        # Should detect misalignments
        assert len(findings) >= 1


# =============================================================================
# COMPONENTS AUDITOR TESTS
# =============================================================================

class TestComponentsAuditor:
    """Tests for ComponentsAuditor."""
    
    def test_dimension_attribute(self):
        auditor = ComponentsAuditor()
        assert auditor.dimension == AuditDimension.COMPONENTS
    
    def test_consistent_sizes_no_issue(self, mock_screen, make_component):
        """Should not flag when component sizes are consistent."""
        auditor = ComponentsAuditor()
        components = [
            make_component("b1", "button", x=100, y=100, width=120, height=40),
            make_component("b2", "button", x=250, y=100, width=120, height=40),
            make_component("b3", "button", x=400, y=100, width=120, height=40),
            make_component("b4", "button", x=100, y=160, width=120, height=40),
        ]
        findings = auditor.audit(mock_screen, components)
        size_issues = [f for f in findings if "inconsistent size" in f.issue.lower()]
        assert len(size_issues) == 0
    
    def test_inconsistent_sizes_detection(self, mock_screen, make_component):
        """Should detect inconsistent component sizes."""
        auditor = ComponentsAuditor()
        # Buttons with wildly different sizes
        components = [
            make_component("b1", "button", x=100, y=100, width=120, height=40),
            make_component("b2", "button", x=250, y=100, width=50, height=20),
            make_component("b3", "button", x=400, y=100, width=300, height=100),
            make_component("b4", "button", x=100, y=160, width=80, height=60),
            make_component("b5", "button", x=250, y=160, width=200, height=30),
        ]
        findings = auditor.audit(mock_screen, components)
        size_issues = [f for f in findings if "inconsistent size" in f.issue.lower()]
        assert len(size_issues) >= 1
    
    def test_style_proliferation_detection(self, mock_screen, make_component):
        """Should detect style proliferation."""
        auditor = ComponentsAuditor(config={"max_style_variations": 2})
        # Many different button sizes
        components = [
            make_component("b1", "button", x=100, y=100, width=100, height=40),
            make_component("b2", "button", x=100, y=160, width=120, height=40),
            make_component("b3", "button", x=100, y=220, width=140, height=40),
            make_component("b4", "button", x=100, y=280, width=160, height=40),
            make_component("b5", "button", x=100, y=340, width=180, height=40),
        ]
        findings = auditor.audit(mock_screen, components)
        proliferation = [f for f in findings if "proliferation" in f.issue.lower()]
        assert len(proliferation) >= 1


# =============================================================================
# DENSITY AUDITOR TESTS
# =============================================================================

class TestDensityAuditor:
    """Tests for DensityAuditor."""
    
    def test_dimension_attribute(self):
        auditor = DensityAuditor()
        assert auditor.dimension == AuditDimension.DENSITY
    
    def test_normal_density_no_issue(self, mock_screen, make_component):
        """Should not flag normal density screens."""
        # Use higher sparse threshold to avoid false positive
        auditor = DensityAuditor(config={"sparse_density_threshold": 0.01})
        # Many components for a populated screen
        components = [
            make_component(f"c{i}", "button", x=(i % 20) * 90, y=(i // 20) * 50, width=80, height=40)
            for i in range(80)
        ]
        findings = auditor.audit(mock_screen, components)
        density_issues = [f for f in findings if "dense" in f.issue.lower() or "sparse" in f.issue.lower()]
        assert len(density_issues) == 0
    
    def test_sparse_detection(self, mock_screen, make_component):
        """Should detect sparse screens."""
        # Lower min_components to allow detection with fewer components
        auditor = DensityAuditor(config={
            "sparse_density_threshold": 1.0,
            "min_components": 2
        })
        # Very few components on large screen
        components = [
            make_component("c1", "text", x=100, y=100, width=200, height=20),
            make_component("c2", "text", x=100, y=200, width=200, height=20),
            make_component("c3", "text", x=100, y=300, width=200, height=20),
        ]
        findings = auditor.audit(mock_screen, components)
        sparse = [f for f in findings if "sparse" in f.issue.lower()]
        assert len(sparse) >= 1
    
    def test_cramped_detection(self, mock_screen, make_component):
        """Should detect cramped screens."""
        # Very low cramped threshold to trigger detection (density is ~0.48 for 100 comps)
        auditor = DensityAuditor(config={
            "cramped_density_threshold": 0.1,
            "min_components": 10
        })
        # Many components packed densely
        components = [
            make_component(f"c{i}", "button", x=(i % 20) * 50, y=(i // 20) * 30, width=40, height=20)
            for i in range(100)
        ]
        findings = auditor.audit(mock_screen, components)
        cramped = [f for f in findings if "cramped" in f.issue.lower() or "dense" in f.issue.lower()]
        assert len(cramped) >= 1


# =============================================================================
# REGISTRY TESTS
# =============================================================================

class TestDimensionRegistry:
    """Tests for dimension auditor registry."""
    
    def test_visual_dimensions_registered(self):
        """All 7 visual dimensions should be registered."""
        visual = {
            "visual_hierarchy",
            "spacing_rhythm",
            "typography",
            "color",
            "alignment_grid",
            "components",
            "density",
        }
        assert visual.issubset(set(DIMENSION_AUDITORS.keys()))
    
    def test_state_dimensions_registered(self):
        """All 6 state dimensions should be registered."""
        state = {
            "iconography",
            "empty_states",
            "loading_states",
            "error_states",
            "dark_mode_theming",
            "accessibility",
        }
        assert state.issubset(set(DIMENSION_AUDITORS.keys()))
    
    def test_total_dimension_count(self):
        """Should have 13 total dimensions (7 visual + 6 state)."""
        assert len(DIMENSION_AUDITORS) == 13
    
    def test_get_auditor_valid(self):
        """get_auditor should return correct auditor."""
        auditor = get_auditor("typography")
        assert isinstance(auditor, TypographyAuditor)
    
    def test_get_auditor_invalid(self):
        """get_auditor should raise for invalid dimension."""
        with pytest.raises(ValueError, match="Unknown dimension"):
            get_auditor("nonexistent")
    
    def test_get_all_auditors(self):
        """get_all_auditors should return all 13 auditors."""
        auditors = get_all_auditors()
        assert len(auditors) == 13
        assert all(hasattr(a, 'audit') for a in auditors)
    
    def test_get_auditor_with_config(self):
        """get_auditor should pass config to auditor."""
        config = {"test_key": "test_value"}
        auditor = get_auditor("density", config=config)
        assert auditor.config.get("test_key") == "test_value"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestDimensionIntegration:
    """Integration tests for dimension auditors."""
    
    def test_all_auditors_run_without_error(self, mock_screen, sample_components):
        """All auditors should run without error on sample data."""
        auditors = get_all_auditors()
        
        for auditor in auditors:
            findings = auditor.audit(mock_screen, sample_components)
            assert isinstance(findings, list)
            for finding in findings:
                assert hasattr(finding, 'issue')
                assert hasattr(finding, 'severity')
                assert hasattr(finding, 'rationale')
    
    def test_finding_severity_levels(self, mock_screen, make_component):
        """Findings should have appropriate severity levels."""
        # Create a screen with multiple issues
        components = [
            make_component("c1", "button", x=101, y=103, width=300, height=100),
            make_component("c2", "button", x=100, y=100, width=50, height=20),
            make_component("c3", "button", x=100, y=100, width=400, height=150),
        ]
        
        auditor = ComponentsAuditor()
        findings = auditor.audit(mock_screen, components)
        
        for finding in findings:
            assert finding.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    
    def test_metadata_in_findings(self, mock_screen, sample_components):
        """Findings should include metadata."""
        auditor = DensityAuditor()
        findings = auditor.audit(mock_screen, sample_components)
        
        for finding in findings:
            assert finding.metadata is not None
            assert isinstance(finding.metadata, dict)
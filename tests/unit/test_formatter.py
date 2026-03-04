"""
Unit tests for instruction formatter (M4-2).

Tests for InstructionFormatter and formatting functions.
"""

import pytest

from src.plan.formatter import (
    InstructionFormatter,
    format_finding,
    format_findings,
    map_to_component,
    determine_file_path,
    generate_changes,
    generate_rationale,
)
from src.plan.instruction_models import IssueType, PropertyChange
from src.plan.templates import InstructionTemplateRegistry, reset_registry
from src.audit.models import AuditFindingCreate, AuditDimension
from src.db.models import EntityType, Severity


# =============================================================================
# COMPONENT MAPPING TESTS
# =============================================================================

class TestMapToComponent:
    """Tests for map_to_component function."""
    
    def test_map_without_registry(self):
        """Test mapping without component registry."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-123",
            dimension=AuditDimension.COLOR,
            issue="Color issue",
        )
        
        component = map_to_component(finding)
        
        assert component.component_id == "btn-123"
        # EntityType.COMPONENT.value returns "Component" (capitalized)
        assert component.component_type == "Component"
        assert component.bounding_box is None
        assert component.selector is None
    
    def test_map_with_registry(self):
        """Test mapping with component registry."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-123",
            dimension=AuditDimension.COLOR,
            issue="Color issue",
        )
        
        registry = {
            "btn-123": {
                "type": "button",
                "bounding_box": (0.1, 0.2, 0.5, 0.3),
                "selector": ".btn-primary",
            }
        }
        
        component = map_to_component(finding, registry)
        
        assert component.component_id == "btn-123"
        assert component.component_type == "button"
        assert component.bounding_box == (0.1, 0.2, 0.5, 0.3)
        assert component.selector == ".btn-primary"
    
    def test_map_with_partial_registry_data(self):
        """Test mapping with partial data in registry."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="input-456",
            dimension=AuditDimension.SPACING_RHYTHM,
            issue="Spacing issue",
        )
        
        registry = {
            "input-456": {
                "type": "input",
            }
        }
        
        component = map_to_component(finding, registry)
        
        assert component.component_type == "input"
        assert component.bounding_box is None


# =============================================================================
# FILE PATH DETERMINATION TESTS
# =============================================================================

class TestDetermineFilePath:
    """Tests for determine_file_path function."""
    
    def test_path_from_metadata(self):
        """Test getting path from metadata."""
        metadata = {"file_path": "components/Button.tsx"}
        path, is_placeholder = determine_file_path("screen-1", metadata)
        
        assert path == "components/Button.tsx"
        assert not is_placeholder
    
    def test_path_from_screen_id_path_like(self):
        """Test getting path from screen_id that looks like path."""
        path, is_placeholder = determine_file_path("views/Home.tsx", None)
        
        assert path == "views/Home.tsx"
        assert not is_placeholder
    
    def test_path_from_screen_id_not_path(self):
        """Test getting path from screen_id that's not a path."""
        path, is_placeholder = determine_file_path("screen-123", None)
        
        assert "screen-123" in path
        assert is_placeholder
    
    def test_path_no_info(self):
        """Test getting path with no information."""
        path, is_placeholder = determine_file_path(None, None)
        
        assert path == "UNKNOWN_FILE"
        assert is_placeholder


# =============================================================================
# CHANGE GENERATION TESTS
# =============================================================================

class TestGenerateChanges:
    """Tests for generate_changes function."""
    
    def test_generate_from_explicit_changes(self):
        """Test generating from explicit changes in metadata."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
            dimension=AuditDimension.COLOR,
            issue="Color issue",
            metadata={
                "changes": [
                    {"property": "color", "old": "#fff", "new": "#000"},
                ]
            }
        )
        
        changes = generate_changes(finding, IssueType.COLOR_CONTRAST)
        
        assert len(changes) == 1
        assert changes[0].property_name == "color"
        assert changes[0].old_value == "#fff"
        assert changes[0].new_value == "#000"
    
    def test_generate_from_single_property(self):
        """Test generating from single property in metadata."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
            dimension=AuditDimension.SPACING_RHYTHM,
            issue="Spacing issue",
            metadata={
                "property": "margin-top",
                "old_value": "8px",
                "new_value": "16px",
            }
        )
        
        changes = generate_changes(finding, IssueType.SPACING)
        
        assert len(changes) == 1
        assert changes[0].property_name == "margin-top"
        assert changes[0].old_value == "8px"
        assert changes[0].new_value == "16px"
    
    def test_generate_spacing_default(self):
        """Test generating default spacing change."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
            dimension=AuditDimension.SPACING_RHYTHM,
            issue="Spacing issue",
        )
        
        changes = generate_changes(finding, IssueType.SPACING)
        
        assert len(changes) == 1
        assert changes[0].property_name == "margin"
        assert changes[0].new_value == "16px"
    
    def test_generate_color_default(self):
        """Test generating default color change."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="text-1",
            dimension=AuditDimension.COLOR,
            issue="Contrast issue",
        )
        
        changes = generate_changes(finding, IssueType.COLOR_CONTRAST)
        
        assert len(changes) == 1
        assert changes[0].property_name == "color"
    
    def test_generate_accessibility_touch_target(self):
        """Test generating accessibility touch target changes."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
            dimension=AuditDimension.ACCESSIBILITY,
            issue="Touch target too small",
            metadata={
                "issue_type": "touch_target",
                "current_height": "32px",
                "current_width": "32px",
            }
        )
        
        changes = generate_changes(finding, IssueType.ACCESSIBILITY)
        
        assert len(changes) == 2
        assert changes[0].property_name == "min-height"
        assert changes[0].new_value == "44px"
        assert changes[1].property_name == "min-width"
        assert changes[1].new_value == "44px"
    
    def test_generate_generic_fallback(self):
        """Test generating generic fallback change."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="elem-1",
            dimension=AuditDimension.DENSITY,
            issue="Density issue",
        )
        
        changes = generate_changes(finding, IssueType.DENSITY)
        
        assert len(changes) == 1


# =============================================================================
# RATIONALE GENERATION TESTS
# =============================================================================

class TestGenerateRationale:
    """Tests for generate_rationale function."""
    
    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset template registry before each test."""
        reset_registry()
        yield
        reset_registry()
    
    def test_uses_finding_rationale(self):
        """Test uses finding's rationale if available."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
            dimension=AuditDimension.COLOR,
            issue="Color issue",
            rationale="This is the custom rationale.",
        )
        
        rationale = generate_rationale(finding, IssueType.COLOR_CONTRAST)
        
        assert rationale == "This is the custom rationale."
    
    def test_generates_from_template(self):
        """Test generates rationale from template."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
            dimension=AuditDimension.SPACING_RHYTHM,
            issue="Spacing issue",
            metadata={
                "property": "margin-top",
                "old_value": "8px",
                "new_value": "16px",
            }
        )
        
        rationale = generate_rationale(finding, IssueType.SPACING)
        
        assert isinstance(rationale, str)
        assert len(rationale) > 0


# =============================================================================
# INSTRUCTION FORMATTER TESTS
# =============================================================================

class TestInstructionFormatter:
    """Tests for InstructionFormatter class."""
    
    @pytest.fixture
    def formatter(self):
        """Create a formatter instance."""
        return InstructionFormatter()
    
    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding."""
        return AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="btn-submit",
            dimension=AuditDimension.COLOR,
            issue="Insufficient contrast ratio",
            rationale="Text contrast is 2.5:1, minimum required is 4.5:1",
            severity=Severity.HIGH,
            metadata={
                "property": "color",
                "old_value": "#999999",
                "new_value": "#333333",
            }
        )
    
    def test_format_instruction_success(self, formatter, sample_finding):
        """Test successful instruction formatting."""
        result = formatter.format_instruction(sample_finding)
        
        assert result.is_valid
        assert result.instruction is not None
        assert result.instruction.finding_id == "btn-submit"
        assert result.instruction.issue_type == IssueType.COLOR_CONTRAST
    
    def test_format_instruction_with_screen_id(self, formatter, sample_finding):
        """Test formatting with screen ID."""
        result = formatter.format_instruction(sample_finding, screen_id="screen-123")
        
        assert result.is_valid
        assert "screen-123" in result.instruction.file_path
    
    def test_format_instruction_with_metadata(self, sample_finding):
        """Test formatting with screen metadata."""
        formatter = InstructionFormatter(
            screen_metadata={"file_path": "components/Form.tsx"}
        )
        result = formatter.format_instruction(sample_finding)
        
        assert result.is_valid
        assert result.instruction.file_path == "components/Form.tsx"
        assert not result.instruction.is_placeholder_path
    
    def test_format_all(self, formatter):
        """Test formatting multiple findings."""
        findings = [
            AuditFindingCreate(
                entity_type=EntityType.COMPONENT,
                entity_id="btn-1",
                dimension=AuditDimension.COLOR,
                issue="Color issue 1",
            ),
            AuditFindingCreate(
                entity_type=EntityType.COMPONENT,
                entity_id="btn-2",
                dimension=AuditDimension.SPACING_RHYTHM,
                issue="Spacing issue 1",
            ),
        ]
        
        batch = formatter.format_all(findings)
        
        assert batch.total_findings == 2
        assert batch.valid_count == 2
        assert len(batch.instructions) == 2
    
    def test_format_all_empty(self, formatter):
        """Test formatting empty findings list."""
        batch = formatter.format_all([])
        
        assert batch.total_findings == 0
        assert batch.valid_count == 0
    
    def test_set_screen_metadata(self, formatter, sample_finding):
        """Test updating screen metadata."""
        formatter.format_instruction(sample_finding)
        formatter.set_screen_metadata({"file_path": "New.tsx"})
        
        result = formatter.format_instruction(sample_finding)
        assert result.instruction.file_path == "New.tsx"
    
    def test_set_component_registry(self, sample_finding):
        """Test using component registry."""
        formatter = InstructionFormatter(
            component_registry={
                "btn-submit": {
                    "type": "button",
                    "selector": ".submit-btn",
                }
            }
        )
        
        result = formatter.format_instruction(sample_finding)
        
        assert result.instruction.component.component_type == "button"
        assert result.instruction.component.selector == ".submit-btn"


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_format_finding(self):
        """Test format_finding convenience function."""
        finding = AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id="test-1",
            dimension=AuditDimension.COLOR,
            issue="Test issue",
        )
        
        result = format_finding(finding)
        
        assert result.is_valid
        assert result.instruction is not None
    
    def test_format_findings(self):
        """Test format_findings convenience function."""
        findings = [
            AuditFindingCreate(
                entity_type=EntityType.COMPONENT,
                entity_id="test-1",
                dimension=AuditDimension.COLOR,
                issue="Issue 1",
            ),
            AuditFindingCreate(
                entity_type=EntityType.COMPONENT,
                entity_id="test-2",
                dimension=AuditDimension.SPACING_RHYTHM,
                issue="Issue 2",
            ),
        ]
        
        batch = format_findings(findings)
        
        assert batch.total_findings == 2
        assert batch.valid_count == 2
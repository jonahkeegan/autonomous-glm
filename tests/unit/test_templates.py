"""
Unit tests for instruction templates (M4-2).

Tests for InstructionTemplateRegistry and template rendering.
"""

import pytest

from src.plan.instruction_models import IssueType, InstructionTemplate
from src.plan.templates import (
    InstructionTemplateRegistry,
    get_default_registry,
    reset_registry,
    _get_builtin_templates,
)


# =============================================================================
# BUILTIN TEMPLATES TESTS
# =============================================================================

class TestBuiltinTemplates:
    """Tests for built-in templates."""
    
    def test_get_builtin_templates_not_empty(self):
        """Test that built-in templates exist."""
        templates = _get_builtin_templates()
        assert len(templates) > 0
    
    def test_all_issue_types_have_templates(self):
        """Test that all issue types have at least one template."""
        templates = _get_builtin_templates()
        
        # Group by issue type
        by_type = {}
        for t in templates:
            if t.issue_type not in by_type:
                by_type[t.issue_type] = []
            by_type[t.issue_type].append(t)
        
        # Check key types
        key_types = [
            IssueType.SPACING,
            IssueType.COLOR_CONTRAST,
            IssueType.TYPOGRAPHY,
            IssueType.ACCESSIBILITY,
            IssueType.GENERIC,
        ]
        for issue_type in key_types:
            assert issue_type in by_type, f"No template for {issue_type}"
    
    def test_generic_template_exists(self):
        """Test that generic fallback template exists."""
        templates = _get_builtin_templates()
        generic = [t for t in templates if t.name == "generic"]
        assert len(generic) == 1
        assert generic[0].fallback


# =============================================================================
# TEMPLATE REGISTRY TESTS
# =============================================================================

class TestInstructionTemplateRegistry:
    """Tests for InstructionTemplateRegistry."""
    
    @pytest.fixture(autouse=True)
    def reset_default_registry(self):
        """Reset default registry before each test."""
        reset_registry()
        yield
        reset_registry()
    
    def test_init_with_builtins(self):
        """Test registry initializes with built-in templates."""
        registry = InstructionTemplateRegistry()
        templates = registry.list_templates()
        assert len(templates) > 0
        assert "generic" in templates
    
    def test_init_with_custom_templates(self):
        """Test registry with custom templates."""
        custom = InstructionTemplate(
            name="custom_test",
            issue_type=IssueType.GENERIC,
            template="Custom: {value}",
            placeholders=["value"],
        )
        registry = InstructionTemplateRegistry(templates=[custom])
        
        assert registry.get_template("custom_test") is not None
    
    def test_register_template(self):
        """Test registering a new template."""
        registry = InstructionTemplateRegistry()
        template = InstructionTemplate(
            name="my_template",
            issue_type=IssueType.SPACING,
            template="Test {x}",
            placeholders=["x"],
        )
        
        registry.register(template)
        
        assert registry.get_template("my_template") == template
    
    def test_get_template_found(self):
        """Test getting an existing template."""
        registry = InstructionTemplateRegistry()
        template = registry.get_template("spacing_issue")
        assert template is not None
        assert template.name == "spacing_issue"
    
    def test_get_template_not_found(self):
        """Test getting a non-existent template."""
        registry = InstructionTemplateRegistry()
        template = registry.get_template("nonexistent")
        assert template is None
    
    def test_get_templates_for_issue_type(self):
        """Test getting templates by issue type."""
        registry = InstructionTemplateRegistry()
        
        spacing_templates = registry.get_templates_for_issue_type(IssueType.SPACING)
        assert len(spacing_templates) > 0
        
        for t in spacing_templates:
            assert t.issue_type == IssueType.SPACING
    
    def test_get_best_template_with_context(self):
        """Test getting best template matching context."""
        registry = InstructionTemplateRegistry()
        
        context = {
            "property": "margin",
            "old": "12px",
            "new": "16px",
        }
        
        template = registry.get_best_template(IssueType.SPACING, context)
        assert template is not None
        assert template.issue_type == IssueType.SPACING
    
    def test_get_best_template_fallback(self):
        """Test fallback when no template matches context."""
        registry = InstructionTemplateRegistry()
        
        # Empty context - should still return a template
        template = registry.get_best_template(IssueType.SPACING, {})
        assert template is not None
    
    def test_render_named_template(self):
        """Test rendering a template by name."""
        registry = InstructionTemplateRegistry()
        
        result = registry.render(
            "spacing_cramped",
            property="margin-top",
            old="8px",
            new="16px",
        )
        
        assert "margin-top" in result
        assert "8px" in result
        assert "16px" in result
    
    def test_render_missing_template(self):
        """Test rendering a non-existent template."""
        registry = InstructionTemplateRegistry()
        
        with pytest.raises(ValueError) as exc_info:
            registry.render("nonexistent", x=1)
        assert "not found" in str(exc_info.value)
    
    def test_render_for_issue_success(self):
        """Test rendering best template for issue type."""
        registry = InstructionTemplateRegistry()
        
        context = {
            "property": "margin",
            "old": "8px",
            "new": "16px",
            "element": "container",
            "rationale": "Too cramped",
        }
        
        result = registry.render_for_issue(IssueType.SPACING, context)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_render_for_issue_with_defaults(self):
        """Test rendering fills in defaults for missing placeholders."""
        registry = InstructionTemplateRegistry()
        
        # Minimal context
        context = {
            "property": "margin",
            "old": "8px",
            "new": "16px",
        }
        
        # Should not raise - defaults filled in
        result = registry.render_for_issue(IssueType.SPACING, context)
        assert isinstance(result, str)
    
    def test_list_templates(self):
        """Test listing all template names."""
        registry = InstructionTemplateRegistry()
        names = registry.list_templates()
        
        assert "generic" in names
        assert "spacing_issue" in names
        assert "color_contrast" in names
    
    def test_list_templates_for_issue_type(self):
        """Test listing template names for specific issue type."""
        registry = InstructionTemplateRegistry()
        names = registry.list_templates_for_issue_type(IssueType.SPACING)
        
        assert len(names) > 0
        assert "spacing_issue" in names or "spacing_cramped" in names


# =============================================================================
# MODULE-LEVEL REGISTRY TESTS
# =============================================================================

class TestDefaultRegistry:
    """Tests for module-level default registry."""
    
    @pytest.fixture(autouse=True)
    def reset_registry_fixture(self):
        """Reset registry before and after each test."""
        reset_registry()
        yield
        reset_registry()
    
    def test_get_default_registry_creates_once(self):
        """Test that default registry is created once."""
        registry1 = get_default_registry()
        registry2 = get_default_registry()
        
        assert registry1 is registry2
    
    def test_reset_registry(self):
        """Test resetting the default registry."""
        registry1 = get_default_registry()
        reset_registry()
        registry2 = get_default_registry()
        
        # They should be different objects after reset
        assert registry1 is not registry2


# =============================================================================
# TEMPLATE RENDERING EDGE CASES
# =============================================================================

class TestTemplateRendering:
    """Tests for template rendering edge cases."""
    
    def test_render_with_extra_placeholders(self):
        """Test rendering ignores extra placeholders."""
        registry = InstructionTemplateRegistry()
        
        result = registry.render(
            "spacing_cramped",
            property="margin",
            old="8px",
            new="16px",
            extra="ignored",  # Not in template
        )
        
        assert "margin" in result
        assert "ignored" not in result
    
    def test_render_generic_template(self):
        """Test rendering the generic fallback template."""
        registry = InstructionTemplateRegistry()
        
        result = registry.render(
            "generic",
            property="style",
            old="current",
            new="proposed",
            element="button",
            rationale="Test rationale",
        )
        
        assert "style" in result
        assert "button" in result
    
    def test_render_accessibility_template(self):
        """Test rendering an accessibility template."""
        registry = InstructionTemplateRegistry()
        
        result = registry.render(
            "accessibility_touch_target",
            element="button",
            current="32x32px",
            criterion="2.5.5",
        )
        
        assert "button" in result
        assert "44x44px" in result
        assert "2.5.5" in result
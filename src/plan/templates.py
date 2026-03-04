"""
Instruction template registry and rendering.

Provides simple string templates for generating instruction rationale
text from audit findings. Uses Python's built-in .format() for
placeholder substitution.
"""

from typing import Optional

from src.plan.instruction_models import IssueType, InstructionTemplate


# =============================================================================
# BUILT-IN TEMPLATES
# =============================================================================

def _get_builtin_templates() -> list[InstructionTemplate]:
    """Return all built-in instruction templates.
    
    Templates are organized by issue type and include:
    - Placeholders needed for rendering
    - Clear, actionable language
    - Standards-aware context
    """
    return [
        # Spacing templates
        InstructionTemplate(
            name="spacing_issue",
            issue_type=IssueType.SPACING,
            template="Adjust {property} from {old} to {new} to establish consistent {spacing_type} rhythm. Current value breaks the {grid} grid system.",
            placeholders=["property", "old", "new", "spacing_type", "grid"],
        ),
        InstructionTemplate(
            name="spacing_cramped",
            issue_type=IssueType.SPACING,
            template="Increase {property} from {old} to {new}. Elements feel cramped with current spacing, affecting readability and touch targets.",
            placeholders=["property", "old", "new"],
        ),
        InstructionTemplate(
            name="spacing_inconsistent",
            issue_type=IssueType.SPACING,
            template="Standardize {property} to {new} for consistency. Current value ({old}) differs from surrounding elements using {expected}.",
            placeholders=["property", "old", "new", "expected"],
        ),
        
        # Color/contrast templates
        InstructionTemplate(
            name="color_contrast",
            issue_type=IssueType.COLOR_CONTRAST,
            template="Change {element} color from {old} to {new} to achieve {ratio}:1 contrast ratio (minimum {required}:1 required for {text_type} text per WCAG {criterion}).",
            placeholders=["element", "old", "new", "ratio", "required", "text_type", "criterion"],
        ),
        InstructionTemplate(
            name="color_inconsistent",
            issue_type=IssueType.COLOR_CONTRAST,
            template="Use design token {token} instead of hardcoded value {old} for {element}. This ensures consistency and enables theming support.",
            placeholders=["token", "old", "element"],
        ),
        InstructionTemplate(
            name="color_accessibility",
            issue_type=IssueType.COLOR_CONTRAST,
            template="Insufficient contrast detected: {old} against {background} yields {ratio}:1. Change to {new} to meet WCAG {level} requirements ({required}:1 minimum).",
            placeholders=["old", "background", "ratio", "new", "level", "required"],
        ),
        
        # Typography templates
        InstructionTemplate(
            name="typography_size",
            issue_type=IssueType.TYPOGRAPHY,
            template="Update {property} from {old} to {new}. Current size {issue_description}.",
            placeholders=["property", "old", "new", "issue_description"],
        ),
        InstructionTemplate(
            name="typography_hierarchy",
            issue_type=IssueType.TYPOGRAPHY,
            template="Establish clear type hierarchy by changing {element} {property} from {old} to {new}. {rationale}.",
            placeholders=["element", "property", "old", "new", "rationale"],
        ),
        InstructionTemplate(
            name="typography_inconsistent",
            issue_type=IssueType.TYPOGRAPHY,
            template="Use typography token {token} ({value}) instead of {old} for consistent {property} across {element}.",
            placeholders=["token", "value", "old", "property", "element"],
        ),
        
        # Alignment templates
        InstructionTemplate(
            name="alignment_grid",
            issue_type=IssueType.ALIGNMENT,
            template="Align {element} to the {grid} grid. Current position ({current}) is off-grid by {offset}.",
            placeholders=["element", "grid", "current", "offset"],
        ),
        InstructionTemplate(
            name="alignment_inconsistent",
            issue_type=IssueType.ALIGNMENT,
            template="Adjust {property} from {old} to {new} to match alignment of {reference_element}.",
            placeholders=["property", "old", "new", "reference_element"],
        ),
        
        # Hierarchy templates
        InstructionTemplate(
            name="hierarchy_weight",
            issue_type=IssueType.HIERARCHY,
            template="Increase visual weight of {element} by changing {property} from {old} to {new}. This element should be more prominent to guide user attention.",
            placeholders=["element", "property", "old", "new"],
        ),
        InstructionTemplate(
            name="hierarchy_competing",
            issue_type=IssueType.HIERARCHY,
            template="Reduce visual prominence of {element} by changing {property} from {old} to {new}. Multiple elements are competing for attention.",
            placeholders=["element", "property", "old", "new"],
        ),
        InstructionTemplate(
            name="hierarchy_focal",
            issue_type=IssueType.HIERARCHY,
            template="Establish clear focal point on {primary_element}. Reduce {property} of {secondary_element} from {old} to {new}.",
            placeholders=["primary_element", "property", "secondary_element", "old", "new"],
        ),
        
        # Accessibility templates
        InstructionTemplate(
            name="accessibility_touch_target",
            issue_type=IssueType.ACCESSIBILITY,
            template="Increase touch target size for {element} to minimum 44x44px. Current size: {current}. WCAG {criterion} requires adequate touch targets for motor-impaired users.",
            placeholders=["element", "current", "criterion"],
        ),
        InstructionTemplate(
            name="accessibility_focus",
            issue_type=IssueType.ACCESSIBILITY,
            template="Add visible focus indicator to {element}. Current implementation lacks focus state, failing WCAG {criterion} (Focus Visible).",
            placeholders=["element", "criterion"],
        ),
        InstructionTemplate(
            name="accessibility_label",
            issue_type=IssueType.ACCESSIBILITY,
            template="Add accessible label to {element}. {rationale} WCAG {criterion} requires {requirement}.",
            placeholders=["element", "rationale", "criterion", "requirement"],
        ),
        InstructionTemplate(
            name="accessibility_aria",
            issue_type=IssueType.ACCESSIBILITY,
            template="Add {aria_attribute}=\"{value}\" to {element}. {rationale}",
            placeholders=["aria_attribute", "value", "element", "rationale"],
        ),
        
        # Component templates
        InstructionTemplate(
            name="component_inconsistent",
            issue_type=IssueType.COMPONENTS,
            template="Standardize {component_type} styling. {element} uses {old} while other {component_type}s use {new}.",
            placeholders=["component_type", "element", "old", "new"],
        ),
        InstructionTemplate(
            name="component_variant",
            issue_type=IssueType.COMPONENTS,
            template="Use {variant} variant for {element} instead of current implementation. {rationale}.",
            placeholders=["variant", "element", "rationale"],
        ),
        
        # Density templates
        InstructionTemplate(
            name="density_sparse",
            issue_type=IssueType.DENSITY,
            template="Reduce whitespace in {area}. Current density ({current}) feels sparse. Consider {suggestion} to improve visual balance.",
            placeholders=["area", "current", "suggestion"],
        ),
        InstructionTemplate(
            name="density_cramped",
            issue_type=IssueType.DENSITY,
            template="Increase spacing in {area}. Current density ({current}) feels cramped. Add {suggestion} to improve readability.",
            placeholders=["area", "current", "suggestion"],
        ),
        
        # Iconography templates
        InstructionTemplate(
            name="iconography_size",
            issue_type=IssueType.ICONOGRAPHY,
            template="Standardize icon size to {new}. Current icon in {element} is {old}, inconsistent with design system.",
            placeholders=["new", "element", "old"],
        ),
        InstructionTemplate(
            name="iconography_clarity",
            issue_type=IssueType.ICONOGRAPHY,
            template="Improve icon clarity in {element}. {rationale} Consider using {suggestion}.",
            placeholders=["element", "rationale", "suggestion"],
        ),
        
        # State templates
        InstructionTemplate(
            name="empty_state",
            issue_type=IssueType.EMPTY_STATES,
            template="Add empty state design for {context}. {rationale} Include helpful guidance for users.",
            placeholders=["context", "rationale"],
        ),
        InstructionTemplate(
            name="loading_state",
            issue_type=IssueType.LOADING_STATES,
            template="Add loading indicator for {context}. {rationale} Use consistent loading pattern from design system.",
            placeholders=["context", "rationale"],
        ),
        InstructionTemplate(
            name="error_state",
            issue_type=IssueType.ERROR_STATES,
            template="Improve error messaging for {context}. {rationale} Ensure error is helpful and actionable.",
            placeholders=["context", "rationale"],
        ),
        
        # Theming templates
        InstructionTemplate(
            name="theming_dark_mode",
            issue_type=IssueType.THEMING,
            template="Add dark mode support for {element}. Use semantic token {token} instead of hardcoded {old}.",
            placeholders=["element", "token", "old"],
        ),
        InstructionTemplate(
            name="theming_semantic",
            issue_type=IssueType.THEMING,
            template="Replace hardcoded value {old} with semantic token {token} in {element}. This enables proper theming support.",
            placeholders=["old", "token", "element"],
        ),
        
        # Generic fallback template
        InstructionTemplate(
            name="generic",
            issue_type=IssueType.GENERIC,
            template="Change {property} from {old} to {new} in {element}. {rationale}",
            placeholders=["property", "old", "new", "element", "rationale"],
            fallback=True,
        ),
        InstructionTemplate(
            name="generic_simple",
            issue_type=IssueType.GENERIC,
            template="Update {element}: {description}",
            placeholders=["element", "description"],
            fallback=True,
        ),
    ]


# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

class InstructionTemplateRegistry:
    """Registry for instruction templates.
    
    Provides template lookup by issue type and name, with fallback
    to generic templates when specific templates aren't available.
    """
    
    def __init__(self, templates: Optional[list[InstructionTemplate]] = None):
        """Initialize registry with templates.
        
        Args:
            templates: List of templates to register. Uses built-ins if None.
        """
        self._templates: dict[str, InstructionTemplate] = {}
        self._by_issue_type: dict[IssueType, list[InstructionTemplate]] = {}
        
        # Load templates
        templates_to_load = templates if templates is not None else _get_builtin_templates()
        for template in templates_to_load:
            self.register(template)
    
    def register(self, template: InstructionTemplate) -> None:
        """Register a template.
        
        Args:
            template: Template to register
        """
        self._templates[template.name] = template
        
        if template.issue_type not in self._by_issue_type:
            self._by_issue_type[template.issue_type] = []
        self._by_issue_type[template.issue_type].append(template)
    
    def get_template(self, name: str) -> Optional[InstructionTemplate]:
        """Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template if found, None otherwise
        """
        return self._templates.get(name)
    
    def get_templates_for_issue_type(
        self, 
        issue_type: IssueType
    ) -> list[InstructionTemplate]:
        """Get all templates for an issue type.
        
        Args:
            issue_type: Issue type to get templates for
            
        Returns:
            List of templates (may be empty)
        """
        return self._by_issue_type.get(issue_type, [])
    
    def get_best_template(
        self, 
        issue_type: IssueType,
        context: Optional[dict] = None
    ) -> InstructionTemplate:
        """Get the best template for an issue type given context.
        
        Prefers specific templates over fallbacks. Returns first matching
        template whose placeholders can be satisfied by context.
        
        Args:
            issue_type: Issue type to get template for
            context: Optional context dict to match against placeholders
            
        Returns:
            Best matching template (falls back to generic if needed)
        """
        templates = self.get_templates_for_issue_type(issue_type)
        
        if context:
            # Try to find a template whose placeholders are all in context
            for template in templates:
                if not template.fallback:
                    missing = template.validate_context(context)
                    if not missing:
                        return template
        
        # Fall back to first non-fallback template for issue type
        for template in templates:
            if not template.fallback:
                return template
        
        # Fall back to any template for issue type
        if templates:
            return templates[0]
        
        # Ultimate fallback to generic
        generic = self.get_template("generic")
        if generic:
            return generic
        
        # This should never happen if built-ins are loaded
        raise ValueError("No templates available, including fallback")
    
    def render(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """Render a named template with provided values.
        
        Args:
            template_name: Name of template to render
            **kwargs: Values for template placeholders
            
        Returns:
            Rendered string
            
        Raises:
            ValueError: If template not found or placeholders missing
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        return template.render(**kwargs)
    
    def render_for_issue(
        self,
        issue_type: IssueType,
        context: dict
    ) -> str:
        """Render the best template for an issue type.
        
        Args:
            issue_type: Issue type
            context: Values for template placeholders
            
        Returns:
            Rendered string
            
        Raises:
            ValueError: If required placeholders are missing
        """
        template = self.get_best_template(issue_type, context)
        
        # Check for missing placeholders
        missing = template.validate_context(context)
        if missing:
            # Try to fill in common defaults
            extended_context = self._fill_defaults(context, missing)
            missing = template.validate_context(extended_context)
            if missing:
                raise ValueError(
                    f"Missing required placeholders for template '{template.name}': {missing}"
                )
            context = extended_context
        
        return template.render(**context)
    
    def _fill_defaults(self, context: dict, missing: list[str]) -> dict:
        """Fill in common default values for missing placeholders.
        
        Args:
            context: Current context
            missing: List of missing placeholder names
            
        Returns:
            Extended context with defaults filled
        """
        defaults = {
            "element": "element",
            "property": "value",
            "old": "current",
            "new": "proposed",
            "rationale": "This improves consistency and usability",
            "criterion": "2.1",
            "level": "AA",
            "grid": "8px",
        }
        
        extended = dict(context)
        for key in missing:
            if key in defaults:
                extended[key] = defaults[key]
        
        return extended
    
    def list_templates(self) -> list[str]:
        """List all registered template names.
        
        Returns:
            List of template names
        """
        return list(self._templates.keys())
    
    def list_templates_for_issue_type(self, issue_type: IssueType) -> list[str]:
        """List template names for an issue type.
        
        Args:
            issue_type: Issue type to list templates for
            
        Returns:
            List of template names
        """
        templates = self._by_issue_type.get(issue_type, [])
        return [t.name for t in templates]


# =============================================================================
# MODULE-LEVEL REGISTRY INSTANCE
# =============================================================================

# Default registry instance with built-in templates
_default_registry: Optional[InstructionTemplateRegistry] = None


def get_default_registry() -> InstructionTemplateRegistry:
    """Get the default template registry.
    
    Creates registry on first access (lazy initialization).
    
    Returns:
        Default InstructionTemplateRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = InstructionTemplateRegistry()
    return _default_registry


def reset_registry() -> None:
    """Reset the default registry (useful for testing)."""
    global _default_registry
    _default_registry = None
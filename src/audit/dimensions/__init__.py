"""
Visual audit dimension auditors.

This package contains dimension-specific auditors that analyze
screens and components for visual design issues.

Available Dimensions (Visual - M3-3):
- visual_hierarchy: Prominence and eye-flow analysis
- spacing_rhythm: Whitespace consistency and vertical rhythm
- typography: Font size hierarchy and weight consistency
- color: Color palette, contrast, and cohesion
- alignment_grid: Grid alignment and positioning
- components: Component consistency and style proliferation
- density: Information density and whitespace sufficiency

Available Dimensions (State & Accessibility - M3-4):
- iconography: Icon size consistency and position patterns
- empty_states: Empty state design and user guidance
- loading_states: Loading indicator consistency
- error_states: Error message styling and helpfulness
- theming: Dark mode / theme contrast validation
- accessibility: WCAG contrast, text size, touch targets
"""

from src.audit.dimensions.base import (
    BaseAuditor,
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
    get_components_in_region,
    calculate_density,
)

from src.audit.dimensions.visual_hierarchy import (
    VisualHierarchyAuditor,
    audit_visual_hierarchy,
)

from src.audit.dimensions.spacing import (
    SpacingRhythmAuditor,
    audit_spacing_rhythm,
)

from src.audit.dimensions.typography import (
    TypographyAuditor,
    audit_typography,
)

from src.audit.dimensions.color import (
    ColorAuditor,
    audit_color,
)

from src.audit.dimensions.alignment import (
    AlignmentGridAuditor,
    audit_alignment_grid,
)

from src.audit.dimensions.components import (
    ComponentsAuditor,
    audit_components,
)

from src.audit.dimensions.density import (
    DensityAuditor,
    audit_density,
)

# State & Accessibility Dimensions (M3-4)
from src.audit.dimensions.iconography import (
    IconographyAuditor,
    audit_iconography,
)

from src.audit.dimensions.empty_states import (
    EmptyStatesAuditor,
    audit_empty_states,
)

from src.audit.dimensions.loading_states import (
    LoadingStatesAuditor,
    audit_loading_states,
)

from src.audit.dimensions.error_states import (
    ErrorStatesAuditor,
    audit_error_states,
)

from src.audit.dimensions.theming import (
    ThemingAuditor,
    audit_theming,
)

from src.audit.dimensions.accessibility import (
    AccessibilityAuditor,
    audit_accessibility,
)


# Dimension auditor registry
DIMENSION_AUDITORS = {
    # Visual Dimensions (M3-3)
    "visual_hierarchy": VisualHierarchyAuditor,
    "spacing_rhythm": SpacingRhythmAuditor,
    "typography": TypographyAuditor,
    "color": ColorAuditor,
    "alignment_grid": AlignmentGridAuditor,
    "components": ComponentsAuditor,
    "density": DensityAuditor,
    # State & Accessibility Dimensions (M3-4)
    "iconography": IconographyAuditor,
    "empty_states": EmptyStatesAuditor,
    "loading_states": LoadingStatesAuditor,
    "error_states": ErrorStatesAuditor,
    "dark_mode_theming": ThemingAuditor,
    "accessibility": AccessibilityAuditor,
}


def get_auditor(dimension: str, config: dict | None = None):
    """Get an auditor instance for a dimension.
    
    Args:
        dimension: Dimension name
        config: Optional configuration
        
    Returns:
        Auditor instance
        
    Raises:
        ValueError: If dimension not found
    """
    if dimension not in DIMENSION_AUDITORS:
        raise ValueError(f"Unknown dimension: {dimension}")
    
    return DIMENSION_AUDITORS[dimension](config=config)


def get_all_auditors(config: dict | None = None) -> list:
    """Get all dimension auditor instances.
    
    Args:
        config: Optional configuration applied to all
        
    Returns:
        List of auditor instances
    """
    return [cls(config=config) for cls in DIMENSION_AUDITORS.values()]


__all__ = [
    # Base
    "BaseAuditor",
    "calculate_distance",
    "get_bbox_center",
    "get_bbox_area",
    "bboxes_overlap",
    "bbox_contains",
    "quantize_to_grid",
    "is_on_grid",
    "calculate_contrast_ratio",
    "rgb_to_luminance",
    "group_by_type",
    "get_components_in_region",
    "calculate_density",
    # Visual Dimensions (M3-3)
    "VisualHierarchyAuditor",
    "audit_visual_hierarchy",
    "SpacingRhythmAuditor",
    "audit_spacing_rhythm",
    "TypographyAuditor",
    "audit_typography",
    "ColorAuditor",
    "audit_color",
    "AlignmentGridAuditor",
    "audit_alignment_grid",
    "ComponentsAuditor",
    "audit_components",
    "DensityAuditor",
    "audit_density",
    # State & Accessibility Dimensions (M3-4)
    "IconographyAuditor",
    "audit_iconography",
    "EmptyStatesAuditor",
    "audit_empty_states",
    "LoadingStatesAuditor",
    "audit_loading_states",
    "ErrorStatesAuditor",
    "audit_error_states",
    "ThemingAuditor",
    "audit_theming",
    "AccessibilityAuditor",
    "audit_accessibility",
    # Registry
    "DIMENSION_AUDITORS",
    "get_auditor",
    "get_all_auditors",
]

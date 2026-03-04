"""
Visual audit dimension auditors.

This package contains dimension-specific auditors that analyze
screens and components for visual design issues.

Available Dimensions:
- visual_hierarchy: Prominence and eye-flow analysis
- spacing_rhythm: Whitespace consistency and vertical rhythm
- typography: Font size hierarchy and weight consistency
- color: Color palette, contrast, and cohesion
- alignment_grid: Grid alignment and positioning
- components: Component consistency and style proliferation
- density: Information density and whitespace sufficiency
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


# Dimension auditor registry
DIMENSION_AUDITORS = {
    "visual_hierarchy": VisualHierarchyAuditor,
    "spacing_rhythm": SpacingRhythmAuditor,
    "typography": TypographyAuditor,
    "color": ColorAuditor,
    "alignment_grid": AlignmentGridAuditor,
    "components": ComponentsAuditor,
    "density": DensityAuditor,
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
    # Visual Hierarchy
    "VisualHierarchyAuditor",
    "audit_visual_hierarchy",
    # Spacing & Rhythm
    "SpacingRhythmAuditor",
    "audit_spacing_rhythm",
    # Typography
    "TypographyAuditor",
    "audit_typography",
    # Color
    "ColorAuditor",
    "audit_color",
    # Alignment & Grid
    "AlignmentGridAuditor",
    "audit_alignment_grid",
    # Components
    "ComponentsAuditor",
    "audit_components",
    # Density
    "DensityAuditor",
    "audit_density",
    # Registry
    "DIMENSION_AUDITORS",
    "get_auditor",
    "get_all_auditors",
]
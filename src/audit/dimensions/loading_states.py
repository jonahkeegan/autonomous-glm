"""
Loading States auditor for analyzing loading indicators.

Analyzes:
- Skeleton screens/spinners consistent
- App feels alive while waiting
- Loading state patterns are followed
"""

from typing import Any, Optional
from collections import Counter

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_center,
    get_bbox_area,
    group_by_type,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Component types that indicate loading state
    "loading_hint_types": ["image", "container"],
    # Properties that suggest loading state
    "loading_property_hints": ["skeleton", "shimmer", "loading", "spinner", "progress"],
    # Minimum components to consider screen as loading state
    "min_loading_components": 1,
    # Maximum ratio of loading components to total before it's a skeleton screen
    "skeleton_ratio_threshold": 0.7,
    # Expected loading indicator position (centered)
    "centered_threshold": 0.25,  # Within 25% of center
}


# =============================================================================
# LOADING STATES AUDITOR
# =============================================================================

class LoadingStatesAuditor(BaseAuditor):
    """Auditor for loading states dimension.
    
    Analyzes loading indicators and skeleton screens.
    """
    
    dimension = AuditDimension.LOADING_STATES
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run loading states audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of loading state findings
        """
        findings = []
        
        # Get screen dimensions
        screen_width = getattr(screen, 'width', 1920)
        screen_height = getattr(screen, 'height', 1080)
        
        # Detect loading-related components
        loading_components = self._detect_loading_components(components)
        
        if not loading_components:
            return findings
        
        # Check 1: Loading indicator positioning
        position_finding = self._check_loading_position(
            loading_components, screen.id, screen_width, screen_height
        )
        if position_finding:
            findings.append(position_finding)
        
        # Check 2: Skeleton screen consistency
        skeleton_finding = self._check_skeleton_consistency(
            components, loading_components, screen.id
        )
        if skeleton_finding:
            findings.append(skeleton_finding)
        
        # Check 3: Multiple loading indicators
        multiple_finding = self._check_multiple_indicators(
            loading_components, screen.id
        )
        if multiple_finding:
            findings.append(multiple_finding)
        
        return findings
    
    def _detect_loading_components(
        self,
        components: list[Component],
    ) -> list[Component]:
        """Detect components that appear to be loading indicators.
        
        Args:
            components: List of all components
            
        Returns:
            List of loading-related components
        """
        loading_hints = self.config["loading_property_hints"]
        loading_components = []
        
        for comp in components:
            # Check component properties for loading hints
            props_str = str(comp.properties).lower()
            
            is_loading = any(hint in props_str for hint in loading_hints)
            
            # Also check for typical loading indicator sizes (small squares)
            bbox = comp.bounding_box
            is_square = abs(bbox.width - bbox.height) < max(bbox.width, bbox.height) * 0.2
            is_small = bbox.width < 100 and bbox.height < 100
            
            if is_loading or (is_square and is_small and comp.type == "image"):
                loading_components.append(comp)
        
        return loading_components
    
    def _check_loading_position(
        self,
        loading_components: list[Component],
        screen_id: str,
        screen_width: int,
        screen_height: int,
    ) -> Optional[AuditFindingCreate]:
        """Check if loading indicators are well positioned.
        
        Args:
            loading_components: Loading-related components
            screen_id: Screen ID
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            Finding if loading indicator positioning is problematic
        """
        if not loading_components:
            return None
        
        center_x = screen_width / 2
        center_y = screen_height / 2
        threshold = self.config["centered_threshold"]
        
        # Check if any loading indicator is centered
        centered_count = 0
        for comp in loading_components:
            comp_center = get_bbox_center(comp.bounding_box)
            
            is_centered_x = abs(comp_center[0] - center_x) < screen_width * threshold
            is_centered_y = abs(comp_center[1] - center_y) < screen_height * threshold
            
            if is_centered_x and is_centered_y:
                centered_count += 1
        
        # If we have loading indicators but none are centered
        if len(loading_components) > 0 and centered_count == 0:
            return self.create_finding(
                entity_id=screen_id,
                issue="Loading indicator not centered",
                rationale=(
                    "Loading indicators should typically be centered on screen "
                    "or near the content being loaded. Off-center loading indicators "
                    "can make the interface feel unbalanced."
                ),
                severity=Severity.LOW,
                metadata={
                    "loading_count": len(loading_components),
                    "centered_count": centered_count,
                },
            )
        
        return None
    
    def _check_skeleton_consistency(
        self,
        components: list[Component],
        loading_components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if skeleton screen is consistent.
        
        Args:
            components: All components
            loading_components: Loading-related components
            screen_id: Screen ID
            
        Returns:
            Finding if skeleton screen has consistency issues
        """
        if len(components) < 3:
            return None
        
        # Check if this appears to be a skeleton screen
        loading_ratio = len(loading_components) / len(components)
        
        if loading_ratio < self.config["skeleton_ratio_threshold"]:
            return None
        
        # For skeleton screens, check size consistency
        # Skeleton elements should have consistent spacing and sizing
        sizes = [(c.bounding_box.width, c.bounding_box.height) for c in loading_components]
        
        if len(sizes) < 2:
            return None
        
        # Check width variance
        widths = [s[0] for s in sizes]
        mean_width = sum(widths) / len(widths)
        
        if mean_width == 0:
            return None
        
        width_variance = sum((w - mean_width) ** 2 for w in widths) / len(widths)
        width_cv = (width_variance ** 0.5) / mean_width
        
        if width_cv > 0.5:  # High variance in skeleton widths
            return self.create_finding(
                entity_id=screen_id,
                issue="Inconsistent skeleton screen element sizes",
                rationale=(
                    f"Skeleton screen elements have inconsistent widths (CV: {width_cv:.2f}). "
                    "Consistent skeleton elements create a more polished loading experience "
                    "and better anticipate the actual content layout."
                ),
                severity=Severity.LOW,
                metadata={
                    "width_coefficient_of_variation": width_cv,
                    "element_count": len(sizes),
                },
            )
        
        return None
    
    def _check_multiple_indicators(
        self,
        loading_components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check for multiple loading indicators.
        
        Args:
            loading_components: Loading-related components
            screen_id: Screen ID
            
        Returns:
            Finding if multiple indicators found
        """
        if len(loading_components) <= 3:
            return None
        
        # Multiple loading indicators can be confusing
        # Check if they're spread across the screen (not in a single area)
        if len(loading_components) < 2:
            return None
        
        centers = [get_bbox_center(c.bounding_box) for c in loading_components]
        
        # Calculate spread
        x_coords = [c[0] for c in centers]
        y_coords = [c[1] for c in centers]
        
        x_range = max(x_coords) - min(x_coords) if x_coords else 0
        y_range = max(y_coords) - min(y_coords) if y_coords else 0
        
        # If loading indicators are spread across > 500px in either direction
        if x_range > 500 or y_range > 500:
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Multiple loading indicators detected ({len(loading_components)})",
                rationale=(
                    f"Found {len(loading_components)} loading indicators spread across "
                    f"the screen ({x_range:.0f}px x {y_range:.0f}px). "
                    "Consider using a single loading indicator or skeleton screen "
                    "for a more cohesive loading experience."
                ),
                severity=Severity.LOW,
                metadata={
                    "indicator_count": len(loading_components),
                    "x_spread": x_range,
                    "y_spread": y_range,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_loading_states(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run loading states audit."""
    auditor = LoadingStatesAuditor(config=config)
    return auditor.audit(screen, components)
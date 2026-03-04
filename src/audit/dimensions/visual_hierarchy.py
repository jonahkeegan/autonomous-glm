"""
Visual Hierarchy auditor for analyzing prominence and eye-flow.

Analyzes:
- Most important element is most prominent
- Eye lands where it should (top-left bias, size hierarchy)
- User can understand screen in 2 seconds
"""

from typing import Any, Optional

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_center,
    get_bbox_area,
    get_bbox_center,
    calculate_distance,
    group_by_type,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Minimum area ratio for primary element (primary/total)
    "min_primary_area_ratio": 0.05,
    # Maximum area ratio for competing elements
    "max_competing_ratio": 0.8,
    # Top-left region for expected focal point (percentage from top-left)
    "focal_region_x": 0.4,
    "focal_region_y": 0.4,
    # Minimum components to analyze hierarchy
    "min_components": 3,
    # Weight factors for prominence score
    "size_weight": 0.5,
    "position_weight": 0.3,
    "center_distance_weight": 0.2,
}


# =============================================================================
# VISUAL HIERARCHY AUDITOR
# =============================================================================

class VisualHierarchyAuditor(BaseAuditor):
    """Auditor for visual hierarchy dimension.
    
    Analyzes prominence, focal points, and eye-flow patterns to ensure
    the most important elements are the most prominent.
    """
    
    dimension = AuditDimension.VISUAL_HIERARCHY
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        # Merge with defaults
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run visual hierarchy audit.
        
        Args:
            screen: The screen to audit
            components: List of detected components
            
        Returns:
            List of hierarchy findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Calculate screen dimensions (assume 1920x1080 if not available)
        screen_width = getattr(screen, 'width', 1920)
        screen_height = getattr(screen, 'height', 1080)
        
        # Calculate prominence scores for all components
        prominence_scores = self._calculate_prominence_scores(
            components, screen_width, screen_height
        )
        
        # Sort by prominence
        sorted_components = sorted(
            zip(components, prominence_scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Check 1: No clear focal point
        focal_finding = self._check_focal_point(
            sorted_components, screen.id, screen_width, screen_height
        )
        if focal_finding:
            findings.append(focal_finding)
        
        # Check 2: Competing elements
        competing_finding = self._check_competing_elements(
            sorted_components, screen.id
        )
        if competing_finding:
            findings.append(competing_finding)
        
        # Check 3: Focal point not in expected region
        position_finding = self._check_focal_position(
            sorted_components, screen.id, screen_width, screen_height
        )
        if position_finding:
            findings.append(position_finding)
        
        # Check 4: Hierarchy depth issues
        depth_finding = self._check_hierarchy_depth(
            sorted_components, screen.id
        )
        if depth_finding:
            findings.append(depth_finding)
        
        return findings
    
    def _calculate_prominence_scores(
        self,
        components: list[Component],
        screen_width: int,
        screen_height: int,
    ) -> list[float]:
        """Calculate prominence score for each component.
        
        Prominence is based on:
        - Size relative to screen
        - Position (top-left bias)
        - Distance from center
        
        Args:
            components: List of components
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            List of prominence scores (0-1)
        """
        scores = []
        screen_area = screen_width * screen_height
        screen_center = (screen_width / 2, screen_height / 2)
        max_distance = calculate_distance((0, 0), screen_center)
        
        for comp in components:
            bbox = comp.bounding_box
            
            # Size score (area relative to screen)
            area = get_bbox_area(bbox)
            size_score = min(area / screen_area * 10, 1.0)  # Normalize
            
            # Position score (top-left bias)
            # Top-left is 1.0, bottom-right is 0.0
            center = get_bbox_center(bbox)
            pos_score = 1.0 - (center[0] / screen_width + center[1] / screen_height) / 2
            
            # Center distance score (closer to center is more prominent)
            dist = calculate_distance(center, screen_center)
            center_score = 1.0 - (dist / max_distance)
            
            # Weighted combination
            prominence = (
                size_score * self.config["size_weight"] +
                pos_score * self.config["position_weight"] +
                center_score * self.config["center_distance_weight"]
            )
            
            scores.append(prominence)
        
        return scores
    
    def _check_focal_point(
        self,
        sorted_components: list[tuple[Component, float]],
        screen_id: str,
        screen_width: int,
        screen_height: int,
    ) -> Optional[AuditFindingCreate]:
        """Check if there's a clear focal point.
        
        A clear focal point exists when:
        - The top-ranked element is significantly more prominent
        - There's not a gradual decline in prominence
        
        Args:
            sorted_components: Components sorted by prominence
            screen_id: Screen ID
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            Finding if no clear focal point, None otherwise
        """
        if len(sorted_components) < 2:
            return None
        
        top_prominence = sorted_components[0][1]
        second_prominence = sorted_components[1][1]
        
        # Check if top element is significantly more prominent
        if top_prominence > 0:
            ratio = second_prominence / top_prominence
            if ratio > self.config["max_competing_ratio"]:
                return self.create_finding(
                    entity_id=screen_id,
                    issue="No clear visual focal point on the screen",
                    rationale=(
                        f"The most prominent element (score: {top_prominence:.2f}) is not "
                        f"significantly more prominent than the second element "
                        f"(score: {second_prominence:.2f}, ratio: {ratio:.2f}). "
                        "Users may not know where to look first."
                    ),
                    severity=Severity.HIGH,
                    metadata={
                        "top_prominence": top_prominence,
                        "second_prominence": second_prominence,
                        "ratio": ratio,
                    },
                )
        
        return None
    
    def _check_competing_elements(
        self,
        sorted_components: list[tuple[Component, float]],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check for competing visual elements.
        
        Multiple elements with similar prominence compete for attention.
        
        Args:
            sorted_components: Components sorted by prominence
            screen_id: Screen ID
            
        Returns:
            Finding if competing elements found, None otherwise
        """
        if len(sorted_components) < 3:
            return None
        
        # Get top 5 components (or fewer if less available)
        top_count = min(5, len(sorted_components))
        top_components = sorted_components[:top_count]
        
        # Check if top elements have similar prominence
        prominences = [p for _, p in top_components]
        avg_prominence = sum(prominences) / len(prominences)
        
        # Count elements close to average (within 20%)
        competing_count = sum(
            1 for p in prominences
            if abs(p - avg_prominence) / avg_prominence < 0.2
        )
        
        if competing_count >= 3:
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Multiple competing visual elements detected ({competing_count} elements)",
                rationale=(
                    f"{competing_count} elements have similar prominence levels, "
                    "creating visual competition. This makes it harder for users "
                    "to identify the primary action or content."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "competing_count": competing_count,
                    "prominences": prominences,
                },
            )
        
        return None
    
    def _check_focal_position(
        self,
        sorted_components: list[tuple[Component, float]],
        screen_id: str,
        screen_width: int,
        screen_height: int,
    ) -> Optional[AuditFindingCreate]:
        """Check if focal point is in expected region.
        
        Users typically look at top-left first (F-pattern).
        
        Args:
            sorted_components: Components sorted by prominence
            screen_id: Screen ID
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            Finding if focal point in unexpected position, None otherwise
        """
        if not sorted_components:
            return None
        
        top_component, top_prominence = sorted_components[0]
        center = get_bbox_center(top_component.bounding_box)
        
        # Define expected focal region (top-left)
        focal_x_max = screen_width * self.config["focal_region_x"]
        focal_y_max = screen_height * self.config["focal_region_y"]
        
        # Check if in expected region
        in_focal_region = center[0] <= focal_x_max and center[1] <= focal_y_max
        
        if not in_focal_region and top_prominence > 0.3:
            # Only flag if the element is prominent enough to matter
            return self.create_finding(
                entity_id=screen_id,
                issue="Primary visual element not in expected focal region",
                rationale=(
                    f"The most prominent element is at ({center[0]:.0f}, {center[1]:.0f}), "
                    f"outside the expected top-left focal region "
                    f"({focal_x_max:.0f}x{focal_y_max:.0f}). "
                    "Users following F-pattern scanning may miss it."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "element_position": center,
                    "focal_region": (focal_x_max, focal_y_max),
                    "prominence": top_prominence,
                },
            )
        
        return None
    
    def _check_hierarchy_depth(
        self,
        sorted_components: list[tuple[Component, float]],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check for hierarchy depth issues.
        
        Too many hierarchy levels can confuse users.
        
        Args:
            sorted_components: Components sorted by prominence
            screen_id: Screen ID
            
        Returns:
            Finding if hierarchy depth issues found, None otherwise
        """
        if len(sorted_components) < 5:
            return None
        
        prominences = [p for _, p in sorted_components]
        
        # Calculate prominence variance
        avg = sum(prominences) / len(prominences)
        variance = sum((p - avg) ** 2 for p in prominences) / len(prominences)
        
        # Very low variance means flat hierarchy (everything same prominence)
        # Very high variance might mean too many levels
        if variance < 0.01:
            return self.create_finding(
                entity_id=screen_id,
                issue="Visual hierarchy is too flat",
                rationale=(
                    "All elements have similar visual prominence, "
                    "creating a flat hierarchy. This makes it difficult "
                    "for users to understand what's important."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "prominence_variance": variance,
                    "avg_prominence": avg,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_visual_hierarchy(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run visual hierarchy audit.
    
    Args:
        screen: Screen to audit
        components: Components on the screen
        config: Optional configuration
        
    Returns:
        List of audit findings
    """
    auditor = VisualHierarchyAuditor(config=config)
    return auditor.audit(screen, components)
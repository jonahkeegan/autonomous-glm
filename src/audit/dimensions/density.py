"""
Density auditor for analyzing information density.

Analyzes:
- Screen feels appropriately dense (not sparse, not cramped)
- Information is digestible
- Whitespace is sufficient
"""

from typing import Any, Optional

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_area,
    calculate_density,
    group_by_type,
)
from src.db.models import Screen, Component, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Minimum components to analyze
    "min_components": 3,
    # Density thresholds (components per 10,000 pixels)
    "sparse_density_threshold": 0.5,
    "dense_density_threshold": 3.0,
    "cramped_density_threshold": 5.0,
    # Maximum component coverage ratio (component area / screen area)
    "max_coverage_ratio": 0.8,
    # Minimum whitespace ratio
    "min_whitespace_ratio": 0.15,
}


# =============================================================================
# DENSITY AUDITOR
# =============================================================================

class DensityAuditor(BaseAuditor):
    """Auditor for density dimension.
    
    Analyzes information density, whitespace sufficiency, and visual balance.
    """
    
    dimension = AuditDimension.DENSITY
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run density audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of density findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Calculate screen dimensions
        screen_width = getattr(screen, 'width', 1920)
        screen_height = getattr(screen, 'height', 1080)
        screen_area = screen_width * screen_height
        
        # Calculate component density
        density = calculate_density(components, screen_width, screen_height)
        
        # Calculate coverage (component area / screen area)
        total_component_area = sum(get_bbox_area(c.bounding_box) for c in components)
        coverage_ratio = total_component_area / screen_area if screen_area > 0 else 0
        
        # Check 1: Too sparse
        sparse_finding = self._check_sparse_density(
            density, len(components), screen.id
        )
        if sparse_finding:
            findings.append(sparse_finding)
        
        # Check 2: Too dense
        dense_finding = self._check_dense_density(
            density, len(components), screen.id
        )
        if dense_finding:
            findings.append(dense_finding)
        
        # Check 3: Insufficient whitespace
        whitespace_finding = self._check_whitespace(
            coverage_ratio, screen.id
        )
        if whitespace_finding:
            findings.append(whitespace_finding)
        
        # Check 4: Uneven distribution
        distribution_finding = self._check_distribution(
            components, screen_width, screen_height, screen.id
        )
        if distribution_finding:
            findings.append(distribution_finding)
        
        return findings
    
    def _check_sparse_density(
        self,
        density: float,
        component_count: int,
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if screen is too sparse.
        
        Args:
            density: Component density
            component_count: Number of components
            screen_id: Screen ID
            
        Returns:
            Finding if too sparse
        """
        if density < self.config["sparse_density_threshold"]:
            return self.create_finding(
                entity_id=screen_id,
                issue="Screen appears too sparse",
                rationale=(
                    f"Density is {density:.2f} components per 10,000 pixels "
                    f"({component_count} components). "
                    "A sparse screen may feel empty or incomplete."
                ),
                severity=Severity.LOW,
                metadata={
                    "density": density,
                    "component_count": component_count,
                    "threshold": self.config["sparse_density_threshold"],
                },
            )
        
        return None
    
    def _check_dense_density(
        self,
        density: float,
        component_count: int,
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if screen is too dense.
        
        Args:
            density: Component density
            component_count: Number of components
            screen_id: Screen ID
            
        Returns:
            Finding if too dense
        """
        if density > self.config["cramped_density_threshold"]:
            return self.create_finding(
                entity_id=screen_id,
                issue="Screen is too dense (cramped)",
                rationale=(
                    f"Density is {density:.2f} components per 10,000 pixels "
                    f"({component_count} components). "
                    "High density makes content hard to scan and overwhelms users."
                ),
                severity=Severity.HIGH,
                metadata={
                    "density": density,
                    "component_count": component_count,
                    "threshold": self.config["cramped_density_threshold"],
                },
            )
        
        if density > self.config["dense_density_threshold"]:
            return self.create_finding(
                entity_id=screen_id,
                issue="Screen has high density",
                rationale=(
                    f"Density is {density:.2f} components per 10,000 pixels "
                    f"({component_count} components). "
                    "Consider breaking content into sections or pages."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "density": density,
                    "component_count": component_count,
                    "threshold": self.config["dense_density_threshold"],
                },
            )
        
        return None
    
    def _check_whitespace(
        self,
        coverage_ratio: float,
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if there's sufficient whitespace.
        
        Args:
            coverage_ratio: Component area / screen area
            screen_id: Screen ID
            
        Returns:
            Finding if insufficient whitespace
        """
        whitespace_ratio = 1 - coverage_ratio
        
        if coverage_ratio > self.config["max_coverage_ratio"]:
            return self.create_finding(
                entity_id=screen_id,
                issue="Insufficient whitespace",
                rationale=(
                    f"Components cover {coverage_ratio:.0%} of the screen, "
                    f"leaving only {whitespace_ratio:.0%} whitespace. "
                    "Whitespace helps users focus and improves readability."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "coverage_ratio": coverage_ratio,
                    "whitespace_ratio": whitespace_ratio,
                    "max_coverage": self.config["max_coverage_ratio"],
                },
            )
        
        return None
    
    def _check_distribution(
        self,
        components: list[Component],
        screen_width: int,
        screen_height: int,
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if components are evenly distributed.
        
        Args:
            components: List of components
            screen_width: Screen width
            screen_height: Screen height
            screen_id: Screen ID
            
        Returns:
            Finding if uneven distribution
        """
        if len(components) < 6:
            return None
        
        # Divide screen into quadrants
        quadrants = [[], [], [], []]  # TL, TR, BL, BR
        
        for comp in components:
            center_x = comp.bounding_box.x + comp.bounding_box.width / 2
            center_y = comp.bounding_box.y + comp.bounding_box.height / 2
            
            if center_x < screen_width / 2:
                if center_y < screen_height / 2:
                    quadrants[0].append(comp)  # Top-left
                else:
                    quadrants[2].append(comp)  # Bottom-left
            else:
                if center_y < screen_height / 2:
                    quadrants[1].append(comp)  # Top-right
                else:
                    quadrants[3].append(comp)  # Bottom-right
        
        counts = [len(q) for q in quadrants]
        total = sum(counts)
        
        if total == 0:
            return None
        
        # Check for severe imbalance (one quadrant has >50% of components)
        max_count = max(counts)
        max_quadrant = ["top-left", "top-right", "bottom-left", "bottom-right"][counts.index(max_count)]
        
        if max_count > total * 0.5:
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Components concentrated in {max_quadrant} quadrant",
                rationale=(
                    f"{max_count} of {total} components ({max_count/total:.0%}) "
                    f"are in the {max_quadrant}. "
                    "Even distribution creates visual balance."
                ),
                severity=Severity.LOW,
                metadata={
                    "quadrant_counts": {
                        "top_left": counts[0],
                        "top_right": counts[1],
                        "bottom_left": counts[2],
                        "bottom_right": counts[3],
                    },
                    "max_quadrant": max_quadrant,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_density(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run density audit."""
    auditor = DensityAuditor(config=config)
    return auditor.audit(screen, components)
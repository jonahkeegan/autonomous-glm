"""
Alignment & Grid auditor for analyzing grid adherence.

Analyzes:
- Elements sit on consistent grid
- Nothing off by 1-2 pixels
- Every element feels locked into layout
"""

from typing import Any, Optional
from collections import Counter

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    is_on_grid,
    get_bbox_center,
    group_by_type,
)
from src.db.models import Screen, Component, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Grid base (4px or 8px)
    "grid_base": 4,
    # Tolerance for grid alignment (pixels)
    "grid_tolerance": 1,
    # Maximum misalignment ratio before finding
    "max_misalignment_ratio": 0.3,
    # Minimum components to analyze
    "min_components": 3,
    # Check left edges alignment
    "check_left_edges": True,
    # Check center alignment
    "check_center_alignment": True,
}


# =============================================================================
# ALIGNMENT & GRID AUDITOR
# =============================================================================

class AlignmentGridAuditor(BaseAuditor):
    """Auditor for alignment and grid dimension.
    
    Analyzes grid adherence, pixel-perfect positioning, and layout precision.
    """
    
    dimension = AuditDimension.ALIGNMENT_GRID
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run alignment and grid audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of alignment findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Check 1: Grid alignment
        grid_finding = self._check_grid_alignment(components, screen.id)
        if grid_finding:
            findings.append(grid_finding)
        
        # Check 2: Left edge alignment
        if self.config["check_left_edges"]:
            left_finding = self._check_left_edge_alignment(components, screen.id)
            if left_finding:
                findings.append(left_finding)
        
        # Check 3: Center alignment within rows
        if self.config["check_center_alignment"]:
            center_finding = self._check_center_alignment(components, screen.id)
            if center_finding:
                findings.append(center_finding)
        
        # Check 4: Baseline alignment
        baseline_finding = self._check_baseline_alignment(components, screen.id)
        if baseline_finding:
            findings.append(baseline_finding)
        
        return findings
    
    def _check_grid_alignment(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if components are aligned to grid.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if grid misalignment found
        """
        grid_base = self.config["grid_base"]
        tolerance = self.config["grid_tolerance"]
        
        misaligned = []
        
        for comp in components:
            bbox = comp.bounding_box
            # Check each edge
            props = {
                'x': bbox.x,
                'y': bbox.y,
                'right': bbox.x + bbox.width,
                'bottom': bbox.y + bbox.height,
            }
            
            for prop, value in props.items():
                if not is_on_grid(value, grid_base, tolerance):
                    misaligned.append({
                        'component': comp.type,
                        'property': prop,
                        'value': round(value, 1),
                    })
        
        if len(misaligned) > len(components) * self.config["max_misalignment_ratio"]:
            # Group by property
            by_prop = Counter(m['property'] for m in misaligned)
            
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Components not aligned to {grid_base}px grid ({len(misaligned)} misalignments)",
                rationale=(
                    f"{len(misaligned)} component properties are off-grid. "
                    f"By property: {', '.join(f'{p}: {c}' for p, c in by_prop.items())}. "
                    "Grid alignment creates visual precision and polish."
                ),
                severity=Severity.LOW,
                metadata={
                    "misaligned_count": len(misaligned),
                    "grid_base": grid_base,
                    "by_property": dict(by_prop),
                },
            )
        
        return None
    
    def _check_left_edge_alignment(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if left edges are aligned within columns.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if left edges misaligned
        """
        if len(components) < 4:
            return None
        
        # Get left edge positions
        left_edges = sorted([c.bounding_box.x for c in components])
        
        # Find clusters of similar x positions
        clusters = self._cluster_values(left_edges, tolerance=4)
        
        # Check for many unique positions (no column structure)
        if len(clusters) > len(components) * 0.6:
            return self.create_finding(
                entity_id=screen_id,
                issue="Left edges not aligned to columns",
                rationale=(
                    f"Found {len(clusters)} distinct left edge positions "
                    f"for {len(components)} components. "
                    "Consistent left alignment creates visual order and readability."
                ),
                severity=Severity.LOW,
                metadata={
                    "unique_positions": len(clusters),
                    "component_count": len(components),
                },
            )
        
        return None
    
    def _check_center_alignment(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if centers are aligned within rows.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if centers misaligned
        """
        if len(components) < 4:
            return None
        
        # Get center x positions
        centers = sorted([get_bbox_center(c.bounding_box)[0] for c in components])
        
        # Find clusters of similar center positions
        clusters = self._cluster_values(centers, tolerance=8)
        
        # Check if components should be center-aligned but aren't
        # Look for pairs that are close in Y but far in center X
        misaligned_pairs = 0
        
        sorted_by_y = sorted(components, key=lambda c: c.bounding_box.y)
        for i, c1 in enumerate(sorted_by_y):
            for c2 in sorted_by_y[i+1:]:
                y1 = c1.bounding_box.y
                y2 = c2.bounding_box.y
                
                # If in same row (within 50px vertically)
                if abs(y2 - y1) < 50:
                    cx1 = get_bbox_center(c1.bounding_box)[0]
                    cx2 = get_bbox_center(c2.bounding_box)[0]
                    
                    # But centers far apart (more than 100px)
                    if abs(cx2 - cx1) > 100:
                        misaligned_pairs += 1
        
        if misaligned_pairs >= 2:
            return self.create_finding(
                entity_id=screen_id,
                issue="Elements in same row not center-aligned",
                rationale=(
                    f"Found {misaligned_pairs} pairs of elements in the same row "
                    "with misaligned centers. Center alignment creates visual balance."
                ),
                severity=Severity.LOW,
                metadata={
                    "misaligned_pairs": misaligned_pairs,
                },
            )
        
        return None
    
    def _check_baseline_alignment(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if text baselines are aligned.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if baselines misaligned
        """
        # Filter to text components
        text_types = {'text', 'label', 'button'}
        text_components = [c for c in components if c.type.lower() in text_types]
        
        if len(text_components) < 3:
            return None
        
        # Get bottom positions (approximate baseline)
        bottoms = sorted([c.bounding_box.y + c.bounding_box.height for c in text_components])
        
        # Cluster bottom positions
        clusters = self._cluster_values(bottoms, tolerance=4)
        
        # Many unique baselines suggests misalignment
        if len(clusters) > len(text_components) * 0.6:
            return self.create_finding(
                entity_id=screen_id,
                issue="Text baselines not aligned",
                rationale=(
                    f"Found {len(clusters)} distinct baseline positions "
                    f"for {len(text_components)} text elements. "
                    "Aligned baselines create visual order in typography."
                ),
                severity=Severity.LOW,
                metadata={
                    "unique_baselines": len(clusters),
                    "text_component_count": len(text_components),
                },
            )
        
        return None
    
    def _cluster_values(
        self,
        values: list[float],
        tolerance: float = 4,
    ) -> list[list[float]]:
        """Cluster similar values together.
        
        Args:
            values: List of values
            tolerance: Maximum difference within cluster
            
        Returns:
            List of clusters
        """
        if not values:
            return []
        
        sorted_values = sorted(values)
        clusters = [[sorted_values[0]]]
        
        for value in sorted_values[1:]:
            if value - clusters[-1][-1] <= tolerance:
                clusters[-1].append(value)
            else:
                clusters.append([value])
        
        return clusters


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_alignment_grid(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run alignment audit."""
    auditor = AlignmentGridAuditor(config=config)
    return auditor.audit(screen, components)
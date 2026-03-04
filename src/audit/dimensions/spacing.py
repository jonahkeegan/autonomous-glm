"""
Spacing & Rhythm auditor for analyzing whitespace consistency.

Analyzes:
- Whitespace is consistent (uses 4px/8px grid)
- Elements breathe (not cramped)
- Vertical rhythm is harmonious
"""

from typing import Any, Optional
from collections import Counter

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_center,
    get_bbox_area,
    quantize_to_grid,
    is_on_grid,
    group_by_type,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Grid base for spacing (4px or 8px)
    "grid_base": 4,
    # Tolerance for grid alignment (pixels)
    "grid_tolerance": 1,
    # Minimum spacing between elements (pixels)
    "min_spacing": 8,
    # Maximum spacing variance ratio (std/mean)
    "max_spacing_variance": 0.5,
    # Cramped threshold (spacing below this percentage of avg)
    "cramped_threshold": 0.5,
    # Minimum components to analyze spacing
    "min_components": 3,
}


# =============================================================================
# SPACING & RHYTHM AUDITOR
# =============================================================================

class SpacingRhythmAuditor(BaseAuditor):
    """Auditor for spacing and rhythm dimension.
    
    Analyzes whitespace consistency, breathing room, and vertical rhythm.
    """
    
    dimension = AuditDimension.SPACING_RHYTHM
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run spacing and rhythm audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of spacing findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Calculate screen dimensions
        screen_width = getattr(screen, 'width', 1920)
        screen_height = getattr(screen, 'height', 1080)
        
        # Calculate spacing between adjacent components
        spacings = self._calculate_spacings(components)
        
        if not spacings:
            return findings
        
        # Check 1: Inconsistent spacing
        consistency_finding = self._check_spacing_consistency(
            spacings, screen.id
        )
        if consistency_finding:
            findings.append(consistency_finding)
        
        # Check 2: Cramped elements
        cramped_finding = self._check_cramped_elements(
            spacings, screen.id
        )
        if cramped_finding:
            findings.append(cramped_finding)
        
        # Check 3: Grid alignment
        grid_finding = self._check_grid_alignment(
            components, screen.id, screen_width, screen_height
        )
        if grid_finding:
            findings.append(grid_finding)
        
        # Check 4: Vertical rhythm
        rhythm_finding = self._check_vertical_rhythm(
            components, screen.id
        )
        if rhythm_finding:
            findings.append(rhythm_finding)
        
        return findings
    
    def _calculate_spacings(
        self,
        components: list[Component],
    ) -> list[float]:
        """Calculate spacing between adjacent components.
        
        Args:
            components: List of components
            
        Returns:
            List of spacing distances
        """
        spacings = []
        
        # Sort by position (top-to-bottom, left-to-right)
        sorted_comps = sorted(
            components,
            key=lambda c: (c.bounding_box.y, c.bounding_box.x)
        )
        
        # Calculate horizontal and vertical gaps
        for i, comp1 in enumerate(sorted_comps):
            for comp2 in sorted_comps[i+1:]:
                bbox1 = comp1.bounding_box
                bbox2 = comp2.bounding_box
                
                # Check if horizontally adjacent
                if bbox1.y < bbox2.y + bbox2.height and bbox2.y < bbox1.y + bbox1.height:
                    # Horizontal gap
                    gap = bbox2.x - (bbox1.x + bbox1.width)
                    if gap > 0:
                        spacings.append(gap)
                
                # Check if vertically adjacent
                if bbox1.x < bbox2.x + bbox2.width and bbox2.x < bbox1.x + bbox1.width:
                    # Vertical gap
                    gap = bbox2.y - (bbox1.y + bbox1.height)
                    if gap > 0:
                        spacings.append(gap)
        
        return spacings
    
    def _check_spacing_consistency(
        self,
        spacings: list[float],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if spacing is consistent.
        
        Args:
            spacings: List of spacing values
            screen_id: Screen ID
            
        Returns:
            Finding if inconsistent spacing found
        """
        if len(spacings) < 3:
            return None
        
        # Calculate statistics
        mean_spacing = sum(spacings) / len(spacings)
        variance = sum((s - mean_spacing) ** 2 for s in spacings) / len(spacings)
        std_dev = variance ** 0.5
        
        # Coefficient of variation
        cv = std_dev / mean_spacing if mean_spacing > 0 else 0
        
        if cv > self.config["max_spacing_variance"]:
            # Find most common spacing values
            quantized = [quantize_to_grid(s, self.config["grid_base"]) for s in spacings]
            counter = Counter(quantized)
            most_common = counter.most_common(3)
            
            return self.create_finding(
                entity_id=screen_id,
                issue="Inconsistent spacing between elements",
                rationale=(
                    f"Spacing varies significantly (CV: {cv:.2f}, mean: {mean_spacing:.1f}px, "
                    f"std: {std_dev:.1f}px). Common spacing values: "
                    f"{', '.join(f'{v}px ({c})' for v, c in most_common)}. "
                    "Consistent spacing creates visual harmony."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "coefficient_of_variation": cv,
                    "mean_spacing": mean_spacing,
                    "std_dev": std_dev,
                    "most_common": most_common,
                },
            )
        
        return None
    
    def _check_cramped_elements(
        self,
        spacings: list[float],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check for cramped elements (insufficient breathing room).
        
        Args:
            spacings: List of spacing values
            screen_id: Screen ID
            
        Returns:
            Finding if cramped elements found
        """
        if not spacings:
            return None
        
        min_spacing = self.config["min_spacing"]
        cramped_count = sum(1 for s in spacings if s < min_spacing)
        
        if cramped_count > 0:
            cramped_ratio = cramped_count / len(spacings)
            
            if cramped_ratio > 0.3:  # More than 30% cramped
                return self.create_finding(
                    entity_id=screen_id,
                    issue=f"Elements are cramped ({cramped_count} gaps below {min_spacing}px)",
                    rationale=(
                        f"{cramped_count} of {len(spacings)} gaps ({cramped_ratio:.0%}) "
                        f"are below the minimum {min_spacing}px spacing. "
                        "Tight spacing makes the interface feel crowded and harder to scan."
                    ),
                    severity=Severity.MEDIUM,
                    metadata={
                        "cramped_count": cramped_count,
                        "total_gaps": len(spacings),
                        "min_spacing_threshold": min_spacing,
                    },
                )
        
        return None
    
    def _check_grid_alignment(
        self,
        components: list[Component],
        screen_id: str,
        screen_width: int,
        screen_height: int,
    ) -> Optional[AuditFindingCreate]:
        """Check if elements are aligned to grid.
        
        Args:
            components: List of components
            screen_id: Screen ID
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            Finding if grid misalignment found
        """
        grid_base = self.config["grid_base"]
        tolerance = self.config["grid_tolerance"]
        
        misaligned_count = 0
        misaligned_examples = []
        
        for comp in components:
            bbox = comp.bounding_box
            # Check x, y, width, height alignment
            checks = [
                ('x', bbox.x),
                ('y', bbox.y),
                ('width', bbox.width),
                ('height', bbox.height),
            ]
            
            for prop, value in checks:
                if not is_on_grid(value, grid_base, tolerance):
                    misaligned_count += 1
                    if len(misaligned_examples) < 3:
                        misaligned_examples.append(
                            f"{comp.type}.{prop}={value:.1f}px"
                        )
        
        if misaligned_count > len(components) * 0.3:  # >30% misaligned
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Elements not aligned to {grid_base}px grid",
                rationale=(
                    f"{misaligned_count} properties are off-grid. "
                    f"Examples: {', '.join(misaligned_examples)}. "
                    f"Grid alignment creates visual precision and polish."
                ),
                severity=Severity.LOW,
                metadata={
                    "misaligned_count": misaligned_count,
                    "grid_base": grid_base,
                    "examples": misaligned_examples,
                },
            )
        
        return None
    
    def _check_vertical_rhythm(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check vertical rhythm consistency.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if vertical rhythm issues found
        """
        if len(components) < 4:
            return None
        
        # Get y-positions
        y_positions = sorted([c.bounding_box.y for c in components])
        
        # Calculate vertical gaps between consecutive elements
        v_gaps = []
        for i in range(len(y_positions) - 1):
            gap = y_positions[i + 1] - y_positions[i]
            if gap > 0:
                v_gaps.append(gap)
        
        if len(v_gaps) < 3:
            return None
        
        # Check for rhythm consistency
        quantized = [quantize_to_grid(g, self.config["grid_base"]) for g in v_gaps]
        counter = Counter(quantized)
        most_common_gap, count = counter.most_common(1)[0]
        
        rhythm_consistency = count / len(quantized)
        
        if rhythm_consistency < 0.4:  # Less than 40% consistency
            return self.create_finding(
                entity_id=screen_id,
                issue="Inconsistent vertical rhythm",
                rationale=(
                    f"Vertical spacing lacks consistent rhythm "
                    f"(consistency: {rhythm_consistency:.0%}). "
                    "A harmonious vertical rhythm helps users scan content naturally."
                ),
                severity=Severity.LOW,
                metadata={
                    "rhythm_consistency": rhythm_consistency,
                    "most_common_gap": most_common_gap,
                    "unique_gaps": len(counter),
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_spacing_rhythm(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run spacing audit."""
    auditor = SpacingRhythmAuditor(config=config)
    return auditor.audit(screen, components)
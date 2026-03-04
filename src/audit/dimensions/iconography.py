"""
Iconography auditor for analyzing icon consistency.

Analyzes:
- Icons are consistent in size
- Icons from cohesive set (not mixed libraries)
- Icons support meaning (not just decoration)
- Icon sizes follow common patterns
"""

from typing import Any, Optional
from collections import Counter
import math

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_center,
    get_bbox_area,
    group_by_type,
    calculate_distance,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Standard icon sizes (pixels)
    "standard_sizes": [16, 20, 24, 32, 48, 64],
    # Tolerance for size matching (pixels)
    "size_tolerance": 2,
    # Maximum size variance ratio (std/mean)
    "max_size_variance": 0.3,
    # Minimum icons to analyze
    "min_icons": 2,
    # Maximum distinct size groups before flagging
    "max_size_groups": 3,
}


# =============================================================================
# ICONOGRAPHY AUDITOR
# =============================================================================

class IconographyAuditor(BaseAuditor):
    """Auditor for iconography dimension.
    
    Analyzes icon size consistency and position patterns.
    """
    
    dimension = AuditDimension.ICONOGRAPHY
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run iconography audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of iconography findings
        """
        findings = []
        
        # Filter to icon components only
        icons = [c for c in components if c.type == "icon"]
        
        if len(icons) < self.config["min_icons"]:
            return findings
        
        # Check 1: Size inconsistency
        size_finding = self._check_size_consistency(icons, screen.id)
        if size_finding:
            findings.append(size_finding)
        
        # Check 2: Non-standard sizes
        nonstandard_finding = self._check_standard_sizes(icons, screen.id)
        if nonstandard_finding:
            findings.append(nonstandard_finding)
        
        # Check 3: Size group proliferation
        proliferation_finding = self._check_size_proliferation(icons, screen.id)
        if proliferation_finding:
            findings.append(proliferation_finding)
        
        return findings
    
    def _check_size_consistency(
        self,
        icons: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if icons have consistent sizes.
        
        Args:
            icons: List of icon components
            screen_id: Screen ID
            
        Returns:
            Finding if size inconsistency found
        """
        if len(icons) < 2:
            return None
        
        # Calculate icon sizes (use max of width/height for square-ish icons)
        sizes = []
        for icon in icons:
            bbox = icon.bounding_box
            # Icons are typically square, use the larger dimension
            size = max(bbox.width, bbox.height)
            sizes.append(size)
        
        # Calculate variance
        mean_size = sum(sizes) / len(sizes)
        if mean_size == 0:
            return None
        
        variance = sum((s - mean_size) ** 2 for s in sizes) / len(sizes)
        std_dev = variance ** 0.5
        cv = std_dev / mean_size
        
        if cv > self.config["max_size_variance"]:
            return self.create_finding(
                entity_id=screen_id,
                issue="Inconsistent icon sizes",
                rationale=(
                    f"Icon sizes vary significantly (CV: {cv:.2f}, mean: {mean_size:.1f}px, "
                    f"std: {std_dev:.1f}px). Consistent icon sizes create visual harmony "
                    "and professional appearance."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "coefficient_of_variation": cv,
                    "mean_size": mean_size,
                    "std_dev": std_dev,
                    "sizes": sizes,
                },
            )
        
        return None
    
    def _check_standard_sizes(
        self,
        icons: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if icons use standard sizes.
        
        Args:
            icons: List of icon components
            screen_id: Screen ID
            
        Returns:
            Finding if non-standard sizes found
        """
        standard_sizes = self.config["standard_sizes"]
        tolerance = self.config["size_tolerance"]
        
        nonstandard = []
        for icon in icons:
            bbox = icon.bounding_box
            size = max(bbox.width, bbox.height)
            
            # Check if size matches any standard size
            is_standard = any(
                abs(size - std) <= tolerance
                for std in standard_sizes
            )
            
            if not is_standard:
                nonstandard.append((icon.id, size))
        
        if len(nonstandard) > len(icons) * 0.5:  # More than 50% non-standard
            return self.create_finding(
                entity_id=screen_id,
                issue="Icons use non-standard sizes",
                rationale=(
                    f"{len(nonstandard)} of {len(icons)} icons have non-standard sizes. "
                    f"Standard sizes ({', '.join(str(s) + 'px' for s in standard_sizes)}) "
                    "ensure consistency across the interface and better alignment."
                ),
                severity=Severity.LOW,
                metadata={
                    "nonstandard_count": len(nonstandard),
                    "total_icons": len(icons),
                    "standard_sizes": standard_sizes,
                    "nonstandard_examples": nonstandard[:5],
                },
            )
        
        return None
    
    def _check_size_proliferation(
        self,
        icons: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check for too many distinct icon size groups.
        
        Args:
            icons: List of icon components
            screen_id: Screen ID
            
        Returns:
            Finding if too many size groups found
        """
        tolerance = self.config["size_tolerance"]
        max_groups = self.config["max_size_groups"]
        
        # Group icons by size (with tolerance)
        size_groups: dict[int, list[str]] = {}
        
        for icon in icons:
            bbox = icon.bounding_box
            size = max(bbox.width, bbox.height)
            
            # Find existing group or create new
            found_group = None
            for group_size in size_groups:
                if abs(size - group_size) <= tolerance:
                    found_group = group_size
                    break
            
            if found_group:
                size_groups[found_group].append(icon.id)
            else:
                size_groups[int(size)] = [icon.id]
        
        if len(size_groups) > max_groups:
            group_summary = [
                f"{size}px: {len(ids)} icons"
                for size, ids in sorted(size_groups.items())
            ]
            
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Too many distinct icon sizes ({len(size_groups)})",
                rationale=(
                    f"Found {len(size_groups)} different icon size groups, "
                    f"exceeding recommended maximum of {max_groups}. "
                    f"Groups: {', '.join(group_summary)}. "
                    "Limit icon sizes to 2-3 options for visual consistency."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "size_group_count": len(size_groups),
                    "max_groups": max_groups,
                    "size_groups": {k: len(v) for k, v in size_groups.items()},
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_iconography(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run iconography audit."""
    auditor = IconographyAuditor(config=config)
    return auditor.audit(screen, components)
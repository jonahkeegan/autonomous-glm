"""
Typography auditor for analyzing type hierarchy.

Analyzes:
- Type sizes establish clear hierarchy
- Font weights don't compete
- Typography feels calm, not chaotic
"""

from typing import Any, Optional
from collections import Counter

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_center,
    group_by_type,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Maximum distinct font sizes before chaos
    "max_font_sizes": 5,
    # Maximum distinct font weights before chaos
    "max_font_weights": 3,
    # Minimum size ratio between hierarchy levels (1.2 = 20% difference)
    "min_hierarchy_ratio": 1.2,
    # Minimum components to analyze
    "min_components": 3,
    # Font size estimation ratio (bbox height / font size)
    "font_size_ratio": 0.8,
}


# =============================================================================
# TYPOGRAPHY AUDITOR
# =============================================================================

class TypographyAuditor(BaseAuditor):
    """Auditor for typography dimension.
    
    Analyzes font size hierarchy, weight consistency, and typography calmness.
    """
    
    dimension = AuditDimension.TYPOGRAPHY
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run typography audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of typography findings
        """
        findings = []
        
        # Filter to text-containing components
        text_components = self._filter_text_components(components)
        
        if len(text_components) < self.config["min_components"]:
            return findings
        
        # Estimate font sizes from bounding boxes
        font_sizes = self._estimate_font_sizes(text_components)
        
        # Check 1: Too many font sizes
        sizes_finding = self._check_font_size_variety(
            font_sizes, text_components, screen.id
        )
        if sizes_finding:
            findings.append(sizes_finding)
        
        # Check 2: Weak hierarchy (sizes too similar)
        hierarchy_finding = self._check_hierarchy_strength(
            font_sizes, screen.id
        )
        if hierarchy_finding:
            findings.append(hierarchy_finding)
        
        # Check 3: Competing large elements
        competing_finding = self._check_competing_sizes(
            font_sizes, text_components, screen.id
        )
        if competing_finding:
            findings.append(competing_finding)
        
        return findings
    
    def _filter_text_components(
        self,
        components: list[Component],
    ) -> list[Component]:
        """Filter to components likely containing text.
        
        Args:
            components: All components
            
        Returns:
            Text-containing components
        """
        text_types = {
            'text', 'label', 'button', 'input', 
            'header', 'navigation', 'card'
        }
        return [c for c in components if c.type.lower() in text_types]
    
    def _estimate_font_sizes(
        self,
        components: list[Component],
    ) -> list[int]:
        """Estimate font sizes from bounding box heights.
        
        Args:
            components: Text components
            
        Returns:
            List of estimated font sizes
        """
        ratio = self.config["font_size_ratio"]
        sizes = []
        
        for comp in components:
            # Estimate font size from bbox height
            estimated = int(comp.bounding_box.height * ratio)
            # Quantize to common sizes
            quantized = self._quantize_font_size(estimated)
            sizes.append(quantized)
        
        return sizes
    
    def _quantize_font_size(self, size: int) -> int:
        """Quantize font size to common values.
        
        Args:
            size: Estimated font size
            
        Returns:
            Quantized size
        """
        common_sizes = [12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64, 72]
        
        for common in common_sizes:
            if size <= common * 1.1:  # Within 10%
                return common
        
        return size  # Return as-is if no match
    
    def _check_font_size_variety(
        self,
        font_sizes: list[int],
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if there are too many distinct font sizes.
        
        Args:
            font_sizes: Estimated font sizes
            components: Text components
            screen_id: Screen ID
            
        Returns:
            Finding if too many sizes found
        """
        counter = Counter(font_sizes)
        unique_sizes = len(counter)
        
        if unique_sizes > self.config["max_font_sizes"]:
            sorted_sizes = sorted(counter.items(), key=lambda x: -x[1])
            
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Too many font sizes ({unique_sizes} distinct sizes)",
                rationale=(
                    f"Found {unique_sizes} different font sizes. "
                    f"Sizes: {', '.join(f'{s}px ({c})' for s, c in sorted_sizes[:6])}. "
                    "Limit font sizes to 4-5 for visual harmony."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "unique_sizes": unique_sizes,
                    "size_distribution": dict(counter),
                },
            )
        
        return None
    
    def _check_hierarchy_strength(
        self,
        font_sizes: list[int],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if typography hierarchy is strong enough.
        
        Args:
            font_sizes: Estimated font sizes
            screen_id: Screen ID
            
        Returns:
            Finding if weak hierarchy found
        """
        if len(font_sizes) < 3:
            return None
        
        counter = Counter(font_sizes)
        unique_sizes = sorted(counter.keys(), reverse=True)
        
        if len(unique_sizes) < 2:
            return None
        
        # Check ratio between consecutive hierarchy levels
        weak_levels = []
        for i in range(len(unique_sizes) - 1):
            larger = unique_sizes[i]
            smaller = unique_sizes[i + 1]
            
            if smaller > 0:
                ratio = larger / smaller
                if ratio < self.config["min_hierarchy_ratio"]:
                    weak_levels.append((larger, smaller, ratio))
        
        if len(weak_levels) >= 2:  # Multiple weak transitions
            return self.create_finding(
                entity_id=screen_id,
                issue="Typography hierarchy is weak",
                rationale=(
                    f"Font size differences are too subtle. "
                    f"Weak transitions: {', '.join(f'{l}px→{s}px ({r:.1f}x)' for l, s, r in weak_levels[:3])}. "
                    "Use larger size differences to establish clear hierarchy."
                ),
                severity=Severity.LOW,
                metadata={
                    "weak_levels": weak_levels,
                    "min_ratio_threshold": self.config["min_hierarchy_ratio"],
                },
            )
        
        return None
    
    def _check_competing_sizes(
        self,
        font_sizes: list[int],
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check for multiple large text elements competing for attention.
        
        Args:
            font_sizes: Estimated font sizes
            components: Text components
            screen_id: Screen ID
            
        Returns:
            Finding if competing sizes found
        """
        if not font_sizes:
            return None
        
        # Find "large" elements (top 25% of sizes)
        sorted_sizes = sorted(font_sizes, reverse=True)
        threshold_idx = max(1, len(sorted_sizes) // 4)
        large_threshold = sorted_sizes[threshold_idx]
        
        large_count = sum(1 for s in font_sizes if s >= large_threshold)
        total = len(font_sizes)
        
        # If more than 30% are "large", they're competing
        if large_count / total > 0.3 and large_count >= 3:
            return self.create_finding(
                entity_id=screen_id,
                issue="Multiple large text elements competing for attention",
                rationale=(
                    f"{large_count} of {total} text elements are large "
                    f"(≥{large_threshold}px). When everything is large, "
                    "nothing stands out. Establish one primary text element."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "large_count": large_count,
                    "total_text_elements": total,
                    "large_threshold": large_threshold,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_typography(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run typography audit."""
    auditor = TypographyAuditor(config=config)
    return auditor.audit(screen, components)
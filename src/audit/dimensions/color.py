"""
Color auditor for analyzing color usage and contrast.

Analyzes:
- Color used with restraint and purpose
- Colors guide attention (not scatter it)
- Contrast ratios meet WCAG AA (4.5:1 for text)
"""

from typing import Any, Optional
from collections import Counter

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    rgb_to_luminance,
    calculate_contrast_ratio,
    group_by_type,
)
from src.db.models import Screen, Component, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # WCAG AA minimum contrast for normal text
    "min_contrast_normal_text": 4.5,
    # WCAG AA minimum contrast for large text (18pt+ or 14pt bold)
    "min_contrast_large_text": 3.0,
    # Maximum distinct colors before chaos
    "max_distinct_colors": 8,
    # Minimum components to analyze
    "min_components": 3,
    # Color categorization tolerance (HSL hue degrees)
    "hue_tolerance": 15,
}


# =============================================================================
# COLOR AUDITOR
# =============================================================================

class ColorAuditor(BaseAuditor):
    """Auditor for color dimension.
    
    Analyzes color palette consistency, contrast ratios, and purposeful usage.
    """
    
    dimension = AuditDimension.COLOR
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run color audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of color findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Extract colors from component properties (if available)
        colors = self._extract_colors(components)
        
        # Check 1: Too many distinct colors
        variety_finding = self._check_color_variety(colors, screen.id)
        if variety_finding:
            findings.append(variety_finding)
        
        # Check 2: Contrast issues (using estimated text colors)
        contrast_finding = self._check_contrast_ratios(
            colors, components, screen.id
        )
        if contrast_finding:
            findings.append(contrast_finding)
        
        # Check 3: Color scattering (colors not cohesive)
        cohesion_finding = self._check_color_cohesion(colors, screen.id)
        if cohesion_finding:
            findings.append(cohesion_finding)
        
        return findings
    
    def _extract_colors(
        self,
        components: list[Component],
    ) -> list[tuple[int, int, int]]:
        """Extract colors from component properties.
        
        Args:
            components: List of components
            
        Returns:
            List of RGB tuples
        """
        colors = []
        
        for comp in components:
            if comp.properties:
                # Check for color in properties
                color = comp.properties.get('color') or comp.properties.get('background')
                if color and isinstance(color, (list, tuple)) and len(color) >= 3:
                    colors.append(tuple(color[:3]))
        
        return colors
    
    def _check_color_variety(
        self,
        colors: list[tuple[int, int, int]],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if there are too many distinct colors.
        
        Args:
            colors: List of RGB colors
            screen_id: Screen ID
            
        Returns:
            Finding if too many colors found
        """
        if len(colors) < 3:
            return None
        
        # Categorize by hue
        hue_categories = self._categorize_by_hue(colors)
        unique_hues = len(hue_categories)
        
        if unique_hues > self.config["max_distinct_colors"]:
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Too many distinct colors ({unique_hues} color families)",
                rationale=(
                    f"Found {unique_hues} distinct color families. "
                    "Excessive color variety scatters attention. "
                    "Use a limited palette (3-5 main colors) for visual cohesion."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "unique_hues": unique_hues,
                    "total_colors": len(colors),
                },
            )
        
        return None
    
    def _check_contrast_ratios(
        self,
        colors: list[tuple[int, int, int]],
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check WCAG contrast ratios.
        
        Args:
            colors: List of RGB colors
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if contrast issues found
        """
        if len(colors) < 2:
            return None
        
        # Check contrast between dominant colors
        contrast_issues = []
        
        for i, c1 in enumerate(colors[:10]):  # Limit to first 10
            for c2 in colors[i+1:i+5]:  # Compare to next 4
                l1 = rgb_to_luminance(*c1)
                l2 = rgb_to_luminance(*c2)
                ratio = calculate_contrast_ratio(l1, l2)
                
                # Check if this might be a text/background pair
                # (one significantly lighter than other)
                if ratio < self.config["min_contrast_normal_text"]:
                    contrast_issues.append({
                        "color1": c1,
                        "color2": c2,
                        "ratio": round(ratio, 2),
                    })
        
        if len(contrast_issues) >= 2:
            return self.create_finding(
                entity_id=screen_id,
                issue="Potential color contrast issues detected",
                rationale=(
                    f"Found {len(contrast_issues)} color pairs with contrast below "
                    f"WCAG AA minimum ({self.config['min_contrast_normal_text']}:1). "
                    "Low contrast makes text hard to read, especially for users with visual impairments."
                ),
                severity=Severity.HIGH,
                standards_refs=[self.link_wcag("1.4.3", "Contrast (Minimum)")],
                metadata={
                    "contrast_issues": contrast_issues[:5],
                    "min_ratio_required": self.config["min_contrast_normal_text"],
                },
            )
        
        return None
    
    def _check_color_cohesion(
        self,
        colors: list[tuple[int, int, int]],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if colors form a cohesive palette.
        
        Args:
            colors: List of RGB colors
            screen_id: Screen ID
            
        Returns:
            Finding if colors lack cohesion
        """
        if len(colors) < 4:
            return None
        
        # Check saturation distribution
        saturations = [self._rgb_to_saturation(*c) for c in colors]
        avg_sat = sum(saturations) / len(saturations)
        
        # High variance in saturation suggests mixed color sources
        sat_variance = sum((s - avg_sat) ** 2 for s in saturations) / len(saturations)
        
        if sat_variance > 0.1:  # High variance
            high_sat = sum(1 for s in saturations if s > 0.7)
            low_sat = sum(1 for s in saturations if s < 0.3)
            
            if high_sat > 0 and low_sat > 0:
                return self.create_finding(
                    entity_id=screen_id,
                    issue="Color palette lacks cohesion",
                    rationale=(
                        "Colors have inconsistent saturation levels "
                        f"(variance: {sat_variance:.2f}). "
                        "Mixing highly saturated and muted colors creates visual discord. "
                        "Choose a consistent saturation level for your palette."
                    ),
                    severity=Severity.LOW,
                    metadata={
                        "saturation_variance": sat_variance,
                        "high_saturation_count": high_sat,
                        "low_saturation_count": low_sat,
                    },
                )
        
        return None
    
    def _categorize_by_hue(
        self,
        colors: list[tuple[int, int, int]],
    ) -> dict[str, list[tuple[int, int, int]]]:
        """Categorize colors by hue.
        
        Args:
            colors: List of RGB colors
            
        Returns:
            Dictionary of hue category -> colors
        """
        categories: dict[str, list[tuple[int, int, int]]] = {}
        
        for color in colors:
            hue = self._rgb_to_hue(*color)
            category = self._get_hue_category(hue)
            
            if category not in categories:
                categories[category] = []
            categories[category].append(color)
        
        return categories
    
    def _rgb_to_hue(self, r: int, g: int, b: int) -> int:
        """Convert RGB to hue (0-360).
        
        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
            
        Returns:
            Hue in degrees (0-360)
        """
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        
        if max_c == min_c:
            return 0
        
        d = max_c - min_c
        
        if max_c == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_c == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        
        return int(h * 60) % 360
    
    def _rgb_to_saturation(self, r: int, g: int, b: int) -> float:
        """Convert RGB to saturation (0-1).
        
        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
            
        Returns:
            Saturation (0-1)
        """
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        
        if max_c == 0:
            return 0
        
        return (max_c - min_c) / max_c
    
    def _get_hue_category(self, hue: int) -> str:
        """Get hue category name.
        
        Args:
            hue: Hue in degrees
            
        Returns:
            Category name
        """
        tolerance = self.config["hue_tolerance"]
        
        # Neutral colors (low saturation handled separately)
        if hue < tolerance:
            return "red"
        elif hue < 60 - tolerance:
            return "orange"
        elif hue < 60 + tolerance:
            return "yellow"
        elif hue < 120 - tolerance:
            return "yellow-green"
        elif hue < 120 + tolerance:
            return "green"
        elif hue < 180 - tolerance:
            return "cyan-green"
        elif hue < 180 + tolerance:
            return "cyan"
        elif hue < 240 - tolerance:
            return "blue-cyan"
        elif hue < 240 + tolerance:
            return "blue"
        elif hue < 300 - tolerance:
            return "purple"
        elif hue < 300 + tolerance:
            return "magenta"
        else:
            return "red"


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_color(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run color audit."""
    auditor = ColorAuditor(config=config)
    return auditor.audit(screen, components)
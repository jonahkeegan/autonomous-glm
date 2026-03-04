"""
Dark Mode / Theming auditor for analyzing theme consistency.

Analyzes:
- If dark mode present, is it designed (not just inverted)
- All tokens/shadows hold up across themes
- Contrast ratios maintained in dark mode
"""

from typing import Any, Optional

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    calculate_contrast_ratio,
    rgb_to_luminance,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Luminance threshold for dark mode detection (0-1)
    "dark_mode_luminance_threshold": 0.3,
    # Luminance threshold for light mode detection (0-1)
    "light_mode_luminance_threshold": 0.7,
    # Minimum WCAG contrast ratio for normal text
    "min_contrast_normal_text": 4.5,
    # Minimum WCAG contrast ratio for large text
    "min_contrast_large_text": 3.0,
    # Minimum components to analyze
    "min_components": 3,
}


# =============================================================================
# THEMING AUDITOR
# =============================================================================

class ThemingAuditor(BaseAuditor):
    """Auditor for dark mode / theming dimension.
    
    Analyzes theme consistency and contrast across modes.
    """
    
    dimension = AuditDimension.DARK_MODE_THEMING
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run theming audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of theming findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Detect theme mode from background colors
        theme_mode = self._detect_theme_mode(components)
        
        # Check 1: Theme contrast ratios
        contrast_finding = self._check_theme_contrast(
            components, screen.id, theme_mode
        )
        if contrast_finding:
            findings.append(contrast_finding)
        
        # Check 2: Inconsistent theme application
        consistency_finding = self._check_theme_consistency(
            components, screen.id, theme_mode
        )
        if consistency_finding:
            findings.append(consistency_finding)
        
        # Check 3: Shadow/depth in dark mode
        if theme_mode == "dark":
            shadow_finding = self._check_dark_mode_shadows(
                components, screen.id
            )
            if shadow_finding:
                findings.append(shadow_finding)
        
        return findings
    
    def _detect_theme_mode(
        self,
        components: list[Component],
    ) -> str:
        """Detect if screen appears to be dark or light mode.
        
        Args:
            components: List of components
            
        Returns:
            "dark", "light", or "unknown"
        """
        # Collect background colors
        bg_luminances = []
        
        for comp in components:
            # Check for background color
            bg = comp.properties.get("background")
            if isinstance(bg, list) and len(bg) >= 3:
                luminance = rgb_to_luminance(bg[0], bg[1], bg[2])
                bg_luminances.append(luminance)
            
            # Container components are more likely to have background colors
            if comp.type in ["container", "card", "navigation", "header", "footer"]:
                if bg:
                    bg_luminances.append(luminance)
        
        if not bg_luminances:
            return "unknown"
        
        # Use average luminance to determine mode
        avg_luminance = sum(bg_luminances) / len(bg_luminances)
        
        if avg_luminance < self.config["dark_mode_luminance_threshold"]:
            return "dark"
        elif avg_luminance > self.config["light_mode_luminance_threshold"]:
            return "light"
        else:
            return "unknown"
    
    def _check_theme_contrast(
        self,
        components: list[Component],
        screen_id: str,
        theme_mode: str,
    ) -> Optional[AuditFindingCreate]:
        """Check contrast ratios for current theme.
        
        Args:
            components: List of components
            screen_id: Screen ID
            theme_mode: Detected theme mode
            
        Returns:
            Finding if contrast issues found
        """
        if theme_mode == "unknown":
            return None
        
        # Collect foreground/background pairs
        low_contrast_pairs = []
        
        for comp in components:
            fg = comp.properties.get("color")
            bg = comp.properties.get("background")
            
            if not fg or not bg:
                continue
            
            if not isinstance(fg, list) or not isinstance(bg, list):
                continue
            
            if len(fg) < 3 or len(bg) < 3:
                continue
            
            fg_luminance = rgb_to_luminance(fg[0], fg[1], fg[2])
            bg_luminance = rgb_to_luminance(bg[0], bg[1], bg[2])
            
            contrast = calculate_contrast_ratio(fg_luminance, bg_luminance)
            
            # Determine minimum contrast based on text size
            bbox = comp.bounding_box
            is_large_text = bbox.height >= 24  # Approximate large text
            
            min_contrast = (
                self.config["min_contrast_large_text"]
                if is_large_text
                else self.config["min_contrast_normal_text"]
            )
            
            if contrast < min_contrast:
                low_contrast_pairs.append({
                    "component_id": comp.id,
                    "contrast": contrast,
                    "required": min_contrast,
                })
        
        if low_contrast_pairs:
            # Format contrast examples
            examples = []
            for p in low_contrast_pairs[:3]:
                examples.append(f"{p['contrast']:.1f}:1 (need {p['required']}:1)")
            
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Low contrast in {theme_mode} mode",
                rationale=(
                    f"Found {len(low_contrast_pairs)} components with insufficient contrast "
                    f"in {theme_mode} mode. WCAG requires 4.5:1 for normal text and 3:1 for "
                    f"large text. Examples: {', '.join(examples)}."
                ),
                severity=Severity.HIGH,
                standards_refs=[self.link_wcag("1.4.3")] if self.standards_registry else [],
                metadata={
                    "theme_mode": theme_mode,
                    "low_contrast_count": len(low_contrast_pairs),
                    "low_contrast_examples": low_contrast_pairs[:5],
                },
            )
        
        return None
    
    def _check_theme_consistency(
        self,
        components: list[Component],
        screen_id: str,
        theme_mode: str,
    ) -> Optional[AuditFindingCreate]:
        """Check for consistent theme application.
        
        Args:
            components: List of components
            screen_id: Screen ID
            theme_mode: Detected theme mode
            
        Returns:
            Finding if theme consistency issues found
        """
        if theme_mode == "unknown":
            return None
        
        # Check for mixed light/dark backgrounds
        dark_bg_count = 0
        light_bg_count = 0
        
        for comp in components:
            bg = comp.properties.get("background")
            if isinstance(bg, list) and len(bg) >= 3:
                luminance = rgb_to_luminance(bg[0], bg[1], bg[2])
                
                if luminance < 0.3:
                    dark_bg_count += 1
                elif luminance > 0.7:
                    light_bg_count += 1
        
        total_colored = dark_bg_count + light_bg_count
        if total_colored < 2:
            return None
        
        # Check for significant mixing
        dark_ratio = dark_bg_count / total_colored
        light_ratio = light_bg_count / total_colored
        
        # If we have significant mix of both (>20% each), flag it
        if dark_ratio > 0.2 and light_ratio > 0.2:
            return self.create_finding(
                entity_id=screen_id,
                issue="Mixed light and dark backgrounds detected",
                rationale=(
                    f"Found {dark_bg_count} dark backgrounds and {light_bg_count} light "
                    "backgrounds on the same screen. This may indicate inconsistent theme "
                    "application or elements that haven't been properly styled for the current theme."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "dark_bg_count": dark_bg_count,
                    "light_bg_count": light_bg_count,
                    "detected_mode": theme_mode,
                },
            )
        
        return None
    
    def _check_dark_mode_shadows(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if dark mode has appropriate depth/shadow treatment.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if dark mode shadow issues found
        """
        # In dark mode, shadows should be replaced with lighter elevation
        # or subtle glows. Check for components that might have black shadows.
        
        components_with_shadows = 0
        potentially_problematic = 0
        
        for comp in components:
            # Check for shadow property
            shadow = comp.properties.get("shadow")
            if shadow:
                components_with_shadows += 1
                
                # Black shadows on dark backgrounds are often invisible
                # or create muddy appearance
                if isinstance(shadow, dict):
                    shadow_color = shadow.get("color")
                    if isinstance(shadow_color, list) and len(shadow_color) >= 3:
                        # Very dark shadow
                        if shadow_color[0] < 50 and shadow_color[1] < 50 and shadow_color[2] < 50:
                            potentially_problematic += 1
        
        # If many components have potentially problematic shadows
        if components_with_shadows > 0 and potentially_problematic > components_with_shadows * 0.5:
            return self.create_finding(
                entity_id=screen_id,
                issue="Dark mode may have ineffective shadows",
                rationale=(
                    f"Found {potentially_problematic} components with very dark shadows in dark mode. "
                    "Dark shadows on dark backgrounds are often invisible. Consider using "
                    "lighter elevation colors or subtle glows for depth in dark mode."
                ),
                severity=Severity.LOW,
                metadata={
                    "shadow_components": components_with_shadows,
                    "problematic_shadows": potentially_problematic,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_theming(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run theming audit."""
    auditor = ThemingAuditor(config=config)
    return auditor.audit(screen, components)
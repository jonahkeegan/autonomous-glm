"""
Accessibility auditor for analyzing screenshot-detectable accessibility issues.

Analyzes:
- Color contrast ratios (WCAG AA - 4.5:1 text, 3:1 UI)
- Component types suggest semantic elements
- Interactive elements are distinguishable
- Text is legible (minimum size)

Note: Cannot check ARIA labels, keyboard nav, screen reader flow (requires DOM access).
"""

from typing import Any, Optional

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    calculate_contrast_ratio,
    rgb_to_luminance,
    group_by_type,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # WCAG AA contrast requirements
    "min_contrast_normal_text": 4.5,  # 4.5:1 for normal text
    "min_contrast_large_text": 3.0,   # 3:1 for large text (18pt+ or 14pt bold)
    "min_contrast_ui": 3.0,           # 3:1 for UI components
    # Large text threshold (bbox height in pixels)
    "large_text_height_threshold": 24,  # ~18pt
    # Minimum text size (pixels)
    "min_text_height": 12,  # ~9pt minimum for readability
    # Interactive component types
    "interactive_types": [
        "button", "input", "select", "checkbox", "radio",
        "switch", "slider", "tab", "navigation"
    ],
    # Minimum touch target size (44x44 px recommended by Apple)
    "min_touch_target": 44,
    # Minimum components to analyze
    "min_components": 1,
}


# =============================================================================
# ACCESSIBILITY AUDITOR
# =============================================================================

class AccessibilityAuditor(BaseAuditor):
    """Auditor for accessibility dimension.
    
    Analyzes screenshot-detectable accessibility issues including
    contrast ratios, text sizes, and interactive element visibility.
    """
    
    dimension = AuditDimension.ACCESSIBILITY
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run accessibility audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of accessibility findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Check 1: Color contrast ratios
        contrast_finding = self._check_contrast_ratios(components, screen.id)
        if contrast_finding:
            findings.append(contrast_finding)
        
        # Check 2: Minimum text size
        text_size_finding = self._check_text_sizes(components, screen.id)
        if text_size_finding:
            findings.append(text_size_finding)
        
        # Check 3: Interactive element visibility
        interactive_finding = self._check_interactive_visibility(components, screen.id)
        if interactive_finding:
            findings.append(interactive_finding)
        
        # Check 4: Touch target sizes
        touch_finding = self._check_touch_targets(components, screen.id)
        if touch_finding:
            findings.append(touch_finding)
        
        return findings
    
    def _check_contrast_ratios(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check color contrast ratios against WCAG requirements.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if contrast issues found
        """
        contrast_issues = []
        
        for comp in components:
            fg = comp.properties.get("color")
            bg = comp.properties.get("background")
            
            if not fg or not bg:
                continue
            
            if not isinstance(fg, list) or not isinstance(bg, list):
                continue
            
            if len(fg) < 3 or len(bg) < 3:
                continue
            
            # Calculate contrast ratio
            fg_luminance = rgb_to_luminance(fg[0], fg[1], fg[2])
            bg_luminance = rgb_to_luminance(bg[0], bg[1], bg[2])
            contrast = calculate_contrast_ratio(fg_luminance, bg_luminance)
            
            # Determine required contrast based on component type and size
            bbox = comp.bounding_box
            
            if comp.type == "text":
                # Text: 4.5:1 normal, 3:1 large
                is_large = bbox.height >= self.config["large_text_height_threshold"]
                required = (
                    self.config["min_contrast_large_text"]
                    if is_large
                    else self.config["min_contrast_normal_text"]
                )
            elif comp.type in self.config["interactive_types"]:
                # UI components: 3:1
                required = self.config["min_contrast_ui"]
            else:
                # Other components: 3:1 for UI parts
                required = self.config["min_contrast_ui"]
            
            if contrast < required:
                contrast_issues.append({
                    "component_id": comp.id,
                    "component_type": comp.type,
                    "contrast": round(contrast, 2),
                    "required": required,
                    "foreground": fg,
                    "background": bg,
                })
        
        if contrast_issues:
            # Sort by severity (lowest contrast first)
            contrast_issues.sort(key=lambda x: x["contrast"])
            
            return self.create_finding(
                entity_id=screen_id,
                issue=f"WCAG contrast violations ({len(contrast_issues)} components)",
                rationale=(
                    f"Found {len(contrast_issues)} components with insufficient color contrast. "
                    f"WCAG 1.4.3 requires 4.5:1 for normal text, 3:1 for large text and UI. "
                    f"Lowest contrast: {contrast_issues[0]['contrast']}:1 "
                    f"(need {contrast_issues[0]['required']}:1) on {contrast_issues[0]['component_type']}."
                ),
                severity=Severity.HIGH,
                standards_refs=[self.link_wcag("1.4.3")] if self.standards_registry else [],
                metadata={
                    "violation_count": len(contrast_issues),
                    "violations": contrast_issues[:10],  # Top 10 worst
                    "wcag_criteria": "1.4.3",
                },
            )
        
        return None
    
    def _check_text_sizes(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if text meets minimum size requirements.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if text size issues found
        """
        min_height = self.config["min_text_height"]
        small_text = []
        
        text_components = [c for c in components if c.type == "text"]
        
        for comp in text_components:
            bbox = comp.bounding_box
            
            # Check if text height is below minimum
            if bbox.height < min_height:
                small_text.append({
                    "component_id": comp.id,
                    "height": bbox.height,
                    "minimum": min_height,
                })
        
        if small_text:
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Text below minimum size ({len(small_text)} instances)",
                rationale=(
                    f"Found {len(small_text)} text components below {min_height}px height. "
                    "Small text is difficult to read, especially for users with visual "
                    "impairments. WCAG recommends minimum 9pt (~12px) for body text."
                ),
                severity=Severity.MEDIUM,
                standards_refs=[self.link_wcag("1.4.4")] if self.standards_registry else [],
                metadata={
                    "small_text_count": len(small_text),
                    "small_text_examples": small_text[:5],
                    "minimum_height": min_height,
                },
            )
        
        return None
    
    def _check_interactive_visibility(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if interactive elements are visually distinguishable.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if interactive visibility issues found
        """
        interactive_types = self.config["interactive_types"]
        interactive_components = [
            c for c in components if c.type in interactive_types
        ]
        
        if not interactive_components:
            return None
        
        # Check for interactive elements without clear visual distinction
        indistinct = []
        
        for comp in interactive_components:
            # Check if component has distinguishing visual properties
            has_border = comp.properties.get("border") is not None
            has_background = comp.properties.get("background") is not None
            has_distinct_color = False
            
            fg = comp.properties.get("color")
            bg = comp.properties.get("background")
            
            if fg and bg and isinstance(fg, list) and isinstance(bg, list):
                if len(fg) >= 3 and len(bg) >= 3:
                    # Check if foreground and background are different enough
                    fg_lum = rgb_to_luminance(fg[0], fg[1], fg[2])
                    bg_lum = rgb_to_luminance(bg[0], bg[1], bg[2])
                    contrast = calculate_contrast_ratio(fg_lum, bg_lum)
                    has_distinct_color = contrast > 2.0
            
            # Interactive elements should have some visual distinction
            is_distinct = has_border or has_background or has_distinct_color
            
            if not is_distinct:
                indistinct.append({
                    "component_id": comp.id,
                    "component_type": comp.type,
                })
        
        if indistinct:
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Interactive elements may lack visual distinction ({len(indistinct)})",
                rationale=(
                    f"Found {len(indistinct)} interactive components without clear visual "
                    "distinction (border, background, or color contrast). Users need to "
                    "be able to identify interactive elements at a glance."
                ),
                severity=Severity.MEDIUM,
                standards_refs=[self.link_wcag("1.4.11")] if self.standards_registry else [],
                metadata={
                    "indistinct_count": len(indistinct),
                    "indistinct_examples": indistinct[:5],
                },
            )
        
        return None
    
    def _check_touch_targets(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if touch targets meet minimum size requirements.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if touch target issues found
        """
        interactive_types = self.config["interactive_types"]
        min_size = self.config["min_touch_target"]
        
        small_targets = []
        
        for comp in components:
            if comp.type not in interactive_types:
                continue
            
            bbox = comp.bounding_box
            
            # Check if touch target is large enough
            if bbox.width < min_size or bbox.height < min_size:
                small_targets.append({
                    "component_id": comp.id,
                    "component_type": comp.type,
                    "width": bbox.width,
                    "height": bbox.height,
                    "minimum": min_size,
                })
        
        if small_targets:
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Touch targets below minimum size ({len(small_targets)})",
                rationale=(
                    f"Found {len(small_targets)} interactive components smaller than "
                    f"{min_size}x{min_size}px. Small touch targets are difficult to "
                    "activate, especially for users with motor impairments. "
                    "WCAG 2.5.5 recommends minimum 44x44px touch targets."
                ),
                severity=Severity.MEDIUM,
                standards_refs=[self.link_wcag("2.5.5")] if self.standards_registry else [],
                metadata={
                    "small_target_count": len(small_targets),
                    "small_targets": small_targets[:5],
                    "minimum_size": min_size,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_accessibility(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run accessibility audit."""
    auditor = AccessibilityAuditor(config=config)
    return auditor.audit(screen, components)
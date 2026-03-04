"""
Error States auditor for analyzing error presentation.

Analyzes:
- Error messages styled consistently
- Errors feel helpful (not hostile)
- Error text is clear and actionable
"""

from typing import Any, Optional
import re

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
    # Component types that commonly contain errors
    "error_container_types": ["text", "container", "card"],
    # Properties that suggest error state
    "error_property_hints": ["error", "warning", "alert", "danger", "invalid", "failed"],
    # Text patterns that suggest error messages
    "error_text_patterns": [
        r"error",
        r"failed",
        r"invalid",
        r"incorrect",
        r"wrong",
        r"unable",
        r"could not",
        r"please (try|enter|select)",
        r"must be",
        r"required",
    ],
    # Minimum components to analyze
    "min_components": 1,
    # Colors that suggest error (red tones)
    "error_color_ranges": [
        (200, 255, 0, 100, 0, 100),   # High R, low G, low B = red
    ],
}


# =============================================================================
# ERROR STATES AUDITOR
# =============================================================================

class ErrorStatesAuditor(BaseAuditor):
    """Auditor for error states dimension.
    
    Analyzes error message styling and helpfulness.
    """
    
    dimension = AuditDimension.ERROR_STATES
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run error states audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of error state findings
        """
        findings = []
        
        # Detect error-related components
        error_components = self._detect_error_components(components)
        
        if not error_components:
            return findings
        
        # Check 1: Error message styling consistency
        style_finding = self._check_error_styling(
            error_components, screen.id
        )
        if style_finding:
            findings.append(style_finding)
        
        # Check 2: Error message helpfulness
        helpful_finding = self._check_error_helpfulness(
            error_components, screen.id
        )
        if helpful_finding:
            findings.append(helpful_finding)
        
        # Check 3: Error visibility/placement
        visibility_finding = self._check_error_visibility(
            error_components, screen.id
        )
        if visibility_finding:
            findings.append(visibility_finding)
        
        return findings
    
    def _detect_error_components(
        self,
        components: list[Component],
    ) -> list[Component]:
        """Detect components that appear to be error-related.
        
        Args:
            components: List of all components
            
        Returns:
            List of error-related components
        """
        error_hints = self.config["error_property_hints"]
        error_patterns = self.config["error_text_patterns"]
        error_components = []
        
        for comp in components:
            # Check component properties for error hints
            props_str = str(comp.properties).lower()
            
            is_error = any(hint in props_str for hint in error_hints)
            
            # Check for error color (red tones in color property)
            if "color" in comp.properties or "background" in comp.properties:
                color = comp.properties.get("color") or comp.properties.get("background")
                if isinstance(color, list) and len(color) >= 3:
                    r, g, b = color[0], color[1], color[2]
                    # Check for red-dominant color
                    if r > 180 and g < 120 and b < 120:
                        is_error = True
            
            # Check for error text patterns in text content
            text_content = comp.properties.get("text", "")
            if text_content:
                text_lower = text_content.lower()
                for pattern in error_patterns:
                    if re.search(pattern, text_lower):
                        is_error = True
                        break
            
            if is_error:
                error_components.append(comp)
        
        return error_components
    
    def _check_error_styling(
        self,
        error_components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if error messages are styled consistently.
        
        Args:
            error_components: Error-related components
            screen_id: Screen ID
            
        Returns:
            Finding if error styling is inconsistent
        """
        if len(error_components) < 2:
            return None
        
        # Check for consistent styling across error components
        styles = []
        for comp in error_components:
            style = {}
            
            # Check color
            if "color" in comp.properties:
                style["color"] = tuple(comp.properties["color"]) if isinstance(comp.properties["color"], list) else comp.properties["color"]
            
            # Check background
            if "background" in comp.properties:
                style["background"] = tuple(comp.properties["background"]) if isinstance(comp.properties["background"], list) else comp.properties["background"]
            
            # Check font weight/size via bbox
            bbox = comp.bounding_box
            style["height"] = bbox.height
            
            if style:
                styles.append(style)
        
        # Check for style variation
        if len(styles) < 2:
            return None
        
        # Check height consistency (error messages should be consistent)
        heights = [s.get("height", 0) for s in styles]
        if heights:
            mean_height = sum(heights) / len(heights)
            if mean_height > 0:
                height_variance = sum((h - mean_height) ** 2 for h in heights) / len(heights)
                height_cv = (height_variance ** 0.5) / mean_height
                
                if height_cv > 0.5:  # 50% variance
                    return self.create_finding(
                        entity_id=screen_id,
                        issue="Inconsistent error message styling",
                        rationale=(
                            f"Error messages have inconsistent sizes (CV: {height_cv:.2f}). "
                            "Consistent error styling helps users quickly recognize and "
                            "understand error states across the interface."
                        ),
                        severity=Severity.LOW,
                        metadata={
                            "height_coefficient_of_variation": height_cv,
                            "error_count": len(error_components),
                        },
                    )
        
        return None
    
    def _check_error_helpfulness(
        self,
        error_components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if error messages appear helpful.
        
        Args:
            error_components: Error-related components
            screen_id: Screen ID
            
        Returns:
            Finding if error messages may not be helpful
        """
        # Check for actionable error messages
        actionable_patterns = [
            r"please",
            r"try",
            r"enter",
            r"select",
            r"click",
            r"must",
            r"should",
            r"need to",
        ]
        
        has_actionable = False
        text_components = [c for c in error_components if c.type == "text"]
        
        for comp in text_components:
            text = comp.properties.get("text", "").lower()
            for pattern in actionable_patterns:
                if re.search(pattern, text):
                    has_actionable = True
                    break
            if has_actionable:
                break
        
        # Check for very short error messages (likely not helpful)
        short_errors = []
        for comp in text_components:
            text = comp.properties.get("text", "")
            if len(text) < 10 and len(text) > 0:  # Very short
                short_errors.append(text)
        
        if short_errors:
            return self.create_finding(
                entity_id=screen_id,
                issue="Error messages may lack helpful detail",
                rationale=(
                    f"Found {len(short_errors)} very short error message(s). "
                    "Effective error messages explain what went wrong and how to fix it. "
                    f"Short messages like '{short_errors[0]}' may leave users confused."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "short_error_count": len(short_errors),
                    "short_error_examples": short_errors[:3],
                    "has_actionable_guidance": has_actionable,
                },
            )
        
        if not has_actionable and text_components:
            return self.create_finding(
                entity_id=screen_id,
                issue="Error messages lack actionable guidance",
                rationale=(
                    "Error messages detected but none appear to include "
                    "actionable guidance. Effective errors tell users what went wrong "
                    "and what they can do to fix it."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "error_count": len(text_components),
                    "has_actionable_guidance": False,
                },
            )
        
        return None
    
    def _check_error_visibility(
        self,
        error_components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if error messages are visible/well-positioned.
        
        Args:
            error_components: Error-related components
            screen_id: Screen ID
            
        Returns:
            Finding if error visibility is problematic
        """
        if not error_components:
            return None
        
        # Check if errors are too small to be noticeable
        small_errors = []
        for comp in error_components:
            bbox = comp.bounding_box
            # Very small error components might be hard to see
            if bbox.width < 50 or bbox.height < 16:
                small_errors.append(comp.id)
        
        if len(small_errors) > len(error_components) * 0.5:
            return self.create_finding(
                entity_id=screen_id,
                issue="Error messages may be too small",
                rationale=(
                    f"{len(small_errors)} of {len(error_components)} error components "
                    "are very small and may be difficult for users to notice. "
                    "Error messages should be prominent enough to catch attention."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "small_error_count": len(small_errors),
                    "total_error_count": len(error_components),
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_error_states(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run error states audit."""
    auditor = ErrorStatesAuditor(config=config)
    return auditor.audit(screen, components)
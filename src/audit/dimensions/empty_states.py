"""
Empty States auditor for analyzing blank screen handling.

Analyzes:
- Blank screens feel intentional (not broken)
- User guided toward first action
- Empty state messaging is helpful
- Detect low component count as potential empty state
"""

from typing import Any, Optional

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_center,
    calculate_density,
    group_by_type,
)
from src.db.models import Screen, Component, BoundingBox, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Minimum components to consider a screen "populated"
    "min_components_for_populated": 5,
    # Maximum density threshold for empty state (components per 10k pixels)
    "empty_density_threshold": 0.1,
    # Minimum screen coverage for non-empty (percentage)
    "min_coverage_threshold": 0.05,
    # Types that suggest intentional empty state design
    "empty_state_hint_types": ["text", "image", "icon", "button"],
    # Types that suggest guidance toward action
    "action_hint_types": ["button", "input"],
}


# =============================================================================
# EMPTY STATES AUDITOR
# =============================================================================

class EmptyStatesAuditor(BaseAuditor):
    """Auditor for empty states dimension.
    
    Analyzes screens that appear to be empty states and checks
    for intentional design and user guidance.
    """
    
    dimension = AuditDimension.EMPTY_STATES
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run empty states audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of empty state findings
        """
        findings = []
        
        # Get screen dimensions
        screen_width = getattr(screen, 'width', 1920)
        screen_height = getattr(screen, 'height', 1080)
        
        # Check if this appears to be an empty state
        is_empty_state = self._detect_empty_state(
            components, screen_width, screen_height
        )
        
        if not is_empty_state:
            return findings
        
        # Check 1: Intentional design
        design_finding = self._check_intentional_design(
            components, screen.id, screen_width, screen_height
        )
        if design_finding:
            findings.append(design_finding)
        
        # Check 2: User guidance
        guidance_finding = self._check_user_guidance(
            components, screen.id
        )
        if guidance_finding:
            findings.append(guidance_finding)
        
        # Check 3: Helpful messaging
        message_finding = self._check_helpful_messaging(
            components, screen.id
        )
        if message_finding:
            findings.append(message_finding)
        
        return findings
    
    def _detect_empty_state(
        self,
        components: list[Component],
        screen_width: int,
        screen_height: int,
    ) -> bool:
        """Detect if this screen appears to be an empty state.
        
        Args:
            components: List of components
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            True if this appears to be an empty state
        """
        # Low component count suggests empty state
        if len(components) < self.config["min_components_for_populated"]:
            return True
        
        # Low density suggests empty state
        density = calculate_density(components, screen_width, screen_height)
        if density < self.config["empty_density_threshold"]:
            return True
        
        # Low screen coverage suggests empty state
        screen_area = screen_width * screen_height
        component_area = sum(
            c.bounding_box.width * c.bounding_box.height
            for c in components
        )
        coverage = component_area / screen_area if screen_area > 0 else 0
        
        if coverage < self.config["min_coverage_threshold"]:
            return True
        
        return False
    
    def _check_intentional_design(
        self,
        components: list[Component],
        screen_id: str,
        screen_width: int,
        screen_height: int,
    ) -> Optional[AuditFindingCreate]:
        """Check if empty state appears intentionally designed.
        
        Args:
            components: List of components
            screen_id: Screen ID
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            Finding if empty state lacks intentional design
        """
        hint_types = self.config["empty_state_hint_types"]
        
        # Check for empty state design elements
        has_illustration = any(c.type == "image" for c in components)
        has_icon = any(c.type == "icon" for c in components)
        has_text = any(c.type == "text" for c in components)
        
        # Check for centered content (common in intentional empty states)
        center_x = screen_width / 2
        center_y = screen_height / 2
        
        centered_components = 0
        for comp in components:
            comp_center = get_bbox_center(comp.bounding_box)
            # Within 20% of center
            if (abs(comp_center[0] - center_x) < screen_width * 0.2 and
                abs(comp_center[1] - center_y) < screen_height * 0.2):
                centered_components += 1
        
        has_centered_content = centered_components > 0
        
        # Good empty state has: illustration/icon + text + centered
        design_score = sum([
            has_illustration or has_icon,
            has_text,
            has_centered_content,
        ])
        
        if design_score < 2 and len(components) > 0:
            return self.create_finding(
                entity_id=screen_id,
                issue="Empty state lacks intentional design",
                rationale=(
                    "This screen appears to be an empty state but lacks "
                    "intentional design elements. Well-designed empty states "
                    "include illustrations or icons, helpful text, and centered content "
                    "to feel deliberate rather than broken."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "has_illustration": has_illustration,
                    "has_icon": has_icon,
                    "has_text": has_text,
                    "has_centered_content": has_centered_content,
                    "design_score": design_score,
                },
            )
        
        return None
    
    def _check_user_guidance(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if empty state guides user toward action.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if empty state lacks user guidance
        """
        action_types = self.config["action_hint_types"]
        
        # Check for actionable elements
        has_button = any(c.type == "button" for c in components)
        has_input = any(c.type == "input" for c in components)
        has_link = any(
            c.type == "text" and "link" in str(c.properties.get('style', '')).lower()
            for c in components
        )
        
        has_action = has_button or has_input or has_link
        
        if not has_action:
            return self.create_finding(
                entity_id=screen_id,
                issue="Empty state lacks user guidance",
                rationale=(
                    "This empty state does not guide users toward a first action. "
                    "Effective empty states include a clear call-to-action button "
                    "or link to help users get started."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "has_button": has_button,
                    "has_input": has_input,
                    "has_link": has_link,
                },
            )
        
        return None
    
    def _check_helpful_messaging(
        self,
        components: list[Component],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if empty state has helpful messaging.
        
        Args:
            components: List of components
            screen_id: Screen ID
            
        Returns:
            Finding if empty state lacks helpful messaging
        """
        text_components = [c for c in components if c.type == "text"]
        
        if not text_components:
            return self.create_finding(
                entity_id=screen_id,
                issue="Empty state lacks helpful messaging",
                rationale=(
                    "This empty state has no text content to explain the situation "
                    "or guide users. Add a brief explanation of why the screen is empty "
                    "and what users can do about it."
                ),
                severity=Severity.HIGH,
                metadata={
                    "text_count": 0,
                },
            )
        
        # Check if text content seems substantial (not just labels)
        # Use bounding box size as proxy for text importance
        substantial_text = [
            t for t in text_components
            if t.bounding_box.width > 100  # Reasonably wide text
        ]
        
        if len(substantial_text) == 0 and len(text_components) > 0:
            return self.create_finding(
                entity_id=screen_id,
                issue="Empty state messaging may be insufficient",
                rationale=(
                    "This empty state has only brief text labels. "
                    "Consider adding a headline and description to explain "
                    "why the screen is empty and what users can do."
                ),
                severity=Severity.LOW,
                metadata={
                    "text_count": len(text_components),
                    "substantial_text_count": 0,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_empty_states(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run empty states audit."""
    auditor = EmptyStatesAuditor(config=config)
    return auditor.audit(screen, components)
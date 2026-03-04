"""
Components auditor for analyzing UI patterns and consistency.

Analyzes:
- Similar components look similar (buttons, inputs)
- Visual patterns are consistent
- Component styles don't proliferate
"""

from typing import Any, Optional
from collections import defaultdict

from src.audit.models import AuditDimension, AuditFindingCreate
from src.audit.dimensions.base import (
    BaseAuditor,
    get_bbox_area,
    get_bbox_center,
    group_by_type,
)
from src.db.models import Screen, Component, Severity


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    # Maximum size variance ratio for similar components
    "max_size_variance": 0.3,
    # Minimum components of same type to check consistency
    "min_type_count": 3,
    # Maximum distinct style variations per component type
    "max_style_variations": 3,
    # Minimum components to analyze
    "min_components": 5,
}


# =============================================================================
# COMPONENTS AUDITOR
# =============================================================================

class ComponentsAuditor(BaseAuditor):
    """Auditor for components dimension.
    
    Analyzes component consistency, pattern adherence, and style proliferation.
    """
    
    dimension = AuditDimension.COMPONENTS
    
    def __init__(
        self,
        standards_registry: Optional[Any] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        super().__init__(standards_registry=standards_registry, config=config)
        self.config = {**DEFAULT_CONFIG, **self.config}
    
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run components audit.
        
        Args:
            screen: Screen to audit
            components: List of components
            
        Returns:
            List of component findings
        """
        findings = []
        
        if len(components) < self.config["min_components"]:
            return findings
        
        # Group components by type
        by_type = group_by_type(components)
        
        # Check 1: Size consistency within component types
        size_finding = self._check_size_consistency(by_type, screen.id)
        if size_finding:
            findings.append(size_finding)
        
        # Check 2: Style proliferation
        style_finding = self._check_style_proliferation(by_type, screen.id)
        if style_finding:
            findings.append(style_finding)
        
        # Check 3: Position consistency (similar components in similar positions)
        position_finding = self._check_position_consistency(by_type, screen.id)
        if position_finding:
            findings.append(position_finding)
        
        return findings
    
    def _check_size_consistency(
        self,
        by_type: dict[str, list[Component]],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if components of same type have consistent sizes.
        
        Args:
            by_type: Components grouped by type
            screen_id: Screen ID
            
        Returns:
            Finding if size inconsistency found
        """
        min_count = self.config["min_type_count"]
        max_variance = self.config["max_size_variance"]
        
        inconsistent_types = []
        
        for comp_type, comps in by_type.items():
            if len(comps) < min_count:
                continue
            
            # Calculate areas
            areas = [get_bbox_area(c.bounding_box) for c in comps]
            mean_area = sum(areas) / len(areas)
            
            if mean_area == 0:
                continue
            
            # Calculate variance
            variance = sum((a - mean_area) ** 2 for a in areas) / len(areas)
            cv = (variance ** 0.5) / mean_area
            
            if cv > max_variance:
                inconsistent_types.append({
                    'type': comp_type,
                    'count': len(comps),
                    'variance': round(cv, 2),
                    'sizes': [(c.bounding_box.width, c.bounding_box.height) for c in comps[:5]],
                })
        
        if inconsistent_types:
            type_list = ', '.join(f"{t['type']} ({t['variance']:.0%})" for t in inconsistent_types[:3])
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Inconsistent sizes for {len(inconsistent_types)} component types",
                rationale=(
                    f"Component types with size variance: {type_list}. "
                    "Consistent component sizes create visual predictability."
                ),
                severity=Severity.MEDIUM,
                metadata={
                    "inconsistent_types": inconsistent_types,
                },
            )
        
        return None
    
    def _check_style_proliferation(
        self,
        by_type: dict[str, list[Component]],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if there are too many style variations per component type.
        
        Args:
            by_type: Components grouped by type
            screen_id: Screen ID
            
        Returns:
            Finding if style proliferation found
        """
        min_count = self.config["min_type_count"]
        max_variations = self.config["max_style_variations"]
        
        proliferating_types = []
        
        for comp_type, comps in by_type.items():
            if len(comps) < min_count:
                continue
            
            # Group by approximate size (width x height buckets)
            size_buckets: dict[str, int] = defaultdict(int)
            for c in comps:
                # Quantize to 10px buckets
                w_bucket = int(c.bounding_box.width / 10) * 10
                h_bucket = int(c.bounding_box.height / 10) * 10
                key = f"{w_bucket}x{h_bucket}"
                size_buckets[key] += 1
            
            # Count distinct variations
            if len(size_buckets) > max_variations:
                proliferating_types.append({
                    'type': comp_type,
                    'variations': len(size_buckets),
                    'buckets': dict(sorted(size_buckets.items(), key=lambda x: -x[1])[:5]),
                })
        
        if proliferating_types:
            type_list = ', '.join(f"{t['type']} ({t['variations']} variations)" for t in proliferating_types[:3])
            return self.create_finding(
                entity_id=screen_id,
                issue=f"Style proliferation detected in {len(proliferating_types)} component types",
                rationale=(
                    f"Too many size variations: {type_list}. "
                    "Limit variations to maintain design system consistency."
                ),
                severity=Severity.LOW,
                metadata={
                    "proliferating_types": proliferating_types,
                },
            )
        
        return None
    
    def _check_position_consistency(
        self,
        by_type: dict[str, list[Component]],
        screen_id: str,
    ) -> Optional[AuditFindingCreate]:
        """Check if similar components appear in consistent positions.
        
        Args:
            by_type: Components grouped by type
            screen_id: Screen ID
            
        Returns:
            Finding if position inconsistency found
        """
        # Focus on navigation and action components
        relevant_types = {'button', 'navigation', 'link', 'input'}
        
        position_issues = []
        
        for comp_type in relevant_types:
            comps = by_type.get(comp_type, [])
            if len(comps) < 3:
                continue
            
            # Check if components are scattered vs grouped
            y_positions = [c.bounding_box.y for c in comps]
            y_spread = max(y_positions) - min(y_positions)
            
            # If spread is large relative to component count, they're scattered
            if y_spread > 500 and len(comps) < 5:
                position_issues.append({
                    'type': comp_type,
                    'count': len(comps),
                    'y_spread': y_spread,
                })
        
        if position_issues:
            type_list = ', '.join(f"{t['type']} (spread: {t['y_spread']:.0f}px)" for t in position_issues[:3])
            return self.create_finding(
                entity_id=screen_id,
                issue="Similar components scattered across screen",
                rationale=(
                    f"Scattered: {type_list}. "
                    "Group related components for better usability."
                ),
                severity=Severity.LOW,
                metadata={
                    "position_issues": position_issues,
                },
            )
        
        return None


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def audit_components(
    screen: Screen,
    components: list[Component],
    config: Optional[dict[str, Any]] = None,
) -> list[AuditFindingCreate]:
    """Convenience function to run components audit."""
    auditor = ComponentsAuditor(config=config)
    return auditor.audit(screen, components)
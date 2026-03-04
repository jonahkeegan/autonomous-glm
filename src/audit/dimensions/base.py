"""
Base auditor class for visual audit dimensions.

Provides common utilities and interface for all dimension auditors.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import math

from src.audit.models import (
    AuditDimension,
    AuditFindingCreate,
    StandardsReference,
    DesignTokenReference,
    WCAGReference,
)
from src.audit.standards import StandardsRegistry
from src.db.models import Screen, Component, BoundingBox, Severity, EntityType


# =============================================================================
# BASE AUDITOR
# =============================================================================

class BaseAuditor(ABC):
    """Abstract base class for dimension auditors.
    
    All dimension auditors inherit from this class and implement
    the audit() method to analyze screens and return findings.
    
    Attributes:
        dimension: The audit dimension this auditor handles
        standards_registry: Registry for linking findings to standards
    """
    
    dimension: AuditDimension
    
    def __init__(
        self,
        standards_registry: Optional[StandardsRegistry] = None,
        config: Optional[dict[str, Any]] = None,
    ):
        """Initialize the auditor.
        
        Args:
            standards_registry: Registry for standards references
            config: Optional configuration dictionary
        """
        self.standards_registry = standards_registry or StandardsRegistry()
        self.config = config or {}
    
    @abstractmethod
    def audit(self, screen: Screen, components: list[Component]) -> list[AuditFindingCreate]:
        """Run the dimension audit.
        
        Args:
            screen: The screen to audit
            components: List of detected components on the screen
            
        Returns:
            List of audit findings
        """
        pass
    
    def create_finding(
        self,
        entity_id: str,
        issue: str,
        rationale: Optional[str] = None,
        severity: Severity = Severity.MEDIUM,
        standards_refs: Optional[list[StandardsReference]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditFindingCreate:
        """Create an audit finding with standard fields populated.
        
        Args:
            entity_id: ID of the entity with the issue
            issue: Description of the issue
            rationale: Why this is an issue
            severity: Issue severity
            standards_refs: References to design standards
            metadata: Additional metadata
            
        Returns:
            AuditFindingCreate ready for persistence
        """
        return AuditFindingCreate(
            entity_type=EntityType.SCREEN,
            entity_id=entity_id,
            dimension=self.dimension,
            issue=issue,
            rationale=rationale,
            severity=severity,
            standards_refs=standards_refs or [],
            metadata=metadata,
        )
    
    def link_wcag(
        self,
        criterion: str,
        custom_note: Optional[str] = None,
    ) -> StandardsReference:
        """Link finding to a WCAG criterion.
        
        Args:
            criterion: WCAG criterion number (e.g., "1.4.3")
            custom_note: Optional custom note
            
        Returns:
            StandardsReference with WCAG link
        """
        return self.standards_registry.link_finding_to_standard(
            wcag_criterion=criterion,
            custom=custom_note,
        )
    
    def link_design_token(
        self,
        token_name: str,
        token_type: str,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
    ) -> StandardsReference:
        """Link finding to a design system token.
        
        Args:
            token_name: Name of the design token
            token_type: Type of token (color, spacing, typography)
            expected_value: Expected value from design system
            actual_value: Actual value detected
            
        Returns:
            StandardsReference with design token link
        """
        return StandardsReference(
            design_token=DesignTokenReference(
                token_name=token_name,
                token_type=token_type,
                expected_value=expected_value,
                actual_value=actual_value,
            )
        )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points.
    
    Args:
        p1: First point (x, y)
        p2: Second point (x, y)
        
    Returns:
        Euclidean distance
    """
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def get_bbox_center(bbox: BoundingBox) -> tuple[float, float]:
    """Get the center point of a bounding box.
    
    Args:
        bbox: Bounding box
        
    Returns:
        Center point (x, y)
    """
    return (bbox.x + bbox.width / 2, bbox.y + bbox.height / 2)


def get_bbox_area(bbox: BoundingBox) -> float:
    """Get the area of a bounding box.
    
    Args:
        bbox: Bounding box
        
    Returns:
        Area in square pixels
    """
    return bbox.width * bbox.height


def bboxes_overlap(bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
    """Check if two bounding boxes overlap.
    
    Args:
        bbox1: First bounding box
        bbox2: Second bounding box
        
    Returns:
        True if boxes overlap
    """
    return not (
        bbox1.x + bbox1.width < bbox2.x or
        bbox2.x + bbox2.width < bbox1.x or
        bbox1.y + bbox1.height < bbox2.y or
        bbox2.y + bbox2.height < bbox1.y
    )


def bbox_contains(outer: BoundingBox, inner: BoundingBox) -> bool:
    """Check if outer bounding box contains inner bounding box.
    
    Args:
        outer: Outer bounding box
        inner: Inner bounding box
        
    Returns:
        True if outer contains inner
    """
    return (
        outer.x <= inner.x and
        outer.y <= inner.y and
        outer.x + outer.width >= inner.x + inner.width and
        outer.y + outer.height >= inner.y + inner.height
    )


def quantize_to_grid(value: float, grid_base: int = 4) -> int:
    """Quantize a value to the nearest grid base.
    
    Args:
        value: Value to quantize
        grid_base: Grid base (default 4px)
        
    Returns:
        Quantized value
    """
    return round(value / grid_base) * grid_base


def is_on_grid(value: float, grid_base: int = 4, tolerance: int = 1) -> bool:
    """Check if a value is on the grid within tolerance.
    
    Args:
        value: Value to check
        grid_base: Grid base (default 4px)
        tolerance: Tolerance in pixels (default 1)
        
    Returns:
        True if value is on grid within tolerance
    """
    remainder = value % grid_base
    return remainder <= tolerance or remainder >= (grid_base - tolerance)


def calculate_contrast_ratio(l1: float, l2: float) -> float:
    """Calculate WCAG contrast ratio between two luminances.
    
    Args:
        l1: First luminance (0-1)
        l2: Second luminance (0-1)
        
    Returns:
        Contrast ratio (1:1 to 21:1)
    """
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def rgb_to_luminance(r: int, g: int, b: int) -> float:
    """Convert RGB to relative luminance.
    
    Args:
        r: Red (0-255)
        g: Green (0-255)
        b: Blue (0-255)
        
    Returns:
        Relative luminance (0-1)
    """
    def adjust(c: int) -> float:
        c_f = c / 255.0
        return c_f / 12.92 if c_f <= 0.03928 else ((c_f + 0.055) / 1.055) ** 2.4
    
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def group_by_type(components: list[Component]) -> dict[str, list[Component]]:
    """Group components by their type.
    
    Args:
        components: List of components
        
    Returns:
        Dictionary mapping type to list of components
    """
    groups: dict[str, list[Component]] = {}
    for comp in components:
        if comp.type not in groups:
            groups[comp.type] = []
        groups[comp.type].append(comp)
    return groups


def get_components_in_region(
    components: list[Component],
    region: BoundingBox,
) -> list[Component]:
    """Get all components whose center is within a region.
    
    Args:
        components: List of components
        region: Region bounding box
        
    Returns:
        List of components in region
    """
    result = []
    for comp in components:
        center = get_bbox_center(comp.bounding_box)
        if (
            region.x <= center[0] <= region.x + region.width and
            region.y <= center[1] <= region.y + region.height
        ):
            result.append(comp)
    return result


def calculate_density(
    components: list[Component],
    screen_width: int,
    screen_height: int,
) -> float:
    """Calculate component density (components per 10,000 pixels).
    
    Args:
        components: List of components
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        
    Returns:
        Density (components per 10,000 pixels)
    """
    area = screen_width * screen_height
    if area == 0:
        return 0.0
    return (len(components) / area) * 10000
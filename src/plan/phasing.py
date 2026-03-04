"""
Phase classification for plan synthesis.

Provides rule-based classification of audit findings into phases
(Critical → Refinement → Polish) based on severity and dimension.
"""

from typing import Optional

from src.audit.models import AuditDimension, AuditFindingCreate
from src.db.models import Severity
from src.plan.models import PhaseType


# =============================================================================
# DEFAULT CLASSIFICATION RULES
# =============================================================================

# Severity to phase mapping (primary classification)
SEVERITY_PHASE_MAP: dict[Severity, PhaseType] = {
    Severity.CRITICAL: PhaseType.CRITICAL,
    Severity.HIGH: PhaseType.CRITICAL,  # High also goes to Critical
    Severity.MEDIUM: PhaseType.REFINEMENT,
    Severity.LOW: PhaseType.POLISH,
}

# Dimension overrides (take precedence over severity)
# These dimensions always go to a specific phase regardless of severity
DIMENSION_PHASE_OVERRIDE: dict[AuditDimension, PhaseType] = {
    # Always Critical - core usability and accessibility
    AuditDimension.VISUAL_HIERARCHY: PhaseType.CRITICAL,
    AuditDimension.ACCESSIBILITY: PhaseType.CRITICAL,
    
    # Always Refinement - visual polish that builds on structure
    AuditDimension.SPACING_RHYTHM: PhaseType.REFINEMENT,
    AuditDimension.TYPOGRAPHY: PhaseType.REFINEMENT,
    AuditDimension.COLOR: PhaseType.REFINEMENT,
    AuditDimension.ALIGNMENT_GRID: PhaseType.REFINEMENT,
    AuditDimension.COMPONENTS: PhaseType.REFINEMENT,
    AuditDimension.DENSITY: PhaseType.REFINEMENT,
    
    # Always Polish - nice-to-have improvements
    AuditDimension.DARK_MODE_THEMING: PhaseType.POLISH,
    AuditDimension.EMPTY_STATES: PhaseType.POLISH,
    AuditDimension.LOADING_STATES: PhaseType.POLISH,
    AuditDimension.ERROR_STATES: PhaseType.POLISH,
    AuditDimension.ICONOGRAPHY: PhaseType.POLISH,
    
    # Deferred dimensions (not yet implemented)
    # AuditDimension.MOTION_TRANSITIONS: PhaseType.POLISH,
    # AuditDimension.RESPONSIVENESS: PhaseType.REFINEMENT,
}


# =============================================================================
# PHASE CLASSIFIER
# =============================================================================

class PhaseClassifier:
    """Classifies audit findings into plan phases.
    
    Uses a two-step process:
    1. Check for dimension override (some dimensions always go to a specific phase)
    2. Fall back to severity-based classification
    
    This ensures accessibility and hierarchy issues are always Critical,
    while state-related issues are always Polish regardless of severity.
    """
    
    def __init__(
        self,
        severity_map: Optional[dict[Severity, PhaseType]] = None,
        dimension_overrides: Optional[dict[AuditDimension, PhaseType]] = None,
    ):
        """Initialize the classifier with optional custom rules.
        
        Args:
            severity_map: Custom severity → phase mapping
            dimension_overrides: Custom dimension → phase overrides
        """
        self.severity_map = severity_map or SEVERITY_PHASE_MAP
        self.dimension_overrides = dimension_overrides or DIMENSION_PHASE_OVERRIDE
    
    def classify_by_severity(self, severity: Severity) -> PhaseType:
        """Classify based on severity alone.
        
        Args:
            severity: The severity level of the finding
            
        Returns:
            The appropriate phase type
        """
        return self.severity_map.get(severity, PhaseType.REFINEMENT)
    
    def classify_by_dimension(self, dimension: AuditDimension) -> Optional[PhaseType]:
        """Classify based on dimension override.
        
        Args:
            dimension: The audit dimension
            
        Returns:
            The override phase type, or None if no override exists
        """
        return self.dimension_overrides.get(dimension)
    
    def classify_finding(
        self, 
        finding: AuditFindingCreate,
        use_override: bool = True
    ) -> PhaseType:
        """Classify an audit finding into a phase.
        
        Args:
            finding: The audit finding to classify
            use_override: Whether to check dimension overrides first
            
        Returns:
            The appropriate phase type
        """
        # Step 1: Check dimension override
        if use_override:
            override = self.classify_by_dimension(finding.dimension)
            if override is not None:
                return override
        
        # Step 2: Fall back to severity
        return self.classify_by_severity(finding.severity)
    
    def classify(
        self, 
        dimension: AuditDimension, 
        severity: Severity,
        use_override: bool = True
    ) -> PhaseType:
        """Classify by dimension and severity directly.
        
        Convenience method for when you have the components separately.
        
        Args:
            dimension: The audit dimension
            severity: The severity level
            use_override: Whether to check dimension overrides first
            
        Returns:
            The appropriate phase type
        """
        # Step 1: Check dimension override
        if use_override:
            override = self.classify_by_dimension(dimension)
            if override is not None:
                return override
        
        # Step 2: Fall back to severity
        return self.classify_by_severity(severity)
    
    def get_phase_order(self, phase: PhaseType) -> int:
        """Get the execution order for a phase.
        
        Args:
            phase: The phase type
            
        Returns:
            Order number (1 = first, 3 = last)
        """
        return phase.order()


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

# Default classifier instance
_default_classifier = PhaseClassifier()


def classify_finding(finding: AuditFindingCreate) -> PhaseType:
    """Classify an audit finding using the default classifier.
    
    This is a convenience function for quick classification without
    instantiating a PhaseClassifier.
    
    Args:
        finding: The audit finding to classify
        
    Returns:
        The appropriate phase type
    """
    return _default_classifier.classify_finding(finding)


def classify(dimension: AuditDimension, severity: Severity) -> PhaseType:
    """Classify by dimension and severity using the default classifier.
    
    Convenience function for quick classification.
    
    Args:
        dimension: The audit dimension
        severity: The severity level
        
    Returns:
        The appropriate phase type
    """
    return _default_classifier.classify(dimension, severity)
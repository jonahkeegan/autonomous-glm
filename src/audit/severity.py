"""
Severity classification engine for audit findings.

Provides matrix-based severity classification for consistent, reproducible results.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.db.models import Severity


# =============================================================================
# IMPACT AND FREQUENCY ENUMS
# =============================================================================

class Impact(str, Enum):
    """Impact level of an issue."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Frequency(str, Enum):
    """Frequency of an issue occurrence."""
    RARE = "rare"
    OCCASIONAL = "occasional"
    FREQUENT = "frequent"
    PERVASIVE = "pervasive"


# =============================================================================
# SEVERITY MATRIX
# =============================================================================

class SeverityMatrix(BaseModel):
    """Configurable matrix for impact × frequency → severity classification."""
    
    # Matrix maps (impact, frequency) -> severity
    # Default matrix follows pragmatic escalation rules
    matrix: dict[str, str] = Field(
        default_factory=lambda: {
            # (impact, frequency) -> severity
            # Low impact
            ("low", "rare"): "low",
            ("low", "occasional"): "low",
            ("low", "frequent"): "medium",
            ("low", "pervasive"): "medium",
            # Medium impact
            ("medium", "rare"): "low",
            ("medium", "occasional"): "medium",
            ("medium", "frequent"): "medium",
            ("medium", "pervasive"): "high",
            # High impact
            ("high", "rare"): "medium",
            ("high", "occasional"): "medium",
            ("high", "frequent"): "high",
            ("high", "pervasive"): "critical",
            # Critical impact
            ("critical", "rare"): "high",
            ("critical", "occasional"): "high",
            ("critical", "frequent"): "critical",
            ("critical", "pervasive"): "critical",
        },
        description="Mapping of (impact, frequency) tuples to severity levels"
    )
    
    def classify(self, impact: Impact, frequency: Frequency) -> Severity:
        """Classify severity based on impact and frequency.
        
        Args:
            impact: Impact level of the issue
            frequency: How often the issue occurs
            
        Returns:
            Severity level
        """
        key = (impact.value, frequency.value)
        severity_str = self.matrix.get(key, "medium")  # Default to medium
        return Severity(severity_str)


# =============================================================================
# PREDEFINED RULES
# =============================================================================

# Issue type -> (default_impact, default_frequency)
# These are baseline rules that can be overridden by context
ISSUE_TYPE_RULES: dict[str, tuple[Impact, Frequency]] = {
    # Visual hierarchy issues
    "hierarchy_unclear": (Impact.HIGH, Frequency.FREQUENT),
    "missing_focal_point": (Impact.HIGH, Frequency.OCCASIONAL),
    "competing_elements": (Impact.MEDIUM, Frequency.FREQUENT),
    
    # Spacing issues
    "inconsistent_spacing": (Impact.MEDIUM, Frequency.FREQUENT),
    "cramped_layout": (Impact.MEDIUM, Frequency.OCCASIONAL),
    "excessive_whitespace": (Impact.LOW, Frequency.OCCASIONAL),
    
    # Typography issues
    "too_many_font_sizes": (Impact.MEDIUM, Frequency.FREQUENT),
    "poor_contrast": (Impact.HIGH, Frequency.FREQUENT),
    "missing_hierarchy": (Impact.MEDIUM, Frequency.OCCASIONAL),
    
    # Color issues
    "color_contrast_failure": (Impact.HIGH, Frequency.FREQUENT),
    "inconsistent_color_usage": (Impact.MEDIUM, Frequency.OCCASIONAL),
    "accessibility_color_issue": (Impact.CRITICAL, Frequency.OCCASIONAL),
    
    # Alignment issues
    "misaligned_elements": (Impact.MEDIUM, Frequency.FREQUENT),
    "broken_grid": (Impact.HIGH, Frequency.OCCASIONAL),
    "inconsistent_rhythm": (Impact.MEDIUM, Frequency.FREQUENT),
    
    # Component issues
    "inconsistent_component_style": (Impact.MEDIUM, Frequency.FREQUENT),
    "missing_interaction_state": (Impact.HIGH, Frequency.OCCASIONAL),
    "unclear_interactive": (Impact.HIGH, Frequency.FREQUENT),
    
    # Accessibility issues (generally higher severity)
    "missing_alt_text": (Impact.HIGH, Frequency.OCCASIONAL),
    "keyboard_trap": (Impact.CRITICAL, Frequency.RARE),
    "no_focus_indicator": (Impact.HIGH, Frequency.FREQUENT),
    "screen_reader_issue": (Impact.HIGH, Frequency.OCCASIONAL),
    
    # State issues
    "missing_empty_state": (Impact.MEDIUM, Frequency.OCCASIONAL),
    "missing_loading_state": (Impact.MEDIUM, Frequency.FREQUENT),
    "unclear_error_message": (Impact.HIGH, Frequency.OCCASIONAL),
    
    # Density issues
    "information_overload": (Impact.HIGH, Frequency.OCCASIONAL),
    "redundant_elements": (Impact.MEDIUM, Frequency.FREQUENT),
}


# =============================================================================
# SEVERITY ENGINE
# =============================================================================

class SeverityEngine:
    """Engine for classifying audit finding severity.
    
    Uses a matrix-based approach for consistent, explainable classifications.
    """
    
    def __init__(
        self,
        matrix: Optional[SeverityMatrix] = None,
        custom_rules: Optional[dict[str, tuple[Impact, Frequency]]] = None,
    ):
        """Initialize severity engine.
        
        Args:
            matrix: Custom severity matrix (uses default if None)
            custom_rules: Custom issue type rules (merged with defaults)
        """
        self.matrix = matrix or SeverityMatrix()
        self.rules = {**ISSUE_TYPE_RULES}
        if custom_rules:
            self.rules.update(custom_rules)
    
    def classify_finding(
        self,
        issue_type: str,
        impact: Optional[str] = None,
        frequency: Optional[str] = None,
    ) -> Severity:
        """Classify a finding's severity.
        
        Args:
            issue_type: Type of issue (e.g., "color_contrast_failure")
            impact: Optional explicit impact level (overrides rules)
            frequency: Optional explicit frequency (overrides rules)
            
        Returns:
            Classified severity level
            
        Example:
            >>> engine = SeverityEngine()
            >>> engine.classify_finding("color_contrast_failure")
            <Severity.HIGH: 'high'>
            >>> engine.classify_finding("color_contrast_failure", impact="critical")
            <Severity.CRITICAL: 'critical'>
        """
        # Get default impact/frequency from rules if available
        default_impact, default_frequency = self.rules.get(
            issue_type, 
            (Impact.MEDIUM, Frequency.OCCASIONAL)
        )
        
        # Use explicit values or fall back to defaults
        impact_enum = Impact(impact) if impact else default_impact
        frequency_enum = Frequency(frequency) if frequency else default_frequency
        
        return self.matrix.classify(impact_enum, frequency_enum)
    
    def classify_with_overrides(
        self,
        issue_type: str,
        impact_multiplier: float = 1.0,
        frequency_multiplier: float = 1.0,
    ) -> Severity:
        """Classify with multipliers for context-specific adjustments.
        
        Args:
            issue_type: Type of issue
            impact_multiplier: Multiplier to adjust impact (0.5 = lower, 2.0 = higher)
            frequency_multiplier: Multiplier to adjust frequency
            
        Returns:
            Classified severity level
        """
        default_impact, default_frequency = self.rules.get(
            issue_type,
            (Impact.MEDIUM, Frequency.OCCASIONAL)
        )
        
        # Apply multipliers to shift impact/frequency
        impact = self._apply_impact_multiplier(default_impact, impact_multiplier)
        frequency = self._apply_frequency_multiplier(default_frequency, frequency_multiplier)
        
        return self.matrix.classify(impact, frequency)
    
    def _apply_impact_multiplier(self, impact: Impact, multiplier: float) -> Impact:
        """Apply multiplier to impact level."""
        levels = [Impact.LOW, Impact.MEDIUM, Impact.HIGH, Impact.CRITICAL]
        idx = levels.index(impact)
        new_idx = max(0, min(len(levels) - 1, int(idx * multiplier)))
        return levels[new_idx]
    
    def _apply_frequency_multiplier(self, frequency: Frequency, multiplier: float) -> Frequency:
        """Apply multiplier to frequency level."""
        levels = [Frequency.RARE, Frequency.OCCASIONAL, Frequency.FREQUENT, Frequency.PERVASIVE]
        idx = levels.index(frequency)
        new_idx = max(0, min(len(levels) - 1, int(idx * multiplier)))
        return levels[new_idx]
    
    def get_rule(self, issue_type: str) -> Optional[tuple[Impact, Frequency]]:
        """Get the default rule for an issue type.
        
        Args:
            issue_type: Type of issue
            
        Returns:
            Tuple of (impact, frequency) or None if not found
        """
        return self.rules.get(issue_type)
    
    def add_rule(self, issue_type: str, impact: Impact, frequency: Frequency) -> None:
        """Add or update a rule for an issue type.
        
        Args:
            issue_type: Type of issue
            impact: Default impact level
            frequency: Default frequency
        """
        self.rules[issue_type] = (impact, frequency)
    
    def explain_classification(
        self,
        issue_type: str,
        impact: Optional[str] = None,
        frequency: Optional[str] = None,
    ) -> dict:
        """Explain why a severity was assigned.
        
        Args:
            issue_type: Type of issue
            impact: Optional explicit impact
            frequency: Optional explicit frequency
            
        Returns:
            Dictionary with classification explanation
        """
        default_impact, default_frequency = self.rules.get(
            issue_type,
            (Impact.MEDIUM, Frequency.OCCASIONAL)
        )
        
        impact_enum = Impact(impact) if impact else default_impact
        frequency_enum = Frequency(frequency) if frequency else default_frequency
        severity = self.matrix.classify(impact_enum, frequency_enum)
        
        return {
            "issue_type": issue_type,
            "impact": impact_enum.value,
            "frequency": frequency_enum.value,
            "severity": severity.value,
            "rule_source": "custom" if issue_type not in ISSUE_TYPE_RULES else "default",
            "overrides": {
                "impact": impact is not None,
                "frequency": frequency is not None,
            },
        }
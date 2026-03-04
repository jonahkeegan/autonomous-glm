"""
Unit tests for plan phasing (phase classification).

Tests for PhaseClassifier and the classify_finding convenience function.
"""

import pytest

from src.plan.phasing import (
    PhaseClassifier,
    classify_finding,
    classify,
    SEVERITY_PHASE_MAP,
    DIMENSION_PHASE_OVERRIDE,
)
from src.plan.models import PhaseType
from src.audit.models import AuditDimension, AuditFindingCreate, EntityType
from src.db.models import Severity


class TestPhaseClassifier:
    """Tests for PhaseClassifier."""
    
    def test_classify_by_severity(self):
        """Classification by severity works correctly."""
        classifier = PhaseClassifier()
        
        assert classifier.classify_by_severity(Severity.CRITICAL) == PhaseType.CRITICAL
        assert classifier.classify_by_severity(Severity.HIGH) == PhaseType.CRITICAL
        assert classifier.classify_by_severity(Severity.MEDIUM) == PhaseType.REFINEMENT
        assert classifier.classify_by_severity(Severity.LOW) == PhaseType.POLISH
    
    def test_classify_by_dimension(self):
        """Classification by dimension override works correctly."""
        classifier = PhaseClassifier()
        
        # Critical dimensions
        assert classifier.classify_by_dimension(AuditDimension.VISUAL_HIERARCHY) == PhaseType.CRITICAL
        assert classifier.classify_by_dimension(AuditDimension.ACCESSIBILITY) == PhaseType.CRITICAL
        
        # Refinement dimensions
        assert classifier.classify_by_dimension(AuditDimension.SPACING_RHYTHM) == PhaseType.REFINEMENT
        assert classifier.classify_by_dimension(AuditDimension.TYPOGRAPHY) == PhaseType.REFINEMENT
        assert classifier.classify_by_dimension(AuditDimension.COLOR) == PhaseType.REFINEMENT
        assert classifier.classify_by_dimension(AuditDimension.ALIGNMENT_GRID) == PhaseType.REFINEMENT
        assert classifier.classify_by_dimension(AuditDimension.COMPONENTS) == PhaseType.REFINEMENT
        assert classifier.classify_by_dimension(AuditDimension.DENSITY) == PhaseType.REFINEMENT
        
        # Polish dimensions
        assert classifier.classify_by_dimension(AuditDimension.DARK_MODE_THEMING) == PhaseType.POLISH
        assert classifier.classify_by_dimension(AuditDimension.EMPTY_STATES) == PhaseType.POLISH
        assert classifier.classify_by_dimension(AuditDimension.LOADING_STATES) == PhaseType.POLISH
        assert classifier.classify_by_dimension(AuditDimension.ERROR_STATES) == PhaseType.POLISH
        assert classifier.classify_by_dimension(AuditDimension.ICONOGRAPHY) == PhaseType.POLISH
    
    def test_classify_finding_with_override(self):
        """Finding classification uses dimension override when enabled."""
        classifier = PhaseClassifier()
        
        # Accessibility is always Critical, even with LOW severity
        finding = AuditFindingCreate(
            dimension=AuditDimension.ACCESSIBILITY,
            severity=Severity.LOW,
            issue="Minor accessibility issue",
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
        )
        
        assert classifier.classify_finding(finding) == PhaseType.CRITICAL
        
        # Empty states are always Polish, even with HIGH severity
        finding = AuditFindingCreate(
            dimension=AuditDimension.EMPTY_STATES,
            severity=Severity.HIGH,
            issue="Missing empty state",
            entity_type=EntityType.COMPONENT,
            entity_id="list-1",
        )
        
        assert classifier.classify_finding(finding) == PhaseType.POLISH
    
    def test_classify_finding_without_override(self):
        """Finding classification falls back to severity when overrides disabled."""
        classifier = PhaseClassifier()
        
        # Accessibility with LOW severity, no override -> Polish
        finding = AuditFindingCreate(
            dimension=AuditDimension.ACCESSIBILITY,
            severity=Severity.LOW,
            issue="Minor accessibility issue",
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
        )
        
        assert classifier.classify_finding(finding, use_override=False) == PhaseType.POLISH
    
    def test_classify_direct(self):
        """Direct classification by dimension and severity."""
        classifier = PhaseClassifier()
        
        # With override
        assert classifier.classify(AuditDimension.ACCESSIBILITY, Severity.LOW) == PhaseType.CRITICAL
        assert classifier.classify(AuditDimension.SPACING_RHYTHM, Severity.CRITICAL) == PhaseType.REFINEMENT
        assert classifier.classify(AuditDimension.EMPTY_STATES, Severity.HIGH) == PhaseType.POLISH
        
        # Without override - falls back to severity
        assert classifier.classify(AuditDimension.ACCESSIBILITY, Severity.LOW, use_override=False) == PhaseType.POLISH
    
    def test_get_phase_order(self):
        """Phase order retrieval."""
        classifier = PhaseClassifier()
        
        assert classifier.get_phase_order(PhaseType.CRITICAL) == 1
        assert classifier.get_phase_order(PhaseType.REFINEMENT) == 2
        assert classifier.get_phase_order(PhaseType.POLISH) == 3
    
    def test_custom_severity_map(self):
        """Custom severity map overrides defaults."""
        custom_map = {
            Severity.CRITICAL: PhaseType.CRITICAL,
            Severity.HIGH: PhaseType.REFINEMENT,  # Different from default
            Severity.MEDIUM: PhaseType.REFINEMENT,
            Severity.LOW: PhaseType.POLISH,
        }
        
        classifier = PhaseClassifier(severity_map=custom_map)
        
        # HIGH now goes to Refinement instead of Critical
        assert classifier.classify_by_severity(Severity.HIGH) == PhaseType.REFINEMENT
    
    def test_custom_dimension_overrides(self):
        """Custom dimension overrides replace defaults."""
        custom_overrides = {
            AuditDimension.ACCESSIBILITY: PhaseType.POLISH,  # Different from default
        }
        
        classifier = PhaseClassifier(dimension_overrides=custom_overrides)
        
        # Accessibility now goes to Polish
        assert classifier.classify_by_dimension(AuditDimension.ACCESSIBILITY) == PhaseType.POLISH
        # No override for hierarchy -> None
        assert classifier.classify_by_dimension(AuditDimension.VISUAL_HIERARCHY) is None


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_classify_finding_function(self):
        """classify_finding uses default classifier."""
        finding = AuditFindingCreate(
            dimension=AuditDimension.ACCESSIBILITY,
            severity=Severity.LOW,
            issue="Issue",
            entity_type=EntityType.COMPONENT,
            entity_id="btn-1",
        )
        
        # Should use default classifier with overrides
        assert classify_finding(finding) == PhaseType.CRITICAL
    
    def test_classify_function(self):
        """classify uses default classifier."""
        # Should use default classifier with overrides
        assert classify(AuditDimension.ACCESSIBILITY, Severity.LOW) == PhaseType.CRITICAL
        assert classify(AuditDimension.SPACING_RHYTHM, Severity.HIGH) == PhaseType.REFINEMENT


class TestDefaultRules:
    """Tests for default classification rules."""
    
    def test_severity_phase_map_complete(self):
        """All severities are mapped."""
        for severity in Severity:
            assert severity in SEVERITY_PHASE_MAP
    
    def test_dimension_override_coverage(self):
        """All implemented dimensions have overrides."""
        implemented_dimensions = [
            AuditDimension.VISUAL_HIERARCHY,
            AuditDimension.ACCESSIBILITY,
            AuditDimension.SPACING_RHYTHM,
            AuditDimension.TYPOGRAPHY,
            AuditDimension.COLOR,
            AuditDimension.ALIGNMENT_GRID,
            AuditDimension.COMPONENTS,
            AuditDimension.DENSITY,
            AuditDimension.DARK_MODE_THEMING,
            AuditDimension.EMPTY_STATES,
            AuditDimension.LOADING_STATES,
            AuditDimension.ERROR_STATES,
            AuditDimension.ICONOGRAPHY,
        ]
        
        for dim in implemented_dimensions:
            assert dim in DIMENSION_PHASE_OVERRIDE, f"Missing override for {dim}"
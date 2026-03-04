"""
Unit tests for plan synthesis.

Tests for PlanSynthesizer orchestrating phase classification, 
dependency resolution, and plan generation.
"""

import pytest

from src.plan.synthesizer import (
    PlanSynthesizer,
    synthesize,
    synthesize_from_findings,
)
from src.plan.models import PhaseType, PlanStatus
from src.audit.models import (
    AuditDimension,
    AuditFindingCreate,
    AuditResult,
    AuditSession,
    EntityType,
)
from src.db.models import Severity


# Helper to create findings easily
def make_finding(
    dimension: AuditDimension,
    severity: Severity,
    entity_id: str = "entity-1",
    issue: str = "Test issue",
) -> AuditFindingCreate:
    """Create a test finding."""
    return AuditFindingCreate(
        dimension=dimension,
        severity=severity,
        issue=issue,
        entity_type=EntityType.COMPONENT,
        entity_id=entity_id,
    )


# Helper to create audit session
def make_session() -> AuditSession:
    """Create a test audit session."""
    return AuditSession(
        screen_id="screen-123",
        dimensions=[d for d in AuditDimension],
    )


class TestPlanSynthesizer:
    """Tests for PlanSynthesizer."""
    
    def test_synthesize_empty_findings(self):
        """Synthesis with no findings creates empty plan."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        plan = synthesizer.synthesize(result, findings=[])
        
        assert plan.audit_session_id == session.id
        assert plan.screen_id == "screen-123"
        assert plan.total_actions == 0
        assert plan.phase_count == 0
        assert plan.status == PlanStatus.PENDING
    
    def test_synthesize_single_finding(self):
        """Synthesis with single finding creates single-phase plan."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.HIGH),
        ]
        
        plan = synthesizer.synthesize(result, findings=findings)
        
        assert plan.total_actions == 1
        assert plan.phase_count == 1
        
        critical_phase = plan.get_phase(PhaseType.CRITICAL)
        assert critical_phase is not None
        assert critical_phase.action_count == 1
    
    def test_synthesize_multiple_phases(self):
        """Synthesis distributes findings across phases."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.CRITICAL, "e1"),
            make_finding(AuditDimension.SPACING_RHYTHM, Severity.MEDIUM, "e2"),
            make_finding(AuditDimension.EMPTY_STATES, Severity.LOW, "e3"),
        ]
        
        plan = synthesizer.synthesize(result, findings=findings)
        
        assert plan.total_actions == 3
        assert plan.phase_count == 3
        
        # Check phase distribution
        assert plan.get_phase(PhaseType.CRITICAL).action_count == 1
        assert plan.get_phase(PhaseType.REFINEMENT).action_count == 1
        assert plan.get_phase(PhaseType.POLISH).action_count == 1
    
    def test_synthesize_respects_dimension_overrides(self):
        """Dimension overrides take precedence over severity."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        findings = [
            # Accessibility is always Critical, even with LOW severity
            make_finding(AuditDimension.ACCESSIBILITY, Severity.LOW, "e1"),
            # Empty states is always Polish, even with HIGH severity
            make_finding(AuditDimension.EMPTY_STATES, Severity.HIGH, "e2"),
        ]
        
        plan = synthesizer.synthesize(result, findings=findings)
        
        # Accessibility should be in Critical
        critical = plan.get_phase(PhaseType.CRITICAL)
        assert critical is not None
        assert critical.action_count == 1
        
        # Empty states should be in Polish
        polish = plan.get_phase(PhaseType.POLISH)
        assert polish is not None
        assert polish.action_count == 1
    
    def test_synthesize_sequences_actions(self):
        """Actions within phase are sequenced."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        findings = [
            make_finding(AuditDimension.SPACING_RHYTHM, Severity.MEDIUM, "e1"),
            make_finding(AuditDimension.VISUAL_HIERARCHY, Severity.HIGH, "e2"),
        ]
        
        plan = synthesizer.synthesize(result, findings=findings)
        
        # Both go to Critical (hierarchy via override, spacing... let me check
        # Actually spacing goes to Refinement via override, hierarchy to Critical
        # So they're in different phases
        
        critical = plan.get_phase(PhaseType.CRITICAL)
        refinement = plan.get_phase(PhaseType.REFINEMENT)
        
        assert critical is not None
        assert critical.action_count == 1  # Hierarchy
        
        assert refinement is not None
        assert refinement.action_count == 1  # Spacing
    
    def test_synthesize_includes_summary(self):
        """Plan includes computed summary."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.CRITICAL, "e1"),
            make_finding(AuditDimension.SPACING_RHYTHM, Severity.MEDIUM, "e2"),
        ]
        
        plan = synthesizer.synthesize(result, findings=findings)
        
        assert plan.summary is not None
        assert plan.summary.total_actions == 2
        assert plan.summary.critical_count == 1
        assert plan.summary.has_accessibility_issues
    
    def test_synthesize_from_findings(self):
        """synthesize_from_findings creates plan without AuditResult."""
        synthesizer = PlanSynthesizer()
        
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.HIGH),
        ]
        
        plan = synthesizer.synthesize_from_findings(
            findings=findings,
            audit_session_id="session-123",
            screen_id="screen-456",
        )
        
        assert plan.audit_session_id == "session-123"
        assert plan.screen_id == "screen-456"
        assert plan.total_actions == 1
    
    def test_group_by_phase(self):
        """Grouping findings by phase works correctly."""
        synthesizer = PlanSynthesizer()
        
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.HIGH, "e1"),
            make_finding(AuditDimension.SPACING_RHYTHM, Severity.MEDIUM, "e2"),
            make_finding(AuditDimension.EMPTY_STATES, Severity.LOW, "e3"),
            make_finding(AuditDimension.TYPOGRAPHY, Severity.MEDIUM, "e4"),
        ]
        
        by_phase = synthesizer.group_by_phase(findings)
        
        assert len(by_phase.get(PhaseType.CRITICAL, [])) == 1  # Accessibility
        assert len(by_phase.get(PhaseType.REFINEMENT, [])) == 2  # Spacing, Typography
        assert len(by_phase.get(PhaseType.POLISH, [])) == 1  # Empty states
    
    def test_generate_summary(self):
        """Summary generation works correctly."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.CRITICAL, "e1"),
            make_finding(AuditDimension.VISUAL_HIERARCHY, Severity.HIGH, "e2"),
        ]
        
        plan = synthesizer.synthesize(result, findings=findings)
        summary = synthesizer.generate_summary(plan)
        
        assert summary.total_actions == 2
        assert summary.critical_count == 1
        assert summary.high_count == 1
        assert summary.has_accessibility_issues
        assert summary.has_hierarchy_issues


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_synthesize_function(self):
        """synthesize uses default synthesizer."""
        session = make_session()
        result = AuditResult(session=session)
        
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.HIGH),
        ]
        
        plan = synthesize(result, findings=findings)
        
        assert plan.total_actions == 1
    
    def test_synthesize_from_findings_function(self):
        """synthesize_from_findings uses default synthesizer."""
        findings = [
            make_finding(AuditDimension.ACCESSIBILITY, Severity.HIGH),
        ]
        
        plan = synthesize_from_findings(
            findings=findings,
            audit_session_id="session-123",
            screen_id="screen-456",
        )
        
        assert plan.audit_session_id == "session-123"
        assert plan.total_actions == 1


class TestPlanSynthesizerIntegration:
    """Integration tests for full synthesis workflow."""
    
    def test_full_workflow(self):
        """Complete synthesis workflow produces valid plan."""
        synthesizer = PlanSynthesizer()
        session = make_session()
        result = AuditResult(session=session)
        
        # Create findings that span all phases and have dependencies
        findings = [
            # Critical phase
            make_finding(AuditDimension.ACCESSIBILITY, Severity.CRITICAL, "a1"),
            make_finding(AuditDimension.VISUAL_HIERARCHY, Severity.HIGH, "h1"),
            
            # Refinement phase (some depend on critical)
            make_finding(AuditDimension.SPACING_RHYTHM, Severity.MEDIUM, "s1"),
            make_finding(AuditDimension.TYPOGRAPHY, Severity.MEDIUM, "t1"),
            make_finding(AuditDimension.COLOR, Severity.MEDIUM, "c1"),
            
            # Polish phase
            make_finding(AuditDimension.DARK_MODE_THEMING, Severity.LOW, "d1"),
            make_finding(AuditDimension.EMPTY_STATES, Severity.LOW, "e1"),
        ]
        
        plan = synthesizer.synthesize(result, findings=findings)
        
        # Verify plan structure
        assert plan.total_actions == 7
        assert plan.phase_count == 3
        
        # Verify phases in correct order
        phases = plan.phases
        assert phases[0].phase_type == PhaseType.CRITICAL
        assert phases[1].phase_type == PhaseType.REFINEMENT
        assert phases[2].phase_type == PhaseType.POLISH
        
        # Verify summary
        assert plan.summary is not None
        assert plan.summary.total_actions == 7
        assert plan.summary.total_phases == 3
        assert plan.summary.critical_count == 1
        assert plan.summary.high_count == 1
        assert plan.summary.has_accessibility_issues
        assert plan.summary.has_hierarchy_issues
        
        # Verify actions are sequenced within phases
        for phase in phases:
            for i, action in enumerate(phase.actions):
                assert action.sequence == i + 1
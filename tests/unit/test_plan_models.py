"""
Unit tests for plan models.

Tests for PhaseType, PlanActionCreate, PlanPhaseCreate, Plan, and PlanSummary.
"""

import pytest
from datetime import datetime

from src.plan.models import (
    PhaseType,
    PlanStatus,
    PlanActionCreate,
    PlanPhaseCreate,
    Plan,
    PlanSummary,
)
from src.audit.models import AuditDimension
from src.db.models import Severity, PhaseName, PhaseStatus


class TestPhaseType:
    """Tests for PhaseType enum."""
    
    def test_phase_types_exist(self):
        """All expected phase types exist."""
        assert PhaseType.CRITICAL.value == "critical"
        assert PhaseType.REFINEMENT.value == "refinement"
        assert PhaseType.POLISH.value == "polish"
    
    def test_phase_order(self):
        """Phase order returns correct values."""
        assert PhaseType.CRITICAL.order() == 1
        assert PhaseType.REFINEMENT.order() == 2
        assert PhaseType.POLISH.order() == 3
    
    def test_from_phase_name(self):
        """Conversion from PhaseName works correctly."""
        assert PhaseType.from_phase_name(PhaseName.CRITICAL) == PhaseType.CRITICAL
        assert PhaseType.from_phase_name(PhaseName.REFINEMENT) == PhaseType.REFINEMENT
        assert PhaseType.from_phase_name(PhaseName.POLISH) == PhaseType.POLISH
    
    def test_to_phase_name(self):
        """Conversion to PhaseName works correctly."""
        assert PhaseType.CRITICAL.to_phase_name() == PhaseName.CRITICAL
        assert PhaseType.REFINEMENT.to_phase_name() == PhaseName.REFINEMENT
        assert PhaseType.POLISH.to_phase_name() == PhaseName.POLISH


class TestPlanStatus:
    """Tests for PlanStatus enum."""
    
    def test_plan_statuses_exist(self):
        """All expected plan statuses exist."""
        assert PlanStatus.PENDING.value == "pending"
        assert PlanStatus.IN_PROGRESS.value == "in_progress"
        assert PlanStatus.COMPLETED.value == "completed"
        assert PlanStatus.FAILED.value == "failed"


class TestPlanActionCreate:
    """Tests for PlanActionCreate model."""
    
    def test_create_minimal_action(self):
        """Create action with minimal required fields."""
        action = PlanActionCreate(
            finding_id="finding-123",
            description="Fix the button color",
            target_entity="Button#submit",
            dimension=AuditDimension.COLOR,
        )
        
        assert action.finding_id == "finding-123"
        assert action.description == "Fix the button color"
        assert action.target_entity == "Button#submit"
        assert action.dimension == AuditDimension.COLOR
        assert action.severity == Severity.MEDIUM  # default
        assert action.sequence == 0
        assert action.dependencies == []
    
    def test_create_full_action(self):
        """Create action with all fields."""
        action = PlanActionCreate(
            finding_id="finding-456",
            description="Update button background",
            target_entity="Button#submit",
            target_property="background-color",
            current_value="#ff0000",
            proposed_value="--color-primary",
            rationale="Non-compliant red color",
            dimension=AuditDimension.COLOR,
            severity=Severity.HIGH,
            sequence=1,
            dependencies=["finding-123"],
            metadata={"contrast_ratio": 2.5},
        )
        
        assert action.finding_id == "finding-456"
        assert action.target_property == "background-color"
        assert action.current_value == "#ff0000"
        assert action.proposed_value == "--color-primary"
        assert action.rationale == "Non-compliant red color"
        assert action.severity == Severity.HIGH
        assert action.sequence == 1
        assert action.dependencies == ["finding-123"]
        assert action.metadata == {"contrast_ratio": 2.5}
    
    def test_with_sequence(self):
        """with_sequence returns updated copy."""
        action = PlanActionCreate(
            finding_id="finding-123",
            description="Fix color",
            target_entity="Button#submit",
            dimension=AuditDimension.COLOR,
        )
        
        updated = action.with_sequence(5)
        
        assert updated.sequence == 5
        assert action.sequence == 0  # original unchanged
    
    def test_with_dependencies(self):
        """with_dependencies returns updated copy."""
        action = PlanActionCreate(
            finding_id="finding-123",
            description="Fix color",
            target_entity="Button#submit",
            dimension=AuditDimension.COLOR,
        )
        
        updated = action.with_dependencies(["dep-1", "dep-2"])
        
        assert updated.dependencies == ["dep-1", "dep-2"]
        assert action.dependencies == []


class TestPlanPhaseCreate:
    """Tests for PlanPhaseCreate model."""
    
    def test_create_minimal_phase(self):
        """Create phase with minimal fields."""
        phase = PlanPhaseCreate(phase_type=PhaseType.CRITICAL)
        
        assert phase.phase_type == PhaseType.CRITICAL
        assert phase.actions == []
        assert phase.status == PhaseStatus.PROPOSED
        assert phase.action_count == 0
    
    def test_create_phase_with_actions(self):
        """Create phase with actions."""
        action1 = PlanActionCreate(
            finding_id="f1",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,
            severity=Severity.CRITICAL,
        )
        action2 = PlanActionCreate(
            finding_id="f2",
            description="Fix contrast",
            target_entity="Button#submit",
            dimension=AuditDimension.ACCESSIBILITY,
            severity=Severity.HIGH,
        )
        
        phase = PlanPhaseCreate(
            phase_type=PhaseType.CRITICAL,
            actions=[action1, action2],
        )
        
        assert phase.action_count == 2
        assert phase.findings_by_severity == {"low": 0, "medium": 0, "high": 1, "critical": 1}
    
    def test_to_db_phase(self):
        """to_db_phase converts to database-compatible dict."""
        action = PlanActionCreate(
            finding_id="f1",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,
        )
        
        phase = PlanPhaseCreate(
            phase_type=PhaseType.CRITICAL,
            actions=[action],
        )
        
        db_dict = phase.to_db_phase(audit_id="audit-123")
        
        assert db_dict["audit_id"] == "audit-123"
        assert db_dict["phase_name"] == PhaseName.CRITICAL
        assert db_dict["sequence"] == 1
        assert len(db_dict["actions"]) == 1
        assert db_dict["status"] == PhaseStatus.PROPOSED


class TestPlan:
    """Tests for Plan model."""
    
    def test_create_minimal_plan(self):
        """Create plan with minimal fields."""
        plan = Plan(
            audit_session_id="session-123",
            screen_id="screen-456",
        )
        
        assert plan.audit_session_id == "session-123"
        assert plan.screen_id == "screen-456"
        assert plan.phases == []
        assert plan.status == PlanStatus.PENDING
        assert plan.total_actions == 0
        assert plan.phase_count == 0
    
    def test_create_plan_with_phases(self):
        """Create plan with phases."""
        action = PlanActionCreate(
            finding_id="f1",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,
        )
        
        phase = PlanPhaseCreate(
            phase_type=PhaseType.CRITICAL,
            actions=[action],
        )
        
        plan = Plan(
            audit_session_id="session-123",
            screen_id="screen-456",
            phases=[phase],
        )
        
        assert plan.total_actions == 1
        assert plan.phase_count == 1
    
    def test_phases_sorted_by_order(self):
        """Phases are sorted by execution order."""
        polish = PlanPhaseCreate(phase_type=PhaseType.POLISH)
        critical = PlanPhaseCreate(phase_type=PhaseType.CRITICAL)
        refinement = PlanPhaseCreate(phase_type=PhaseType.REFINEMENT)
        
        plan = Plan(
            audit_session_id="session-123",
            screen_id="screen-456",
            phases=[polish, critical, refinement],  # Wrong order
        )
        
        # Should be sorted: Critical, Refinement, Polish
        assert plan.phases[0].phase_type == PhaseType.CRITICAL
        assert plan.phases[1].phase_type == PhaseType.REFINEMENT
        assert plan.phases[2].phase_type == PhaseType.POLISH
    
    def test_get_phase(self):
        """get_phase retrieves specific phase."""
        critical = PlanPhaseCreate(phase_type=PhaseType.CRITICAL)
        refinement = PlanPhaseCreate(phase_type=PhaseType.REFINEMENT)
        
        plan = Plan(
            audit_session_id="session-123",
            screen_id="screen-456",
            phases=[critical, refinement],
        )
        
        assert plan.get_phase(PhaseType.CRITICAL) == critical
        assert plan.get_phase(PhaseType.REFINEMENT) == refinement
        assert plan.get_phase(PhaseType.POLISH) is None
    
    def test_compute_summary(self):
        """compute_summary attaches PlanSummary."""
        action = PlanActionCreate(
            finding_id="f1",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,
            severity=Severity.CRITICAL,
        )
        
        phase = PlanPhaseCreate(
            phase_type=PhaseType.CRITICAL,
            actions=[action],
        )
        
        plan = Plan(
            audit_session_id="session-123",
            screen_id="screen-456",
            phases=[phase],
        )
        
        plan_with_summary = plan.compute_summary()
        
        assert plan_with_summary.summary is not None
        assert plan_with_summary.summary.total_actions == 1
        assert plan_with_summary.summary.critical_count == 1


class TestPlanSummary:
    """Tests for PlanSummary model."""
    
    def test_from_plan_empty(self):
        """from_plan with empty plan."""
        plan = Plan(
            audit_session_id="session-123",
            screen_id="screen-456",
        )
        
        summary = PlanSummary.from_plan(plan)
        
        assert summary.total_actions == 0
        assert summary.total_phases == 0
        assert summary.by_phase == {}
        assert summary.by_severity == {"low": 0, "medium": 0, "high": 0, "critical": 0}
        assert summary.critical_count == 0
        assert summary.high_count == 0
        assert not summary.has_accessibility_issues
        assert not summary.has_hierarchy_issues
    
    def test_from_plan_with_findings(self):
        """from_plan with findings across phases."""
        critical_action = PlanActionCreate(
            finding_id="f1",
            description="Fix accessibility",
            target_entity="Button",
            dimension=AuditDimension.ACCESSIBILITY,
            severity=Severity.CRITICAL,
        )
        high_action = PlanActionCreate(
            finding_id="f2",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,
            severity=Severity.HIGH,
        )
        medium_action = PlanActionCreate(
            finding_id="f3",
            description="Fix spacing",
            target_entity="Container",
            dimension=AuditDimension.SPACING_RHYTHM,
            severity=Severity.MEDIUM,
        )
        low_action = PlanActionCreate(
            finding_id="f4",
            description="Fix empty state",
            target_entity="EmptyList",
            dimension=AuditDimension.EMPTY_STATES,
            severity=Severity.LOW,
        )
        
        critical_phase = PlanPhaseCreate(
            phase_type=PhaseType.CRITICAL,
            actions=[critical_action, high_action],
        )
        refinement_phase = PlanPhaseCreate(
            phase_type=PhaseType.REFINEMENT,
            actions=[medium_action],
        )
        polish_phase = PlanPhaseCreate(
            phase_type=PhaseType.POLISH,
            actions=[low_action],
        )
        
        plan = Plan(
            audit_session_id="session-123",
            screen_id="screen-456",
            phases=[critical_phase, refinement_phase, polish_phase],
        )
        
        summary = PlanSummary.from_plan(plan)
        
        assert summary.total_actions == 4
        assert summary.total_phases == 3
        assert summary.by_phase == {"critical": 2, "refinement": 1, "polish": 1}
        assert summary.by_severity == {"low": 1, "medium": 1, "high": 1, "critical": 1}
        assert summary.critical_count == 1
        assert summary.high_count == 1
        assert summary.has_accessibility_issues
        assert summary.has_hierarchy_issues
    
    def test_priority_score(self):
        """Priority score calculation."""
        summary = PlanSummary(
            total_actions=5,
            critical_count=2,
            high_count=3,
            has_accessibility_issues=True,
            has_hierarchy_issues=True,
        )
        
        # 2 * 10 + 3 * 5 + 3 + 2 = 40
        assert summary.priority_score == 40.0
    
    def test_estimated_effort(self):
        """Estimated effort levels."""
        assert PlanSummary(total_actions=3).estimated_effort == "low"
        assert PlanSummary(total_actions=10).estimated_effort == "medium"
        assert PlanSummary(total_actions=25).estimated_effort == "high"
        assert PlanSummary(total_actions=50).estimated_effort == "very_high"
"""
Plan and report persistence for M4-4.

Provides high-level persistence functions for saving and retrieving
Plans, PlanPhases, and Reports to/from the database.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from src.db.crud import (
    create_plan_phase,
    get_plan_phase,
    list_plan_phases,
    update_plan_phase,
    delete_plan_phase,
)
from src.db.database import connection
from src.db.models import PhaseName, PhaseStatus, PlanPhaseCreate, PlanPhaseUpdate
from src.plan.models import Plan, PlanPhaseCreate as SynthesizerPhase, PlanStatus, PhaseType


# =============================================================================
# PLAN PERSISTENCE CLASS
# =============================================================================

class PlanPersistence:
    """Persistence manager for Plans and Reports.
    
    Provides methods for saving, retrieving, and updating Plans and their
    associated entities in the database.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the persistence manager.
        
        Args:
            db_path: Optional path to SQLite database file
        """
        self.db_path = db_path
    
    # =========================================================================
    # PLAN OPERATIONS
    # =========================================================================
    
    def save_plan(self, plan: Plan) -> str:
        """Save a complete plan with all phases to the database.
        
        Args:
            plan: Plan object from plan synthesis
        
        Returns:
            The plan ID
        
        Raises:
            ValueError: If plan is invalid
        """
        plan_id = plan.id
        
        # Save each phase
        for phase in plan.phases:
            # Convert synthesizer phase to db phase
            db_phase = self._convert_phase(phase, plan_id)
            create_plan_phase(db_phase, self.db_path)
        
        # Save plan metadata to a plans table (or create if needed)
        self._save_plan_metadata(plan)
        
        return plan_id
    
    def _convert_phase(
        self,
        phase: SynthesizerPhase,
        plan_id: str
    ) -> PlanPhaseCreate:
        """Convert a synthesizer PlanPhaseCreate to db PlanPhaseCreate.
        
        Args:
            phase: Phase from plan synthesis
            plan_id: Parent plan ID
        
        Returns:
            PlanPhaseCreate for database
        """
        from src.db.models import PlanAction
        
        # Convert actions
        actions = []
        for action in phase.actions:
            actions.append(PlanAction(
                description=action.description,
                target_entity=action.target_entity,
                fix=action.proposed_value or action.description,
                rationale=action.rationale,
            ))
        
        # Map phase type to PhaseName
        phase_name_map = {
            PhaseType.CRITICAL: PhaseName.CRITICAL,
            PhaseType.REFINEMENT: PhaseName.REFINEMENT,
            PhaseType.POLISH: PhaseName.POLISH,
        }
        
        return PlanPhaseCreate(
            audit_id=plan_id,  # Use plan_id as audit_id for linking
            phase_name=phase_name_map[phase.phase_type],
            sequence=phase.phase_type.order(),
            actions=actions,
            status=phase.status,
        )
    
    def _save_plan_metadata(self, plan: Plan) -> None:
        """Save plan metadata to database.
        
        Creates a simple metadata record for the plan.
        
        Args:
            plan: Plan object
        """
        now = datetime.now().isoformat()
        
        with connection(self.db_path) as conn:
            # Check if plans table exists, create if not
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    audit_session_id TEXT,
                    screen_id TEXT,
                    status TEXT DEFAULT 'pending',
                    total_actions INTEGER DEFAULT 0,
                    summary_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Insert or replace plan metadata
            conn.execute("""
                INSERT OR REPLACE INTO plans 
                (id, audit_session_id, screen_id, status, total_actions, summary_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.id,
                plan.audit_session_id,
                plan.screen_id,
                plan.status.value,
                plan.total_actions,
                json.dumps(plan.summary.model_dump()) if plan.summary else None,
                plan.created_at.isoformat() if plan.created_at else now,
                now,
            ))
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Retrieve a complete plan with all phases.
        
        Args:
            plan_id: UUID of the plan
        
        Returns:
            Plan object or None if not found
        """
        with connection(self.db_path) as conn:
            # Get plan metadata
            cursor = conn.execute(
                "SELECT * FROM plans WHERE id = ?", (plan_id,)
            )
            plan_row = cursor.fetchone()
            
            if plan_row is None:
                return None
            
            plan_dict = dict(plan_row)
        
        # Get all phases for this plan
        phases = list_plan_phases(
            audit_id=plan_id,
            limit=10,
            db_path=self.db_path
        )
        
        # Convert db phases back to synthesizer phases
        synthesizer_phases = []
        for db_phase in phases:
            synth_phase = self._db_phase_to_synthesizer(db_phase)
            synthesizer_phases.append(synth_phase)
        
        # Reconstruct Plan object
        from src.plan.models import PlanSummary
        
        summary = None
        if plan_dict.get("summary_json"):
            summary_data = json.loads(plan_dict["summary_json"])
            summary = PlanSummary(**summary_data)
        
        return Plan(
            id=plan_dict["id"],
            audit_session_id=plan_dict.get("audit_session_id", ""),
            screen_id=plan_dict.get("screen_id", ""),
            phases=synthesizer_phases,
            status=PlanStatus(plan_dict.get("status", "pending")),
            summary=summary,
            created_at=datetime.fromisoformat(plan_dict["created_at"]) if plan_dict.get("created_at") else None,
        )
    
    def _db_phase_to_synthesizer(self, db_phase: Any) -> SynthesizerPhase:
        """Convert a database PlanPhase to synthesizer PlanPhaseCreate.
        
        Args:
            db_phase: PlanPhase from database
        
        Returns:
            PlanPhaseCreate for synthesis
        """
        from src.plan.models import PlanActionCreate
        from src.audit.models import AuditDimension
        from src.db.models import Severity
        
        # Map phase name back to phase type
        phase_type_map = {
            PhaseName.CRITICAL: PhaseType.CRITICAL,
            PhaseName.REFINEMENT: PhaseType.REFINEMENT,
            PhaseName.POLISH: PhaseType.POLISH,
        }
        
        # Convert actions
        actions = []
        for action in db_phase.actions:
            actions.append(PlanActionCreate(
                finding_id="",  # Not stored in db
                description=action.description,
                target_entity=action.target_entity,
                proposed_value=action.fix,
                rationale=action.rationale,
                dimension=AuditDimension.ACCESSIBILITY,  # Default
                severity=Severity.MEDIUM,  # Default
            ))
        
        return SynthesizerPhase(
            id=db_phase.id,
            phase_type=phase_type_map[db_phase.phase_name],
            actions=actions,
            status=db_phase.status,
            created_at=db_phase.created_at,
        )
    
    def get_plans_by_session(self, session_id: str) -> list[Plan]:
        """Get all plans for an audit session.
        
        Args:
            session_id: UUID of the audit session
        
        Returns:
            List of Plan objects
        """
        plans = []
        
        with connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM plans WHERE audit_session_id = ? ORDER BY created_at DESC",
                (session_id,),
            )
            rows = cursor.fetchall()
            
            for row in rows:
                plan = self.get_plan(row["id"])
                if plan:
                    plans.append(plan)
        
        return plans
    
    def update_plan_status(
        self,
        plan_id: str,
        status: PlanStatus
    ) -> bool:
        """Update the status of a plan.
        
        Args:
            plan_id: UUID of the plan
            status: New status
        
        Returns:
            True if updated, False if not found
        """
        now = datetime.now().isoformat()
        
        with connection(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE plans SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, plan_id),
            )
            return cursor.rowcount > 0
    
    # =========================================================================
    # PLAN PHASE OPERATIONS
    # =========================================================================
    
    def save_plan_phase(self, phase: SynthesizerPhase, plan_id: str) -> str:
        """Save a single plan phase.
        
        Args:
            phase: PlanPhaseCreate from synthesis
            plan_id: Parent plan ID
        
        Returns:
            Phase ID
        """
        db_phase = self._convert_phase(phase, plan_id)
        result = create_plan_phase(db_phase, self.db_path)
        return result.id
    
    def get_plan_phase(self, phase_id: str) -> Optional[Any]:
        """Get a plan phase by ID.
        
        Args:
            phase_id: UUID of the phase
        
        Returns:
            PlanPhase from database
        """
        return get_plan_phase(phase_id, self.db_path)
    
    def update_plan_phase_status(
        self,
        phase_id: str,
        status: PhaseStatus
    ) -> bool:
        """Update the status of a plan phase.
        
        Args:
            phase_id: UUID of the phase
            status: New status
        
        Returns:
            True if updated
        """
        update = PlanPhaseUpdate(status=status)
        result = update_plan_phase(phase_id, update, self.db_path)
        return result is not None
    
    # =========================================================================
    # REPORT OPERATIONS
    # =========================================================================
    
    def save_report(self, report: Any) -> str:
        """Save a report to the database.
        
        Args:
            report: FullReport object
        
        Returns:
            Report ID
        """
        report_id = report.metadata.id
        now = datetime.now().isoformat()
        
        with connection(self.db_path) as conn:
            # Create reports table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    audit_session_id TEXT,
                    screen_id TEXT,
                    version TEXT DEFAULT '1.0.0',
                    report_json TEXT NOT NULL,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Insert report
            conn.execute("""
                INSERT OR REPLACE INTO reports
                (id, report_type, audit_session_id, screen_id, version, report_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                report.metadata.report_type.value,
                report.metadata.audit_session_id,
                report.metadata.screen_id,
                report.metadata.version,
                json.dumps(report.to_json_dict()),
                report.metadata.created_at.isoformat(),
                now,
            ))
        
        return report_id
    
    def get_report(self, report_id: str) -> Optional[Any]:
        """Get a report by ID.
        
        Args:
            report_id: UUID of the report
        
        Returns:
            FullReport object or None
        """
        from src.plan.report_models import (
            FullReport, ReportMetadata, ReportType,
            AuditSummaryReport, ImplementationPlanReport, DesignProposalReport
        )
        
        with connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM reports WHERE id = ?", (report_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            report_data = json.loads(row["report_json"])
        
        # Reconstruct the report object
        metadata = ReportMetadata(
            id=report_data["metadata"]["id"],
            report_type=ReportType(report_data["metadata"]["report_type"]),
            audit_session_id=report_data["metadata"].get("audit_session_id"),
            screen_id=report_data["metadata"].get("screen_id"),
            version=report_data["metadata"].get("version", "1.0.0"),
            created_at=datetime.fromisoformat(report_data["metadata"]["created_at"]),
        )
        
        # Build component reports
        audit_summary = None
        if report_data.get("audit_summary"):
            # Simplified reconstruction - in production would fully deserialize
            audit_summary = AuditSummaryReport(
                metadata=metadata,
                summary=report_data["audit_summary"]["summary"],
                findings_by_severity=report_data["audit_summary"].get("findings_by_severity", {}),
                findings_by_dimension=report_data["audit_summary"].get("findings_by_dimension", {}),
                top_issues=report_data["audit_summary"].get("top_issues", []),
                standards_violated=report_data["audit_summary"].get("standards_violated", []),
            )
        
        implementation_plan = None
        if report_data.get("implementation_plan"):
            implementation_plan = ImplementationPlanReport(
                metadata=metadata,
                summary=report_data["implementation_plan"]["summary"],
                phases=report_data["implementation_plan"].get("phases", {}),
                all_instructions=report_data["implementation_plan"].get("all_instructions", []),
                estimated_effort=report_data["implementation_plan"].get("estimated_effort", "medium"),
            )
        
        design_proposals = None
        if report_data.get("design_proposals"):
            design_proposals = DesignProposalReport(
                metadata=metadata,
                summary=report_data["design_proposals"]["summary"],
                token_proposals=report_data["design_proposals"].get("token_proposals", []),
                component_proposals=report_data["design_proposals"].get("component_proposals", []),
                before_after_descriptions=report_data["design_proposals"].get("before_after_descriptions", {}),
                requires_human_approval=report_data["design_proposals"].get("requires_human_approval", True),
            )
        
        return FullReport(
            metadata=metadata,
            audit_summary=audit_summary,
            implementation_plan=implementation_plan,
            design_proposals=design_proposals,
            overall_summary=report_data.get("overall_summary", {}),
        )
    
    def get_reports_by_session(self, session_id: str) -> list[Any]:
        """Get all reports for an audit session.
        
        Args:
            session_id: UUID of the audit session
        
        Returns:
            List of FullReport objects
        """
        reports = []
        
        with connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM reports WHERE audit_session_id = ? ORDER BY created_at DESC",
                (session_id,),
            )
            rows = cursor.fetchall()
            
            for row in rows:
                report = self.get_report(row["id"])
                if report:
                    reports.append(report)
        
        return reports
    
    def delete_report(self, report_id: str) -> bool:
        """Delete a report by ID.
        
        Args:
            report_id: UUID of the report
        
        Returns:
            True if deleted
        """
        with connection(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM reports WHERE id = ?", (report_id,)
            )
            return cursor.rowcount > 0


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def save_plan(plan: Plan, db_path: Optional[Path] = None) -> str:
    """Save a plan to the database.
    
    Args:
        plan: Plan object
        db_path: Optional database path
    
    Returns:
        Plan ID
    """
    persistence = PlanPersistence(db_path)
    return persistence.save_plan(plan)


def get_plan(plan_id: str, db_path: Optional[Path] = None) -> Optional[Plan]:
    """Get a plan by ID.
    
    Args:
        plan_id: Plan UUID
        db_path: Optional database path
    
    Returns:
        Plan or None
    """
    persistence = PlanPersistence(db_path)
    return persistence.get_plan(plan_id)


def get_plans_by_session(session_id: str, db_path: Optional[Path] = None) -> list[Plan]:
    """Get all plans for an audit session.
    
    Args:
        session_id: Audit session UUID
        db_path: Optional database path
    
    Returns:
        List of Plans
    """
    persistence = PlanPersistence(db_path)
    return persistence.get_plans_by_session(session_id)


def update_plan_status(
    plan_id: str,
    status: PlanStatus,
    db_path: Optional[Path] = None
) -> bool:
    """Update plan status.
    
    Args:
        plan_id: Plan UUID
        status: New status
        db_path: Optional database path
    
    Returns:
        True if updated
    """
    persistence = PlanPersistence(db_path)
    return persistence.update_plan_status(plan_id, status)


def save_report(report: Any, db_path: Optional[Path] = None) -> str:
    """Save a report to the database.
    
    Args:
        report: FullReport object
        db_path: Optional database path
    
    Returns:
        Report ID
    """
    persistence = PlanPersistence(db_path)
    return persistence.save_report(report)


def get_report(report_id: str, db_path: Optional[Path] = None) -> Optional[Any]:
    """Get a report by ID.
    
    Args:
        report_id: Report UUID
        db_path: Optional database path
    
    Returns:
        FullReport or None
    """
    persistence = PlanPersistence(db_path)
    return persistence.get_report(report_id)
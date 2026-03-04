"""
Plan synthesis orchestrator.

Coordinates phase classification, dependency resolution, and plan generation
to produce complete, sequenced improvement plans from audit results.
"""

from collections import defaultdict
from typing import Optional

from src.audit.models import AuditDimension, AuditFindingCreate, AuditResult, AuditSession
from src.db.models import Severity, PhaseStatus
from src.plan.models import (
    PhaseType,
    PlanStatus,
    PlanActionCreate,
    PlanPhaseCreate,
    Plan,
    PlanSummary,
)
from src.plan.phasing import PhaseClassifier, classify_finding
from src.plan.dependencies import DependencyResolver


# =============================================================================
# PLAN SYNTHESIZER
# =============================================================================

class PlanSynthesizer:
    """Synthesizes phased improvement plans from audit results.
    
    The synthesis process:
    1. Extract findings from audit result
    2. Classify each finding into a phase (Critical, Refinement, Polish)
    3. Group findings by phase
    4. Within each phase, resolve dependencies and sequence actions
    5. Generate summary statistics
    
    Example:
        >>> synthesizer = PlanSynthesizer()
        >>> audit_result = AuditResult(session=audit_session)
        >>> plan = synthesizer.synthesize(audit_result)
        >>> print(f"Plan has {plan.total_actions} actions in {plan.phase_count} phases")
    """
    
    def __init__(
        self,
        classifier: Optional[PhaseClassifier] = None,
        resolver: Optional[DependencyResolver] = None,
    ):
        """Initialize the synthesizer with optional custom components.
        
        Args:
            classifier: Custom phase classifier
            resolver: Custom dependency resolver
        """
        self.classifier = classifier or PhaseClassifier()
        self.resolver = resolver or DependencyResolver()
    
    def synthesize(
        self,
        audit_result: AuditResult,
        findings: Optional[list[AuditFindingCreate]] = None,
        screen_id: Optional[str] = None,
    ) -> Plan:
        """Synthesize a complete plan from an audit result.
        
        Args:
            audit_result: The audit result containing session and findings
            findings: Optional explicit list of findings (if not in audit_result)
            screen_id: Optional screen ID (defaults to session's screen_id)
            
        Returns:
            A complete Plan with all phases and sequenced actions
        """
        # Get session info
        session = audit_result.session
        screen_id = screen_id or session.screen_id
        
        # Get findings to process
        # Note: In a full implementation, we'd fetch findings from DB by ID
        # For now, we accept findings as a parameter
        findings = findings or []
        
        # Group findings by phase
        by_phase = self.group_by_phase(findings)
        
        # Create phases with sequenced actions
        phases: list[PlanPhaseCreate] = []
        for phase_type in [PhaseType.CRITICAL, PhaseType.REFINEMENT, PhaseType.POLISH]:
            phase_findings = by_phase.get(phase_type, [])
            if phase_findings:
                actions = self.sequence_actions(phase_findings, phase_type)
                phase = PlanPhaseCreate(
                    phase_type=phase_type,
                    actions=actions,
                    status=PhaseStatus.PROPOSED,
                )
                phases.append(phase)
        
        # Create the plan
        plan = Plan(
            audit_session_id=session.id,
            screen_id=screen_id,
            phases=phases,
            status=PlanStatus.PENDING,
        )
        
        # Compute and attach summary
        return plan.compute_summary()
    
    def synthesize_from_findings(
        self,
        findings: list[AuditFindingCreate],
        audit_session_id: str,
        screen_id: str,
    ) -> Plan:
        """Synthesize a plan directly from findings.
        
        Convenience method when you have findings but no AuditResult.
        
        Args:
            findings: List of audit findings
            audit_session_id: ID of the audit session
            screen_id: ID of the audited screen
            
        Returns:
            A complete Plan with all phases and sequenced actions
        """
        # Group findings by phase
        by_phase = self.group_by_phase(findings)
        
        # Create phases with sequenced actions
        phases: list[PlanPhaseCreate] = []
        for phase_type in [PhaseType.CRITICAL, PhaseType.REFINEMENT, PhaseType.POLISH]:
            phase_findings = by_phase.get(phase_type, [])
            if phase_findings:
                actions = self.sequence_actions(phase_findings, phase_type)
                phase = PlanPhaseCreate(
                    phase_type=phase_type,
                    actions=actions,
                    status=PhaseStatus.PROPOSED,
                )
                phases.append(phase)
        
        # Create the plan
        plan = Plan(
            audit_session_id=audit_session_id,
            screen_id=screen_id,
            phases=phases,
            status=PlanStatus.PENDING,
        )
        
        # Compute and attach summary
        return plan.compute_summary()
    
    def group_by_phase(
        self, 
        findings: list[AuditFindingCreate]
    ) -> dict[PhaseType, list[AuditFindingCreate]]:
        """Group findings by their target phase.
        
        Args:
            findings: List of audit findings to group
            
        Returns:
            Dict mapping phase type to list of findings
        """
        by_phase: dict[PhaseType, list[AuditFindingCreate]] = defaultdict(list)
        
        for finding in findings:
            phase = self.classifier.classify_finding(finding)
            by_phase[phase].append(finding)
        
        return dict(by_phase)
    
    def sequence_actions(
        self,
        findings: list[AuditFindingCreate],
        phase_type: PhaseType,
    ) -> list[PlanActionCreate]:
        """Convert findings to sequenced actions within a phase.
        
        Args:
            findings: Findings to convert (all should belong to same phase)
            phase_type: The phase these actions belong to
            
        Returns:
            List of sequenced PlanActionCreate objects
        """
        if not findings:
            return []
        
        # Convert findings to actions
        actions = [self._finding_to_action(f) for f in findings]
        
        # Resolve dependencies within the phase
        sequenced = self.resolver.resolve_order(actions)
        
        # Add dependency references
        sequenced = self.resolver.add_dependencies_to_actions(sequenced)
        
        return sequenced
    
    def _finding_to_action(self, finding: AuditFindingCreate) -> PlanActionCreate:
        """Convert an AuditFindingCreate to a PlanActionCreate.
        
        Args:
            finding: The finding to convert
            
        Returns:
            A PlanActionCreate with appropriate fields populated
        """
        # Build description from issue and rationale
        description = finding.issue
        if finding.rationale:
            description = f"{finding.issue}: {finding.rationale}"
        
        # Build target entity from entity_type and entity_id
        target_entity = f"{finding.entity_type.value}#{finding.entity_id}"
        
        # Extract property from metadata if available
        target_property = None
        current_value = None
        proposed_value = None
        
        if finding.metadata:
            target_property = finding.metadata.get("property")
            current_value = finding.metadata.get("current_value")
            proposed_value = finding.metadata.get("proposed_value")
        
        # Build rationale from standards refs
        rationale = None
        if finding.standards_refs:
            refs = []
            for ref in finding.standards_refs:
                if ref.wcag:
                    refs.append(f"WCAG {ref.wcag.criterion}: {ref.wcag.name}")
                elif ref.design_token:
                    refs.append(f"Token: {ref.design_token.token_name}")
                elif ref.custom:
                    refs.append(ref.custom)
            if refs:
                rationale = "References: " + "; ".join(refs)
        
        return PlanActionCreate(
            finding_id=finding.entity_id,  # Use entity_id as temporary finding ID
            description=description,
            target_entity=target_entity,
            target_property=target_property,
            current_value=current_value,
            proposed_value=proposed_value,
            rationale=rationale,
            dimension=finding.dimension,
            severity=finding.severity,
            metadata=finding.metadata,
        )
    
    def generate_summary(self, plan: Plan) -> PlanSummary:
        """Generate summary statistics for a plan.
        
        Args:
            plan: The plan to summarize
            
        Returns:
            PlanSummary with statistics
        """
        return PlanSummary.from_plan(plan)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_default_synthesizer = PlanSynthesizer()


def synthesize(
    audit_result: AuditResult,
    findings: Optional[list[AuditFindingCreate]] = None,
    screen_id: Optional[str] = None,
) -> Plan:
    """Synthesize a plan using the default synthesizer.
    
    Args:
        audit_result: The audit result to synthesize
        findings: Optional explicit list of findings
        screen_id: Optional screen ID
        
    Returns:
        A complete Plan
    """
    return _default_synthesizer.synthesize(audit_result, findings, screen_id)


def synthesize_from_findings(
    findings: list[AuditFindingCreate],
    audit_session_id: str,
    screen_id: str,
) -> Plan:
    """Synthesize a plan from findings using the default synthesizer.
    
    Args:
        findings: List of audit findings
        audit_session_id: ID of the audit session
        screen_id: ID of the audited screen
        
    Returns:
        A complete Plan
    """
    return _default_synthesizer.synthesize_from_findings(
        findings, audit_session_id, screen_id
    )
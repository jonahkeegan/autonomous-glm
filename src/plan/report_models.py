"""
Pydantic models for report generation.

Defines models for audit summary reports, implementation plan reports,
design proposal reports, and full aggregated reports for both human
consumption (Markdown) and agent consumption (JSON).
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# REPORT TYPE ENUM
# =============================================================================

class ReportType(str, Enum):
    """Types of reports that can be generated."""
    
    AUDIT_SUMMARY = "audit_summary"
    IMPLEMENTATION_PLAN = "implementation_plan"
    DESIGN_PROPOSAL = "design_proposal"
    FULL_REPORT = "full_report"


# =============================================================================
# REPORT METADATA
# =============================================================================

class ReportMetadata(BaseModel):
    """Metadata for all report types."""
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique report identifier"
    )
    report_type: ReportType = Field(
        ...,
        description="Type of report"
    )
    audit_session_id: Optional[str] = Field(
        default=None,
        description="ID of the source audit session"
    )
    screen_id: Optional[str] = Field(
        default=None,
        description="ID of the audited screen"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the report was created"
    )
    version: str = Field(
        default="1.0.0",
        description="Report format version"
    )
    generator: str = Field(
        default="autonomous-glm",
        description="Report generator identifier"
    )
    
    model_config = {"frozen": True}


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

class FindingsSummary(BaseModel):
    """Summary statistics for audit findings."""
    
    total_findings: int = Field(default=0, description="Total number of findings")
    by_severity: dict[str, int] = Field(
        default_factory=lambda: {"low": 0, "medium": 0, "high": 0, "critical": 0},
        description="Findings count by severity level"
    )
    by_dimension: dict[str, int] = Field(
        default_factory=dict,
        description="Findings count by audit dimension"
    )
    by_phase: dict[str, int] = Field(
        default_factory=dict,
        description="Findings count by plan phase"
    )
    critical_count: int = Field(default=0, description="Number of critical findings")
    high_count: int = Field(default=0, description="Number of high findings")
    jobs_filtered_count: int = Field(
        default=0,
        description="Number of findings flagged by Jobs filter"
    )
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score (critical=10, high=5)."""
        return (self.critical_count * 10) + (self.high_count * 5)
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if any critical findings exist."""
        return self.critical_count > 0


class InstructionsSummary(BaseModel):
    """Summary statistics for implementation instructions."""
    
    total_instructions: int = Field(default=0, description="Total number of instructions")
    by_phase: dict[str, int] = Field(
        default_factory=dict,
        description="Instructions count by phase"
    )
    by_issue_type: dict[str, int] = Field(
        default_factory=dict,
        description="Instructions count by issue type"
    )
    high_confidence_count: int = Field(
        default=0,
        description="Instructions with high confidence (>=0.8)"
    )
    requires_inspection_count: int = Field(
        default=0,
        description="Instructions requiring manual inspection"
    )
    
    @property
    def automation_rate(self) -> float:
        """Calculate the percentage of instructions that can be automated."""
        if self.total_instructions == 0:
            return 0.0
        return self.high_confidence_count / self.total_instructions


class ProposalsSummary(BaseModel):
    """Summary statistics for design system proposals."""
    
    total_proposals: int = Field(default=0, description="Total number of proposals")
    token_proposals: int = Field(default=0, description="Token proposals count")
    component_proposals: int = Field(default=0, description="Component proposals count")
    by_priority: dict[str, int] = Field(
        default_factory=dict,
        description="Proposals count by priority level"
    )
    affected_screens: int = Field(
        default=0,
        description="Number of screens affected by proposals"
    )
    average_impact_score: float = Field(
        default=0.0,
        description="Average impact score across proposals"
    )


# =============================================================================
# AUDIT SUMMARY REPORT
# =============================================================================

class AuditSummaryReport(BaseModel):
    """Report summarizing audit findings for a screen."""
    
    metadata: ReportMetadata = Field(..., description="Report metadata")
    summary: FindingsSummary = Field(..., description="Findings summary")
    findings_by_severity: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Findings grouped by severity"
    )
    findings_by_dimension: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Findings grouped by dimension"
    )
    top_issues: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Top 5 most critical issues"
    )
    standards_violated: list[str] = Field(
        default_factory=list,
        description="List of violated standards (WCAG, design tokens)"
    )
    
    @classmethod
    def from_audit_result(
        cls,
        audit_result: Any,
        findings: list[Any],
        metadata: Optional[ReportMetadata] = None
    ) -> "AuditSummaryReport":
        """Create report from AuditResult and findings list.
        
        Args:
            audit_result: AuditResult object with session and stats
            findings: List of AuditFindingCreate objects
            metadata: Optional metadata (will be created if not provided)
        
        Returns:
            AuditSummaryReport instance
        """
        # Build summary statistics
        summary = FindingsSummary()
        
        findings_by_severity: dict[str, list[dict]] = {
            "low": [], "medium": [], "high": [], "critical": []
        }
        findings_by_dimension: dict[str, list[dict]] = {}
        
        for finding in findings:
            # Get severity
            sev = getattr(finding, 'severity', None)
            sev_value = sev.value if hasattr(sev, 'value') else 'medium'
            
            # Get dimension
            dim = getattr(finding, 'dimension', None)
            dim_value = dim.value if hasattr(dim, 'value') else 'unknown'
            
            # Convert to dict
            finding_dict = finding.model_dump() if hasattr(finding, 'model_dump') else dict(finding)
            
            # Group by severity
            if sev_value in findings_by_severity:
                findings_by_severity[sev_value].append(finding_dict)
            
            # Group by dimension
            if dim_value not in findings_by_dimension:
                findings_by_dimension[dim_value] = []
            findings_by_dimension[dim_value].append(finding_dict)
            
            # Update summary
            summary.total_findings += 1
            summary.by_severity[sev_value] = summary.by_severity.get(sev_value, 0) + 1
            summary.by_dimension[dim_value] = summary.by_dimension.get(dim_value, 0) + 1
            
            if sev_value == "critical":
                summary.critical_count += 1
            elif sev_value == "high":
                summary.high_count += 1
            
            # Check Jobs filter
            if getattr(finding, 'jobs_filtered', False):
                summary.jobs_filtered_count += 1
        
        # Get top issues (critical first, then high)
        top_issues = findings_by_severity["critical"][:3] + findings_by_severity["high"][:2]
        
        # Collect standards violated
        standards = set()
        for finding in findings:
            refs = getattr(finding, 'standards_refs', [])
            for ref in refs:
                if hasattr(ref, 'wcag') and ref.wcag:
                    standards.add(f"WCAG {ref.wcag.criterion}")
                if hasattr(ref, 'design_token') and ref.design_token:
                    standards.add(ref.design_token.token_name)
        
        # Create metadata if not provided
        if metadata is None:
            session_id = getattr(audit_result, 'session', None)
            session_id = str(getattr(session_id, 'id', 'unknown')) if session_id else 'unknown'
            
            metadata = ReportMetadata(
                report_type=ReportType.AUDIT_SUMMARY,
                audit_session_id=session_id,
            )
        
        return cls(
            metadata=metadata,
            summary=summary,
            findings_by_severity=findings_by_severity,
            findings_by_dimension=findings_by_dimension,
            top_issues=top_issues[:5],
            standards_violated=sorted(list(standards)),
        )


# =============================================================================
# IMPLEMENTATION PLAN REPORT
# =============================================================================

class ImplementationPlanReport(BaseModel):
    """Report containing implementation instructions for fixing issues."""
    
    metadata: ReportMetadata = Field(..., description="Report metadata")
    summary: InstructionsSummary = Field(..., description="Instructions summary")
    phases: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Instructions grouped by phase (Critical/Refinement/Polish)"
    )
    all_instructions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="All instructions in sequence order"
    )
    estimated_effort: str = Field(
        default="medium",
        description="Estimated effort level (low/medium/high/very_high)"
    )
    
    @classmethod
    def from_plan(
        cls,
        plan: Any,
        instructions: list[Any],
        metadata: Optional[ReportMetadata] = None
    ) -> "ImplementationPlanReport":
        """Create report from Plan and instructions.
        
        Args:
            plan: Plan object with phases
            instructions: List of ImplementationInstruction objects
            metadata: Optional metadata (will be created if not provided)
        
        Returns:
            ImplementationPlanReport instance
        """
        summary = InstructionsSummary()
        phases: dict[str, list[dict]] = {
            "critical": [],
            "refinement": [],
            "polish": []
        }
        all_instructions = []
        
        for instruction in instructions:
            # Convert to dict
            inst_dict = instruction.model_dump() if hasattr(instruction, 'model_dump') else dict(instruction)
            all_instructions.append(inst_dict)
            
            # Update summary
            summary.total_instructions += 1
            
            # Get issue type
            issue_type = inst_dict.get('issue_type', 'unknown')
            summary.by_issue_type[issue_type] = summary.by_issue_type.get(issue_type, 0) + 1
            
            # Get phase
            phase = inst_dict.get('phase', 'refinement').lower()
            if phase in phases:
                phases[phase].append(inst_dict)
            summary.by_phase[phase] = summary.by_phase.get(phase, 0) + 1
            
            # Check confidence
            confidence = inst_dict.get('confidence', 0.0)
            if confidence >= 0.8:
                summary.high_confidence_count += 1
            
            # Check inspection flag
            if inst_dict.get('requires_inspection', False):
                summary.requires_inspection_count += 1
        
        # Get estimated effort from plan
        effort = "medium"
        if hasattr(plan, 'summary') and plan.summary:
            effort = getattr(plan.summary, 'estimated_effort', 'medium')
        
        # Create metadata if not provided
        if metadata is None:
            plan_id = str(getattr(plan, 'id', 'unknown'))
            session_id = getattr(plan, 'audit_session_id', None)
            
            metadata = ReportMetadata(
                report_type=ReportType.IMPLEMENTATION_PLAN,
                audit_session_id=session_id,
            )
        
        return cls(
            metadata=metadata,
            summary=summary,
            phases=phases,
            all_instructions=all_instructions,
            estimated_effort=effort,
        )


# =============================================================================
# DESIGN PROPOSAL REPORT
# =============================================================================

class DesignProposalReport(BaseModel):
    """Report containing design system proposals."""
    
    metadata: ReportMetadata = Field(..., description="Report metadata")
    summary: ProposalsSummary = Field(..., description="Proposals summary")
    token_proposals: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Token proposals"
    )
    component_proposals: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Component variant proposals"
    )
    before_after_descriptions: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Before/after descriptions keyed by proposal ID"
    )
    requires_human_approval: bool = Field(
        default=True,
        description="Whether human approval is required"
    )
    
    @classmethod
    def from_design_system_proposal(
        cls,
        proposal: Any,
        metadata: Optional[ReportMetadata] = None
    ) -> "DesignProposalReport":
        """Create report from DesignSystemProposal.
        
        Args:
            proposal: DesignSystemProposal object
            metadata: Optional metadata (will be created if not provided)
        
        Returns:
            DesignProposalReport instance
        """
        summary = ProposalsSummary()
        
        # Extract token proposals
        token_proposals = []
        for tp in getattr(proposal, 'token_proposals', []):
            tp_dict = tp.model_dump() if hasattr(tp, 'model_dump') else dict(tp)
            token_proposals.append(tp_dict)
            summary.token_proposals += 1
            summary.total_proposals += 1
        
        # Extract component proposals
        component_proposals = []
        for cp in getattr(proposal, 'component_proposals', []):
            cp_dict = cp.model_dump() if hasattr(cp, 'model_dump') else dict(cp)
            component_proposals.append(cp_dict)
            summary.component_proposals += 1
            summary.total_proposals += 1
        
        # Update summary
        priority = getattr(proposal, 'priority', None)
        priority_value = priority.value if hasattr(priority, 'value') else 'medium'
        summary.by_priority[priority_value] = 1
        summary.affected_screens = getattr(proposal, 'total_affected_screens', 0)
        summary.average_impact_score = getattr(proposal, 'impact_score', 0.0)
        
        # Extract before/after descriptions
        before_after = {}
        ba_summaries = getattr(proposal, 'before_after_summaries', {})
        for key, ba in ba_summaries.items():
            before_after[key] = ba.model_dump() if hasattr(ba, 'model_dump') else dict(ba)
        
        # Determine if human approval required
        requires_approval = True
        if summary.total_proposals == 0:
            requires_approval = False
        elif priority_value == "low" and summary.average_impact_score < 0.3:
            requires_approval = False
        
        # Create metadata if not provided
        if metadata is None:
            proposal_id = str(getattr(proposal, 'id', 'unknown'))
            session_id = getattr(proposal, 'audit_session_id', None)
            
            metadata = ReportMetadata(
                report_type=ReportType.DESIGN_PROPOSAL,
                audit_session_id=session_id,
            )
        
        return cls(
            metadata=metadata,
            summary=summary,
            token_proposals=token_proposals,
            component_proposals=component_proposals,
            before_after_descriptions=before_after,
            requires_human_approval=requires_approval,
        )


# =============================================================================
# FULL REPORT (AGGREGATE)
# =============================================================================

class FullReport(BaseModel):
    """Complete report containing audit, implementation, and design proposals."""
    
    metadata: ReportMetadata = Field(..., description="Report metadata")
    audit_summary: Optional[AuditSummaryReport] = Field(
        default=None,
        description="Audit findings summary"
    )
    implementation_plan: Optional[ImplementationPlanReport] = Field(
        default=None,
        description="Implementation instructions"
    )
    design_proposals: Optional[DesignProposalReport] = Field(
        default=None,
        description="Design system proposals"
    )
    overall_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Cross-section summary statistics"
    )
    
    @field_validator("metadata", mode="before")
    @classmethod
    def ensure_full_report_type(cls, v):
        """Ensure metadata has FULL_REPORT type."""
        if isinstance(v, dict):
            v["report_type"] = ReportType.FULL_REPORT
        return v
    
    def compute_overall_summary(self) -> dict[str, Any]:
        """Compute overall summary across all report sections."""
        summary = {
            "has_critical_findings": False,
            "total_findings": 0,
            "total_instructions": 0,
            "total_proposals": 0,
            "estimated_effort": "medium",
            "requires_human_approval": False,
            "automation_rate": 0.0,
            "priority_score": 0.0,
        }
        
        if self.audit_summary:
            summary["total_findings"] = self.audit_summary.summary.total_findings
            summary["has_critical_findings"] = self.audit_summary.summary.has_critical_issues
            summary["priority_score"] = self.audit_summary.summary.priority_score
        
        if self.implementation_plan:
            summary["total_instructions"] = self.implementation_plan.summary.total_instructions
            summary["estimated_effort"] = self.implementation_plan.estimated_effort
            summary["automation_rate"] = self.implementation_plan.summary.automation_rate
        
        if self.design_proposals:
            summary["total_proposals"] = self.design_proposals.summary.total_proposals
            summary["requires_human_approval"] = self.design_proposals.requires_human_approval
        
        self.overall_summary = summary
        return summary
    
    @classmethod
    def from_components(
        cls,
        audit_summary: Optional[AuditSummaryReport] = None,
        implementation_plan: Optional[ImplementationPlanReport] = None,
        design_proposals: Optional[DesignProposalReport] = None,
        metadata: Optional[ReportMetadata] = None
    ) -> "FullReport":
        """Create full report from component reports.
        
        Args:
            audit_summary: Optional audit summary report
            implementation_plan: Optional implementation plan report
            design_proposals: Optional design proposal report
            metadata: Optional metadata (will be derived if not provided)
        
        Returns:
            FullReport instance
        """
        # Derive metadata from first available component
        if metadata is None:
            for component in [audit_summary, implementation_plan, design_proposals]:
                if component and hasattr(component, 'metadata'):
                    metadata = ReportMetadata(
                        report_type=ReportType.FULL_REPORT,
                        audit_session_id=component.metadata.audit_session_id,
                        screen_id=component.metadata.screen_id,
                    )
                    break
            
            if metadata is None:
                metadata = ReportMetadata(report_type=ReportType.FULL_REPORT)
        
        report = cls(
            metadata=metadata,
            audit_summary=audit_summary,
            implementation_plan=implementation_plan,
            design_proposals=design_proposals,
        )
        report.compute_overall_summary()
        return report
    
    def to_json_dict(self) -> dict[str, Any]:
        """Export to JSON-serializable dict."""
        return {
            "metadata": self.metadata.model_dump(),
            "audit_summary": self.audit_summary.model_dump() if self.audit_summary else None,
            "implementation_plan": self.implementation_plan.model_dump() if self.implementation_plan else None,
            "design_proposals": self.design_proposals.model_dump() if self.design_proposals else None,
            "overall_summary": self.overall_summary,
        }
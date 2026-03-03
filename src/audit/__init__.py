"""
Audit framework for Autonomous-GLM.

Provides core audit infrastructure including:
- Audit dimension models and session tracking
- Severity classification engine
- Standards reference registry (WCAG, design tokens)
- Jobs/Ive design philosophy filter
- Audit orchestrator with plugin architecture
- Audit persistence layer

Usage:
    from src.audit import (
        AuditOrchestrator,
        AuditDimension,
        AuditSession,
        AuditResult,
        SeverityEngine,
        JobsFilter,
        StandardsRegistry,
        create_default_orchestrator,
    )
    
    # Create orchestrator
    orchestrator = create_default_orchestrator()
    
    # Register dimension auditors
    def audit_hierarchy(screen):
        return [...]
    
    orchestrator.register_dimension(
        AuditDimension.VISUAL_HIERARCHY,
        audit_hierarchy
    )
    
    # Run audit
    result = orchestrator.run_audit(screen_id="...")
"""

from .models import (
    AuditDimension,
    AuditSession,
    AuditSessionStatus,
    AuditResult,
    AuditFindingCreate,
    DimensionStats,
    StandardsReference,
    DesignTokenReference,
    WCAGReference,
    DimensionAuditor,
)

from .severity import (
    Impact,
    Frequency,
    SeverityMatrix,
    SeverityEngine,
    ISSUE_TYPE_RULES,
)

from .standards import (
    DesignToken,
    StandardsRegistry,
    WCAG_CRITERIA,
)

from .jobs_filter import (
    FilterQuestion,
    FilterResult,
    JobsFilter,
)

from .orchestrator import (
    AuditOrchestrator,
    create_default_orchestrator,
)

from .persistence import (
    save_audit_session,
    get_audit_session,
    get_audit_sessions_by_screen,
    complete_audit_session,
    save_audit_finding,
    get_findings_by_screen,
    get_findings_by_dimension,
    get_findings_by_session,
    ensure_audit_tables,
)

__all__ = [
    # Models
    "AuditDimension",
    "AuditSession",
    "AuditSessionStatus",
    "AuditResult",
    "AuditFindingCreate",
    "DimensionStats",
    "StandardsReference",
    "DesignTokenReference",
    "WCAGReference",
    "DimensionAuditor",
    # Severity
    "Impact",
    "Frequency",
    "SeverityMatrix",
    "SeverityEngine",
    "ISSUE_TYPE_RULES",
    # Standards
    "DesignToken",
    "StandardsRegistry",
    "WCAG_CRITERIA",
    # Jobs Filter
    "FilterQuestion",
    "FilterResult",
    "JobsFilter",
    # Orchestrator
    "AuditOrchestrator",
    "create_default_orchestrator",
    # Persistence
    "save_audit_session",
    "get_audit_session",
    "get_audit_sessions_by_screen",
    "complete_audit_session",
    "save_audit_finding",
    "get_findings_by_screen",
    "get_findings_by_dimension",
    "get_findings_by_session",
    "ensure_audit_tables",
]
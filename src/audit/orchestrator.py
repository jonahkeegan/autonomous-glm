"""
Audit orchestrator for coordinating dimension audits.

Provides plugin architecture for registering and running audit dimensions.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from .models import (
    AuditDimension,
    AuditSession,
    AuditSessionStatus,
    AuditResult,
    AuditFindingCreate,
    DimensionStats,
    DimensionAuditor,
)
from .severity import SeverityEngine
from .jobs_filter import JobsFilter, FilterResult
from .persistence import save_audit_session, save_audit_finding, complete_audit_session
from src.db.models import Screen, Severity, EntityType

logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT ORCHESTRATOR
# =============================================================================

class AuditOrchestrator:
    """Main orchestrator for coordinating audit dimensions.
    
    Provides a plugin architecture where dimension auditors register themselves.
    The orchestrator runs audits across all registered dimensions and aggregates
    results.
    
    Example:
        >>> orchestrator = AuditOrchestrator()
        >>> 
        >>> # Register a dimension auditor
        >>> def audit_hierarchy(screen: Screen) -> list[AuditFindingCreate]:
        ...     return [AuditFindingCreate(...)]
        >>> 
        >>> orchestrator.register_dimension(AuditDimension.VISUAL_HIERARCHY, audit_hierarchy)
        >>> 
        >>> # Run audit
        >>> result = orchestrator.run_audit(screen_id="...")
    """
    
    def __init__(
        self,
        severity_engine: Optional[SeverityEngine] = None,
        jobs_filter: Optional[JobsFilter] = None,
        jobs_filter_enabled: bool = True,
        max_findings_per_dimension: int = 100,
    ):
        """Initialize audit orchestrator.
        
        Args:
            severity_engine: Custom severity engine (uses default if None)
            jobs_filter: Custom Jobs filter (uses default if None)
            jobs_filter_enabled: Whether to apply Jobs filter
            max_findings_per_dimension: Maximum findings per dimension
        """
        self._dimensions: dict[AuditDimension, DimensionAuditor] = {}
        self.severity_engine = severity_engine or SeverityEngine()
        self.jobs_filter = jobs_filter or JobsFilter(enabled=jobs_filter_enabled)
        self.max_findings_per_dimension = max_findings_per_dimension
    
    def register_dimension(
        self,
        dimension: AuditDimension,
        auditor: DimensionAuditor,
    ) -> None:
        """Register an auditor for a dimension.
        
        Args:
            dimension: The audit dimension
            auditor: Callable that takes a screen and returns findings
        """
        self._dimensions[dimension] = auditor
        logger.info(f"Registered auditor for dimension: {dimension.value}")
    
    def unregister_dimension(self, dimension: AuditDimension) -> bool:
        """Unregister an auditor for a dimension.
        
        Args:
            dimension: The audit dimension to unregister
            
        Returns:
            True if dimension was registered, False otherwise
        """
        if dimension in self._dimensions:
            del self._dimensions[dimension]
            logger.info(f"Unregistered auditor for dimension: {dimension.value}")
            return True
        return False
    
    def get_registered_dimensions(self) -> list[AuditDimension]:
        """Get list of registered dimensions.
        
        Returns:
            List of registered audit dimensions
        """
        return list(self._dimensions.keys())
    
    def run_audit(
        self,
        screen_id: str,
        screen: Optional[Screen] = None,
        dimensions: Optional[list[AuditDimension]] = None,
        entity_type: EntityType = EntityType.SCREEN,
    ) -> AuditResult:
        """Run an audit on a screen.
        
        Args:
            screen_id: UUID of the screen to audit
            screen: Optional Screen object (for in-memory auditing)
            dimensions: Optional list of dimensions (defaults to all registered)
            entity_type: Type of entity being audited
            
        Returns:
            AuditResult with all findings and statistics
        """
        # Determine which dimensions to run
        dims_to_run = dimensions or list(self._dimensions.keys())
        
        # Filter to only registered dimensions
        dims_to_run = [d for d in dims_to_run if d in self._dimensions]
        
        if not dims_to_run:
            logger.warning(f"No registered dimensions to audit for screen {screen_id}")
            dims_to_run = []
        
        # Create audit session
        session = AuditSession(
            screen_id=screen_id,
            dimensions=dims_to_run,
            status=AuditSessionStatus.PENDING,
        )
        
        # Persist session
        try:
            session = save_audit_session(session)
        except Exception as e:
            logger.error(f"Failed to persist audit session: {e}")
            # Continue with in-memory session
        
        # Mark session as started
        session = session.mark_started()
        
        # Create result container
        result = AuditResult(session=session)
        
        # Run each dimension
        for dimension in dims_to_run:
            try:
                logger.info(f"Running dimension audit: {dimension.value}")
                finding_ids = self._run_dimension_audit(
                    session=session,
                    dimension=dimension,
                    screen=screen,
                    screen_id=screen_id,
                    entity_type=entity_type,
                    result=result,
                )
                
                # Update session with completed dimension
                session = session.add_dimension_result(dimension, finding_ids)
                
            except Exception as e:
                logger.error(f"Dimension audit failed for {dimension.value}: {e}")
                # Continue with other dimensions
        
        # Mark session complete
        success = len(session.completed_dimensions) > 0
        session = session.mark_completed(success=success)
        
        # Persist completion
        try:
            complete_audit_session(session.id, session.model_dump())
        except Exception as e:
            logger.error(f"Failed to persist session completion: {e}")
        
        # Update result with final session
        result.session = session
        
        logger.info(
            f"Audit complete: {len(session.finding_ids)} findings across "
            f"{len(session.completed_dimensions)} dimensions"
        )
        
        return result
    
    def _run_dimension_audit(
        self,
        session: AuditSession,
        dimension: AuditDimension,
        screen: Optional[Screen],
        screen_id: str,
        entity_type: EntityType,
        result: AuditResult,
    ) -> list[str]:
        """Run a single dimension audit.
        
        Args:
            session: Current audit session
            dimension: Dimension to audit
            screen: Optional Screen object
            screen_id: Screen UUID
            entity_type: Type of entity
            result: AuditResult to update
            
        Returns:
            List of finding IDs created
        """
        auditor = self._dimensions.get(dimension)
        if not auditor:
            return []
        
        # Get findings from auditor
        # Auditor may take screen object or just screen_id
        try:
            if screen:
                raw_findings = auditor(screen)
            else:
                # Create minimal screen-like object
                raw_findings = auditor(type('ScreenStub', (), {'id': screen_id})())
        except Exception as e:
            logger.error(f"Auditor failed for {dimension.value}: {e}")
            return []
        
        # Limit findings per dimension
        if len(raw_findings) > self.max_findings_per_dimension:
            logger.warning(
                f"Truncating findings for {dimension.value}: "
                f"{len(raw_findings)} -> {self.max_findings_per_dimension}"
            )
            raw_findings = raw_findings[:self.max_findings_per_dimension]
        
        # Process each finding
        finding_ids = []
        stats = DimensionStats(dimension=dimension)
        
        for raw_finding in raw_findings:
            # Ensure dimension is set
            if raw_finding.dimension != dimension:
                raw_finding.dimension = dimension
            
            # Ensure entity info is set
            if not raw_finding.entity_id:
                raw_finding.entity_id = screen_id
            if not raw_finding.entity_type:
                raw_finding.entity_type = entity_type
            
            # Classify severity if not already set
            if raw_finding.severity == Severity.MEDIUM and raw_finding.issue:
                # Use engine to classify if still at default
                issue_type = self._extract_issue_type(raw_finding.issue)
                raw_finding.severity = self.severity_engine.classify_finding(issue_type)
            
            # Apply Jobs filter
            filter_result = self.jobs_filter.auto_evaluate(raw_finding.issue)
            raw_finding.jobs_filtered = not filter_result.passes
            raw_finding.jobs_filter_score = filter_result.score
            
            # Persist finding
            try:
                finding_id = save_audit_finding(session.id, raw_finding)
                finding_ids.append(finding_id)
                
                # Update stats
                stats.add_finding(
                    severity=raw_finding.severity,
                    jobs_filtered=raw_finding.jobs_filtered,
                )
                
            except Exception as e:
                logger.error(f"Failed to persist finding: {e}")
        
        # Add to result
        result.add_dimension_findings(dimension, finding_ids, stats)
        
        return finding_ids
    
    def _extract_issue_type(self, issue_description: str) -> str:
        """Extract issue type from description for severity classification.
        
        Args:
            issue_description: Description of the issue
            
        Returns:
            Issue type string for severity engine
        """
        desc_lower = issue_description.lower()
        
        # Map keywords to issue types
        type_mappings = [
            (["contrast", "color contrast", "wcag"], "color_contrast_failure"),
            (["hierarchy", "focal point", "prominent"], "hierarchy_unclear"),
            (["spacing", "whitespace", "margin", "padding"], "inconsistent_spacing"),
            (["typography", "font", "text size"], "too_many_font_sizes"),
            (["alignment", "grid", "misalign"], "misaligned_elements"),
            (["component", "style", "inconsistent"], "inconsistent_component_style"),
            (["interactive", "clickable", "button"], "unclear_interactive"),
            (["alt text", "screen reader", "aria"], "missing_alt_text"),
            (["keyboard", "focus", "tab"], "no_focus_indicator"),
            (["empty state", "no data", "blank"], "missing_empty_state"),
            (["loading", "spinner", "skeleton"], "missing_loading_state"),
            (["error", "error message"], "unclear_error_message"),
        ]
        
        for keywords, issue_type in type_mappings:
            if any(kw in desc_lower for kw in keywords):
                return issue_type
        
        return "unknown_issue"
    
    def run_dimension_audit_standalone(
        self,
        dimension: AuditDimension,
        screen: Screen,
    ) -> list[AuditFindingCreate]:
        """Run a single dimension audit without persistence.
        
        Useful for testing or preview mode.
        
        Args:
            dimension: Dimension to audit
            screen: Screen to audit
            
        Returns:
            List of findings (not persisted)
        """
        auditor = self._dimensions.get(dimension)
        if not auditor:
            return []
        
        findings = auditor(screen)
        
        # Process findings (classify, filter) without persistence
        for finding in findings:
            finding.dimension = dimension
            
            # Classify severity
            issue_type = self._extract_issue_type(finding.issue)
            finding.severity = self.severity_engine.classify_finding(issue_type)
            
            # Apply Jobs filter
            filter_result = self.jobs_filter.auto_evaluate(finding.issue)
            finding.jobs_filtered = not filter_result.passes
            finding.jobs_filter_score = filter_result.score
        
        return findings


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_default_orchestrator(
    jobs_filter_enabled: bool = True,
    max_findings_per_dimension: int = 100,
) -> AuditOrchestrator:
    """Create an orchestrator with default configuration.
    
    Args:
        jobs_filter_enabled: Whether to enable Jobs filter
        max_findings_per_dimension: Maximum findings per dimension
        
    Returns:
        Configured AuditOrchestrator
    """
    return AuditOrchestrator(
        severity_engine=SeverityEngine(),
        jobs_filter=JobsFilter(enabled=jobs_filter_enabled),
        jobs_filter_enabled=jobs_filter_enabled,
        max_findings_per_dimension=max_findings_per_dimension,
    )
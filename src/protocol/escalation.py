"""
Human-in-the-loop escalation triggers for agent communication.

Implements escalation triggers per AGENTS.md:
1. Design System Changes
2. Disputed Findings
3. Critical Severity Issues
4. Subjective Polish decisions
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageAck,
    MessageType,
    ReviewType,
    create_human_required_message,
)
from src.protocol.sync import SyncLogger, get_sync_logger


class EscalationTrigger(str, Enum):
    """
    Triggers for human escalation per AGENTS.md.
    
    These conditions always require human review.
    """
    DESIGN_SYSTEM_CHANGE = "design_system_change"
    DISPUTED_FINDING = "disputed_finding"
    CRITICAL_SEVERITY = "critical_severity"
    SUBJECTIVE_POLISH = "subjective_polish"
    MANUAL_REQUEST = "manual_request"


class EscalationStatus(str, Enum):
    """Status of an escalation."""
    PENDING = "pending"  # Awaiting human review
    ACKNOWLEDGED = "acknowledged"  # Human has seen it
    IN_REVIEW = "in_review"  # Human is reviewing
    RESOLVED = "resolved"  # Resolution reached
    TIMEOUT = "timeout"  # No response within timeout


class EscalationRecord(BaseModel):
    """Record of an escalation for tracking."""
    escalation_id: str = Field(default_factory=lambda: str(uuid4()))
    trigger: EscalationTrigger
    reason: str
    status: EscalationStatus = EscalationStatus.PENDING
    message: Optional[AgentMessage] = None
    related_artifact_id: Optional[str] = None
    related_audit_id: Optional[str] = None
    related_proposal_id: Optional[str] = None
    blocking: bool = True  # Blocks downstream propagation by default
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    options: Optional[list[dict[str, str]]] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "escalation_id": self.escalation_id,
            "trigger": self.trigger.value,
            "reason": self.reason,
            "status": self.status.value,
            "related_artifact_id": self.related_artifact_id,
            "related_audit_id": self.related_audit_id,
            "related_proposal_id": self.related_proposal_id,
            "blocking": self.blocking,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
            "acknowledged_at": self.acknowledged_at.isoformat() + "Z" if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() + "Z" if self.resolved_at else None,
            "resolution": self.resolution,
            "options": self.options,
        }


class EscalationManager:
    """
    Manages human-in-the-loop escalations.
    
    Per AGENTS.md, escalations are required for:
    - Design system changes (any add/modify to tokens, components, standards)
    - Disputed findings (when agents contest an audit finding)
    - Critical severity issues (visual/interaction problems rated critical)
    - Subjective polish (decisions where "taste" is the discriminator)
    """
    
    # Map EscalationTrigger to ReviewType
    TRIGGER_TO_REVIEW_TYPE = {
        EscalationTrigger.DESIGN_SYSTEM_CHANGE: ReviewType.DESIGN_SYSTEM_CHANGE,
        EscalationTrigger.DISPUTED_FINDING: ReviewType.DISPUTED_FINDING,
        EscalationTrigger.CRITICAL_SEVERITY: ReviewType.CRITICAL_SEVERITY,
        EscalationTrigger.SUBJECTIVE_POLISH: ReviewType.SUBJECTIVE_POLISH,
        EscalationTrigger.MANUAL_REQUEST: ReviewType.DESIGN_SYSTEM_CHANGE,  # Default
    }
    
    def __init__(self, sync_logger: Optional[SyncLogger] = None):
        """
        Initialize the escalation manager.
        
        Args:
            sync_logger: Optional sync logger for logging escalations
        """
        self.sync_logger = sync_logger or get_sync_logger()
        self._escalations: dict[str, EscalationRecord] = {}
    
    def check_escalation_triggers(
        self,
        message_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_disputed: bool = False,
        is_design_system_change: bool = False,
        is_subjective: bool = False,
    ) -> list[EscalationTrigger]:
        """
        Check which escalation triggers fire for a given context.
        
        Args:
            message_type: Type of message being processed
            severity: Severity level if applicable
            is_disputed: Whether this is a disputed finding
            is_design_system_change: Whether this changes the design system
            is_subjective: Whether this is a subjective/polish decision
            
        Returns:
            List of triggers that fired
        """
        triggers = []
        
        # Design system changes always escalate
        if is_design_system_change:
            triggers.append(EscalationTrigger.DESIGN_SYSTEM_CHANGE)
        
        # Disputed findings always escalate
        if is_disputed:
            triggers.append(EscalationTrigger.DISPUTED_FINDING)
        
        # Critical severity always escalates
        if severity and severity.upper() == "CRITICAL":
            triggers.append(EscalationTrigger.CRITICAL_SEVERITY)
        
        # Subjective polish decisions escalate
        if is_subjective:
            triggers.append(EscalationTrigger.SUBJECTIVE_POLISH)
        
        return triggers
    
    def escalate_to_human(
        self,
        trigger: EscalationTrigger,
        reason: str,
        blocking: bool = True,
        related_artifact_id: Optional[str] = None,
        related_audit_id: Optional[str] = None,
        related_proposal_id: Optional[str] = None,
        options: Optional[list[dict[str, str]]] = None,
        report_path: Optional[str] = None,
    ) -> tuple[EscalationRecord, AgentMessage]:
        """
        Escalate an issue to human review.
        
        Args:
            trigger: The trigger that caused escalation
            reason: Why human review is needed
            blocking: Whether this blocks downstream propagation
            related_artifact_id: Related artifact if applicable
            related_audit_id: Related audit if applicable
            related_proposal_id: Related proposal if applicable
            options: Available options for human decision
            report_path: Path to relevant report
            
        Returns:
            Tuple of (EscalationRecord, HUMAN_REQUIRED message)
        """
        # Create escalation record
        record = EscalationRecord(
            trigger=trigger,
            reason=reason,
            blocking=blocking,
            related_artifact_id=related_artifact_id,
            related_audit_id=related_audit_id,
            related_proposal_id=related_proposal_id,
            options=options,
        )
        
        # Create HUMAN_REQUIRED message
        review_type = self.TRIGGER_TO_REVIEW_TYPE.get(trigger, ReviewType.DESIGN_SYSTEM_CHANGE)
        message = create_human_required_message(
            review_type=review_type,
            reason=reason,
            blocking=blocking,
            related_artifact_id=related_artifact_id,
            related_audit_id=related_audit_id,
            related_proposal_id=related_proposal_id,
            options=options,
            report_path=report_path,
        )
        
        record.message = message
        self._escalations[record.escalation_id] = record
        
        # Log the escalation
        self.sync_logger.log_send(message, status="pending")
        
        return record, message
    
    def track_escalation(self, escalation_id: str) -> Optional[EscalationRecord]:
        """
        Get the current status of an escalation.
        
        Args:
            escalation_id: The escalation ID to look up
            
        Returns:
            EscalationRecord if found, None otherwise
        """
        return self._escalations.get(escalation_id)
    
    def acknowledge_escalation(self, escalation_id: str) -> Optional[EscalationRecord]:
        """
        Mark an escalation as acknowledged by human.
        
        Args:
            escalation_id: The escalation ID
            
        Returns:
            Updated EscalationRecord if found
        """
        if escalation_id not in self._escalations:
            return None
        
        record = self._escalations[escalation_id]
        record.status = EscalationStatus.ACKNOWLEDGED
        record.acknowledged_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()
        
        return record
    
    def resolve_escalation(
        self,
        escalation_id: str,
        resolution: str,
    ) -> Optional[EscalationRecord]:
        """
        Resolve an escalation.
        
        Args:
            escalation_id: The escalation ID
            resolution: The resolution decision
            
        Returns:
            Updated EscalationRecord if found
        """
        if escalation_id not in self._escalations:
            return None
        
        record = self._escalations[escalation_id]
        record.status = EscalationStatus.RESOLVED
        record.resolution = resolution
        record.resolved_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()
        
        return record
    
    def mark_timeout(self, escalation_id: str) -> Optional[EscalationRecord]:
        """
        Mark an escalation as timed out.
        
        Args:
            escalation_id: The escalation ID
            
        Returns:
            Updated EscalationRecord if found
        """
        if escalation_id not in self._escalations:
            return None
        
        record = self._escalations[escalation_id]
        record.status = EscalationStatus.TIMEOUT
        record.updated_at = datetime.utcnow()
        
        return record
    
    def get_pending_escalations(self) -> list[EscalationRecord]:
        """Get all pending escalations."""
        return [
            e for e in self._escalations.values()
            if e.status in (EscalationStatus.PENDING, EscalationStatus.ACKNOWLEDGED, EscalationStatus.IN_REVIEW)
        ]
    
    def get_blocking_escalations(self) -> list[EscalationRecord]:
        """Get all blocking pending escalations."""
        return [
            e for e in self._escalations.values()
            if e.blocking and e.status in (EscalationStatus.PENDING, EscalationStatus.ACKNOWLEDGED, EscalationStatus.IN_REVIEW)
        ]
    
    def get_escalations_by_trigger(self, trigger: EscalationTrigger) -> list[EscalationRecord]:
        """Get all escalations of a specific trigger type."""
        return [e for e in self._escalations.values() if e.trigger == trigger]
    
    def get_escalations_by_audit(self, audit_id: str) -> list[EscalationRecord]:
        """Get all escalations for an audit."""
        return [e for e in self._escalations.values() if e.related_audit_id == audit_id]
    
    def clear_resolved(self, older_than_hours: int = 24) -> int:
        """
        Clear resolved escalations older than threshold.
        
        Args:
            older_than_hours: Clear escalations resolved more than this many hours ago
            
        Returns:
            Number of escalations cleared
        """
        cutoff = datetime.utcnow()
        to_remove = []
        
        for escalation_id, escalation in self._escalations.items():
            if escalation.status in (EscalationStatus.RESOLVED, EscalationStatus.TIMEOUT):
                if escalation.resolved_at:
                    age_hours = (cutoff - escalation.resolved_at).total_seconds() / 3600
                    if age_hours > older_than_hours:
                        to_remove.append(escalation_id)
        
        for escalation_id in to_remove:
            del self._escalations[escalation_id]
        
        return len(to_remove)


# Module-level manager instance
_escalation_manager: Optional[EscalationManager] = None


def get_escalation_manager(sync_logger: Optional[SyncLogger] = None) -> EscalationManager:
    """
    Get the singleton escalation manager instance.
    
    Args:
        sync_logger: Optional sync logger
        
    Returns:
        EscalationManager instance
    """
    global _escalation_manager
    if _escalation_manager is None:
        _escalation_manager = EscalationManager(sync_logger=sync_logger)
    return _escalation_manager


def reset_escalation_manager() -> None:
    """Reset the singleton escalation manager (for testing)."""
    global _escalation_manager
    _escalation_manager = None
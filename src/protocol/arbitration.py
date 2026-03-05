"""
Arbitration routing for agent dispute resolution.

Routes disputes to Claude (the designated arbiter) and tracks
dispute status through resolution or escalation.
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
    DisputePayload,
    DisputeSeverity,
    create_dispute_message,
)
from src.protocol.retry import RetryManager, RetryConfig, RetryableError


class DisputeStatus(str, Enum):
    """Status of a dispute."""
    PENDING = "pending"  # Awaiting arbiter review
    IN_REVIEW = "in_review"  # Arbiter is reviewing
    RESOLVED = "resolved"  # Resolution reached
    ESCALATED = "escalated"  # Escalated to human
    TIMEOUT = "timeout"  # No response within timeout


class DisputeResolution(BaseModel):
    """Resolution of a dispute."""
    dispute_id: str
    status: DisputeStatus
    decision: Optional[str] = Field(default=None, description="Arbiter's decision")
    rationale: Optional[str] = Field(default=None, description="Reasoning for decision")
    resolved_by: Optional[str] = Field(default=None, description="Agent who resolved")
    resolved_at: Optional[datetime] = Field(default=None)
    escalated_to: Optional[str] = Field(default=None, description="Human if escalated")


class DisputeRecord(BaseModel):
    """Record of a dispute for tracking."""
    dispute_id: str = Field(default_factory=lambda: str(uuid4()))
    audit_id: str
    finding_id: str
    finding_summary: Optional[str] = None
    dispute_reason: str
    proposed_alternative: Optional[str] = None
    severity: Optional[DisputeSeverity] = None
    source_agent: str
    status: DisputeStatus = DisputeStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolution: Optional[DisputeResolution] = None
    retry_count: int = Field(default=0, ge=0)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dispute_id": self.dispute_id,
            "audit_id": self.audit_id,
            "finding_id": self.finding_id,
            "finding_summary": self.finding_summary,
            "dispute_reason": self.dispute_reason,
            "proposed_alternative": self.proposed_alternative,
            "severity": self.severity.value if self.severity else None,
            "source_agent": self.source_agent,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
            "resolution": self.resolution.model_dump() if self.resolution else None,
            "retry_count": self.retry_count,
        }


class Arbitrator:
    """
    Routes disputes to Claude (the designated arbiter).
    
    Per AGENTS.md and PRD:
    - Claude acts as Product Manager / Arbiter
    - All disputes route through Claude
    - Complex disputes can escalate to human
    """
    
    DEFAULT_ARBITER = AgentType.CLAUDE
    DEFAULT_TIMEOUT = 300.0  # 5 minutes
    
    def __init__(
        self,
        retry_manager: Optional[RetryManager] = None,
        arbiter: AgentType = DEFAULT_ARBITER,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        Initialize the arbitrator.
        
        Args:
            retry_manager: Optional retry manager for routing
            arbiter: The arbiter agent (defaults to Claude)
            timeout: Timeout for arbiter response
        """
        self.retry_manager = retry_manager or RetryManager()
        self.arbiter = arbiter
        self.timeout = timeout
        self._disputes: dict[str, DisputeRecord] = {}
    
    def create_dispute(
        self,
        audit_id: str,
        finding_id: str,
        dispute_reason: str,
        source_agent: AgentType,
        finding_summary: Optional[str] = None,
        proposed_alternative: Optional[str] = None,
        severity: Optional[DisputeSeverity] = None,
    ) -> DisputeRecord:
        """
        Create a new dispute record.
        
        Args:
            audit_id: ID of the related audit
            finding_id: ID of the disputed finding
            dispute_reason: Reason for the dispute
            source_agent: Agent initiating the dispute
            finding_summary: Optional summary of the finding
            proposed_alternative: Optional alternative interpretation
            severity: Optional severity level
            
        Returns:
            The created DisputeRecord
        """
        record = DisputeRecord(
            audit_id=audit_id,
            finding_id=finding_id,
            finding_summary=finding_summary,
            dispute_reason=dispute_reason,
            proposed_alternative=proposed_alternative,
            severity=severity,
            source_agent=source_agent.value,
        )
        self._disputes[record.dispute_id] = record
        return record
    
    def route_to_arbiter(
        self,
        dispute: DisputeRecord,
    ) -> AgentMessage:
        """
        Route a dispute to the arbiter.
        
        Args:
            dispute: The dispute to route
            
        Returns:
            The DISPUTE message to send
        """
        message = create_dispute_message(
            source_agent=AgentType(dispute.source_agent),
            target_agent=self.arbiter,
            dispute_id=dispute.dispute_id,
            audit_id=dispute.audit_id,
            finding_id=dispute.finding_id,
            dispute_reason=dispute.dispute_reason,
            finding_summary=dispute.finding_summary,
            proposed_alternative=dispute.proposed_alternative,
            severity=dispute.severity,
            requires_response=True,
        )
        
        # Update dispute status
        dispute.status = DisputeStatus.IN_REVIEW
        dispute.updated_at = datetime.utcnow()
        dispute.retry_count += 1
        
        return message
    
    def track_dispute_status(self, dispute_id: str) -> Optional[DisputeRecord]:
        """
        Get the current status of a dispute.
        
        Args:
            dispute_id: The dispute ID to look up
            
        Returns:
            DisputeRecord if found, None otherwise
        """
        return self._disputes.get(dispute_id)
    
    def handle_arbiter_response(
        self,
        response: AgentMessage,
    ) -> DisputeResolution:
        """
        Handle a response from the arbiter.
        
        Args:
            response: The response message from the arbiter
            
        Returns:
            DisputeResolution with the outcome
        """
        payload = response.payload
        dispute_id = payload.get("dispute_id")
        
        if not dispute_id or dispute_id not in self._disputes:
            raise ValueError(f"Unknown dispute ID: {dispute_id}")
        
        dispute = self._disputes[dispute_id]
        
        # Check if escalated
        if payload.get("escalated", False):
            resolution = DisputeResolution(
                dispute_id=dispute_id,
                status=DisputeStatus.ESCALATED,
                escalated_to="human",
                resolved_by=response.source_agent.value,
                resolved_at=datetime.utcnow(),
            )
        else:
            resolution = DisputeResolution(
                dispute_id=dispute_id,
                status=DisputeStatus.RESOLVED,
                decision=payload.get("decision"),
                rationale=payload.get("rationale"),
                resolved_by=response.source_agent.value,
                resolved_at=datetime.utcnow(),
            )
        
        # Update dispute record
        dispute.resolution = resolution
        dispute.status = resolution.status
        dispute.updated_at = datetime.utcnow()
        
        return resolution
    
    def mark_timeout(self, dispute_id: str) -> Optional[DisputeResolution]:
        """
        Mark a dispute as timed out.
        
        Args:
            dispute_id: The dispute ID
            
        Returns:
            DisputeResolution if dispute exists
        """
        if dispute_id not in self._disputes:
            return None
        
        dispute = self._disputes[dispute_id]
        resolution = DisputeResolution(
            dispute_id=dispute_id,
            status=DisputeStatus.TIMEOUT,
        )
        
        dispute.resolution = resolution
        dispute.status = DisputeStatus.TIMEOUT
        dispute.updated_at = datetime.utcnow()
        
        return resolution
    
    def escalate_to_human(
        self,
        dispute_id: str,
        reason: str,
    ) -> Optional[DisputeResolution]:
        """
        Escalate a dispute to human review.
        
        Args:
            dispute_id: The dispute ID
            reason: Reason for escalation
            
        Returns:
            DisputeResolution if dispute exists
        """
        if dispute_id not in self._disputes:
            return None
        
        dispute = self._disputes[dispute_id]
        resolution = DisputeResolution(
            dispute_id=dispute_id,
            status=DisputeStatus.ESCALATED,
            escalated_to="human",
            rationale=reason,
            resolved_at=datetime.utcnow(),
        )
        
        dispute.resolution = resolution
        dispute.status = DisputeStatus.ESCALATED
        dispute.updated_at = datetime.utcnow()
        
        return resolution
    
    def get_pending_disputes(self) -> list[DisputeRecord]:
        """Get all pending disputes."""
        return [
            d for d in self._disputes.values()
            if d.status in (DisputeStatus.PENDING, DisputeStatus.IN_REVIEW)
        ]
    
    def get_disputes_by_audit(self, audit_id: str) -> list[DisputeRecord]:
        """Get all disputes for an audit."""
        return [d for d in self._disputes.values() if d.audit_id == audit_id]
    
    def clear_resolved(self, older_than_hours: int = 24) -> int:
        """
        Clear resolved disputes older than threshold.
        
        Args:
            older_than_hours: Clear disputes resolved more than this many hours ago
            
        Returns:
            Number of disputes cleared
        """
        cutoff = datetime.utcnow()
        to_remove = []
        
        for dispute_id, dispute in self._disputes.items():
            if dispute.status in (DisputeStatus.RESOLVED, DisputeStatus.ESCALATED, DisputeStatus.TIMEOUT):
                if dispute.resolution and dispute.resolution.resolved_at:
                    age_hours = (cutoff - dispute.resolution.resolved_at).total_seconds() / 3600
                    if age_hours > older_than_hours:
                        to_remove.append(dispute_id)
        
        for dispute_id in to_remove:
            del self._disputes[dispute_id]
        
        return len(to_remove)


# Module-level arbitrator instance
_arbitrator: Optional[Arbitrator] = None


def get_arbitrator(
    retry_manager: Optional[RetryManager] = None,
    arbiter: AgentType = AgentType.CLAUDE,
) -> Arbitrator:
    """
    Get the singleton arbitrator instance.
    
    Args:
        retry_manager: Optional retry manager
        arbiter: The arbiter agent
        
    Returns:
        Arbitrator instance
    """
    global _arbitrator
    if _arbitrator is None:
        _arbitrator = Arbitrator(retry_manager=retry_manager, arbiter=arbiter)
    return _arbitrator


def reset_arbitrator() -> None:
    """Reset the singleton arbitrator (for testing)."""
    global _arbitrator
    _arbitrator = None
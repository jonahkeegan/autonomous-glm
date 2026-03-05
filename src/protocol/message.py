"""
Pydantic models for agent-to-agent message communication.

Defines structured message types for communication between autonomous-glm
and other agents (Claude, Minimax, Codex, Human) via Unix domain sockets.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class AgentType(str, Enum):
    """Supported agent types for message routing."""
    AUTONOMOUS_GLM = "autonomous-glm"
    CLAUDE = "claude"
    MINIMAX = "minimax"
    CODEX = "codex"
    HUMAN = "human"


class MessageType(str, Enum):
    """Supported message types for agent communication."""
    # Core message types (from interface schemas)
    AUDIT_COMPLETE = "AUDIT_COMPLETE"
    DESIGN_PROPOSAL = "DESIGN_PROPOSAL"
    DISPUTE = "DISPUTE"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    # Handshake message types (for M5-2)
    HELLO = "HELLO"
    ACK = "ACK"
    READY = "READY"
    # Error handling
    ERROR = "ERROR"


class ProposalType(str, Enum):
    """Types of design system proposals."""
    TOKEN_ADDITION = "token_addition"
    TOKEN_MODIFICATION = "token_modification"
    COMPONENT_ADDITION = "component_addition"
    COMPONENT_MODIFICATION = "component_modification"
    STANDARD_UPDATE = "standard_update"


class ChangeType(str, Enum):
    """Types of changes in a proposal."""
    ADD = "add"
    MODIFY = "modify"
    REMOVE = "remove"


class ReviewType(str, Enum):
    """Types of human review required."""
    DESIGN_SYSTEM_CHANGE = "design_system_change"
    DISPUTED_FINDING = "disputed_finding"
    CRITICAL_SEVERITY = "critical_severity"
    SUBJECTIVE_POLISH = "subjective_polish"
    COMPLEX_ARIA = "complex_aria"
    NOVEL_COMPONENT = "novel_component"
    CROSS_AGENT_IMPACT = "cross_agent_impact"


class DisputeSeverity(str, Enum):
    """Severity levels for disputes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Payload models for each message type

class AuditCompletePayload(BaseModel):
    """Payload for AUDIT_COMPLETE messages."""
    artifact_id: str = Field(..., description="ID of the audited artifact")
    audit_id: str = Field(..., description="Unique ID for this audit")
    findings_count: int = Field(..., ge=0, description="Total number of findings")
    critical_count: Optional[int] = Field(default=0, ge=0, description="Number of critical severity findings")
    phases: list[str] = Field(..., description="Phases with findings")
    report_path: Optional[str] = Field(default=None, description="Path to the full audit report")

    @field_validator("phases")
    @classmethod
    def validate_phases(cls, v: list[str]) -> list[str]:
        """Validate phase values."""
        valid_phases = {"Critical", "Refinement", "Polish"}
        for phase in v:
            if phase not in valid_phases:
                raise ValueError(f"Invalid phase: {phase}. Must be one of {valid_phases}")
        return v


class ProposalChange(BaseModel):
    """A single change in a design system proposal."""
    target_file: Optional[str] = Field(default=None, description="Target file for the change")
    change_type: ChangeType = Field(..., description="Type of change")
    old_value: Optional[str] = Field(default=None, description="Old value (for modifications)")
    new_value: Optional[str] = Field(default=None, description="New value")
    rationale: Optional[str] = Field(default=None, description="Reason for the change")


class DesignProposalPayload(BaseModel):
    """Payload for DESIGN_PROPOSAL messages."""
    proposal_id: str = Field(..., description="Unique ID for this proposal")
    proposal_type: ProposalType = Field(..., description="Type of design system change")
    changes: list[ProposalChange] = Field(..., description="List of proposed changes")
    affected_components: Optional[list[str]] = Field(default=None, description="Components affected by this proposal")
    human_approval_required: bool = Field(..., description="Whether human approval is required")
    audit_source: Optional[str] = Field(default=None, description="ID of the audit that triggered this proposal")


class DisputePayload(BaseModel):
    """Payload for DISPUTE messages."""
    dispute_id: str = Field(..., description="Unique ID for this dispute")
    audit_id: str = Field(..., description="ID of the related audit")
    finding_id: str = Field(..., description="ID of the disputed finding")
    finding_summary: Optional[str] = Field(default=None, description="Summary of the disputed finding")
    dispute_reason: str = Field(..., description="Reason for the dispute")
    proposed_alternative: Optional[str] = Field(default=None, description="Alternative interpretation or resolution")
    severity: Optional[DisputeSeverity] = Field(default=None, description="Dispute severity/urgency")


class HumanRequiredPayload(BaseModel):
    """Payload for HUMAN_REQUIRED messages."""
    review_type: ReviewType = Field(..., description="Type of human review required")
    reason: str = Field(..., description="Why human review is needed")
    related_artifact_id: Optional[str] = Field(default=None, description="Related artifact ID if applicable")
    related_audit_id: Optional[str] = Field(default=None, description="Related audit ID if applicable")
    related_proposal_id: Optional[str] = Field(default=None, description="Related design proposal ID if applicable")
    blocking: bool = Field(..., description="Whether this blocks downstream propagation")
    options: Optional[list[dict[str, str]]] = Field(default=None, description="Available options for human decision")
    report_path: Optional[str] = Field(default=None, description="Path to relevant report or context")


class HumanReviewOption(BaseModel):
    """An option for human review decision."""
    label: str = Field(..., description="Option label")
    description: Optional[str] = Field(default=None, description="Option description")
    action: Optional[str] = Field(default=None, description="Action to take")


# Handshake payloads (for M5-2)

class HelloPayload(BaseModel):
    """Payload for HELLO messages during handshake."""
    agent_name: str = Field(..., description="Name of the initiating agent")
    version: str = Field(..., description="Protocol version")
    capabilities: list[str] = Field(default_factory=list, description="Supported capabilities")


class AckPayload(BaseModel):
    """Payload for ACK messages during handshake."""
    agent_name: str = Field(..., description="Name of the acknowledging agent")
    status: str = Field(..., description="Acknowledgment status")
    message: Optional[str] = Field(default=None, description="Optional message")


class ReadyPayload(BaseModel):
    """Payload for READY messages during handshake."""
    agent_name: str = Field(..., description="Name of the ready agent")
    status: str = Field(default="ready", description="Ready status")


class ErrorPayload(BaseModel):
    """Payload for ERROR messages."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional error details")


# Core message models

class AgentMessage(BaseModel):
    """
    Core message model for agent-to-agent communication.
    
    Matches the structure defined in interface schemas for validation.
    """
    message_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for this message")
    source_agent: AgentType = Field(..., description="Source agent identifier")
    target_agent: AgentType = Field(..., description="Target agent for this message")
    message_type: MessageType = Field(..., description="Message type identifier")
    payload: dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="ISO-8601 timestamp")
    requires_response: bool = Field(default=False, description="Whether a response is required")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        }

    def to_json(self) -> str:
        """Serialize message to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "AgentMessage":
        """Deserialize message from JSON string."""
        return cls.model_validate_json(json_str)


class MessageAck(BaseModel):
    """
    Acknowledgment response for message delivery.
    
    Returned by the receiving agent to confirm message receipt.
    """
    message_id: str = Field(..., description="ID of the acknowledged message")
    status: str = Field(..., description="Acknowledgment status (acknowledged, rejected, error)")
    error_message: Optional[str] = Field(default=None, description="Error message if status is error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of acknowledgment")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        valid_statuses = {"acknowledged", "rejected", "error", "pending"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v

    def to_json(self) -> str:
        """Serialize acknowledgment to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "MessageAck":
        """Deserialize acknowledgment from JSON string."""
        return cls.model_validate_json(json_str)


# Factory functions for creating typed messages

def create_audit_complete_message(
    target_agent: AgentType,
    artifact_id: str,
    audit_id: str,
    findings_count: int,
    phases: list[str],
    critical_count: int = 0,
    report_path: Optional[str] = None,
    requires_response: bool = False,
) -> AgentMessage:
    """Create an AUDIT_COMPLETE message."""
    payload = AuditCompletePayload(
        artifact_id=artifact_id,
        audit_id=audit_id,
        findings_count=findings_count,
        critical_count=critical_count,
        phases=phases,
        report_path=report_path,
    )
    return AgentMessage(
        source_agent=AgentType.AUTONOMOUS_GLM,
        target_agent=target_agent,
        message_type=MessageType.AUDIT_COMPLETE,
        payload=payload.model_dump(),
        requires_response=requires_response,
    )


def create_design_proposal_message(
    target_agent: AgentType,
    proposal_id: str,
    proposal_type: ProposalType,
    changes: list[ProposalChange],
    human_approval_required: bool,
    affected_components: Optional[list[str]] = None,
    audit_source: Optional[str] = None,
    requires_response: bool = True,
) -> AgentMessage:
    """Create a DESIGN_PROPOSAL message."""
    payload = DesignProposalPayload(
        proposal_id=proposal_id,
        proposal_type=proposal_type,
        changes=changes,
        affected_components=affected_components,
        human_approval_required=human_approval_required,
        audit_source=audit_source,
    )
    return AgentMessage(
        source_agent=AgentType.AUTONOMOUS_GLM,
        target_agent=target_agent,
        message_type=MessageType.DESIGN_PROPOSAL,
        payload=payload.model_dump(),
        requires_response=requires_response,
    )


def create_dispute_message(
    source_agent: AgentType,
    target_agent: AgentType,
    dispute_id: str,
    audit_id: str,
    finding_id: str,
    dispute_reason: str,
    finding_summary: Optional[str] = None,
    proposed_alternative: Optional[str] = None,
    severity: Optional[DisputeSeverity] = None,
    requires_response: bool = True,
) -> AgentMessage:
    """Create a DISPUTE message."""
    payload = DisputePayload(
        dispute_id=dispute_id,
        audit_id=audit_id,
        finding_id=finding_id,
        finding_summary=finding_summary,
        dispute_reason=dispute_reason,
        proposed_alternative=proposed_alternative,
        severity=severity,
    )
    return AgentMessage(
        source_agent=source_agent,
        target_agent=target_agent,
        message_type=MessageType.DISPUTE,
        payload=payload.model_dump(),
        requires_response=requires_response,
    )


def create_human_required_message(
    review_type: ReviewType,
    reason: str,
    blocking: bool,
    related_artifact_id: Optional[str] = None,
    related_audit_id: Optional[str] = None,
    related_proposal_id: Optional[str] = None,
    options: Optional[list[dict[str, str]]] = None,
    report_path: Optional[str] = None,
) -> AgentMessage:
    """Create a HUMAN_REQUIRED message."""
    payload = HumanRequiredPayload(
        review_type=review_type,
        reason=reason,
        related_artifact_id=related_artifact_id,
        related_audit_id=related_audit_id,
        related_proposal_id=related_proposal_id,
        blocking=blocking,
        options=options,
        report_path=report_path,
    )
    return AgentMessage(
        source_agent=AgentType.AUTONOMOUS_GLM,
        target_agent=AgentType.HUMAN,
        message_type=MessageType.HUMAN_REQUIRED,
        payload=payload.model_dump(),
        requires_response=True,  # Always requires response for human review
    )


def create_hello_message(
    target_agent: AgentType,
    agent_name: str,
    version: str,
    capabilities: Optional[list[str]] = None,
) -> AgentMessage:
    """Create a HELLO message for handshake."""
    payload = HelloPayload(
        agent_name=agent_name,
        version=version,
        capabilities=capabilities or [],
    )
    return AgentMessage(
        source_agent=AgentType.AUTONOMOUS_GLM,
        target_agent=target_agent,
        message_type=MessageType.HELLO,
        payload=payload.model_dump(),
        requires_response=True,
    )


def create_ack_message(
    target_agent: AgentType,
    original_message_id: str,
    agent_name: str,
    status: str = "acknowledged",
    message: Optional[str] = None,
) -> MessageAck:
    """Create an ACK response for a message."""
    return MessageAck(
        message_id=original_message_id,
        status=status,
        error_message=message,
    )


def create_error_message(
    target_agent: AgentType,
    error_code: str,
    error_message: str,
    details: Optional[dict[str, Any]] = None,
) -> AgentMessage:
    """Create an ERROR message."""
    payload = ErrorPayload(
        error_code=error_code,
        error_message=error_message,
        details=details,
    )
    return AgentMessage(
        source_agent=AgentType.AUTONOMOUS_GLM,
        target_agent=target_agent,
        message_type=MessageType.ERROR,
        payload=payload.model_dump(),
        requires_response=False,
    )
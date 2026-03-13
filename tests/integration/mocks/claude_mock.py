"""
Claude (PM/Arbiter) mock for integration testing.

Claude acts as the Product Manager and Arbiter in the multi-agent system.
Responsibilities:
- Receives audit summaries
- Routes disputes
- Confirms design system changes
- Arbitrates between agents
"""

from typing import Optional

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageAck,
    MessageType,
)
from tests.integration.mocks.base_mock import BaseAgentMock, MockConfig, MockResponse


class ClaudeMock(BaseAgentMock):
    """
    Mock for Claude (PM/Arbiter) agent.
    
    Claude-specific behavior:
    - Handles AUDIT_COMPLETE with summary acknowledgment
    - Handles DISPUTE with arbitration resolution
    - Handles DESIGN_PROPOSAL with PM review
    - Can escalate to Human for complex decisions
    """
    
    agent_type = AgentType.CLAUDE
    
    def __init__(
        self,
        config: Optional[MockConfig] = None,
        auto_approve_proposals: bool = True,
        auto_resolve_disputes: bool = True,
    ):
        """
        Initialize Claude mock.
        
        Args:
            config: Mock configuration
            auto_approve_proposals: Whether to auto-approve design proposals
            auto_resolve_disputes: Whether to auto-resolve disputes
        """
        super().__init__(config)
        self.auto_approve_proposals = auto_approve_proposals
        self.auto_resolve_disputes = auto_resolve_disputes
        self._resolved_disputes: list[str] = []
        self._approved_proposals: list[str] = []
        
        # Set PM capabilities
        self.set_capabilities([
            "audit_review",
            "dispute_arbitration",
            "design_system_approval",
            "escalation_to_human",
        ])
    
    def handle_message(self, message: AgentMessage) -> MessageAck:
        """Handle message with Claude-specific logic."""
        # Handle DESIGN_PROPOSAL
        if message.message_type == MessageType.DESIGN_PROPOSAL:
            return self._handle_design_proposal(message)
        
        # Handle DISPUTE
        if message.message_type == MessageType.DISPUTE:
            return self._handle_dispute(message)
        
        # Handle AUDIT_COMPLETE
        if message.message_type == MessageType.AUDIT_COMPLETE:
            return self._handle_audit_complete(message)
        
        # Fall back to base behavior
        return super().handle_message(message)
    
    def _handle_design_proposal(self, message: AgentMessage) -> MessageAck:
        """Handle design system proposal."""
        proposal_id = message.payload.get("proposal_id", "unknown")
        
        if self.auto_approve_proposals:
            self._approved_proposals.append(proposal_id)
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        # If not auto-approve, check configured response
        response = self._response_overrides.get(
            MessageType.DESIGN_PROPOSAL,
            self.config.default_response,
        )
        
        if response == MockResponse.ESCALATE:
            # Escalate to human for design system changes
            return MessageAck(
                message_id=message.message_id,
                status="pending",
                error_message="Design proposal escalated to human review",
            )
        
        return self._generate_ack(message, response)
    
    def _handle_dispute(self, message: AgentMessage) -> MessageAck:
        """Handle dispute as arbiter."""
        dispute_id = message.payload.get("dispute_id", "unknown")
        
        if self.auto_resolve_disputes:
            self._resolved_disputes.append(dispute_id)
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        # If not auto-resolve, check configured response
        response = self._response_overrides.get(
            MessageType.DISPUTE,
            self.config.default_response,
        )
        
        if response == MockResponse.ESCALATE:
            # Escalate complex disputes to human
            return MessageAck(
                message_id=message.message_id,
                status="pending",
                error_message="Dispute escalated to human arbiter",
            )
        
        return self._generate_ack(message, response)
    
    def _handle_audit_complete(self, message: AgentMessage) -> MessageAck:
        """Handle audit completion summary."""
        # Claude receives audit summaries for PM awareness
        return MessageAck(
            message_id=message.message_id,
            status="acknowledged",
        )
    
    def get_resolved_disputes(self) -> list[str]:
        """Get list of resolved dispute IDs."""
        return self._resolved_disputes.copy()
    
    def get_approved_proposals(self) -> list[str]:
        """Get list of approved proposal IDs."""
        return self._approved_proposals.copy()
    
    def reset(self) -> None:
        """Reset mock to initial state."""
        super().reset()
        self._resolved_disputes.clear()
        self._approved_proposals.clear()
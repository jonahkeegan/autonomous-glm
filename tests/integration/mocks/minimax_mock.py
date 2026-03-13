"""
Minimax (Frontend Engineer) mock for integration testing.

Minimax receives implementation-ready audit findings and phased plans
for frontend implementation work.
"""

from typing import Optional

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageAck,
    MessageType,
)
from tests.integration.mocks.base_mock import BaseAgentMock, MockConfig


class MinimaxMock(BaseAgentMock):
    """
    Mock for Minimax (Frontend Engineer) agent.
    
    Minimax-specific behavior:
    - Receives AUDIT_COMPLETE with implementation-ready findings
    - Receives DESIGN_PROPOSAL for frontend token/component changes
    - Acknowledges phased plans
    """
    
    agent_type = AgentType.MINIMAX
    
    def __init__(
        self,
        config: Optional[MockConfig] = None,
        auto_accept_findings: bool = True,
    ):
        """
        Initialize Minimax mock.
        
        Args:
            config: Mock configuration
            auto_accept_findings: Whether to auto-accept all findings
        """
        super().__init__(config)
        self.auto_accept_findings = auto_accept_findings
        self._received_findings: list[dict] = []
        self._received_proposals: list[str] = []
        
        # Set FE engineer capabilities
        self.set_capabilities([
            "implement_findings",
            "apply_design_tokens",
            "component_updates",
            "css_modifications",
        ])
    
    def handle_message(self, message: AgentMessage) -> MessageAck:
        """Handle message with Minimax-specific logic."""
        # Handle AUDIT_COMPLETE with findings
        if message.message_type == MessageType.AUDIT_COMPLETE:
            return self._handle_audit_complete(message)
        
        # Handle DESIGN_PROPOSAL for token/component changes
        if message.message_type == MessageType.DESIGN_PROPOSAL:
            return self._handle_design_proposal(message)
        
        # Fall back to base behavior
        return super().handle_message(message)
    
    def _handle_audit_complete(self, message: AgentMessage) -> MessageAck:
        """Handle audit completion with findings."""
        if self.auto_accept_findings:
            findings_count = message.payload.get("findings_count", 0)
            phases = message.payload.get("phases", [])
            self._received_findings.append({
                "audit_id": message.payload.get("audit_id"),
                "findings_count": findings_count,
                "phases": phases,
            })
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        return super().handle_message(message)
    
    def _handle_design_proposal(self, message: AgentMessage) -> MessageAck:
        """Handle design proposal for frontend changes."""
        proposal_id = message.payload.get("proposal_id", "unknown")
        proposal_type = message.payload.get("proposal_type", "unknown")
        
        # Track proposals that affect frontend
        if proposal_type in ["token_addition", "token_modification", 
                             "component_addition", "component_modification"]:
            self._received_proposals.append(proposal_id)
        
        return MessageAck(
            message_id=message.message_id,
            status="acknowledged",
        )
    
    def get_received_findings(self) -> list[dict]:
        """Get list of received audit findings."""
        return self._received_findings.copy()
    
    def get_received_proposals(self) -> list[str]:
        """Get list of received proposal IDs."""
        return self._received_proposals.copy()
    
    def reset(self) -> None:
        """Reset mock to initial state."""
        super().reset()
        self._received_findings.clear()
        self._received_proposals.clear()
"""
Codex (Backend Engineer) mock for integration testing.

Codex receives visual fit confirmations post-API integration
and handles backend-related audit findings.
"""

from typing import Optional

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageAck,
    MessageType,
)
from tests.integration.mocks.base_mock import BaseAgentMock, MockConfig


class CodexMock(BaseAgentMock):
    """
    Mock for Codex (Backend Engineer) agent.
    
    Codex-specific behavior:
    - Receives AUDIT_COMPLETE for API integration confirmations
    - Handles backend-related findings
    - Acknowledges design proposals affecting backend
    """
    
    agent_type = AgentType.CODEX
    
    def __init__(
        self,
        config: Optional[MockConfig] = None,
        auto_confirm: bool = True,
    ):
        """
        Initialize Codex mock.
        
        Args:
            config: Mock configuration
            auto_confirm: Whether to auto-confirm all requests
        """
        super().__init__(config)
        self.auto_confirm = auto_confirm
        self._received_audits: list[str] = []
        self._confirmed_integrations: list[str] = []
        
        # Set BE engineer capabilities
        self.set_capabilities([
            "api_integration",
            "visual_fit_confirmation",
            "backend_validation",
            "data_layer_updates",
        ])
    
    def handle_message(self, message: AgentMessage) -> MessageAck:
        """Handle message with Codex-specific logic."""
        # Handle AUDIT_COMPLETE for visual fit confirmation
        if message.message_type == MessageType.AUDIT_COMPLETE:
            return self._handle_audit_complete(message)
        
        # Handle DESIGN_PROPOSAL for backend changes
        if message.message_type == MessageType.DESIGN_PROPOSAL:
            return self._handle_design_proposal(message)
        
        # Fall back to base behavior
        return super().handle_message(message)
    
    def _handle_audit_complete(self, message: AgentMessage) -> MessageAck:
        """Handle audit completion for backend confirmation."""
        audit_id = message.payload.get("audit_id", "unknown")
        self._received_audits.append(audit_id)
        
        if self.auto_confirm:
            self._confirmed_integrations.append(audit_id)
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        return super().handle_message(message)
    
    def _handle_design_proposal(self, message: AgentMessage) -> MessageAck:
        """Handle design proposal for backend changes."""
        proposal_type = message.payload.get("proposal_type", "unknown")
        
        # Backend mainly cares about standard updates
        if proposal_type == "standard_update":
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        return MessageAck(
            message_id=message.message_id,
            status="acknowledged",
        )
    
    def get_received_audits(self) -> list[str]:
        """Get list of received audit IDs."""
        return self._received_audits.copy()
    
    def get_confirmed_integrations(self) -> list[str]:
        """Get list of confirmed integration IDs."""
        return self._confirmed_integrations.copy()
    
    def reset(self) -> None:
        """Reset mock to initial state."""
        super().reset()
        self._received_audits.clear()
        self._confirmed_integrations.clear()
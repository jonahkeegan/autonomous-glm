"""
Human (Design Lead) mock for integration testing.

The Human mock simulates the Design Lead who:
- Receives disputed findings
- Reviews design system proposals
- Provides override authority
- Makes final decisions on escalated issues
"""

from typing import Optional

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageAck,
    MessageType,
    ReviewType,
)
from tests.integration.mocks.base_mock import BaseAgentMock, MockConfig, MockResponse


class HumanMock(BaseAgentMock):
    """
    Mock for Human (Design Lead) agent.
    
    Human-specific behavior:
    - Handles HUMAN_REQUIRED for escalations
    - Reviews disputed findings
    - Approves/rejects design system changes
    - Provides final arbitration
    """
    
    agent_type = AgentType.HUMAN
    
    def __init__(
        self,
        config: Optional[MockConfig] = None,
        auto_approve: bool = True,
        review_delay_ms: int = 0,
    ):
        """
        Initialize Human mock.
        
        Args:
            config: Mock configuration
            auto_approve: Whether to auto-approve all requests
            review_delay_ms: Simulated review delay in milliseconds
        """
        super().__init__(config)
        self.auto_approve = auto_approve
        self.review_delay_ms = review_delay_ms
        self._pending_reviews: list[dict] = []
        self._completed_reviews: list[dict] = []
        self._decisions: list[dict] = []
        
        # Set Design Lead capabilities
        self.set_capabilities([
            "dispute_resolution",
            "design_system_approval",
            "override_authority",
            "final_arbitration",
        ])
    
    def handle_message(self, message: AgentMessage) -> MessageAck:
        """Handle message with Human-specific logic."""
        # Handle HUMAN_REQUIRED for escalations
        if message.message_type == MessageType.HUMAN_REQUIRED:
            return self._handle_human_required(message)
        
        # Handle DESIGN_PROPOSAL requiring human approval
        if message.message_type == MessageType.DESIGN_PROPOSAL:
            return self._handle_design_proposal(message)
        
        # Handle DISPUTE escalated to human
        if message.message_type == MessageType.DISPUTE:
            return self._handle_dispute(message)
        
        # Fall back to base behavior
        return super().handle_message(message)
    
    def _handle_human_required(self, message: AgentMessage) -> MessageAck:
        """Handle human-required escalation."""
        review_type = message.payload.get("review_type", "unknown")
        reason = message.payload.get("reason", "")
        blocking = message.payload.get("blocking", False)
        
        # Log pending review
        review = {
            "message_id": message.message_id,
            "review_type": review_type,
            "reason": reason,
            "blocking": blocking,
        }
        self._pending_reviews.append(review)
        
        if self.auto_approve:
            # Auto-approve
            self._completed_reviews.append(review)
            self._decisions.append({
                "message_id": message.message_id,
                "decision": "approved",
                "review_type": review_type,
            })
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        # Check for configured response
        response = self._response_overrides.get(
            MessageType.HUMAN_REQUIRED,
            self.config.default_response,
        )
        
        if response == MockResponse.DELAY:
            # Simulate review delay
            return MessageAck(
                message_id=message.message_id,
                status="pending",
                error_message=f"Under review (simulated delay: {self.review_delay_ms}ms)",
            )
        
        return self._generate_ack(message, response)
    
    def _handle_design_proposal(self, message: AgentMessage) -> MessageAck:
        """Handle design proposal requiring human approval."""
        proposal_id = message.payload.get("proposal_id", "unknown")
        human_approval_required = message.payload.get("human_approval_required", False)
        
        if not human_approval_required:
            # Not required, just acknowledge
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        if self.auto_approve:
            self._decisions.append({
                "message_id": message.message_id,
                "decision": "approved",
                "proposal_id": proposal_id,
            })
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        # Needs manual review
        return MessageAck(
            message_id=message.message_id,
            status="pending",
            error_message="Design proposal pending human review",
        )
    
    def _handle_dispute(self, message: AgentMessage) -> MessageAck:
        """Handle dispute escalated to human."""
        dispute_id = message.payload.get("dispute_id", "unknown")
        
        if self.auto_approve:
            self._decisions.append({
                "message_id": message.message_id,
                "decision": "resolved",
                "dispute_id": dispute_id,
            })
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        return MessageAck(
            message_id=message.message_id,
            status="pending",
            error_message="Dispute pending human review",
        )
    
    def get_pending_reviews(self) -> list[dict]:
        """Get list of pending reviews."""
        return self._pending_reviews.copy()
    
    def get_completed_reviews(self) -> list[dict]:
        """Get list of completed reviews."""
        return self._completed_reviews.copy()
    
    def get_decisions(self) -> list[dict]:
        """Get list of decisions made."""
        return self._decisions.copy()
    
    def reset(self) -> None:
        """Reset mock to initial state."""
        super().reset()
        self._pending_reviews.clear()
        self._completed_reviews.clear()
        self._decisions.clear()
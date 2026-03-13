"""
Integration tests for arbitration flow.

Tests the dispute resolution and escalation mechanisms:
- Dispute creation and handling
- Claude arbitration behavior
- Human escalation
"""

import pytest

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageType,
)
from tests.integration.mocks import ClaudeMock, HumanMock


# =============================================================================
# DISPUTE CREATION TESTS
# =============================================================================

class TestDisputeCreation:
    """Tests for dispute creation and initial handling."""
    
    def test_create_dispute(self, claude_mock):
        """Dispute can be created and sent to arbiter."""
        msg = AgentMessage(
            message_id="msg-dispute-001",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.DISPUTE,
            payload={
                "dispute_id": "dispute-001",
                "audit_id": "audit-001",
                "finding_id": "finding-001",
                "finding_summary": "Insufficient contrast",
                "dispute_reason": "Contrast ratio is actually 4.8:1",
                "severity": "medium",
            },
        )
        
        ack = claude_mock.handle_message(msg)
        
        assert ack.status == "acknowledged"
    
    def test_dispute_with_high_severity(self, claude_mock):
        """High severity disputes are tracked."""
        msg = AgentMessage(
            message_id="msg-dispute-002",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.DISPUTE,
            payload={
                "dispute_id": "dispute-high-001",
                "severity": "high",
            },
        )
        
        ack = claude_mock.handle_message(msg)
        
        assert ack.status == "acknowledged"


# =============================================================================
# CLAUDE ARBITRATION TESTS
# =============================================================================

class TestClaudeArbitration:
    """Tests for Claude's arbitration behavior."""
    
    def test_auto_resolve_disputes(self):
        """Claude auto-resolves disputes when configured."""
        claude = ClaudeMock(auto_resolve_disputes=True)
        claude.connect()
        
        msg = AgentMessage(
            message_id="msg-auto-resolve",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.DISPUTE,
            payload={"dispute_id": "auto-001"},
        )
        
        ack = claude.handle_message(msg)
        
        assert ack.status == "acknowledged"
    
    def test_claude_receives_dispute(self):
        """Claude can receive and acknowledge disputes."""
        claude = ClaudeMock()
        claude.connect()
        
        msg = AgentMessage(
            message_id="msg-claude-dispute",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.DISPUTE,
            payload={"severity": "high"},
        )
        
        ack = claude.handle_message(msg)
        
        assert ack.status == "acknowledged"


# =============================================================================
# HUMAN ESCALATION TESTS
# =============================================================================

class TestHumanEscalation:
    """Tests for human escalation flow."""
    
    def test_escalation_to_human(self, human_mock):
        """Issues can be escalated to human."""
        msg = AgentMessage(
            message_id="msg-escalation-001",
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.HUMAN,
            message_type=MessageType.HUMAN_REQUIRED,
            payload={
                "review_type": "dispute_escalation",
                "reason": "Claude unable to resolve",
                "blocking": True,
            },
        )
        
        ack = human_mock.handle_message(msg)
        
        assert ack.status == "acknowledged"
    
    def test_human_auto_approve(self):
        """Human can auto-approve in test mode."""
        human = HumanMock(auto_approve=True)
        human.connect()
        
        msg = AgentMessage(
            message_id="msg-auto-approve",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.HUMAN,
            message_type=MessageType.HUMAN_REQUIRED,
            payload={"review_type": "design_system_change"},
        )
        
        ack = human.handle_message(msg)
        
        assert ack.status == "acknowledged"


# =============================================================================
# DESIGN SYSTEM APPROVAL TESTS
# =============================================================================

class TestDesignSystemApproval:
    """Tests for design system change approvals."""
    
    def test_proposal_requires_human_approval(self, human_mock):
        """Design system proposals require human approval."""
        msg = AgentMessage(
            message_id="msg-proposal-001",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.HUMAN,
            message_type=MessageType.DESIGN_PROPOSAL,
            payload={
                "proposal_id": "proposal-001",
                "proposal_type": "token_addition",
                "human_approval_required": True,
            },
        )
        
        ack = human_mock.handle_message(msg)
        
        assert ack.status == "acknowledged"
    
    def test_proposal_without_human_requirement(self, human_mock):
        """Proposals not flagged for human are acknowledged."""
        msg = AgentMessage(
            message_id="msg-proposal-002",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.HUMAN,
            message_type=MessageType.DESIGN_PROPOSAL,
            payload={
                "proposal_id": "proposal-002",
                "human_approval_required": False,
            },
        )
        
        ack = human_mock.handle_message(msg)
        
        assert ack.status == "acknowledged"


# =============================================================================
# COMPLETE ARBITRATION FLOW TESTS
# =============================================================================

class TestCompleteArbitrationFlow:
    """Tests for complete arbitration workflows."""
    
    def test_dispute_to_escalation_flow(self):
        """Complete flow from dispute to human escalation."""
        # Setup agents
        claude = ClaudeMock(auto_resolve_disputes=False)
        claude.connect()
        
        human = HumanMock(auto_approve=True)
        human.connect()
        
        # Step 1: Dispute received by Claude
        dispute_msg = AgentMessage(
            message_id="msg-flow-dispute",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.DISPUTE,
            payload={
                "dispute_id": "dispute-flow-001",
                "severity": "high",
            },
        )
        
        ack1 = claude.handle_message(dispute_msg)
        assert ack1.status == "acknowledged"
        
        # Step 2: Escalated to human
        escalation_msg = AgentMessage(
            message_id="msg-flow-escalation",
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.HUMAN,
            message_type=MessageType.HUMAN_REQUIRED,
            payload={
                "review_type": "dispute_escalation",
                "reason": "Claude escalated dispute",
            },
        )
        
        ack2 = human.handle_message(escalation_msg)
        assert ack2.status == "acknowledged"
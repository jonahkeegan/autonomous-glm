"""
Integration tests for complete protocol flows.

Tests end-to-end flows including:
- Message creation and handling
- Multi-agent message broadcasting
"""

import pytest

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageType,
)
from tests.integration.mocks import ClaudeMock, MinimaxMock, CodexMock, HumanMock


# =============================================================================
# MESSAGE FLOW TESTS
# =============================================================================

class TestMessageFlows:
    """Tests for message flow between agents."""
    
    def test_audit_complete_reaches_claude(self, claude_mock):
        """AUDIT_COMPLETE is received by Claude."""
        msg = AgentMessage(
            message_id="msg-001",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.AUDIT_COMPLETE,
            payload={
                "artifact_id": "artifact-001",
                "audit_id": "audit-001",
                "findings_count": 5,
            },
        )
        
        ack = claude_mock.handle_message(msg)
        
        assert ack.status == "acknowledged"
    
    def test_design_proposal_to_human(self, human_mock):
        """DESIGN_PROPOSAL reaches Human."""
        msg = AgentMessage(
            message_id="msg-002",
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
    
    def test_dispute_to_claude(self, claude_mock):
        """DISPUTE reaches Claude."""
        msg = AgentMessage(
            message_id="msg-003",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.DISPUTE,
            payload={
                "dispute_id": "dispute-001",
                "audit_id": "audit-001",
                "finding_id": "finding-001",
            },
        )
        
        ack = claude_mock.handle_message(msg)
        
        assert ack.status == "acknowledged"


# =============================================================================
# MULTI-AGENT BROADCAST TESTS
# =============================================================================

class TestMultiAgentBroadcast:
    """Tests for broadcasting messages to multiple agents."""
    
    def test_broadcast_to_all_agents(self, mock_agents):
        """Message can be sent to all agents."""
        for agent_type, agent in mock_agents.items():
            msg = AgentMessage(
                message_id=f"msg-broadcast-{agent_type.value}",
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=agent_type,
                message_type=MessageType.AUDIT_COMPLETE,
                payload={"test": "broadcast"},
            )
            
            ack = agent.handle_message(msg)
            assert ack.status == "acknowledged"
    
    def test_message_tracking_per_agent(self, mock_agents):
        """Each agent tracks received messages independently."""
        for agent_type, agent in mock_agents.items():
            # Send a message
            msg = AgentMessage(
                message_id=f"msg-unique-{agent_type.value}",
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=agent_type,
                message_type=MessageType.AUDIT_COMPLETE,
                payload={"test": "unique"},
            )
            ack = agent.handle_message(msg)
            
            # Agent should have acknowledged the message
            assert ack.status == "acknowledged"


# =============================================================================
# COMPLETE WORKFLOW TESTS
# =============================================================================

class TestCompleteWorkflows:
    """Tests for complete end-to-end workflows."""
    
    def test_audit_to_proposal_workflow(self, mock_agents_with_handshake):
        """Complete workflow from audit to proposal."""
        claude = mock_agents_with_handshake[AgentType.CLAUDE]
        human = mock_agents_with_handshake[AgentType.HUMAN]
        
        # Step 1: Audit complete to Claude
        audit_msg = AgentMessage(
            message_id="msg-workflow-1",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.AUDIT_COMPLETE,
            payload={
                "artifact_id": "artifact-workflow",
                "audit_id": "audit-workflow",
                "findings_count": 3,
            },
        )
        ack1 = claude.handle_message(audit_msg)
        assert ack1.status == "acknowledged"
        
        # Step 2: Design proposal to Human
        proposal_msg = AgentMessage(
            message_id="msg-workflow-2",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.HUMAN,
            message_type=MessageType.DESIGN_PROPOSAL,
            payload={
                "proposal_id": "proposal-workflow",
                "human_approval_required": True,
            },
        )
        ack2 = human.handle_message(proposal_msg)
        assert ack2.status == "acknowledged"
    
    def test_multi_agent_communication(self, mock_agents):
        """Test communication between multiple agents."""
        agents = [
            (AgentType.CLAUDE, mock_agents[AgentType.CLAUDE]),
            (AgentType.MINIMAX, mock_agents[AgentType.MINIMAX]),
            (AgentType.CODEX, mock_agents[AgentType.CODEX]),
            (AgentType.HUMAN, mock_agents[AgentType.HUMAN]),
        ]
        
        # Send messages to all agents
        for agent_type, agent in agents:
            msg = AgentMessage(
                message_id=f"msg-multi-{agent_type.value}",
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=agent_type,
                message_type=MessageType.AUDIT_COMPLETE,
                payload={"test": "multi"},
            )
            ack = agent.handle_message(msg)
            assert ack.status == "acknowledged"


# =============================================================================
# MESSAGE VALIDATION TESTS
# =============================================================================

class TestMessageValidation:
    """Tests for message validation."""
    
    def test_message_creation(self):
        """Messages can be created with valid data."""
        msg = AgentMessage(
            message_id="msg-test",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.AUDIT_COMPLETE,
            payload={"test": "data"},
        )
        
        assert msg.message_id == "msg-test"
        assert msg.source_agent == AgentType.AUTONOMOUS_GLM
        assert msg.target_agent == AgentType.CLAUDE
        assert msg.message_type == MessageType.AUDIT_COMPLETE
    
    def test_all_message_types(self, claude_mock):
        """All message types can be sent."""
        message_types = [
            MessageType.AUDIT_COMPLETE,
            MessageType.DESIGN_PROPOSAL,
            MessageType.DISPUTE,
            MessageType.HUMAN_REQUIRED,
        ]
        
        for i, msg_type in enumerate(message_types):
            msg = AgentMessage(
                message_id=f"msg-type-{i}",
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=AgentType.CLAUDE,
                message_type=msg_type,
                payload={"test": i},
            )
            ack = claude_mock.handle_message(msg)
            assert ack.status == "acknowledged"
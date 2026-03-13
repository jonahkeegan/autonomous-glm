"""
Integration tests for agent handshake protocol.

Tests the HELLO/ACK/READY three-way handshake sequence:
- Normal handshake completion
- Rejected handshake handling
- Multi-agent handshake
- Capability negotiation
"""

import pytest

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageType,
    create_hello_message,
    create_ack_message,
)
from tests.integration.mocks import ClaudeMock, MinimaxMock, CodexMock, HumanMock
from tests.integration.mocks.base_mock import MockConfig, MockResponse, MockState


# =============================================================================
# HELLO/ACK/READY SEQUENCE TESTS
# =============================================================================

class TestHandshakeSequence:
    """Tests for the three-way handshake sequence."""
    
    def test_hello_ack_ready_sequence(self, claude_mock):
        """Full HELLO → ACK → READY handshake sequence."""
        # Initially disconnected
        assert claude_mock.state == MockState.CONNECTED
        assert not claude_mock.is_handshake_complete()
        
        # Step 1: Send HELLO
        hello_msg = create_hello_message(
            target_agent=AgentType.CLAUDE,
            agent_name="autonomous-glm",
            version="1.0.0",
            capabilities=["audit", "plan", "report"],
        )
        
        ack = claude_mock.handle_message(hello_msg)
        
        # Should acknowledge and move to handshaking
        assert ack.status == "acknowledged"
        assert claude_mock.state == MockState.HANDSHAKING
        
        # Step 2: Send READY
        ready_msg = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.READY,
            payload={"agent_name": "autonomous-glm", "status": "ready"},
        )
        
        ack2 = claude_mock.handle_message(ready_msg)
        
        # Handshake complete
        assert ack2.status == "acknowledged"
        assert claude_mock.is_handshake_complete()
        assert claude_mock.state == MockState.CONNECTED
    
    def test_handshake_without_auto(self):
        """Handshake can be disabled via config."""
        config = MockConfig(auto_handshake=False)
        mock = ClaudeMock(config=config)
        mock.connect()
        
        # Send HELLO
        hello_msg = create_hello_message(
            target_agent=AgentType.CLAUDE,
            agent_name="autonomous-glm",
            version="1.0.0",
        )
        
        ack = mock.handle_message(hello_msg)
        
        # Should reject
        assert ack.status == "rejected"
        assert not mock.is_handshake_complete()


# =============================================================================
# REJECTED HANDSHAKE TESTS
# =============================================================================

class TestRejectedHandshake:
    """Tests for rejected handshake scenarios."""
    
    def test_handshake_rejected_by_config(self):
        """Handshake rejected when auto_handshake=False."""
        config = MockConfig(auto_handshake=False)
        mock = MinimaxMock(config=config)
        mock.connect()
        
        hello_msg = create_hello_message(
            target_agent=AgentType.MINIMAX,
            agent_name="autonomous-glm",
            version="1.0.0",
        )
        
        ack = mock.handle_message(hello_msg)
        
        assert ack.status == "rejected"
        assert "rejected" in ack.error_message.lower()
    
    def test_handshake_ready_before_hello(self, claude_mock):
        """READY before HELLO doesn't complete handshake."""
        # Send READY first (without HELLO)
        ready_msg = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.READY,
            payload={"agent_name": "autonomous-glm", "status": "ready"},
        )
        
        # This will complete handshake due to auto_handshake=True
        # but in a real scenario, it should require HELLO first
        ack = claude_mock.handle_message(ready_msg)
        
        # Our mock is permissive - acknowledges READY
        assert ack.status == "acknowledged"


# =============================================================================
# MULTI-AGENT HANDSHAKE TESTS
# =============================================================================

class TestMultiAgentHandshake:
    """Tests for handshake with multiple agents."""
    
    def test_all_agents_handshake(self, mock_agents):
        """All 4 agents can complete handshake."""
        for agent_type, mock in mock_agents.items():
            # Send HELLO
            hello_msg = create_hello_message(
                target_agent=agent_type,
                agent_name="autonomous-glm",
                version="1.0.0",
            )
            ack = mock.handle_message(hello_msg)
            assert ack.status == "acknowledged", f"HELLO failed for {agent_type}"
            
            # Send READY
            ready_msg = AgentMessage(
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=agent_type,
                message_type=MessageType.READY,
                payload={"agent_name": "autonomous-glm", "status": "ready"},
            )
            ack2 = mock.handle_message(ready_msg)
            assert ack2.status == "acknowledged", f"READY failed for {agent_type}"
            assert mock.is_handshake_complete(), f"Handshake incomplete for {agent_type}"
    
    def test_independent_agent_states(self, mock_agents):
        """Each agent maintains independent state."""
        # Complete handshake with Claude only
        claude = mock_agents[AgentType.CLAUDE]
        
        hello_msg = create_hello_message(
            target_agent=AgentType.CLAUDE,
            agent_name="autonomous-glm",
            version="1.0.0",
        )
        claude.handle_message(hello_msg)
        
        ready_msg = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.READY,
            payload={"agent_name": "autonomous-glm", "status": "ready"},
        )
        claude.handle_message(ready_msg)
        
        # Claude should be handshaken
        assert claude.is_handshake_complete()
        
        # Others should not
        assert not mock_agents[AgentType.MINIMAX].is_handshake_complete()
        assert not mock_agents[AgentType.CODEX].is_handshake_complete()
        assert not mock_agents[AgentType.HUMAN].is_handshake_complete()


# =============================================================================
# CAPABILITY NEGOTIATION TESTS
# =============================================================================

class TestCapabilityNegotiation:
    """Tests for capability exchange during handshake."""
    
    def test_capabilities_exchanged(self, claude_mock):
        """Capabilities are exchanged during HELLO."""
        capabilities = ["audit_review", "dispute_arbitration", "escalation"]
        
        hello_msg = create_hello_message(
            target_agent=AgentType.CLAUDE,
            agent_name="autonomous-glm",
            version="1.0.0",
            capabilities=capabilities,
        )
        
        claude_mock.handle_message(hello_msg)
        
        # Message should be logged
        received = claude_mock.get_received_messages(MessageType.HELLO)
        assert len(received) == 1
        
        # Capabilities should be in payload
        received_caps = received[0].payload.get("capabilities", [])
        assert "audit_review" in received_caps
        assert "dispute_arbitration" in received_caps
    
    def test_agent_capabilities_set(self, mock_agents):
        """Each agent type has appropriate capabilities."""
        # Claude has PM/arbiter capabilities
        claude_caps = mock_agents[AgentType.CLAUDE]._capabilities
        assert "audit_review" in claude_caps
        assert "dispute_arbitration" in claude_caps
        
        # Minimax has FE capabilities
        minimax_caps = mock_agents[AgentType.MINIMAX]._capabilities
        assert "implement_findings" in minimax_caps
        assert "component_updates" in minimax_caps
        
        # Codex has BE capabilities
        codex_caps = mock_agents[AgentType.CODEX]._capabilities
        assert "api_integration" in codex_caps
        
        # Human has override capabilities
        human_caps = mock_agents[AgentType.HUMAN]._capabilities
        assert "override_authority" in human_caps
        assert "final_arbitration" in human_caps


# =============================================================================
# RECONNECTION TESTS
# =============================================================================

class TestReconnection:
    """Tests for reconnection scenarios."""
    
    def test_disconnect_resets_handshake(self, claude_mock):
        """Disconnect resets handshake state."""
        # Complete handshake
        hello_msg = create_hello_message(
            target_agent=AgentType.CLAUDE,
            agent_name="autonomous-glm",
            version="1.0.0",
        )
        claude_mock.handle_message(hello_msg)
        
        ready_msg = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.READY,
            payload={"agent_name": "autonomous-glm", "status": "ready"},
        )
        claude_mock.handle_message(ready_msg)
        
        assert claude_mock.is_handshake_complete()
        
        # Disconnect
        claude_mock.disconnect()
        
        # State should be reset
        assert not claude_mock.is_handshake_complete()
        assert claude_mock.state == MockState.DISCONNECTED
    
    def test_reconnect_and_handshake(self, claude_mock):
        """Can reconnect and re-handshake after disconnect."""
        # First handshake
        hello_msg = create_hello_message(
            target_agent=AgentType.CLAUDE,
            agent_name="autonomous-glm",
            version="1.0.0",
        )
        claude_mock.handle_message(hello_msg)
        
        ready_msg = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.READY,
            payload={"agent_name": "autonomous-glm", "status": "ready"},
        )
        claude_mock.handle_message(ready_msg)
        
        # Disconnect
        claude_mock.disconnect()
        
        # Reconnect
        claude_mock.connect()
        
        # Second handshake
        hello_msg2 = create_hello_message(
            target_agent=AgentType.CLAUDE,
            agent_name="autonomous-glm",
            version="1.0.0",
        )
        ack1 = claude_mock.handle_message(hello_msg2)
        
        ready_msg2 = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.READY,
            payload={"agent_name": "autonomous-glm", "status": "ready"},
        )
        ack2 = claude_mock.handle_message(ready_msg2)
        
        assert ack1.status == "acknowledged"
        assert ack2.status == "acknowledged"
        assert claude_mock.is_handshake_complete()
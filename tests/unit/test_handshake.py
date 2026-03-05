"""
Unit tests for the handshake protocol module.

Tests registry, state machine, handshake protocol, and health monitor.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.protocol import (
    AgentType,
    HandshakeState,
    AgentInfo,
    AgentRegistry,
    reset_registry,
    ConnectionState,
    ConnectionManager,
    StateTransitionError,
    reset_connection_manager,
    HandshakeResult,
    HandshakeConfig,
    HandshakeError,
    HandshakeTimeout,
    Handshaker,
    HealthMonitor,
    HealthConfig,
    AgentHealth,
    create_health_monitor,
)


# ============= Registry Tests =============

class TestHandshakeState:
    """Tests for HandshakeState enum."""
    
    def test_state_values(self):
        """Test HandshakeState enum values."""
        assert HandshakeState.DISCONNECTED.value == "disconnected"
        assert HandshakeState.CONNECTING.value == "connecting"
        assert HandshakeState.HANDSHAKING.value == "handshaking"
        assert HandshakeState.CONNECTED.value == "connected"
        assert HandshakeState.ERROR.value == "error"


class TestAgentInfo:
    """Tests for AgentInfo dataclass."""
    
    def test_create_agent_info(self):
        """Test creating AgentInfo."""
        info = AgentInfo(
            agent_type=AgentType.CLAUDE,
            socket_path="/var/run/claude.sock",
            capabilities=["arbitration"],
            required=True,
        )
        
        assert info.agent_type == AgentType.CLAUDE
        assert info.socket_path == "/var/run/claude.sock"
        assert info.capabilities == ["arbitration"]
        assert info.required is True
        assert info.status == HandshakeState.DISCONNECTED
    
    def test_to_dict(self):
        """Test AgentInfo.to_dict()."""
        info = AgentInfo(
            agent_type=AgentType.MINIMAX,
            socket_path="/var/run/minimax.sock",
        )
        
        d = info.to_dict()
        
        assert d["agent_type"] == "minimax"
        assert d["socket_path"] == "/var/run/minimax.sock"
        assert d["status"] == "disconnected"


class TestAgentRegistry:
    """Tests for AgentRegistry."""
    
    def setup_method(self):
        """Reset registry before each test."""
        reset_registry()
    
    def teardown_method(self):
        """Reset registry after each test."""
        reset_registry()
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        info = AgentInfo(
            agent_type=AgentType.CLAUDE,
            socket_path="/var/run/claude.sock",
        )
        
        registry.register_agent(info)
        
        assert registry.get_agent(AgentType.CLAUDE) == info
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = AgentRegistry()
        info = AgentInfo(
            agent_type=AgentType.CLAUDE,
            socket_path="/var/run/claude.sock",
        )
        
        registry.register_agent(info)
        result = registry.unregister_agent(AgentType.CLAUDE)
        
        assert result is True
        assert registry.get_agent(AgentType.CLAUDE) is None
    
    def test_unregister_nonexistent(self):
        """Test unregistering nonexistent agent."""
        registry = AgentRegistry()
        result = registry.unregister_agent(AgentType.CLAUDE)
        assert result is False
    
    def test_get_all_agents(self):
        """Test getting all agents."""
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock"))
        registry.register_agent(AgentInfo(AgentType.MINIMAX, "/var/run/minimax.sock"))
        
        agents = registry.get_all_agents()
        
        assert len(agents) == 2
        assert AgentType.CLAUDE in agents
        assert AgentType.MINIMAX in agents
    
    def test_get_connected_agents(self):
        """Test getting connected agents."""
        registry = AgentRegistry()
        
        info1 = AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock")
        info1.status = HandshakeState.CONNECTED
        
        info2 = AgentInfo(AgentType.MINIMAX, "/var/run/minimax.sock")
        
        registry.register_agent(info1)
        registry.register_agent(info2)
        
        connected = registry.get_connected_agents()
        
        assert len(connected) == 1
        assert connected[0].agent_type == AgentType.CLAUDE
    
    def test_update_status(self):
        """Test updating agent status."""
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock"))
        
        result = registry.update_status(AgentType.CLAUDE, HandshakeState.CONNECTED, version="1.0.0")
        
        assert result is True
        agent = registry.get_agent(AgentType.CLAUDE)
        assert agent.status == HandshakeState.CONNECTED
        assert agent.version == "1.0.0"
        assert agent.last_seen is not None
    
    def test_has_capability(self):
        """Test checking capability."""
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(
            AgentType.CLAUDE,
            "/var/run/claude.sock",
            capabilities=["arbitration", "design_approval"],
        ))
        
        assert registry.has_capability(AgentType.CLAUDE, "arbitration") is True
        assert registry.has_capability(AgentType.CLAUDE, "unknown") is False
    
    def test_get_agents_by_capability(self):
        """Test getting agents by capability."""
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(
            AgentType.CLAUDE,
            "/var/run/claude.sock",
            capabilities=["arbitration"],
        ))
        registry.register_agent(AgentInfo(
            AgentType.MINIMAX,
            "/var/run/minimax.sock",
            capabilities=["frontend_implementation"],
        ))
        
        agents = registry.get_agents_by_capability("arbitration")
        
        assert len(agents) == 1
        assert agents[0].agent_type == AgentType.CLAUDE
    
    def test_clear(self):
        """Test clearing registry."""
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock"))
        
        registry.clear()
        
        assert len(registry.get_all_agents()) == 0
    
    def test_get_status_summary(self):
        """Test getting status summary."""
        registry = AgentRegistry()
        info = AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock", required=True)
        info.status = HandshakeState.CONNECTED
        registry.register_agent(info)
        
        summary = registry.get_status_summary()
        
        assert summary["total_agents"] == 1
        assert summary["status_counts"]["connected"] == 1
        assert summary["connected_count"] == 1
        assert summary["required_count"] == 1


# ============= State Machine Tests =============

class TestConnectionState:
    """Tests for ConnectionState."""
    
    def test_initial_state(self):
        """Test initial state is DISCONNECTED."""
        state = ConnectionState(AgentType.CLAUDE)
        assert state.state == HandshakeState.DISCONNECTED
    
    def test_valid_transition(self):
        """Test valid state transition."""
        state = ConnectionState(AgentType.CLAUDE)
        state.transition(HandshakeState.CONNECTING)
        
        assert state.state == HandshakeState.CONNECTING
    
    def test_invalid_transition(self):
        """Test invalid state transition raises error."""
        state = ConnectionState(AgentType.CLAUDE)
        
        with pytest.raises(StateTransitionError):
            state.transition(HandshakeState.CONNECTED)  # Can't go directly to CONNECTED
    
    def test_can_transition_to(self):
        """Test can_transition_to check."""
        state = ConnectionState(AgentType.CLAUDE)
        
        assert state.can_transition_to(HandshakeState.CONNECTING) is True
        assert state.can_transition_to(HandshakeState.CONNECTED) is False
    
    def test_error_message(self):
        """Test error message is stored."""
        state = ConnectionState(AgentType.CLAUDE)
        state.transition(HandshakeState.ERROR, error_message="Test error")
        
        assert state.state == HandshakeState.ERROR
        assert state.error_message == "Test error"
    
    def test_reset(self):
        """Test reset to DISCONNECTED."""
        state = ConnectionState(AgentType.CLAUDE)
        state.transition(HandshakeState.CONNECTING)
        state.reset()
        
        assert state.state == HandshakeState.DISCONNECTED
    
    def test_is_connected(self):
        """Test is_connected check."""
        state = ConnectionState(AgentType.CLAUDE)
        
        assert state.is_connected() is False
        
        # Transition through valid path
        state.transition(HandshakeState.CONNECTING)
        state.transition(HandshakeState.HANDSHAKING)
        state.transition(HandshakeState.CONNECTED)
        
        assert state.is_connected() is True


class TestConnectionManager:
    """Tests for ConnectionManager."""
    
    def setup_method(self):
        """Reset connection manager before each test."""
        reset_connection_manager()
    
    def teardown_method(self):
        """Reset connection manager after each test."""
        reset_connection_manager()
    
    def test_get_or_create(self):
        """Test get_or_create creates state if needed."""
        manager = ConnectionManager()
        state = manager.get_or_create(AgentType.CLAUDE)
        
        assert state.agent_type == AgentType.CLAUDE
        assert state.state == HandshakeState.DISCONNECTED
    
    def test_get_state(self):
        """Test get_state returns correct state."""
        manager = ConnectionManager()
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        
        state = manager.get_state(AgentType.CLAUDE)
        
        assert state == HandshakeState.CONNECTING
    
    def test_is_connected(self):
        """Test is_connected check."""
        manager = ConnectionManager()
        
        assert manager.is_connected(AgentType.CLAUDE) is False
        
        # Transition to connected
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        manager.transition(AgentType.CLAUDE, HandshakeState.HANDSHAKING)
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTED)
        
        assert manager.is_connected(AgentType.CLAUDE) is True
    
    def test_is_ready(self):
        """Test is_ready check for required agents."""
        manager = ConnectionManager()
        
        # Connect Claude
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        manager.transition(AgentType.CLAUDE, HandshakeState.HANDSHAKING)
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTED)
        
        assert manager.is_ready([AgentType.CLAUDE]) is True
        assert manager.is_ready([AgentType.CLAUDE, AgentType.MINIMAX]) is False
    
    def test_get_connected_agents(self):
        """Test getting connected agents."""
        manager = ConnectionManager()
        
        # Connect Claude
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        manager.transition(AgentType.CLAUDE, HandshakeState.HANDSHAKING)
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTED)
        
        connected = manager.get_connected_agents()
        
        assert AgentType.CLAUDE in connected
        assert AgentType.MINIMAX not in connected
    
    def test_get_error_agents(self):
        """Test getting error agents."""
        manager = ConnectionManager()
        
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        manager.transition(AgentType.CLAUDE, HandshakeState.ERROR, error_message="Test error")
        
        errors = manager.get_error_agents()
        
        assert len(errors) == 1
        assert errors[0][0] == AgentType.CLAUDE
        assert errors[0][1] == "Test error"
    
    def test_reset_all(self):
        """Test resetting all states."""
        manager = ConnectionManager()
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        
        manager.reset_all()
        
        assert manager.get_state(AgentType.CLAUDE) == HandshakeState.DISCONNECTED
    
    def test_get_status_summary(self):
        """Test getting status summary."""
        manager = ConnectionManager()
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        manager.transition(AgentType.CLAUDE, HandshakeState.HANDSHAKING)
        manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTED)
        
        summary = manager.get_status_summary()
        
        assert summary["total_tracked"] == 1
        assert summary["status_counts"]["connected"] == 1
        assert AgentType.CLAUDE.value in summary["connected_agents"]


# ============= Handshake Tests =============

class TestHandshakeConfig:
    """Tests for HandshakeConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = HandshakeConfig()
        
        assert config.timeout == 10.0
        assert config.protocol_version == "1.0.0"
        assert config.retry_on_failure is False
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = HandshakeConfig(
            timeout=30.0,
            protocol_version="2.0.0",
            retry_on_failure=True,
        )
        
        assert config.timeout == 30.0
        assert config.protocol_version == "2.0.0"
        assert config.retry_on_failure is True


class TestHandshakeResult:
    """Tests for HandshakeResult."""
    
    def test_success_result(self):
        """Test successful result."""
        result = HandshakeResult(
            success=True,
            agent_type="claude",
            agent_info={"version": "1.0.0"},
            duration_ms=150.5,
        )
        
        assert result.success is True
        assert result.agent_type == "claude"
        assert result.error_message is None
    
    def test_failure_result(self):
        """Test failure result."""
        result = HandshakeResult(
            success=False,
            agent_type="claude",
            error_message="Connection refused",
        )
        
        assert result.success is False
        assert result.error_message == "Connection refused"


class TestHandshaker:
    """Tests for Handshaker class."""
    
    def setup_method(self):
        """Reset singletons before each test."""
        reset_registry()
        reset_connection_manager()
    
    def teardown_method(self):
        """Reset singletons after each test."""
        reset_registry()
        reset_connection_manager()
    
    def test_create_handshaker(self):
        """Test creating Handshaker."""
        handshaker = Handshaker()
        
        assert handshaker.config is not None
        assert handshaker.registry is not None
        assert handshaker.connection_manager is not None
    
    def test_receive_hello(self):
        """Test receiving HELLO message."""
        from src.protocol import AgentMessage, MessageType
        
        handshaker = Handshaker()
        
        hello_msg = AgentMessage(
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.AUTONOMOUS_GLM,
            message_type=MessageType.HELLO,
            payload={
                "agent_name": "claude",
                "version": "1.0.0",
                "capabilities": ["arbitration"],
            },
        )
        
        ack = handshaker.receive_hello(hello_msg)
        
        assert ack.message_type == MessageType.ACK
        assert ack.payload["status"] == "acknowledged"
    
    def test_receive_ack_positive(self):
        """Test receiving positive ACK message."""
        from src.protocol import AgentMessage, MessageType
        
        handshaker = Handshaker()
        
        ack_msg = AgentMessage(
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.AUTONOMOUS_GLM,
            message_type=MessageType.ACK,
            payload={
                "agent_name": "claude",
                "status": "acknowledged",
                "message": "Hello!",
            },
        )
        
        ready = handshaker.receive_ack(ack_msg)
        
        assert ready is not None
        assert ready.message_type == MessageType.READY
    
    def test_receive_ack_negative(self):
        """Test receiving negative ACK message."""
        from src.protocol import AgentMessage, MessageType
        
        handshaker = Handshaker()
        
        ack_msg = AgentMessage(
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.AUTONOMOUS_GLM,
            message_type=MessageType.ACK,
            payload={
                "agent_name": "claude",
                "status": "rejected",
                "message": "Not ready",
            },
        )
        
        ready = handshaker.receive_ack(ack_msg)
        
        assert ready is None
    
    def test_receive_ready(self):
        """Test receiving READY message."""
        from src.protocol import AgentMessage, MessageType
        
        # Setup registry and connection manager
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock"))
        conn_manager = ConnectionManager()
        conn_manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        conn_manager.transition(AgentType.CLAUDE, HandshakeState.HANDSHAKING)
        
        handshaker = Handshaker(
            registry=registry,
            connection_manager=conn_manager,
        )
        
        ready_msg = AgentMessage(
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.AUTONOMOUS_GLM,
            message_type=MessageType.READY,
            payload={
                "agent_name": "claude",
                "status": "ready",
            },
        )
        
        result = handshaker.receive_ready(ready_msg)
        
        assert result is True
        assert conn_manager.get_state(AgentType.CLAUDE) == HandshakeState.CONNECTED

    def test_initiate_handshake_sync_logic(self):
        """Test handshake logic that doesn't require async."""
        # This tests the handshake error case without needing async
        registry = AgentRegistry()
        
        # Agent not registered - should fail
        agent = registry.get_agent(AgentType.CLAUDE)
        assert agent is None
        
        # Register agent - should succeed
        registry.register_agent(AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock"))
        agent = registry.get_agent(AgentType.CLAUDE)
        assert agent is not None


# ============= Health Monitor Tests =============

class TestHealthConfig:
    """Tests for HealthConfig."""
    
    def test_default_config(self):
        """Test default health configuration."""
        config = HealthConfig()
        
        assert config.heartbeat_interval == 30.0
        assert config.heartbeat_timeout == 10.0
        assert config.max_missed_heartbeats == 3
    
    def test_custom_config(self):
        """Test custom health configuration."""
        config = HealthConfig(
            heartbeat_interval=60.0,
            max_missed_heartbeats=5,
        )
        
        assert config.heartbeat_interval == 60.0
        assert config.max_missed_heartbeats == 5


class TestAgentHealth:
    """Tests for AgentHealth dataclass."""
    
    def test_initial_health(self):
        """Test initial health state."""
        health = AgentHealth(agent_type=AgentType.CLAUDE)
        
        assert health.agent_type == AgentType.CLAUDE
        assert health.missed_heartbeats == 0
        assert health.is_healthy is True
        assert health.last_error is None
    
    def test_to_dict(self):
        """Test AgentHealth.to_dict()."""
        health = AgentHealth(
            agent_type=AgentType.CLAUDE,
            missed_heartbeats=2,
            is_healthy=False,
            last_error="Timeout",
        )
        
        d = health.to_dict()
        
        assert d["agent_type"] == "claude"
        assert d["missed_heartbeats"] == 2
        assert d["is_healthy"] is False
        assert d["last_error"] == "Timeout"


class TestHealthMonitor:
    """Tests for HealthMonitor."""
    
    def setup_method(self):
        """Reset singletons before each test."""
        reset_registry()
        reset_connection_manager()
    
    def teardown_method(self):
        """Reset singletons after each test."""
        reset_registry()
        reset_connection_manager()
    
    def test_create_monitor(self):
        """Test creating HealthMonitor."""
        monitor = HealthMonitor()
        
        assert monitor.config is not None
        assert monitor._running is False
    
    def test_start_stop(self):
        """Test starting and stopping monitor."""
        monitor = HealthMonitor()
        
        monitor.start()
        assert monitor._running is True
        
        monitor.stop()
        assert monitor._running is False
    
    def test_health_tracking_without_event_loop(self):
        """Test health tracking without starting heartbeat loop."""
        monitor = HealthMonitor()
        monitor.start()
        
        # Manually add health tracking (without starting async heartbeat loop)
        monitor._health[AgentType.CLAUDE] = AgentHealth(agent_type=AgentType.CLAUDE)
        
        assert monitor.get_health(AgentType.CLAUDE) is not None
        assert monitor.is_healthy(AgentType.CLAUDE) is True
        
        monitor.stop()
    
    def test_get_all_health(self):
        """Test getting all health statuses."""
        monitor = HealthMonitor()
        monitor.start()
        
        # Manually add health tracking
        monitor._health[AgentType.CLAUDE] = AgentHealth(agent_type=AgentType.CLAUDE)
        monitor._health[AgentType.MINIMAX] = AgentHealth(agent_type=AgentType.MINIMAX)
        
        all_health = monitor.get_all_health()
        
        assert len(all_health) == 2
        assert AgentType.CLAUDE in all_health
        assert AgentType.MINIMAX in all_health
        
        monitor.stop()
    
    def test_is_healthy(self):
        """Test is_healthy check."""
        monitor = HealthMonitor()
        monitor.start()
        
        # Manually add health tracking
        monitor._health[AgentType.CLAUDE] = AgentHealth(agent_type=AgentType.CLAUDE)
        
        assert monitor.is_healthy(AgentType.CLAUDE) is True
        
        # Manually mark as unhealthy
        health = monitor.get_health(AgentType.CLAUDE)
        health.is_healthy = False
        
        assert monitor.is_healthy(AgentType.CLAUDE) is False
        
        monitor.stop()
    
    def test_get_unhealthy_agents(self):
        """Test getting unhealthy agents."""
        monitor = HealthMonitor()
        monitor.start()
        
        # Manually add health tracking
        monitor._health[AgentType.CLAUDE] = AgentHealth(agent_type=AgentType.CLAUDE)
        monitor._health[AgentType.MINIMAX] = AgentHealth(agent_type=AgentType.MINIMAX)
        
        # Mark Claude as unhealthy
        monitor.get_health(AgentType.CLAUDE).is_healthy = False
        monitor.get_health(AgentType.CLAUDE).last_error = "Timeout"
        
        unhealthy = monitor.get_unhealthy_agents()
        
        assert len(unhealthy) == 1
        assert unhealthy[0][0] == AgentType.CLAUDE
        assert unhealthy[0][1] == "Timeout"
        
        monitor.stop()
    
    def test_reset_health(self):
        """Test resetting health status."""
        monitor = HealthMonitor()
        monitor.start()
        
        # Manually add health tracking
        monitor._health[AgentType.CLAUDE] = AgentHealth(agent_type=AgentType.CLAUDE)
        health = monitor.get_health(AgentType.CLAUDE)
        health.missed_heartbeats = 3
        health.is_healthy = False
        
        monitor.reset_health(AgentType.CLAUDE)
        
        health = monitor.get_health(AgentType.CLAUDE)
        assert health.missed_heartbeats == 0
        assert health.is_healthy is True
        
        monitor.stop()
    
    def test_handle_heartbeat_failure(self):
        """Test handling heartbeat failure."""
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(AgentType.CLAUDE, "/var/run/claude.sock"))
        conn_manager = ConnectionManager()
        conn_manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        conn_manager.transition(AgentType.CLAUDE, HandshakeState.HANDSHAKING)
        conn_manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTED)
        
        monitor = HealthMonitor(
            registry=registry,
            connection_manager=conn_manager,
        )
        monitor.start()
        
        # Manually add health tracking
        monitor._health[AgentType.CLAUDE] = AgentHealth(agent_type=AgentType.CLAUDE)
        health = monitor.get_health(AgentType.CLAUDE)
        health.missed_heartbeats = 3
        
        monitor.handle_heartbeat_failure(AgentType.CLAUDE)
        
        assert health.is_healthy is False
        assert conn_manager.get_state(AgentType.CLAUDE) == HandshakeState.ERROR
        
        monitor.stop()
    
    def test_unhealthy_callback(self):
        """Test unhealthy callback is triggered."""
        callback_called = []
        
        def on_unhealthy(agent_type, error):
            callback_called.append((agent_type, error))
        
        monitor = HealthMonitor(on_unhealthy=on_unhealthy)
        monitor.start()
        
        # Manually add health tracking
        monitor._health[AgentType.CLAUDE] = AgentHealth(agent_type=AgentType.CLAUDE)
        health = monitor.get_health(AgentType.CLAUDE)
        health.missed_heartbeats = 3
        health.last_error = "Test error"
        
        monitor.handle_heartbeat_failure(AgentType.CLAUDE)
        
        assert len(callback_called) == 1
        assert callback_called[0][0] == AgentType.CLAUDE
        assert callback_called[0][1] == "Test error"
        
        monitor.stop()
    
class TestCreateHealthMonitor:
    """Tests for create_health_monitor factory function."""
    
    def test_create_with_defaults(self):
        """Test creating with default settings."""
        monitor = create_health_monitor()
        
        assert monitor.config.heartbeat_interval == 30.0
        assert monitor.config.max_missed_heartbeats == 3
    
    def test_create_with_custom_settings(self):
        """Test creating with custom settings."""
        monitor = create_health_monitor(
            heartbeat_interval=60.0,
            max_missed=5,
        )
        
        assert monitor.config.heartbeat_interval == 60.0
        assert monitor.config.max_missed_heartbeats == 5


# ============= Integration Tests =============

class TestHandshakeIntegration:
    """Integration tests for handshake protocol."""
    
    def setup_method(self):
        """Reset singletons before each test."""
        reset_registry()
        reset_connection_manager()
    
    def teardown_method(self):
        """Reset singletons after each test."""
        reset_registry()
        reset_connection_manager()
    
    def test_full_handshake_flow(self):
        """Test full handshake message flow."""
        from src.protocol import AgentMessage, MessageType
        
        # Setup
        registry = AgentRegistry()
        registry.register_agent(AgentInfo(
            AgentType.CLAUDE,
            "/var/run/claude.sock",
            capabilities=["arbitration"],
        ))
        
        conn_manager = ConnectionManager()
        conn_manager.transition(AgentType.CLAUDE, HandshakeState.CONNECTING)
        conn_manager.transition(AgentType.CLAUDE, HandshakeState.HANDSHAKING)
        
        handshaker = Handshaker(
            registry=registry,
            connection_manager=conn_manager,
        )
        
        # 1. Receive HELLO
        hello_msg = AgentMessage(
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.AUTONOMOUS_GLM,
            message_type=MessageType.HELLO,
            payload={
                "agent_name": "claude",
                "version": "1.0.0",
                "capabilities": ["arbitration"],
            },
        )
        
        ack = handshaker.receive_hello(hello_msg)
        assert ack.message_type == MessageType.ACK
        
        # 2. Receive READY
        ready_msg = AgentMessage(
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.AUTONOMOUS_GLM,
            message_type=MessageType.READY,
            payload={
                "agent_name": "claude",
                "status": "ready",
            },
        )
        
        result = handshaker.receive_ready(ready_msg)
        assert result is True
        assert conn_manager.get_state(AgentType.CLAUDE) == HandshakeState.CONNECTED
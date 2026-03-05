"""
Connection state machine for agent handshakes.

Manages connection states and transitions for agent communication.
"""

import logging
from typing import Optional

from src.protocol.message import AgentType
from src.protocol.registry import HandshakeState

logger = logging.getLogger(__name__)


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


# Valid state transitions
VALID_TRANSITIONS: dict[HandshakeState, set[HandshakeState]] = {
    HandshakeState.DISCONNECTED: {
        HandshakeState.CONNECTING,
        HandshakeState.ERROR,
    },
    HandshakeState.CONNECTING: {
        HandshakeState.HANDSHAKING,
        HandshakeState.DISCONNECTED,
        HandshakeState.ERROR,
    },
    HandshakeState.HANDSHAKING: {
        HandshakeState.CONNECTED,
        HandshakeState.DISCONNECTED,
        HandshakeState.ERROR,
    },
    HandshakeState.CONNECTED: {
        HandshakeState.DISCONNECTED,
        HandshakeState.ERROR,
    },
    HandshakeState.ERROR: {
        HandshakeState.DISCONNECTED,
        HandshakeState.CONNECTING,
    },
}


class ConnectionState:
    """
    State machine for a single agent connection.
    
    Tracks the current state and validates transitions.
    """
    
    def __init__(self, agent_type: AgentType):
        """
        Initialize connection state for an agent.
        
        Args:
            agent_type: The agent this state tracks
        """
        self.agent_type = agent_type
        self._state = HandshakeState.DISCONNECTED
        self._error_message: Optional[str] = None
        self._transition_count = 0
    
    @property
    def state(self) -> HandshakeState:
        """Get current state."""
        return self._state
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if in ERROR state."""
        return self._error_message
    
    def can_transition_to(self, new_state: HandshakeState) -> bool:
        """
        Check if transition to new state is valid.
        
        Args:
            new_state: Target state to check
            
        Returns:
            True if transition is valid, False otherwise
        """
        return new_state in VALID_TRANSITIONS.get(self._state, set())
    
    def transition(self, new_state: HandshakeState, error_message: Optional[str] = None) -> bool:
        """
        Transition to a new state.
        
        Args:
            new_state: Target state to transition to
            error_message: Optional error message for ERROR state
            
        Returns:
            True if transition succeeded
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        if not self.can_transition_to(new_state):
            raise StateTransitionError(
                f"Invalid transition from {self._state.value} to {new_state.value} "
                f"for agent {self.agent_type.value}"
            )
        
        old_state = self._state
        self._state = new_state
        self._transition_count += 1
        
        if new_state == HandshakeState.ERROR:
            self._error_message = error_message
        else:
            self._error_message = None
        
        logger.debug(
            f"State transition: {self.agent_type.value} {old_state.value} -> {new_state.value}"
        )
        return True
    
    def reset(self) -> None:
        """Reset state to DISCONNECTED."""
        self._state = HandshakeState.DISCONNECTED
        self._error_message = None
    
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._state == HandshakeState.CONNECTED
    
    def is_error(self) -> bool:
        """Check if currently in error state."""
        return self._state == HandshakeState.ERROR
    
    def __repr__(self) -> str:
        return f"ConnectionState({self.agent_type.value}, {self._state.value})"


class ConnectionManager:
    """
    Manages connection states for all agents.
    
    Provides a unified interface for checking and updating
    connection states across all registered agents.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self._states: dict[AgentType, ConnectionState] = {}
    
    def get_or_create(self, agent_type: AgentType) -> ConnectionState:
        """
        Get or create connection state for an agent.
        
        Args:
            agent_type: Agent to get state for
            
        Returns:
            ConnectionState for the agent
        """
        if agent_type not in self._states:
            self._states[agent_type] = ConnectionState(agent_type)
        return self._states[agent_type]
    
    def get_state(self, agent_type: AgentType) -> HandshakeState:
        """
        Get the current state for an agent.
        
        Args:
            agent_type: Agent to check
            
        Returns:
            Current HandshakeState (DISCONNECTED if not tracked)
        """
        state = self._states.get(agent_type)
        return state.state if state else HandshakeState.DISCONNECTED
    
    def transition(
        self,
        agent_type: AgentType,
        new_state: HandshakeState,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Transition an agent to a new state.
        
        Args:
            agent_type: Agent to transition
            new_state: Target state
            error_message: Optional error message
            
        Returns:
            True if transition succeeded
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        state = self.get_or_create(agent_type)
        return state.transition(new_state, error_message)
    
    def is_connected(self, agent_type: AgentType) -> bool:
        """
        Check if an agent is connected.
        
        Args:
            agent_type: Agent to check
            
        Returns:
            True if connected, False otherwise
        """
        return self.get_state(agent_type) == HandshakeState.CONNECTED
    
    def is_ready(self, required_agents: Optional[list[AgentType]] = None) -> bool:
        """
        Check if all required agents are connected.
        
        Args:
            required_agents: List of required agents (if None, checks all tracked)
            
        Returns:
            True if all required agents are connected
        """
        if required_agents is None:
            # Check all tracked agents
            return all(
                state.is_connected()
                for state in self._states.values()
            )
        
        return all(
            self.is_connected(agent)
            for agent in required_agents
        )
    
    def get_connected_agents(self) -> list[AgentType]:
        """
        Get list of all connected agents.
        
        Returns:
            List of connected agent types
        """
        return [
            agent_type for agent_type, state in self._states.items()
            if state.is_connected()
        ]
    
    def get_error_agents(self) -> list[tuple[AgentType, Optional[str]]]:
        """
        Get list of agents in error state with their error messages.
        
        Returns:
            List of (agent_type, error_message) tuples
        """
        return [
            (agent_type, state.error_message)
            for agent_type, state in self._states.items()
            if state.is_error()
        ]
    
    def reset(self, agent_type: AgentType) -> None:
        """
        Reset an agent's state to DISCONNECTED.
        
        Args:
            agent_type: Agent to reset
        """
        state = self._states.get(agent_type)
        if state:
            state.reset()
    
    def reset_all(self) -> None:
        """Reset all agent states to DISCONNECTED."""
        for state in self._states.values():
            state.reset()
    
    def clear(self) -> None:
        """Clear all tracked states."""
        self._states.clear()
    
    def get_status_summary(self) -> dict:
        """
        Get a summary of all connection states.
        
        Returns:
            Dictionary with state counts and details
        """
        status_counts = {}
        for status in HandshakeState:
            status_counts[status.value] = sum(
                1 for state in self._states.values()
                if state.state == status
            )
        
        return {
            "total_tracked": len(self._states),
            "status_counts": status_counts,
            "connected_agents": [a.value for a in self.get_connected_agents()],
            "error_agents": [
                {"agent": a.value, "error": err}
                for a, err in self.get_error_agents()
            ],
        }


# Module-level manager singleton
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.
    
    Returns:
        The global ConnectionManager instance
    """
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


def reset_connection_manager() -> None:
    """Reset the global connection manager (mainly for testing)."""
    global _manager
    _manager = None
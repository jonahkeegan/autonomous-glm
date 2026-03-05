"""
Agent registry for discovery and tracking.

Provides config-based agent discovery and capability tracking for
communication between autonomous-glm and other agents.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.config.loader import get_config
from src.protocol.message import AgentType

logger = logging.getLogger(__name__)


class HandshakeState(str, Enum):
    """Connection states for agent handshakes."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    agent_type: AgentType
    socket_path: str
    capabilities: list[str] = field(default_factory=list)
    required: bool = False
    status: HandshakeState = HandshakeState.DISCONNECTED
    last_seen: Optional[datetime] = None
    version: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "agent_type": self.agent_type.value,
            "socket_path": self.socket_path,
            "capabilities": self.capabilities,
            "required": self.required,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "version": self.version,
        }


class HandshakeAgentConfig(BaseModel):
    """Configuration for a single agent in the handshake protocol."""
    type: str = Field(..., description="Agent type identifier")
    socket_path: str = Field(..., description="Path to Unix domain socket")
    capabilities: list[str] = Field(default_factory=list, description="Agent capabilities")
    required: bool = Field(default=False, description="Whether connection is required")


class AgentRegistry:
    """
    Central registry of known agents.
    
    Manages agent discovery, registration, and capability tracking.
    Loads agent definitions from configuration.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self._agents: dict[AgentType, AgentInfo] = {}
        self._initialized = False
    
    def register_agent(self, agent_info: AgentInfo) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent_info: Information about the agent to register
        """
        self._agents[agent_info.agent_type] = agent_info
        logger.info(f"Registered agent: {agent_info.agent_type.value}")
    
    def unregister_agent(self, agent_type: AgentType) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_type: Type of agent to unregister
            
        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_type in self._agents:
            del self._agents[agent_type]
            logger.info(f"Unregistered agent: {agent_type.value}")
            return True
        return False
    
    def get_agent(self, agent_type: AgentType) -> Optional[AgentInfo]:
        """
        Get information about a specific agent.
        
        Args:
            agent_type: Type of agent to look up
            
        Returns:
            AgentInfo if found, None otherwise
        """
        return self._agents.get(agent_type)
    
    def get_all_agents(self) -> list[AgentType]:
        """
        Get all registered agent types.
        
        Returns:
            List of registered agent types
        """
        return list(self._agents.keys())
    
    def get_connected_agents(self) -> list[AgentInfo]:
        """
        Get all agents currently in CONNECTED state.
        
        Returns:
            List of connected agent info
        """
        return [
            info for info in self._agents.values()
            if info.status == HandshakeState.CONNECTED
        ]
    
    def get_required_agents(self) -> list[AgentInfo]:
        """
        Get all agents marked as required.
        
        Returns:
            List of required agent info
        """
        return [
            info for info in self._agents.values()
            if info.required
        ]
    
    def update_status(
        self,
        agent_type: AgentType,
        status: HandshakeState,
        version: Optional[str] = None,
    ) -> bool:
        """
        Update the status of an agent.
        
        Args:
            agent_type: Type of agent to update
            status: New status value
            version: Optional version string from handshake
            
        Returns:
            True if updated, False if agent not found
        """
        agent = self._agents.get(agent_type)
        if agent:
            agent.status = status
            agent.last_seen = datetime.utcnow()
            if version:
                agent.version = version
            logger.debug(f"Updated {agent_type.value} status to {status.value}")
            return True
        return False
    
    def has_capability(self, agent_type: AgentType, capability: str) -> bool:
        """
        Check if an agent has a specific capability.
        
        Args:
            agent_type: Type of agent to check
            capability: Capability to look for
            
        Returns:
            True if agent has capability, False otherwise
        """
        agent = self._agents.get(agent_type)
        if agent:
            return capability in agent.capabilities
        return False
    
    def get_agents_by_capability(self, capability: str) -> list[AgentInfo]:
        """
        Get all agents with a specific capability.
        
        Args:
            capability: Capability to filter by
            
        Returns:
            List of agents with the capability
        """
        return [
            info for info in self._agents.values()
            if capability in info.capabilities
        ]
    
    def load_from_config(self) -> int:
        """
        Load agent definitions from configuration.
        
        Reads the handshake.agents section from config and registers
        each defined agent.
        
        Returns:
            Number of agents loaded
        """
        try:
            config = get_config()
            
            # Get handshake config if it exists
            handshake_config = getattr(config, 'handshake', None)
            if not handshake_config:
                logger.warning("No handshake configuration found")
                return 0
            
            agents_config = getattr(handshake_config, 'agents', [])
            if not agents_config:
                logger.warning("No agents defined in handshake configuration")
                return 0
            
            loaded = 0
            for agent_cfg in agents_config:
                try:
                    # Parse agent type from string
                    agent_type_str = agent_cfg.get('type', '')
                    try:
                        agent_type = AgentType(agent_type_str)
                    except ValueError:
                        logger.warning(f"Unknown agent type: {agent_type_str}")
                        continue
                    
                    agent_info = AgentInfo(
                        agent_type=agent_type,
                        socket_path=agent_cfg.get('socket_path', ''),
                        capabilities=agent_cfg.get('capabilities', []),
                        required=agent_cfg.get('required', False),
                    )
                    
                    self.register_agent(agent_info)
                    loaded += 1
                    
                except Exception as e:
                    logger.error(f"Failed to load agent config: {e}")
            
            self._initialized = True
            logger.info(f"Loaded {loaded} agents from configuration")
            return loaded
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return 0
    
    def is_initialized(self) -> bool:
        """Check if registry has been initialized from config."""
        return self._initialized
    
    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        self._initialized = False
        logger.info("Cleared agent registry")
    
    def get_status_summary(self) -> dict:
        """
        Get a summary of registry status.
        
        Returns:
            Dictionary with status counts and details
        """
        status_counts = {}
        for status in HandshakeState:
            status_counts[status.value] = sum(
                1 for info in self._agents.values()
                if info.status == status
            )
        
        return {
            "total_agents": len(self._agents),
            "status_counts": status_counts,
            "connected_count": len(self.get_connected_agents()),
            "required_count": len(self.get_required_agents()),
            "initialized": self._initialized,
        }


# Module-level registry singleton
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.
    
    Creates and initializes the registry on first call.
    
    Returns:
        The global AgentRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _registry
    if _registry:
        _registry.clear()
    _registry = None
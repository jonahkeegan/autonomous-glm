"""
Health monitor for agent connections.

Provides heartbeat/ping functionality for monitoring connection health
and detecting stale connections.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

from src.protocol.message import AgentType, MessageType, create_hello_message
from src.protocol.registry import AgentRegistry, HandshakeState, get_registry
from src.protocol.state import ConnectionManager, get_connection_manager
from src.protocol.transport import (
    SocketConfig,
    UnixSocketClient,
    TransportError,
)

logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_HEARTBEAT_INTERVAL = 30.0  # seconds
DEFAULT_HEARTBEAT_TIMEOUT = 10.0  # seconds
DEFAULT_MAX_MISSED_HEARTBEATS = 3


@dataclass
class HealthConfig:
    """Configuration for health monitoring."""
    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL
    heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT
    max_missed_heartbeats: int = DEFAULT_MAX_MISSED_HEARTBEATS


@dataclass
class AgentHealth:
    """Health status for a single agent."""
    agent_type: AgentType
    last_heartbeat: Optional[datetime] = None
    missed_heartbeats: int = 0
    is_healthy: bool = True
    last_error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "agent_type": self.agent_type.value,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "missed_heartbeats": self.missed_heartbeats,
            "is_healthy": self.is_healthy,
            "last_error": self.last_error,
        }


class HealthMonitor:
    """
    Monitors agent connection health via periodic heartbeats.
    
    Sends ping messages at configured intervals and tracks
    missed heartbeats to detect unhealthy connections.
    """
    
    def __init__(
        self,
        config: Optional[HealthConfig] = None,
        socket_config: Optional[SocketConfig] = None,
        registry: Optional[AgentRegistry] = None,
        connection_manager: Optional[ConnectionManager] = None,
        on_unhealthy: Optional[Callable[[AgentType, str], None]] = None,
    ):
        """
        Initialize the health monitor.
        
        Args:
            config: Health monitoring configuration
            socket_config: Socket transport configuration
            registry: Agent registry
            connection_manager: Connection manager
            on_unhealthy: Callback when agent becomes unhealthy
        """
        self.config = config or HealthConfig()
        self.socket_config = socket_config or SocketConfig()
        self.registry = registry or get_registry()
        self.connection_manager = connection_manager or get_connection_manager()
        self.on_unhealthy = on_unhealthy
        
        self._health: dict[AgentType, AgentHealth] = {}
        self._heartbeat_tasks: dict[AgentType, asyncio.Task] = {}
        self._client = UnixSocketClient(self.socket_config)
        self._running = False
    
    def start(self) -> None:
        """Start the health monitor."""
        self._running = True
        logger.info("Health monitor started")
    
    def stop(self) -> None:
        """Stop the health monitor and all heartbeat tasks."""
        self._running = False
        
        # Cancel all heartbeat tasks
        for task in self._heartbeat_tasks.values():
            task.cancel()
        self._heartbeat_tasks.clear()
        
        logger.info("Health monitor stopped")
    
    def start_heartbeat(self, agent_type: AgentType) -> None:
        """
        Start heartbeat monitoring for an agent.
        
        Args:
            agent_type: Agent to monitor
        """
        if agent_type in self._heartbeat_tasks:
            logger.warning(f"Heartbeat already running for {agent_type.value}")
            return
        
        # Initialize health status
        self._health[agent_type] = AgentHealth(agent_type=agent_type)
        
        # Create heartbeat task
        task = asyncio.create_task(self._heartbeat_loop(agent_type))
        self._heartbeat_tasks[agent_type] = task
        
        logger.info(f"Started heartbeat for {agent_type.value}")
    
    def stop_heartbeat(self, agent_type: AgentType) -> None:
        """
        Stop heartbeat monitoring for an agent.
        
        Args:
            agent_type: Agent to stop monitoring
        """
        task = self._heartbeat_tasks.pop(agent_type, None)
        if task:
            task.cancel()
            logger.info(f"Stopped heartbeat for {agent_type.value}")
        
        # Remove health status
        self._health.pop(agent_type, None)
    
    def stop_all_heartbeats(self) -> None:
        """Stop all heartbeat monitoring."""
        for agent_type in list(self._heartbeat_tasks.keys()):
            self.stop_heartbeat(agent_type)
    
    async def check_agent_health(self, agent_type: AgentType) -> bool:
        """
        Check if an agent is healthy.
        
        Sends a ping and waits for response.
        
        Args:
            agent_type: Agent to check
            
        Returns:
            True if agent is healthy, False otherwise
        """
        health = self._health.get(agent_type)
        if not health:
            health = AgentHealth(agent_type=agent_type)
            self._health[agent_type] = health
        
        try:
            # Send a simple ping message (reuse HELLO type for health check)
            ping_msg = create_hello_message(
                target_agent=agent_type,
                agent_name=AgentType.AUTONOMOUS_GLM.value,
                version="health-check",
                capabilities=[],
            )
            
            # Wait for response with timeout
            ack = await asyncio.wait_for(
                self._client.send_message(agent_type, ping_msg),
                timeout=self.config.heartbeat_timeout,
            )
            
            if ack and ack.status == "acknowledged":
                health.last_heartbeat = datetime.utcnow()
                health.missed_heartbeats = 0
                health.is_healthy = True
                health.last_error = None
                return True
            else:
                health.missed_heartbeats += 1
                health.last_error = f"Bad ACK status: {ack.status if ack else 'no response'}"
                return False
                
        except asyncio.TimeoutError:
            health.missed_heartbeats += 1
            health.last_error = "Heartbeat timeout"
            logger.warning(f"Heartbeat timeout for {agent_type.value}")
            return False
            
        except TransportError as e:
            health.missed_heartbeats += 1
            health.last_error = str(e)
            logger.warning(f"Heartbeat transport error for {agent_type.value}: {e}")
            return False
            
        except Exception as e:
            health.missed_heartbeats += 1
            health.last_error = str(e)
            logger.error(f"Heartbeat error for {agent_type.value}: {e}")
            return False
    
    def handle_heartbeat_failure(self, agent_type: AgentType) -> None:
        """
        Handle a heartbeat failure.
        
        Updates health status and triggers callback if agent is unhealthy.
        
        Args:
            agent_type: Agent that failed heartbeat
        """
        health = self._health.get(agent_type)
        if not health:
            return
        
        logger.warning(
            f"Heartbeat failure for {agent_type.value}: "
            f"{health.missed_heartbeats}/{self.config.max_missed_heartbeats} missed"
        )
        
        if health.missed_heartbeats >= self.config.max_missed_heartbeats:
            health.is_healthy = False
            
            # Update connection state
            try:
                self.connection_manager.transition(
                    agent_type,
                    HandshakeState.ERROR,
                    error_message=f"Missed {health.missed_heartbeats} heartbeats",
                )
                self.registry.update_status(agent_type, HandshakeState.ERROR)
            except Exception:
                pass
            
            # Trigger callback
            if self.on_unhealthy:
                try:
                    self.on_unhealthy(agent_type, health.last_error or "Unknown error")
                except Exception as e:
                    logger.error(f"Error in unhealthy callback: {e}")
    
    def get_health(self, agent_type: AgentType) -> Optional[AgentHealth]:
        """
        Get health status for an agent.
        
        Args:
            agent_type: Agent to check
            
        Returns:
            AgentHealth if being monitored, None otherwise
        """
        return self._health.get(agent_type)
    
    def get_all_health(self) -> dict[AgentType, AgentHealth]:
        """
        Get health status for all monitored agents.
        
        Returns:
            Dictionary of agent type to health status
        """
        return dict(self._health)
    
    def is_healthy(self, agent_type: AgentType) -> bool:
        """
        Check if an agent is currently healthy.
        
        Args:
            agent_type: Agent to check
            
        Returns:
            True if healthy, False otherwise
        """
        health = self._health.get(agent_type)
        return health.is_healthy if health else False
    
    def get_unhealthy_agents(self) -> list[tuple[AgentType, str]]:
        """
        Get list of unhealthy agents with their errors.
        
        Returns:
            List of (agent_type, error_message) tuples
        """
        return [
            (agent_type, health.last_error or "Unknown")
            for agent_type, health in self._health.items()
            if not health.is_healthy
        ]
    
    def reset_health(self, agent_type: AgentType) -> None:
        """
        Reset health status for an agent.
        
        Args:
            agent_type: Agent to reset
        """
        if agent_type in self._health:
            self._health[agent_type] = AgentHealth(agent_type=agent_type)
            logger.info(f"Reset health status for {agent_type.value}")
    
    async def _heartbeat_loop(self, agent_type: AgentType) -> None:
        """
        Run heartbeat loop for an agent.
        
        Args:
            agent_type: Agent to monitor
        """
        while self._running:
            try:
                # Check health
                is_healthy = await self.check_agent_health(agent_type)
                
                if not is_healthy:
                    self.handle_heartbeat_failure(agent_type)
                
                # Wait for next interval
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                logger.debug(f"Heartbeat loop cancelled for {agent_type.value}")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop for {agent_type.value}: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
    
    async def close(self) -> None:
        """Close the health monitor and client connections."""
        self.stop()
        await self._client.disconnect_all()


def create_health_monitor(
    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
    max_missed: int = DEFAULT_MAX_MISSED_HEARTBEATS,
    on_unhealthy: Optional[Callable[[AgentType, str], None]] = None,
) -> HealthMonitor:
    """
    Create a health monitor with custom settings.
    
    Args:
        heartbeat_interval: Seconds between heartbeats
        max_missed: Maximum missed heartbeats before unhealthy
        on_unhealthy: Callback for unhealthy agents
        
    Returns:
        Configured HealthMonitor instance
    """
    config = HealthConfig(
        heartbeat_interval=heartbeat_interval,
        max_missed_heartbeats=max_missed,
    )
    return HealthMonitor(config=config, on_unhealthy=on_unhealthy)
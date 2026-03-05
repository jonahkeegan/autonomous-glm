"""
Message router for agent-to-agent communication.

Routes messages to appropriate agents and manages message type handlers.
"""

import logging
from typing import Callable, Optional

from src.protocol.message import AgentMessage, AgentType, MessageAck, MessageType
from src.protocol.transport import (
    SocketConfig,
    UnixSocketClient,
    broadcast as transport_broadcast,
    send_message as transport_send_message,
)

logger = logging.getLogger(__name__)


# Type alias for message handlers
MessageHandler = Callable[[AgentMessage], MessageAck]


class MessageRouter:
    """
    Routes messages to appropriate agents and handles incoming messages.
    
    Manages connection pooling and message type handlers.
    """
    
    def __init__(self, config: Optional[SocketConfig] = None):
        """
        Initialize the message router.
        
        Args:
            config: Socket configuration
        """
        self.config = config or SocketConfig()
        self._client = UnixSocketClient(self.config)
        self._handlers: dict[MessageType, MessageHandler] = {}
        self._default_handler: Optional[MessageHandler] = None
    
    def register_handler(
        self,
        message_type: MessageType,
        handler: MessageHandler,
    ) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: The message type to handle
            handler: Function that processes the message and returns an ack
        """
        self._handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type.value}")
    
    def unregister_handler(self, message_type: MessageType) -> None:
        """
        Unregister a handler for a specific message type.
        
        Args:
            message_type: The message type to stop handling
        """
        if message_type in self._handlers:
            del self._handlers[message_type]
            logger.debug(f"Unregistered handler for {message_type.value}")
    
    def set_default_handler(self, handler: Optional[MessageHandler]) -> None:
        """
        Set a default handler for unregistered message types.
        
        Args:
            handler: Function that processes the message and returns an ack
        """
        self._default_handler = handler
    
    def get_handler(self, message_type: MessageType) -> Optional[MessageHandler]:
        """
        Get the handler for a message type.
        
        Args:
            message_type: The message type
            
        Returns:
            The registered handler or the default handler
        """
        return self._handlers.get(message_type, self._default_handler)
    
    async def route(self, message: AgentMessage) -> MessageAck:
        """
        Route a message to its target agent.
        
        Args:
            message: The message to route
            
        Returns:
            MessageAck from the target agent
            
        Raises:
            TransportError: If message cannot be delivered
        """
        logger.debug(
            f"Routing message {message.message_id} to {message.target_agent.value}"
        )
        return await self._client.send_message(message.target_agent, message)
    
    async def route_and_forget(self, message: AgentMessage) -> None:
        """
        Route a message without waiting for acknowledgment.
        
        Args:
            message: The message to route
        """
        await self._client.send_message(
            message.target_agent, 
            message, 
            wait_for_ack=False
        )
    
    async def broadcast(
        self,
        message: AgentMessage,
        agents: Optional[list[AgentType]] = None,
    ) -> list[tuple[AgentType, Optional[MessageAck], Optional[Exception]]]:
        """
        Broadcast a message to multiple agents.
        
        Args:
            message: The message to broadcast
            agents: List of target agents (defaults to Claude, Minimax, Codex)
            
        Returns:
            List of (agent, ack, error) tuples
        """
        return await transport_broadcast(message, agents, self.config)
    
    def handle_message(self, message: AgentMessage) -> MessageAck:
        """
        Handle an incoming message using registered handlers.
        
        Args:
            message: The incoming message
            
        Returns:
            MessageAck based on handler result
        """
        handler = self.get_handler(message.message_type)
        
        if handler:
            try:
                return handler(message)
            except Exception as e:
                logger.error(
                    f"Handler error for {message.message_type.value}: {e}"
                )
                return MessageAck(
                    message_id=message.message_id,
                    status="error",
                    error_message=str(e),
                )
        else:
            logger.warning(
                f"No handler for message type {message.message_type.value}"
            )
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
    
    async def disconnect_all(self) -> None:
        """Disconnect from all agents."""
        await self._client.disconnect_all()
    
    def get_socket_path(self, agent: AgentType) -> str:
        """
        Get the socket path for an agent.
        
        Args:
            agent: The agent to get the path for
            
        Returns:
            Socket file path
        """
        return self.config.get_socket_path(agent)


# Agent endpoint resolution

def get_agent_socket_path(agent: AgentType, socket_dir: str = "/var/run/autonomous-glm") -> str:
    """
    Get the socket path for a specific agent.
    
    Args:
        agent: The agent type
        socket_dir: Base directory for sockets
        
    Returns:
        Full path to the agent's socket file
    """
    import os
    return os.path.join(socket_dir, f"{agent.value}.sock")


def resolve_agent_endpoint(agent: AgentType, config: Optional[SocketConfig] = None) -> str:
    """
    Resolve the endpoint for an agent.
    
    Args:
        agent: The agent type
        config: Socket configuration
        
    Returns:
        Socket path for the agent
    """
    cfg = config or SocketConfig()
    return cfg.get_socket_path(agent)


# Convenience functions

async def route_message(
    message: AgentMessage,
    config: Optional[SocketConfig] = None,
) -> MessageAck:
    """
    Route a message to its target agent.
    
    Convenience function using a temporary router.
    
    Args:
        message: The message to route
        config: Socket configuration
        
    Returns:
        MessageAck from the target agent
    """
    router = MessageRouter(config)
    try:
        return await router.route(message)
    finally:
        await router.disconnect_all()


async def broadcast_message(
    message: AgentMessage,
    agents: Optional[list[AgentType]] = None,
    config: Optional[SocketConfig] = None,
) -> list[tuple[AgentType, Optional[MessageAck], Optional[Exception]]]:
    """
    Broadcast a message to multiple agents.
    
    Convenience function using module-level broadcast.
    
    Args:
        message: The message to broadcast
        agents: List of target agents
        config: Socket configuration
        
    Returns:
        List of (agent, ack, error) tuples
    """
    return await transport_broadcast(message, agents, config)
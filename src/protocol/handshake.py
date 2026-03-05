"""
Handshake protocol for agent connections.

Implements the HELLO → ACK → READY handshake sequence for
establishing connections between agents.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.protocol.message import (
    AgentMessage,
    AgentType,
    HelloPayload,
    AckPayload,
    ReadyPayload,
    MessageType,
    create_hello_message,
)
from src.protocol.registry import (
    AgentInfo,
    AgentRegistry,
    HandshakeState,
    get_registry,
)
from src.protocol.state import (
    ConnectionManager,
    StateTransitionError,
    get_connection_manager,
)
from src.protocol.transport import (
    SocketConfig,
    UnixSocketClient,
    ConnectionError as TransportConnectionError,
    TransportError,
)

logger = logging.getLogger(__name__)


# Default handshake configuration
DEFAULT_HANDSHAKE_TIMEOUT = 10.0  # seconds
DEFAULT_PROTOCOL_VERSION = "1.0.0"


class HandshakeResult(BaseModel):
    """Result of a handshake attempt."""
    success: bool = Field(..., description="Whether handshake succeeded")
    agent_type: str = Field(..., description="Agent type that was targeted")
    agent_info: Optional[dict] = Field(default=None, description="Peer agent info if successful")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    duration_ms: Optional[float] = Field(default=None, description="Handshake duration in milliseconds")
    
    class Config:
        arbitrary_types_allowed = True


@dataclass
class HandshakeConfig:
    """Configuration for handshake behavior."""
    timeout: float = DEFAULT_HANDSHAKE_TIMEOUT
    protocol_version: str = DEFAULT_PROTOCOL_VERSION
    retry_on_failure: bool = False
    retry_delay: float = 1.0


class HandshakeError(Exception):
    """Raised when handshake fails."""
    pass


class HandshakeTimeout(HandshakeError):
    """Raised when handshake times out."""
    pass


class Handshaker:
    """
    Executes the handshake protocol with remote agents.
    
    Implements the three-way handshake:
    1. Send HELLO with agent info and capabilities
    2. Receive ACK with peer status
    3. Send READY to confirm connection
    """
    
    def __init__(
        self,
        config: Optional[HandshakeConfig] = None,
        socket_config: Optional[SocketConfig] = None,
        registry: Optional[AgentRegistry] = None,
        connection_manager: Optional[ConnectionManager] = None,
    ):
        """
        Initialize the handshaker.
        
        Args:
            config: Handshake configuration
            socket_config: Socket transport configuration
            registry: Agent registry (uses global if not provided)
            connection_manager: Connection manager (uses global if not provided)
        """
        self.config = config or HandshakeConfig()
        self.socket_config = socket_config or SocketConfig()
        self.registry = registry or get_registry()
        self.connection_manager = connection_manager or get_connection_manager()
        self._client = UnixSocketClient(self.socket_config)
    
    async def initiate_handshake(
        self,
        agent_type: AgentType,
        capabilities: Optional[list[str]] = None,
    ) -> HandshakeResult:
        """
        Initiate handshake with a remote agent.
        
        Sends HELLO, waits for ACK, sends READY.
        
        Args:
            agent_type: Target agent to handshake with
            capabilities: Our capabilities to advertise
            
        Returns:
            HandshakeResult with success status and details
        """
        start_time = datetime.utcnow()
        
        try:
            # Update state to CONNECTING
            self.connection_manager.transition(
                agent_type,
                HandshakeState.CONNECTING,
            )
            
            # Get agent info from registry
            agent_info = self.registry.get_agent(agent_type)
            if not agent_info:
                raise HandshakeError(f"Agent {agent_type.value} not in registry")
            
            # Update registry status
            self.registry.update_status(agent_type, HandshakeState.CONNECTING)
            
            # Step 1: Send HELLO
            hello_msg = create_hello_message(
                target_agent=agent_type,
                agent_name=AgentType.AUTONOMOUS_GLM.value,
                version=self.config.protocol_version,
                capabilities=capabilities or [],
            )
            
            # Update state to HANDSHAKING
            self.connection_manager.transition(
                agent_type,
                HandshakeState.HANDSHAKING,
            )
            self.registry.update_status(agent_type, HandshakeState.HANDSHAKING)
            
            # Send HELLO and wait for ACK with timeout
            try:
                ack = await asyncio.wait_for(
                    self._client.send_message(agent_type, hello_msg),
                    timeout=self.config.timeout,
                )
            except asyncio.TimeoutError:
                raise HandshakeTimeout(
                    f"Handshake timeout waiting for ACK from {agent_type.value}"
                )
            except TransportConnectionError as e:
                raise HandshakeError(
                    f"Connection failed to {agent_type.value}: {e}"
                )
            
            if not ack or ack.status != "acknowledged":
                error_msg = ack.error_message if ack else "No ACK received"
                raise HandshakeError(f"HELLO rejected by {agent_type.value}: {error_msg}")
            
            # Step 2: Send READY
            ready_msg = self._create_ready_message(agent_type)
            
            try:
                ready_ack = await asyncio.wait_for(
                    self._client.send_message(agent_type, ready_msg),
                    timeout=self.config.timeout,
                )
            except asyncio.TimeoutError:
                raise HandshakeTimeout(
                    f"Handshake timeout waiting for READY confirmation from {agent_type.value}"
                )
            
            if not ready_ack or ready_ack.status != "acknowledged":
                error_msg = ready_ack.error_message if ready_ack else "No READY confirmation"
                raise HandshakeError(f"READY rejected by {agent_type.value}: {error_msg}")
            
            # Step 3: Mark as CONNECTED
            self.connection_manager.transition(
                agent_type,
                HandshakeState.CONNECTED,
            )
            self.registry.update_status(
                agent_type,
                HandshakeState.CONNECTED,
                version=self.config.protocol_version,
            )
            
            # Calculate duration
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Handshake completed with {agent_type.value} in {duration_ms:.1f}ms")
            
            return HandshakeResult(
                success=True,
                agent_type=agent_type.value,
                agent_info={
                    "version": self.config.protocol_version,
                    "capabilities": capabilities or [],
                },
                duration_ms=duration_ms,
            )
            
        except (HandshakeError, StateTransitionError) as e:
            # Update state to ERROR
            try:
                self.connection_manager.transition(
                    agent_type,
                    HandshakeState.ERROR,
                    error_message=str(e),
                )
                self.registry.update_status(agent_type, HandshakeState.ERROR)
            except StateTransitionError:
                pass  # Already in error state
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(f"Handshake failed with {agent_type.value}: {e}")
            
            return HandshakeResult(
                success=False,
                agent_type=agent_type.value,
                error_message=str(e),
                duration_ms=duration_ms,
            )
    
    def receive_hello(self, message: AgentMessage) -> AgentMessage:
        """
        Handle incoming HELLO message.
        
        Validates the HELLO and creates an ACK response.
        
        Args:
            message: Incoming HELLO message
            
        Returns:
            ACK message to send back
        """
        try:
            # Parse HELLO payload
            payload = HelloPayload.model_validate(message.payload)
            
            logger.info(
                f"Received HELLO from {payload.agent_name} "
                f"(version: {payload.version}, capabilities: {payload.capabilities})"
            )
            
            # Create ACK response
            ack_payload = AckPayload(
                agent_name=AgentType.AUTONOMOUS_GLM.value,
                status="acknowledged",
                message=f"Hello acknowledged from {AgentType.AUTONOMOUS_GLM.value}",
            )
            
            return AgentMessage(
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=message.source_agent,
                message_type=MessageType.ACK,
                payload=ack_payload.model_dump(),
                requires_response=False,
            )
            
        except Exception as e:
            logger.error(f"Failed to process HELLO: {e}")
            
            # Create error ACK
            ack_payload = AckPayload(
                agent_name=AgentType.AUTONOMOUS_GLM.value,
                status="rejected",
                message=str(e),
            )
            
            return AgentMessage(
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=message.source_agent,
                message_type=MessageType.ACK,
                payload=ack_payload.model_dump(),
                requires_response=False,
            )
    
    def receive_ack(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Handle incoming ACK message.
        
        Validates the ACK and prepares READY message if acknowledged.
        
        Args:
            message: Incoming ACK message
            
        Returns:
            READY message if ACK is positive, None otherwise
        """
        try:
            payload = AckPayload.model_validate(message.payload)
            
            logger.info(
                f"Received ACK from {payload.agent_name} "
                f"(status: {payload.status})"
            )
            
            if payload.status == "acknowledged":
                # Create READY message
                ready_payload = ReadyPayload(
                    agent_name=AgentType.AUTONOMOUS_GLM.value,
                    status="ready",
                )
                
                return AgentMessage(
                    source_agent=AgentType.AUTONOMOUS_GLM,
                    target_agent=message.source_agent,
                    message_type=MessageType.READY,
                    payload=ready_payload.model_dump(),
                    requires_response=True,
                )
            else:
                logger.warning(f"ACK rejected: {payload.message}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to process ACK: {e}")
            return None
    
    def receive_ready(self, message: AgentMessage) -> bool:
        """
        Handle incoming READY message.
        
        Marks the connection as established.
        
        Args:
            message: Incoming READY message
            
        Returns:
            True if READY was processed successfully
        """
        try:
            payload = ReadyPayload.model_validate(message.payload)
            
            logger.info(
                f"Received READY from {payload.agent_name} "
                f"(status: {payload.status})"
            )
            
            # Update connection state
            try:
                self.connection_manager.transition(
                    message.source_agent,
                    HandshakeState.CONNECTED,
                )
                self.registry.update_status(
                    message.source_agent,
                    HandshakeState.CONNECTED,
                )
            except StateTransitionError as e:
                logger.warning(f"State transition error on READY: {e}")
            
            return payload.status == "ready"
            
        except Exception as e:
            logger.error(f"Failed to process READY: {e}")
            return False
    
    def handle_handshake_timeout(self, agent_type: AgentType) -> None:
        """
        Handle a handshake timeout.
        
        Updates state and logs the timeout.
        
        Args:
            agent_type: Agent that timed out
        """
        logger.warning(f"Handshake timeout with {agent_type.value}")
        
        try:
            self.connection_manager.transition(
                agent_type,
                HandshakeState.ERROR,
                error_message="Handshake timeout",
            )
            self.registry.update_status(agent_type, HandshakeState.ERROR)
        except StateTransitionError:
            pass  # Already in error state
    
    def _create_ready_message(self, target: AgentType) -> AgentMessage:
        """Create a READY message for the target agent."""
        payload = ReadyPayload(
            agent_name=AgentType.AUTONOMOUS_GLM.value,
            status="ready",
        )
        
        return AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=target,
            message_type=MessageType.READY,
            payload=payload.model_dump(),
            requires_response=True,
        )
    
    async def close(self) -> None:
        """Close the underlying client connection."""
        await self._client.disconnect_all()


async def handshake_with_agent(
    agent_type: AgentType,
    capabilities: Optional[list[str]] = None,
    config: Optional[HandshakeConfig] = None,
) -> HandshakeResult:
    """
    Convenience function to handshake with an agent.
    
    Creates a temporary Handshaker instance and performs handshake.
    
    Args:
        agent_type: Target agent
        capabilities: Capabilities to advertise
        config: Handshake configuration
        
    Returns:
        HandshakeResult
    """
    handshaker = Handshaker(config=config)
    try:
        return await handshaker.initiate_handshake(agent_type, capabilities)
    finally:
        await handshaker.close()
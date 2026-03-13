"""
Base class for agent mocks.

Provides configurable responses, message logging, and state tracking
for testing multi-agent communication protocols.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageAck,
    MessageType,
    AuditCompletePayload,
    DesignProposalPayload,
    DisputePayload,
    HumanRequiredPayload,
    HelloPayload,
    AckPayload,
    ReadyPayload,
    ErrorPayload,
)


class MockResponse(str, Enum):
    """Predefined response types for mock configuration."""
    ACCEPT = "accept"
    REJECT = "reject"
    ESCALATE = "escalate"
    DELAY = "delay"
    ERROR = "error"


class MockState(str, Enum):
    """Mock connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class LoggedMessage:
    """Record of a message sent or received by a mock."""
    direction: str  # "sent" or "received"
    message: AgentMessage
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response: Optional[MessageAck] = None


@dataclass
class MockConfig:
    """Configuration for mock behavior."""
    default_response: MockResponse = MockResponse.ACCEPT
    response_delay_ms: int = 0
    reject_message: str = "Rejected by mock"
    error_message: str = "Mock error"
    auto_handshake: bool = True


class BaseAgentMock:
    """
    Base class for agent mocks with configurable responses and logging.
    
    Subclasses should override:
    - agent_type: The AgentType this mock represents
    - handle_message(): Custom message handling logic
    
    Features:
    - Configurable default response (accept, reject, escalate, error, delay)
    - Per-message-type response overrides
    - Message logging for verification
    - State tracking (connected, handshake_complete)
    - Simulated delays for timing tests
    - Error injection for failure scenarios
    """
    
    agent_type: AgentType = AgentType.HUMAN  # Override in subclass
    
    def __init__(self, config: Optional[MockConfig] = None):
        """
        Initialize the mock agent.
        
        Args:
            config: Mock configuration. Uses defaults if not provided.
        """
        self.config = config or MockConfig()
        self.state = MockState.DISCONNECTED
        self.messages_received: list[LoggedMessage] = []
        self.messages_sent: list[LoggedMessage] = []
        self._response_overrides: dict[MessageType, MockResponse] = {}
        self._custom_handlers: dict[MessageType, Callable[[AgentMessage], MessageAck]] = {}
        self._capabilities: list[str] = []
        self._handshake_complete = False
    
    def configure_response(
        self,
        message_type: MessageType,
        response: MockResponse,
    ) -> None:
        """
        Override response for a specific message type.
        
        Args:
            message_type: Message type to override
            response: Response to use for this message type
        """
        self._response_overrides[message_type] = response
    
    def configure_handler(
        self,
        message_type: MessageType,
        handler: Callable[[AgentMessage], MessageAck],
    ) -> None:
        """
        Set a custom handler for a specific message type.
        
        Args:
            message_type: Message type to handle
            handler: Function to handle the message and return ACK
        """
        self._custom_handlers[message_type] = handler
    
    def set_capabilities(self, capabilities: list[str]) -> None:
        """Set agent capabilities for handshake."""
        self._capabilities = capabilities
    
    def connect(self) -> None:
        """Simulate connection establishment."""
        self.state = MockState.CONNECTED
    
    def disconnect(self) -> None:
        """Simulate disconnection."""
        self.state = MockState.DISCONNECTED
        self._handshake_complete = False
    
    def complete_handshake(self) -> None:
        """Mark handshake as complete."""
        self._handshake_complete = True
        self.state = MockState.CONNECTED
    
    def is_connected(self) -> bool:
        """Check if mock is connected."""
        return self.state == MockState.CONNECTED
    
    def is_handshake_complete(self) -> bool:
        """Check if handshake is complete."""
        return self._handshake_complete
    
    def handle_message(self, message: AgentMessage) -> MessageAck:
        """
        Handle an incoming message and return acknowledgment.
        
        This method:
        1. Logs the received message
        2. Checks for custom handler
        3. Falls back to default response behavior
        4. Logs the response
        
        Args:
            message: The incoming message
            
        Returns:
            MessageAck with appropriate status
        """
        # Log received message
        logged = LoggedMessage(
            direction="received",
            message=message,
            timestamp=datetime.utcnow(),
        )
        self.messages_received.append(logged)
        
        # Handle handshake messages specially
        if message.message_type == MessageType.HELLO:
            return self._handle_hello(message)
        elif message.message_type == MessageType.READY:
            return self._handle_ready(message)
        
        # Check for custom handler
        if message.message_type in self._custom_handlers:
            ack = self._custom_handlers[message.message_type](message)
            logged.response = ack
            return ack
        
        # Determine response
        response = self._response_overrides.get(
            message.message_type,
            self.config.default_response,
        )
        
        # Generate ACK based on response type
        ack = self._generate_ack(message, response)
        logged.response = ack
        return ack
    
    def _handle_hello(self, message: AgentMessage) -> MessageAck:
        """Handle HELLO message for handshake."""
        if self.config.auto_handshake:
            self.state = MockState.HANDSHAKING
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        return MessageAck(
            message_id=message.message_id,
            status="rejected",
            error_message="Handshake rejected by mock configuration",
        )
    
    def _handle_ready(self, message: AgentMessage) -> MessageAck:
        """Handle READY message to complete handshake."""
        if self.config.auto_handshake:
            self.complete_handshake()
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        return MessageAck(
            message_id=message.message_id,
            status="pending",
            error_message="Handshake pending",
        )
    
    def _generate_ack(self, message: AgentMessage, response: MockResponse) -> MessageAck:
        """Generate ACK based on response type."""
        if response == MockResponse.ACCEPT:
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        elif response == MockResponse.REJECT:
            return MessageAck(
                message_id=message.message_id,
                status="rejected",
                error_message=self.config.reject_message,
            )
        elif response == MockResponse.ESCALATE:
            # Escalate to human - return pending status
            return MessageAck(
                message_id=message.message_id,
                status="pending",
                error_message="Escalated to human review",
            )
        elif response == MockResponse.ERROR:
            return MessageAck(
                message_id=message.message_id,
                status="error",
                error_message=self.config.error_message,
            )
        elif response == MockResponse.DELAY:
            # Simulate delay - still acknowledge
            return MessageAck(
                message_id=message.message_id,
                status="acknowledged",
            )
        
        # Default to accept
        return MessageAck(
            message_id=message.message_id,
            status="acknowledged",
        )
    
    def send_message(
        self,
        target: AgentType,
        message_type: MessageType,
        payload: dict[str, Any],
        requires_response: bool = False,
    ) -> AgentMessage:
        """
        Create and log an outgoing message.
        
        Args:
            target: Target agent
            message_type: Message type
            payload: Message payload
            requires_response: Whether response is required
            
        Returns:
            The created message
        """
        message = AgentMessage(
            message_id=str(uuid4()),
            source_agent=self.agent_type,
            target_agent=target,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            requires_response=requires_response,
        )
        
        logged = LoggedMessage(
            direction="sent",
            message=message,
            timestamp=datetime.utcnow(),
        )
        self.messages_sent.append(logged)
        
        return message
    
    def get_received_messages(
        self,
        message_type: Optional[MessageType] = None,
    ) -> list[AgentMessage]:
        """
        Get received messages, optionally filtered by type.
        
        Args:
            message_type: Optional message type filter
            
        Returns:
            List of received messages
        """
        messages = [lm.message for lm in self.messages_received]
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        return messages
    
    def get_sent_messages(
        self,
        message_type: Optional[MessageType] = None,
    ) -> list[AgentMessage]:
        """
        Get sent messages, optionally filtered by type.
        
        Args:
            message_type: Optional message type filter
            
        Returns:
            List of sent messages
        """
        messages = [lm.message for lm in self.messages_sent]
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        return messages
    
    def clear_history(self) -> None:
        """Clear message history."""
        self.messages_received.clear()
        self.messages_sent.clear()
    
    def reset(self) -> None:
        """Reset mock to initial state."""
        self.clear_history()
        self.state = MockState.DISCONNECTED
        self._handshake_complete = False
        self._response_overrides.clear()
        self._custom_handlers.clear()
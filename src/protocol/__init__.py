"""
Protocol module for agent-to-agent communication.

Provides message models, validation, transport, and routing for
communication between autonomous-glm and other agents.
"""

from src.protocol.message import (
    AgentMessage,
    AgentType,
    AckPayload,
    AuditCompletePayload,
    ChangeType,
    DesignProposalPayload,
    DisputePayload,
    DisputeSeverity,
    ErrorPayload,
    HelloPayload,
    HumanRequiredPayload,
    HumanReviewOption,
    MessageAck,
    MessageType,
    ProposalChange,
    ProposalType,
    ReadyPayload,
    ReviewType,
    create_ack_message,
    create_audit_complete_message,
    create_design_proposal_message,
    create_dispute_message,
    create_error_message,
    create_hello_message,
    create_human_required_message,
)
from src.protocol.validator import (
    MessageValidator,
    ValidationError,
    validate_message,
    validate_message_schema,
)
from src.protocol.transport import (
    SocketConfig,
    UnixSocketClient,
    UnixSocketServer,
    TransportError,
    ConnectionError as TransportConnectionError,
    MessageFramingError,
    send_message,
    broadcast,
)
from src.protocol.router import (
    MessageRouter,
    MessageHandler,
    get_agent_socket_path,
    resolve_agent_endpoint,
    route_message,
    broadcast_message,
)
from src.protocol.registry import (
    HandshakeState,
    AgentInfo,
    AgentRegistry,
    HandshakeAgentConfig,
    get_registry,
    reset_registry,
)
from src.protocol.state import (
    ConnectionState,
    ConnectionManager,
    StateTransitionError,
    get_connection_manager,
    reset_connection_manager,
)
from src.protocol.handshake import (
    HandshakeResult,
    HandshakeConfig,
    HandshakeError,
    HandshakeTimeout,
    Handshaker,
    handshake_with_agent,
)
from src.protocol.health import (
    HealthMonitor,
    HealthConfig,
    AgentHealth,
    create_health_monitor,
)
# M5-3: Arbitration & Reliability
from src.protocol.retry import (
    RetryConfig,
    RetryState,
    RetryManager,
    RetryableError,
    PermanentError,
    ErrorType,
    create_retry_config_from_dict,
)
from src.protocol.sync import (
    SyncEventType,
    SyncStatus,
    SyncLogEntry,
    SyncStats,
    SyncLogger,
    get_sync_logger,
    reset_sync_logger,
)
from src.protocol.dedup import (
    CacheEntry,
    DeduplicationCache,
    get_dedup_cache,
    reset_dedup_cache,
    is_duplicate,
    mark_processed,
)
from src.protocol.arbitration import (
    DisputeStatus,
    DisputeResolution,
    DisputeRecord,
    Arbitrator,
    get_arbitrator,
    reset_arbitrator,
)
from src.protocol.escalation import (
    EscalationTrigger,
    EscalationStatus,
    EscalationRecord,
    EscalationManager,
    get_escalation_manager,
    reset_escalation_manager,
)
from src.protocol.dead_letter import (
    DeadLetterEntry,
    DeadLetterQueue,
    get_dead_letter_queue,
    reset_dead_letter_queue,
    add_to_dlq,
)

__all__ = [
    # Message types
    "AgentMessage",
    "MessageAck",
    "AgentType",
    "MessageType",
    # Payload models
    "AuditCompletePayload",
    "DesignProposalPayload",
    "DisputePayload",
    "HumanRequiredPayload",
    "ProposalChange",
    "HumanReviewOption",
    "HelloPayload",
    "AckPayload",
    "ReadyPayload",
    "ErrorPayload",
    # Enums
    "ProposalType",
    "ChangeType",
    "ReviewType",
    "DisputeSeverity",
    "HandshakeState",
    # Factory functions
    "create_audit_complete_message",
    "create_design_proposal_message",
    "create_dispute_message",
    "create_human_required_message",
    "create_hello_message",
    "create_ack_message",
    "create_error_message",
    # Validation
    "MessageValidator",
    "ValidationError",
    "validate_message",
    "validate_message_schema",
    # Transport
    "SocketConfig",
    "UnixSocketClient",
    "UnixSocketServer",
    "TransportError",
    "TransportConnectionError",
    "MessageFramingError",
    "send_message",
    "broadcast",
    # Router
    "MessageRouter",
    "MessageHandler",
    "get_agent_socket_path",
    "resolve_agent_endpoint",
    "route_message",
    "broadcast_message",
    # Registry
    "AgentInfo",
    "AgentRegistry",
    "HandshakeAgentConfig",
    "get_registry",
    "reset_registry",
    # State
    "ConnectionState",
    "ConnectionManager",
    "StateTransitionError",
    "get_connection_manager",
    "reset_connection_manager",
    # Handshake
    "HandshakeResult",
    "HandshakeConfig",
    "HandshakeError",
    "HandshakeTimeout",
    "Handshaker",
    "handshake_with_agent",
    # Health
    "HealthMonitor",
    "HealthConfig",
    "AgentHealth",
    "create_health_monitor",
    # M5-3: Retry
    "RetryConfig",
    "RetryState",
    "RetryManager",
    "RetryableError",
    "PermanentError",
    "ErrorType",
    "create_retry_config_from_dict",
    # M5-3: Sync
    "SyncEventType",
    "SyncStatus",
    "SyncLogEntry",
    "SyncStats",
    "SyncLogger",
    "get_sync_logger",
    "reset_sync_logger",
    # M5-3: Deduplication
    "CacheEntry",
    "DeduplicationCache",
    "get_dedup_cache",
    "reset_dedup_cache",
    "is_duplicate",
    "mark_processed",
    # M5-3: Arbitration
    "DisputeStatus",
    "DisputeResolution",
    "DisputeRecord",
    "Arbitrator",
    "get_arbitrator",
    "reset_arbitrator",
    # M5-3: Escalation
    "EscalationTrigger",
    "EscalationStatus",
    "EscalationRecord",
    "EscalationManager",
    "get_escalation_manager",
    "reset_escalation_manager",
    # M5-3: Dead Letter Queue
    "DeadLetterEntry",
    "DeadLetterQueue",
    "get_dead_letter_queue",
    "reset_dead_letter_queue",
    "add_to_dlq",
]

"""
Unit tests for the protocol module.

Tests message models, validation, transport, and routing.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.protocol import (
    AgentMessage,
    AgentType,
    AuditCompletePayload,
    DesignProposalPayload,
    DisputePayload,
    DisputeSeverity,
    HumanRequiredPayload,
    HumanReviewOption,
    MessageAck,
    MessageType,
    ProposalChange,
    ProposalType,
    ReviewType,
    ChangeType,
    SocketConfig,
    MessageValidator,
    ValidationError as ProtocolValidationError,
    UnixSocketClient,
    UnixSocketServer,
    MessageRouter,
    create_audit_complete_message,
    create_design_proposal_message,
    create_dispute_message,
    create_human_required_message,
    validate_message,
)


# ============= Message Model Tests =============

class TestAgentMessage:
    """Tests for AgentMessage model."""
    
    def test_create_message_with_required_fields(self):
        """Test creating a message with only required fields."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        assert message.source_agent == AgentType.AUTONOMOUS_GLM
        assert message.target_agent == AgentType.CLAUDE
        assert message.message_type == MessageType.HELLO
        assert message.payload == {}
        assert message.message_id is not None
        assert message.timestamp is not None
    
    def test_message_id_is_uuid(self):
        """Test that message_id is a valid UUID."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        # UUID format: 8-4-4-4-12 hex characters
        import uuid
        uuid.UUID(message.message_id)  # Raises if invalid
    
    def test_timestamp_is_datetime(self):
        """Test that timestamp is a datetime object."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        # Should be a datetime object
        assert isinstance(message.timestamp, datetime)
    
    def test_to_json_and_from_json(self):
        """Test JSON serialization roundtrip."""
        original = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.MINIMAX,
            message_type=MessageType.AUDIT_COMPLETE,
            payload={
                "artifact_id": "test-123",
                "audit_id": "audit-456",
                "findings_count": 5,
                "critical_count": 1,
                "phases": ["Critical", "Refinement"],
            },
            requires_response=True,
        )
        
        json_str = original.to_json()
        parsed = AgentMessage.from_json(json_str)
        
        assert parsed.message_id == original.message_id
        assert parsed.source_agent == original.source_agent
        assert parsed.target_agent == original.target_agent
        assert parsed.message_type == original.message_type
        assert parsed.payload == original.payload
        assert parsed.requires_response == original.requires_response
    
    def test_to_dict(self):
        """Test dict serialization."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={"key": "value"},
        )
        
        d = message.model_dump()
        
        assert d["source_agent"] == AgentType.AUTONOMOUS_GLM
        assert d["target_agent"] == AgentType.CLAUDE
        assert d["message_type"] == MessageType.HELLO
        assert d["payload"] == {"key": "value"}


class TestMessageAck:
    """Tests for MessageAck model."""
    
    def test_create_ack_with_required_fields(self):
        """Test creating an ack with required fields."""
        ack = MessageAck(
            message_id="test-123",
            status="acknowledged",
        )
        
        assert ack.message_id == "test-123"
        assert ack.status == "acknowledged"
        assert ack.error_message is None
    
    def test_create_ack_with_error(self):
        """Test creating an ack with error message."""
        ack = MessageAck(
            message_id="test-123",
            status="error",
            error_message="Something went wrong",
        )
        
        assert ack.status == "error"
        assert ack.error_message == "Something went wrong"
    
    def test_ack_json_roundtrip(self):
        """Test ack JSON serialization."""
        original = MessageAck(
            message_id="test-456",
            status="acknowledged",
        )
        
        json_str = original.to_json()
        parsed = MessageAck.from_json(json_str)
        
        assert parsed.message_id == original.message_id
        assert parsed.status == original.status
    
    def test_invalid_status_raises(self):
        """Test that invalid status raises validation error."""
        with pytest.raises(ValidationError):
            MessageAck(
                message_id="test-123",
                status="invalid_status",
            )


class TestPayloadModels:
    """Tests for payload models."""
    
    def test_audit_complete_payload(self):
        """Test AuditCompletePayload creation."""
        payload = AuditCompletePayload(
            artifact_id="artifact-123",
            audit_id="audit-456",
            findings_count=10,
            critical_count=2,
            phases=["Critical", "Refinement", "Polish"],
        )
        
        assert payload.artifact_id == "artifact-123"
        assert payload.audit_id == "audit-456"
        assert payload.findings_count == 10
        assert payload.critical_count == 2
        assert payload.phases == ["Critical", "Refinement", "Polish"]
    
    def test_audit_complete_payload_invalid_phase(self):
        """Test AuditCompletePayload with invalid phase."""
        with pytest.raises(ValidationError):
            AuditCompletePayload(
                artifact_id="artifact-123",
                audit_id="audit-456",
                findings_count=10,
                phases=["InvalidPhase"],
            )
    
    def test_design_proposal_payload(self):
        """Test DesignProposalPayload creation."""
        change = ProposalChange(
            target_file="src/components/Button.tsx",
            change_type=ChangeType.MODIFY,
            old_value="padding: 8px",
            new_value="padding: 12px",
            rationale="Improve touch target size",
        )
        
        payload = DesignProposalPayload(
            proposal_id="proposal-123",
            proposal_type=ProposalType.COMPONENT_MODIFICATION,
            changes=[change],
            human_approval_required=True,
        )
        
        assert payload.proposal_id == "proposal-123"
        assert payload.proposal_type == ProposalType.COMPONENT_MODIFICATION
        assert len(payload.changes) == 1
        assert payload.changes[0].change_type == ChangeType.MODIFY
    
    def test_dispute_payload(self):
        """Test DisputePayload creation."""
        payload = DisputePayload(
            dispute_id="dispute-123",
            audit_id="audit-456",
            finding_id="finding-789",
            dispute_reason="False positive",
            severity=DisputeSeverity.MEDIUM,
            proposed_alternative="Ignore this finding",
        )
        
        assert payload.dispute_id == "dispute-123"
        assert payload.audit_id == "audit-456"
        assert payload.finding_id == "finding-789"
        assert payload.severity == DisputeSeverity.MEDIUM
    
    def test_human_required_payload(self):
        """Test HumanRequiredPayload creation."""
        payload = HumanRequiredPayload(
            review_type=ReviewType.DESIGN_SYSTEM_CHANGE,
            reason="Choose between two layout options",
            blocking=True,
            options=[
                {"label": "Approve", "action": "approve"},
                {"label": "Reject", "action": "reject"},
            ],
        )
        
        assert payload.review_type == ReviewType.DESIGN_SYSTEM_CHANGE
        assert len(payload.options) == 2
        assert payload.blocking is True


class TestFactoryFunctions:
    """Tests for message factory functions."""
    
    def test_create_audit_complete_message(self):
        """Test audit complete message factory."""
        message = create_audit_complete_message(
            target_agent=AgentType.CLAUDE,
            artifact_id="artifact-123",
            audit_id="audit-456",
            findings_count=5,
            phases=["Critical"],
            critical_count=1,
        )
        
        assert message.target_agent == AgentType.CLAUDE
        assert message.message_type == MessageType.AUDIT_COMPLETE
        assert message.payload["artifact_id"] == "artifact-123"
        assert message.payload["audit_id"] == "audit-456"
        assert message.requires_response is False
    
    def test_create_design_proposal_message(self):
        """Test design proposal message factory."""
        message = create_design_proposal_message(
            target_agent=AgentType.HUMAN,
            proposal_id="proposal-123",
            proposal_type=ProposalType.TOKEN_MODIFICATION,
            changes=[],
            human_approval_required=True,
        )
        
        assert message.target_agent == AgentType.HUMAN
        assert message.message_type == MessageType.DESIGN_PROPOSAL
        assert message.requires_response is True
    
    def test_create_dispute_message(self):
        """Test dispute message factory."""
        message = create_dispute_message(
            source_agent=AgentType.MINIMAX,
            target_agent=AgentType.CLAUDE,
            dispute_id="dispute-123",
            audit_id="audit-456",
            finding_id="finding-789",
            dispute_reason="False positive",
            severity=DisputeSeverity.HIGH,
        )
        
        assert message.source_agent == AgentType.MINIMAX
        assert message.target_agent == AgentType.CLAUDE
        assert message.message_type == MessageType.DISPUTE
        assert message.requires_response is True
    
    def test_create_human_required_message(self):
        """Test human required message factory."""
        message = create_human_required_message(
            review_type=ReviewType.COMPLEX_ARIA,
            reason="Complex ARIA pattern detected",
            blocking=True,
        )
        
        assert message.target_agent == AgentType.HUMAN
        assert message.message_type == MessageType.HUMAN_REQUIRED
        assert message.requires_response is True


# ============= Validator Tests =============

class TestMessageValidator:
    """Tests for MessageValidator."""
    
    def test_validate_basic_message(self):
        """Test validation of basic message structure."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        validator = MessageValidator()
        is_valid, errors = validator.validate_message(message)
        
        assert is_valid is True
        assert errors == []
    
    def test_validate_source_agent(self):
        """Test source agent validation."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        validator = MessageValidator()
        
        assert validator.validate_source_agent(message, AgentType.AUTONOMOUS_GLM) is True
        assert validator.validate_source_agent(message, AgentType.CLAUDE) is False
    
    def test_validate_target_agent(self):
        """Test target agent validation."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        validator = MessageValidator()
        
        assert validator.validate_target_agent(
            message, [AgentType.CLAUDE, AgentType.MINIMAX]
        ) is True
        assert validator.validate_target_agent(
            message, [AgentType.MINIMAX]
        ) is False
    
    def test_schema_caching(self):
        """Test that schemas are cached."""
        validator = MessageValidator()
        
        # Load schema twice
        schema1 = validator._load_schema("audit-complete.schema.json")
        schema2 = validator._load_schema("audit-complete.schema.json")
        
        assert schema1 is schema2  # Same object reference
    
    def test_clear_cache(self):
        """Test cache clearing."""
        validator = MessageValidator()
        
        # Load schema
        validator._load_schema("audit-complete.schema.json")
        assert len(validator._schema_cache) > 0
        
        # Clear cache
        validator.clear_cache()
        assert len(validator._schema_cache) == 0


class TestValidateMessageFunction:
    """Tests for module-level validate_message function."""
    
    def test_validate_message_valid(self):
        """Test validate_message with valid message."""
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        is_valid, errors = validate_message(message)
        
        assert is_valid is True
        assert errors == []


# ============= Transport Tests =============

class TestSocketConfig:
    """Tests for SocketConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SocketConfig()
        
        assert config.socket_dir == "/var/run/autonomous-glm"
        assert config.socket_timeout == 30.0
        assert config.buffer_size == 65536
        assert config.max_message_size == 10 * 1024 * 1024
    
    def test_get_socket_path(self):
        """Test socket path generation."""
        config = SocketConfig(socket_dir="/tmp/test")
        
        path = config.get_socket_path(AgentType.CLAUDE)
        
        assert path == "/tmp/test/claude.sock"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SocketConfig(
            socket_dir="/custom/path",
            socket_timeout=60.0,
            buffer_size=131072,
        )
        
        assert config.socket_dir == "/custom/path"
        assert config.socket_timeout == 60.0
        assert config.buffer_size == 131072


class TestUnixSocketServer:
    """Tests for UnixSocketServer."""
    
    @pytest.fixture
    def temp_socket_dir(self):
        """Create a temporary directory for socket files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.mark.asyncio
    async def test_server_start_stop(self, temp_socket_dir):
        """Test server start and stop."""
        socket_path = os.path.join(temp_socket_dir, "test.sock")
        config = SocketConfig(socket_dir=temp_socket_dir)
        
        server = UnixSocketServer(socket_path, config)
        
        await server.start()
        assert server._running is True
        assert os.path.exists(socket_path)
        
        await server.stop()
        assert server._running is False
        assert not os.path.exists(socket_path)
    
    @pytest.mark.asyncio
    async def test_server_with_handler(self, temp_socket_dir):
        """Test server with custom message handler."""
        socket_path = os.path.join(temp_socket_dir, "test.sock")
        config = SocketConfig(socket_dir=temp_socket_dir)
        
        received_messages = []
        
        def handler(message: AgentMessage) -> MessageAck:
            received_messages.append(message)
            return MessageAck(message_id=message.message_id, status="processed")
        
        server = UnixSocketServer(socket_path, config, message_handler=handler)
        
        await server.start()
        assert server._running is True
        
        await server.stop()


class TestUnixSocketClient:
    """Tests for UnixSocketClient."""
    
    @pytest.fixture
    def temp_socket_dir(self):
        """Create a temporary directory for socket files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.mark.asyncio
    async def test_client_disconnect_all(self, temp_socket_dir):
        """Test client disconnect_all."""
        config = SocketConfig(socket_dir=temp_socket_dir)
        client = UnixSocketClient(config)
        
        # Should not raise even with no connections
        await client.disconnect_all()


# ============= Router Tests =============

class TestMessageRouter:
    """Tests for MessageRouter."""
    
    def test_register_handler(self):
        """Test handler registration."""
        router = MessageRouter()
        
        def handler(message: AgentMessage) -> MessageAck:
            return MessageAck(message_id=message.message_id, status="ok")
        
        router.register_handler(MessageType.HELLO, handler)
        
        assert router.get_handler(MessageType.HELLO) == handler
    
    def test_unregister_handler(self):
        """Test handler unregistration."""
        router = MessageRouter()
        
        def handler(message: AgentMessage) -> MessageAck:
            return MessageAck(message_id=message.message_id, status="ok")
        
        router.register_handler(MessageType.HELLO, handler)
        router.unregister_handler(MessageType.HELLO)
        
        assert router.get_handler(MessageType.HELLO) is None
    
    def test_set_default_handler(self):
        """Test default handler setting."""
        router = MessageRouter()
        
        def handler(message: AgentMessage) -> MessageAck:
            return MessageAck(message_id=message.message_id, status="default")
        
        router.set_default_handler(handler)
        
        assert router.get_handler(MessageType.HELLO) == handler
    
    def test_handle_message_with_handler(self):
        """Test message handling with registered handler."""
        router = MessageRouter()
        
        handled_messages = []
        
        def handler(message: AgentMessage) -> MessageAck:
            handled_messages.append(message)
            return MessageAck(message_id=message.message_id, status="acknowledged")
        
        router.register_handler(MessageType.HELLO, handler)
        
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        ack = router.handle_message(message)
        
        assert len(handled_messages) == 1
        assert ack.status == "acknowledged"
    
    def test_handle_message_without_handler(self):
        """Test message handling without registered handler."""
        router = MessageRouter()
        
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        ack = router.handle_message(message)
        
        assert ack.status == "acknowledged"
    
    def test_handle_message_with_handler_error(self):
        """Test message handling when handler raises error."""
        router = MessageRouter()
        
        def handler(message: AgentMessage) -> MessageAck:
            raise ValueError("Handler error")
        
        router.register_handler(MessageType.HELLO, handler)
        
        message = AgentMessage(
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.CLAUDE,
            message_type=MessageType.HELLO,
            payload={},
        )
        
        ack = router.handle_message(message)
        
        assert ack.status == "error"
        assert "Handler error" in ack.error_message
    
    def test_get_socket_path(self):
        """Test socket path generation."""
        config = SocketConfig(socket_dir="/custom/path")
        router = MessageRouter(config)
        
        path = router.get_socket_path(AgentType.CLAUDE)
        
        assert path == "/custom/path/claude.sock"


class TestAgentEndpointResolution:
    """Tests for agent endpoint resolution functions."""
    
    def test_get_agent_socket_path(self):
        """Test get_agent_socket_path function."""
        from src.protocol.router import get_agent_socket_path
        
        path = get_agent_socket_path(AgentType.CLAUDE, "/test/dir")
        
        assert path == "/test/dir/claude.sock"
    
    def test_resolve_agent_endpoint(self):
        """Test resolve_agent_endpoint function."""
        from src.protocol.router import resolve_agent_endpoint
        
        path = resolve_agent_endpoint(AgentType.MINIMAX)
        
        assert path.endswith("minimax.sock")


# ============= Enum Tests =============

class TestEnums:
    """Tests for enum types."""
    
    def test_agent_type_values(self):
        """Test AgentType enum values."""
        assert AgentType.AUTONOMOUS_GLM.value == "autonomous-glm"
        assert AgentType.CLAUDE.value == "claude"
        assert AgentType.MINIMAX.value == "minimax"
        assert AgentType.CODEX.value == "codex"
        assert AgentType.HUMAN.value == "human"
    
    def test_message_type_values(self):
        """Test MessageType enum values."""
        assert MessageType.HELLO.value == "HELLO"
        assert MessageType.ACK.value == "ACK"
        assert MessageType.READY.value == "READY"
        assert MessageType.ERROR.value == "ERROR"
        assert MessageType.AUDIT_COMPLETE.value == "AUDIT_COMPLETE"
        assert MessageType.DESIGN_PROPOSAL.value == "DESIGN_PROPOSAL"
        assert MessageType.DISPUTE.value == "DISPUTE"
        assert MessageType.HUMAN_REQUIRED.value == "HUMAN_REQUIRED"
    
    def test_proposal_type_values(self):
        """Test ProposalType enum values."""
        assert ProposalType.TOKEN_ADDITION.value == "token_addition"
        assert ProposalType.TOKEN_MODIFICATION.value == "token_modification"
        assert ProposalType.COMPONENT_ADDITION.value == "component_addition"
        assert ProposalType.COMPONENT_MODIFICATION.value == "component_modification"
        assert ProposalType.STANDARD_UPDATE.value == "standard_update"
    
    def test_change_type_values(self):
        """Test ChangeType enum values."""
        assert ChangeType.ADD.value == "add"
        assert ChangeType.MODIFY.value == "modify"
        assert ChangeType.REMOVE.value == "remove"
    
    def test_review_type_values(self):
        """Test ReviewType enum values."""
        assert ReviewType.DESIGN_SYSTEM_CHANGE.value == "design_system_change"
        assert ReviewType.DISPUTED_FINDING.value == "disputed_finding"
        assert ReviewType.CRITICAL_SEVERITY.value == "critical_severity"
        assert ReviewType.COMPLEX_ARIA.value == "complex_aria"
    
    def test_dispute_severity_values(self):
        """Test DisputeSeverity enum values."""
        assert DisputeSeverity.LOW.value == "low"
        assert DisputeSeverity.MEDIUM.value == "medium"
        assert DisputeSeverity.HIGH.value == "high"
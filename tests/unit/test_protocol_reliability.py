"""
Unit tests for M5-3: Arbitration & Reliability modules.

Tests for:
- retry.py: Exponential backoff retry logic
- sync.py: Message synchronization logging
- dedup.py: Message deduplication cache
- arbitration.py: Dispute routing to arbiter
- escalation.py: Human-in-the-loop escalation
- dead_letter.py: Dead Letter Queue
"""

import asyncio
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

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
from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageType,
    DisputeSeverity,
    ReviewType,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_dlq_file():
    """Create a temporary DLQ file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_message():
    """Create a sample agent message for testing."""
    return AgentMessage(
        message_id="test-msg-001",
        source_agent=AgentType.AUTONOMOUS_GLM,
        target_agent=AgentType.CLAUDE,
        message_type=MessageType.AUDIT_COMPLETE,
        payload={"audit_id": "audit-123", "findings_count": 5},
    )


@pytest.fixture
def sample_dispute_message():
    """Create a sample dispute message for testing."""
    return AgentMessage(
        message_id="dispute-msg-001",
        source_agent=AgentType.AUTONOMOUS_GLM,
        target_agent=AgentType.CLAUDE,
        message_type=MessageType.DISPUTE,
        payload={
            "dispute_id": "dispute-123",
            "audit_id": "audit-456",
            "finding_id": "finding-789",
            "dispute_reason": "Incorrect severity assessment",
        },
    )


# =============================================================================
# Retry Tests
# =============================================================================

class TestRetryConfig:
    """Tests for RetryConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 5
        assert config.base_delay == 1.0
        assert config.max_delay == 1800.0
        assert config.jitter is True
        assert config.exponential_base == 2.0
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=3,
            base_delay=0.5,
            max_delay=60.0,
            jitter=False,
        )
        assert config.max_retries == 3
        assert config.base_delay == 0.5
        assert config.max_delay == 60.0
        assert config.jitter is False
    
    def test_validation_negative_retries(self):
        """Test validation rejects negative retries."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            RetryConfig(max_retries=-1)
    
    def test_validation_zero_base_delay(self):
        """Test validation rejects zero base delay."""
        with pytest.raises(ValueError, match="base_delay must be positive"):
            RetryConfig(base_delay=0)
    
    def test_create_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "max_retries": 10,
            "base_delay": 2.0,
            "max_delay": 300.0,
        }
        config = create_retry_config_from_dict(config_dict)
        assert config.max_retries == 10
        assert config.base_delay == 2.0
        assert config.max_delay == 300.0


class TestRetryState:
    """Tests for RetryState."""
    
    def test_initial_state(self):
        """Test initial state creation."""
        state = RetryState(message_id="msg-001")
        assert state.message_id == "msg-001"
        assert state.attempt == 0
        assert state.next_delay == 0.0
        assert state.last_error is None
    
    def test_increment(self):
        """Test state increment."""
        state = RetryState(message_id="msg-001")
        new_state = state.increment(delay=2.5, error="Connection failed")
        
        assert new_state.attempt == 1
        assert new_state.next_delay == 2.5
        assert new_state.last_error == "Connection failed"
        assert new_state.total_delay == 2.5


class TestRetryManager:
    """Tests for RetryManager."""
    
    def test_calculate_backoff_no_jitter(self):
        """Test backoff calculation without jitter."""
        config = RetryConfig(jitter=False, base_delay=1.0, exponential_base=2.0, max_delay=100.0)
        manager = RetryManager(config)
        
        assert manager.calculate_backoff(0) == 1.0   # 1 * 2^0
        assert manager.calculate_backoff(1) == 2.0   # 1 * 2^1
        assert manager.calculate_backoff(2) == 4.0   # 1 * 2^2
        assert manager.calculate_backoff(3) == 8.0   # 1 * 2^3
    
    def test_calculate_backoff_max_delay(self):
        """Test backoff respects max_delay."""
        config = RetryConfig(jitter=False, base_delay=1.0, exponential_base=2.0, max_delay=10.0)
        manager = RetryManager(config)
        
        # 2^10 = 1024, but should cap at 10
        assert manager.calculate_backoff(10) == 10.0
    
    def test_calculate_backoff_with_jitter(self):
        """Test backoff calculation with jitter is within bounds."""
        config = RetryConfig(jitter=True, base_delay=1.0, exponential_base=2.0, max_delay=100.0)
        manager = RetryManager(config)
        
        # Run multiple times to test jitter randomness
        for _ in range(100):
            delay = manager.calculate_backoff(2)  # Base delay = 4.0
            assert 0 <= delay <= 4.0
    
    def test_classify_error_transient(self):
        """Test error classification for transient errors."""
        manager = RetryManager()
        
        assert manager.classify_error(Exception("Connection timeout")) == ErrorType.TRANSIENT
        assert manager.classify_error(Exception("Network unavailable")) == ErrorType.TRANSIENT
        assert manager.classify_error(Exception("503 Service Unavailable")) == ErrorType.TRANSIENT
    
    def test_classify_error_permanent(self):
        """Test error classification for permanent errors."""
        manager = RetryManager()
        
        assert manager.classify_error(Exception("Invalid message format")) == ErrorType.PERMANENT
        assert manager.classify_error(Exception("401 Unauthorized")) == ErrorType.PERMANENT
        assert manager.classify_error(Exception("404 Not Found")) == ErrorType.PERMANENT
    
    def test_classify_error_rate_limit(self):
        """Test error classification for rate limit errors."""
        manager = RetryManager()
        
        assert manager.classify_error(Exception("Rate limit exceeded")) == ErrorType.RATE_LIMIT
        assert manager.classify_error(Exception("429 Too Many Requests")) == ErrorType.RATE_LIMIT
    
    def test_should_retry_retryable_error(self):
        """Test should_retry for retryable errors."""
        manager = RetryManager()
        
        assert manager.should_retry(RetryableError("Temporary failure")) is True
        assert manager.should_retry(Exception("Connection timeout")) is True
        assert manager.should_retry(Exception("Rate limit exceeded")) is True
    
    def test_should_retry_permanent_error(self):
        """Test should_retry for permanent errors."""
        manager = RetryManager()
        
        assert manager.should_retry(PermanentError("Invalid format")) is False
        assert manager.should_retry(Exception("401 Unauthorized")) is False
    
    def test_can_retry(self):
        """Test can_retry checks attempt count."""
        config = RetryConfig(max_retries=3)
        manager = RetryManager(config)
        
        assert manager.can_retry("msg-001") is True  # attempt 0
        
        manager.update_state("msg-001")
        assert manager.can_retry("msg-001") is True  # attempt 1
        
        manager.update_state("msg-001")
        assert manager.can_retry("msg-001") is True  # attempt 2
        
        manager.update_state("msg-001")
        assert manager.can_retry("msg-001") is False  # attempt 3 = max
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, sample_message):
        """Test successful execution without retry."""
        manager = RetryManager()
        
        call_count = 0
        
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await manager.execute_with_retry(successful_func, sample_message)
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_eventual_success(self, sample_message):
        """Test eventual success after retries."""
        config = RetryConfig(max_retries=5, jitter=False, base_delay=0.01)
        manager = RetryManager(config)
        
        call_count = 0
        
        async def eventually_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("Temporary failure")
            return "success"
        
        result = await manager.execute_with_retry(eventually_succeed, sample_message)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_max_exceeded(self, sample_message):
        """Test max retries exceeded."""
        config = RetryConfig(max_retries=2, jitter=False, base_delay=0.01)
        manager = RetryManager(config)
        
        async def always_fail():
            raise RetryableError("Always fails")
        
        with pytest.raises(RetryableError, match="Max retries"):
            await manager.execute_with_retry(always_fail, sample_message)


# =============================================================================
# Sync Tests
# =============================================================================

class TestSyncLogEntry:
    """Tests for SyncLogEntry."""
    
    def test_to_ndjson(self):
        """Test NDJSON serialization."""
        entry = SyncLogEntry(
            event=SyncEventType.SEND,
            message_id="msg-001",
            source_agent="autonomous_glm",
            target_agent="claude",
            message_type="AUDIT_COMPLETE",
            status=SyncStatus.SUCCESS,
            attempt=1,
        )
        
        line = entry.to_ndjson()
        data = json.loads(line)
        
        assert data["event"] == "SEND"
        assert data["message_id"] == "msg-001"
        assert data["source_agent"] == "autonomous_glm"
        assert data["attempt"] == 1
    
    def test_from_ndjson(self):
        """Test NDJSON deserialization."""
        line = '{"timestamp":"2025-01-01T00:00:00Z","event":"RETRY","message_id":"msg-001","source_agent":"claude","target_agent":"minimax","message_type":"DISPUTE","status":"pending","attempt":2,"delay_ms":500}'
        
        entry = SyncLogEntry.from_ndjson(line)
        
        assert entry.event == SyncEventType.RETRY
        assert entry.message_id == "msg-001"
        assert entry.attempt == 2
        assert entry.delay_ms == 500


class TestSyncLogger:
    """Tests for SyncLogger."""
    
    def test_log_send(self, temp_log_file, sample_message):
        """Test logging send events."""
        logger = SyncLogger(log_path=temp_log_file)
        logger.log_send(sample_message, status="success")
        
        # Verify file written
        with open(temp_log_file) as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["event"] == "SEND"
        assert data["message_id"] == "test-msg-001"
    
    def test_log_retry(self, temp_log_file, sample_message):
        """Test logging retry events."""
        logger = SyncLogger(log_path=temp_log_file)
        logger.log_retry(sample_message, attempt=2, delay=1.5)
        
        with open(temp_log_file) as f:
            data = json.loads(f.read())
        
        assert data["event"] == "RETRY"
        assert data["attempt"] == 2
        assert data["delay_ms"] == 1500
    
    def test_log_failure(self, temp_log_file, sample_message):
        """Test logging failure events."""
        logger = SyncLogger(log_path=temp_log_file)
        logger.log_failure(sample_message, error="Connection refused", attempt=3)
        
        with open(temp_log_file) as f:
            data = json.loads(f.read())
        
        assert data["event"] == "FAILURE"
        assert data["error"] == "Connection refused"
    
    def test_log_dlq(self, temp_log_file, sample_message):
        """Test logging DLQ events."""
        logger = SyncLogger(log_path=temp_log_file)
        logger.log_dlq(sample_message, error="Max retries exceeded", attempts=5)
        
        with open(temp_log_file) as f:
            data = json.loads(f.read())
        
        assert data["event"] == "DLQ"
        assert data["attempt"] == 5  # Uses "attempt" not "attempts"
    
    def test_get_sync_stats(self, temp_log_file, sample_message):
        """Test statistics tracking."""
        logger = SyncLogger(log_path=temp_log_file)
        
        logger.log_send(sample_message)
        logger.log_send(sample_message)
        logger.log_failure(sample_message, error="Failed")
        
        stats = logger.get_sync_stats()
        
        assert stats.total_sent == 2
        assert stats.total_failed == 1
    
    def test_read_recent_entries(self, temp_log_file, sample_message):
        """Test reading recent entries."""
        logger = SyncLogger(log_path=temp_log_file)
        
        for i in range(5):
            logger.log_send(sample_message)
        
        entries = logger.read_recent_entries(limit=3)
        
        assert len(entries) == 3
    
    def test_thread_safety(self, temp_log_file, sample_message):
        """Test thread-safe logging."""
        logger = SyncLogger(log_path=temp_log_file)
        
        def log_messages(count):
            for i in range(count):
                logger.log_send(sample_message)
        
        threads = [threading.Thread(target=log_messages, args=(10,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        stats = logger.get_sync_stats()
        assert stats.total_sent == 50


# =============================================================================
# Deduplication Tests
# =============================================================================

class TestCacheEntry:
    """Tests for CacheEntry."""
    
    def test_expiration(self):
        """Test entry expiration check."""
        entry = CacheEntry(
            message_id="msg-001",
            processed_at=time.time() - 3600,  # 1 hour ago
            ttl=1800,  # 30 min TTL
        )
        
        assert entry.is_expired() is True
        
        entry2 = CacheEntry(
            message_id="msg-002",
            processed_at=time.time(),
            ttl=3600,
        )
        
        assert entry2.is_expired() is False


class TestDeduplicationCache:
    """Tests for DeduplicationCache."""
    
    def test_is_duplicate(self):
        """Test duplicate detection."""
        cache = DeduplicationCache()
        
        assert cache.is_duplicate("msg-001") is False
        cache.mark_processed("msg-001")
        assert cache.is_duplicate("msg-001") is True
    
    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        cache = DeduplicationCache(default_ttl=1)  # 1 second TTL
        
        cache.mark_processed("msg-001")
        assert cache.is_duplicate("msg-001") is True
        
        time.sleep(1.1)
        assert cache.is_duplicate("msg-001") is False
    
    def test_lru_eviction(self):
        """Test LRU eviction when max size reached."""
        cache = DeduplicationCache(max_size=5)
        
        for i in range(7):
            cache.mark_processed(f"msg-{i}")
        
        # First 2 should be evicted
        assert cache.is_duplicate("msg-0") is False
        assert cache.is_duplicate("msg-1") is False
        
        # Last 5 should still be cached
        for i in range(2, 7):
            assert cache.is_duplicate(f"msg-{i}") is True
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        cache = DeduplicationCache()
        
        cache.is_duplicate("msg-001")  # miss
        cache.mark_processed("msg-001")
        cache.is_duplicate("msg-001")  # hit
        cache.is_duplicate("msg-002")  # miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["hit_rate"] == pytest.approx(1/3, rel=0.01)
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = DeduplicationCache(default_ttl=1)
        
        cache.mark_processed("msg-001")
        cache.mark_processed("msg-002")
        time.sleep(1.1)
        cache.mark_processed("msg-003")  # This one is fresh
        
        removed = cache.cleanup_expired()
        
        assert removed == 2
        assert cache.get_size() == 1


# =============================================================================
# Arbitration Tests
# =============================================================================

class TestArbitrator:
    """Tests for Arbitrator."""
    
    def test_create_dispute(self):
        """Test dispute creation."""
        arbiter = Arbitrator()
        
        dispute = arbiter.create_dispute(
            audit_id="audit-123",
            finding_id="finding-456",
            dispute_reason="Incorrect severity",
            source_agent=AgentType.AUTONOMOUS_GLM,
        )
        
        assert dispute.audit_id == "audit-123"
        assert dispute.finding_id == "finding-456"
        assert dispute.status == DisputeStatus.PENDING
    
    def test_route_to_arbiter(self):
        """Test routing dispute to arbiter."""
        arbiter = Arbitrator()
        
        dispute = arbiter.create_dispute(
            audit_id="audit-123",
            finding_id="finding-456",
            dispute_reason="Test dispute",
            source_agent=AgentType.AUTONOMOUS_GLM,
        )
        
        message = arbiter.route_to_arbiter(dispute)
        
        assert message.message_type == MessageType.DISPUTE
        assert message.target_agent == AgentType.CLAUDE
        assert dispute.status == DisputeStatus.IN_REVIEW
    
    def test_handle_arbiter_response(self):
        """Test handling arbiter response."""
        arbiter = Arbitrator()
        
        dispute = arbiter.create_dispute(
            audit_id="audit-123",
            finding_id="finding-456",
            dispute_reason="Test dispute",
            source_agent=AgentType.AUTONOMOUS_GLM,
        )
        
        # Simulate arbiter response
        response = AgentMessage(
            message_id="response-001",
            source_agent=AgentType.CLAUDE,
            target_agent=AgentType.AUTONOMOUS_GLM,
            message_type=MessageType.DISPUTE,
            payload={
                "dispute_id": dispute.dispute_id,
                "decision": "upheld",
                "rationale": "Finding is accurate",
            },
        )
        
        resolution = arbiter.handle_arbiter_response(response)
        
        assert resolution.status == DisputeStatus.RESOLVED
        assert resolution.decision == "upheld"
        assert dispute.status == DisputeStatus.RESOLVED
    
    def test_escalate_to_human(self):
        """Test escalation to human."""
        arbiter = Arbitrator()
        
        dispute = arbiter.create_dispute(
            audit_id="audit-123",
            finding_id="finding-456",
            dispute_reason="Complex issue",
            source_agent=AgentType.AUTONOMOUS_GLM,
        )
        
        resolution = arbiter.escalate_to_human(
            dispute.dispute_id,
            reason="Requires human judgment",
        )
        
        assert resolution.status == DisputeStatus.ESCALATED
        assert resolution.escalated_to == "human"
    
    def test_get_pending_disputes(self):
        """Test getting pending disputes."""
        arbiter = Arbitrator()
        
        # Create multiple disputes
        arbiter.create_dispute("audit-1", "finding-1", "Reason 1", AgentType.AUTONOMOUS_GLM)
        arbiter.create_dispute("audit-2", "finding-2", "Reason 2", AgentType.AUTONOMOUS_GLM)
        
        pending = arbiter.get_pending_disputes()
        
        assert len(pending) == 2


# =============================================================================
# Escalation Tests
# =============================================================================

class TestEscalationManager:
    """Tests for EscalationManager."""
    
    def test_check_escalation_triggers_design_system(self):
        """Test design system change trigger."""
        manager = EscalationManager()
        
        triggers = manager.check_escalation_triggers(is_design_system_change=True)
        
        assert EscalationTrigger.DESIGN_SYSTEM_CHANGE in triggers
    
    def test_check_escalation_triggers_critical(self):
        """Test critical severity trigger."""
        manager = EscalationManager()
        
        triggers = manager.check_escalation_triggers(severity="CRITICAL")
        
        assert EscalationTrigger.CRITICAL_SEVERITY in triggers
    
    def test_check_escalation_triggers_disputed(self):
        """Test disputed finding trigger."""
        manager = EscalationManager()
        
        triggers = manager.check_escalation_triggers(is_disputed=True)
        
        assert EscalationTrigger.DISPUTED_FINDING in triggers
    
    def test_check_escalation_triggers_subjective(self):
        """Test subjective polish trigger."""
        manager = EscalationManager()
        
        triggers = manager.check_escalation_triggers(is_subjective=True)
        
        assert EscalationTrigger.SUBJECTIVE_POLISH in triggers
    
    def test_escalate_to_human(self, temp_log_file):
        """Test escalation to human."""
        sync_logger = SyncLogger(log_path=temp_log_file)
        manager = EscalationManager(sync_logger=sync_logger)
        
        record, message = manager.escalate_to_human(
            trigger=EscalationTrigger.CRITICAL_SEVERITY,
            reason="Critical accessibility issue",
            related_audit_id="audit-123",
        )
        
        assert record.trigger == EscalationTrigger.CRITICAL_SEVERITY
        assert record.status == EscalationStatus.PENDING
        assert record.blocking is True
        assert message.message_type == MessageType.HUMAN_REQUIRED
    
    def test_resolve_escalation(self, temp_log_file):
        """Test resolving an escalation."""
        sync_logger = SyncLogger(log_path=temp_log_file)
        manager = EscalationManager(sync_logger=sync_logger)
        
        record, _ = manager.escalate_to_human(
            trigger=EscalationTrigger.DESIGN_SYSTEM_CHANGE,
            reason="New token proposal",
        )
        
        resolved = manager.resolve_escalation(
            record.escalation_id,
            resolution="Approved with modifications",
        )
        
        assert resolved.status == EscalationStatus.RESOLVED
        assert resolved.resolution == "Approved with modifications"
    
    def test_get_blocking_escalations(self, temp_log_file):
        """Test getting blocking escalations."""
        sync_logger = SyncLogger(log_path=temp_log_file)
        manager = EscalationManager(sync_logger=sync_logger)
        
        # Create blocking escalation
        manager.escalate_to_human(
            trigger=EscalationTrigger.CRITICAL_SEVERITY,
            reason="Critical issue",
            blocking=True,
        )
        
        # Create non-blocking escalation
        manager.escalate_to_human(
            trigger=EscalationTrigger.SUBJECTIVE_POLISH,
            reason="Minor polish",
            blocking=False,
        )
        
        blocking = manager.get_blocking_escalations()
        
        assert len(blocking) == 1


# =============================================================================
# Dead Letter Queue Tests
# =============================================================================

class TestDeadLetterQueue:
    """Tests for DeadLetterQueue."""
    
    def test_add_to_dlq(self, sample_message):
        """Test adding message to DLQ."""
        dlq = DeadLetterQueue()
        
        entry = dlq.add_to_dlq(
            message=sample_message,
            error="Max retries exceeded",
            attempts=5,
        )
        
        assert entry.error == "Max retries exceeded"
        assert entry.attempts == 5
        assert entry.replayed is False
    
    def test_get_dlq_entries(self, sample_message):
        """Test getting DLQ entries."""
        dlq = DeadLetterQueue()
        
        for i in range(3):
            msg = AgentMessage(
                message_id=f"msg-{i}",
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=AgentType.CLAUDE,
                message_type=MessageType.AUDIT_COMPLETE,
                payload={},
            )
            dlq.add_to_dlq(msg, error=f"Error {i}")
        
        entries = dlq.get_dlq_entries()
        
        assert len(entries) == 3
    
    def test_replay_dlq_entry(self, sample_message):
        """Test marking entry as replayed."""
        dlq = DeadLetterQueue()
        
        entry = dlq.add_to_dlq(sample_message, error="Failed")
        
        result = dlq.replay_dlq_entry(entry.entry_id)
        
        assert result is True
        updated = dlq.get_entry(entry.entry_id)
        assert updated.replayed is True
    
    def test_purge_dlq(self, sample_message):
        """Test purging DLQ entries."""
        dlq = DeadLetterQueue()
        
        for i in range(5):
            msg = AgentMessage(
                message_id=f"msg-{i}",
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=AgentType.CLAUDE,
                message_type=MessageType.AUDIT_COMPLETE,
                payload={},
            )
            dlq.add_to_dlq(msg, error=f"Error {i}")
        
        purged = dlq.purge_dlq()
        
        assert purged == 5
        assert dlq.get_size() == 0
    
    def test_max_size_eviction(self):
        """Test max size eviction."""
        dlq = DeadLetterQueue(max_size=3)
        
        for i in range(5):
            msg = AgentMessage(
                message_id=f"msg-{i}",
                source_agent=AgentType.AUTONOMOUS_GLM,
                target_agent=AgentType.CLAUDE,
                message_type=MessageType.AUDIT_COMPLETE,
                payload={},
            )
            dlq.add_to_dlq(msg, error=f"Error {i}")
        
        assert dlq.get_size() == 3
        
        # First 2 entries should be evicted
        entries = dlq.get_dlq_entries(limit=10)
        message_ids = [e.message.message_id for e in entries]
        assert "msg-0" not in message_ids
        assert "msg-1" not in message_ids
    
    def test_get_stats(self, sample_message):
        """Test getting DLQ statistics."""
        dlq = DeadLetterQueue()
        
        dlq.add_to_dlq(sample_message, error="Error 1")
        
        msg2 = AgentMessage(
            message_id="msg-002",
            source_agent=AgentType.AUTONOMOUS_GLM,
            target_agent=AgentType.MINIMAX,
            message_type=MessageType.DISPUTE,
            payload={},
        )
        dlq.add_to_dlq(msg2, error="Error 2")
        
        stats = dlq.get_stats()
        
        assert stats["total_entries"] == 2
        assert "claude" in stats["by_target_agent"]
        assert "minimax" in stats["by_target_agent"]
    
    def test_persistence(self, temp_dlq_file, sample_message):
        """Test DLQ persistence to disk."""
        # Create DLQ with persistence
        dlq1 = DeadLetterQueue(persist_path=temp_dlq_file)
        entry = dlq1.add_to_dlq(sample_message, error="Test error")
        
        # Create new DLQ instance to load from disk
        dlq2 = DeadLetterQueue(persist_path=temp_dlq_file)
        
        entries = dlq2.get_dlq_entries()
        assert len(entries) == 1
        assert entries[0].message.message_id == "test-msg-001"


# =============================================================================
# Integration Tests
# =============================================================================

class TestReliabilityIntegration:
    """Integration tests for reliability components."""
    
    def test_retry_to_dlq_flow(self, sample_message):
        """Test flow from retry to DLQ."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        retry_manager = RetryManager(config)
        dlq = DeadLetterQueue()
        
        call_count = 0
        
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Always fails")
        
        async def run_test():
            try:
                await retry_manager.execute_with_retry(always_fail, sample_message)
            except RetryableError as e:
                # Add to DLQ on max retries exceeded
                dlq.add_to_dlq(sample_message, error=str(e), attempts=call_count)
        
        asyncio.run(run_test())
        
        assert call_count == 3  # Initial + 2 retries
        assert dlq.get_size() == 1
    
    def test_dedup_with_sync_logging(self, temp_log_file, sample_message):
        """Test deduplication with sync logging."""
        cache = DeduplicationCache()
        logger = SyncLogger(log_path=temp_log_file)
        
        # First send - not duplicate
        if not cache.is_duplicate(sample_message.message_id):
            cache.mark_processed(sample_message.message_id)
            logger.log_send(sample_message)
        
        # Second send - is duplicate
        if not cache.is_duplicate(sample_message.message_id):
            logger.log_send(sample_message)
        
        stats = logger.get_sync_stats()
        assert stats.total_sent == 1  # Only logged once
    
    def test_arbitration_escalation_flow(self, temp_log_file):
        """Test arbitration to escalation flow."""
        sync_logger = SyncLogger(log_path=temp_log_file)
        arbiter = Arbitrator()
        escalation_manager = EscalationManager(sync_logger=sync_logger)
        
        # Create and route dispute
        dispute = arbiter.create_dispute(
            audit_id="audit-123",
            finding_id="finding-456",
            dispute_reason="Critical severity disagreement",
            source_agent=AgentType.AUTONOMOUS_GLM,
            severity=DisputeSeverity.HIGH,
        )
        
        # Arbiter decides to escalate
        resolution = arbiter.escalate_to_human(
            dispute.dispute_id,
            reason="Requires human judgment",
        )
        
        # Escalate via escalation manager
        triggers = escalation_manager.check_escalation_triggers(
            is_disputed=True,
            severity="CRITICAL",
        )
        
        assert EscalationTrigger.DISPUTED_FINDING in triggers
        assert resolution.status == DisputeStatus.ESCALATED
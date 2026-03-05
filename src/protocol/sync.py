"""
Message synchronization logging for agent communication.

Provides thread-safe NDJSON logging to /logs/sync-log.ndjson for
tracking message send, receive, retry, and failure events.
"""

import json
import os
import threading
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.protocol.message import AgentMessage, AgentType, MessageType


class SyncEventType(str, Enum):
    """Types of sync log events."""
    SEND = "SEND"
    RECEIVE = "RECEIVE"
    RETRY = "RETRY"
    FAILURE = "FAILURE"
    DLQ = "DLQ"


class SyncStatus(str, Enum):
    """Status of sync events."""
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"


class SyncLogEntry(BaseModel):
    """A single sync log entry."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event: SyncEventType
    message_id: str
    source_agent: str
    target_agent: str
    message_type: str
    status: SyncStatus
    attempt: int = Field(default=1, ge=1)
    delay_ms: Optional[int] = Field(default=None, description="Delay before retry in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if applicable")
    
    def to_ndjson(self) -> str:
        """Convert to NDJSON line."""
        data = {
            "timestamp": self.timestamp.isoformat() + "Z",
            "event": self.event.value,
            "message_id": self.message_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "message_type": self.message_type,
            "status": self.status.value,
            "attempt": self.attempt,
        }
        if self.delay_ms is not None:
            data["delay_ms"] = self.delay_ms
        if self.error is not None:
            data["error"] = self.error
        return json.dumps(data, separators=(",", ":"))
    
    @classmethod
    def from_ndjson(cls, line: str) -> "SyncLogEntry":
        """Parse from NDJSON line."""
        data = json.loads(line)
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"].rstrip("Z")),
            event=SyncEventType(data["event"]),
            message_id=data["message_id"],
            source_agent=data["source_agent"],
            target_agent=data["target_agent"],
            message_type=data["message_type"],
            status=SyncStatus(data["status"]),
            attempt=data.get("attempt", 1),
            delay_ms=data.get("delay_ms"),
            error=data.get("error"),
        )


class SyncStats(BaseModel):
    """Statistics from sync log."""
    total_sent: int = Field(default=0, ge=0)
    total_received: int = Field(default=0, ge=0)
    total_retried: int = Field(default=0, ge=0)
    total_failed: int = Field(default=0, ge=0)
    total_dlq: int = Field(default=0, ge=0)
    by_agent: dict[str, dict[str, int]] = Field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    by_message_type: dict[str, dict[str, int]] = Field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_sent": self.total_sent,
            "total_received": self.total_received,
            "total_retried": self.total_retried,
            "total_failed": self.total_failed,
            "total_dlq": self.total_dlq,
            "by_agent": {k: dict(v) for k, v in self.by_agent.items()},
            "by_message_type": {k: dict(v) for k, v in self.by_message_type.items()},
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() + "Z" if self.last_error_time else None,
        }


class SyncLogger:
    """
    Thread-safe sync logger for agent messages.
    
    Writes NDJSON entries to /logs/sync-log.ndjson.
    Maintains in-memory statistics for quick access.
    """
    
    DEFAULT_LOG_PATH = "logs/sync-log.ndjson"
    
    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the sync logger.
        
        Args:
            log_path: Path to the NDJSON log file. Defaults to logs/sync-log.ndjson
        """
        self.log_path = Path(log_path or self.DEFAULT_LOG_PATH)
        self._lock = threading.Lock()
        self._stats = SyncStats()
        self._ensure_log_file()
    
    def _ensure_log_file(self) -> None:
        """Ensure log directory and file exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()
    
    def _write_entry(self, entry: SyncLogEntry) -> None:
        """Write a log entry to the file (thread-safe)."""
        with self._lock:
            with open(self.log_path, "a") as f:
                f.write(entry.to_ndjson() + "\n")
            self._update_stats(entry)
    
    def _update_stats(self, entry: SyncLogEntry) -> None:
        """Update in-memory statistics."""
        if entry.event == SyncEventType.SEND:
            self._stats.total_sent += 1
        elif entry.event == SyncEventType.RECEIVE:
            self._stats.total_received += 1
        elif entry.event == SyncEventType.RETRY:
            self._stats.total_retried += 1
        elif entry.event == SyncEventType.FAILURE:
            self._stats.total_failed += 1
            self._stats.last_error = entry.error
            self._stats.last_error_time = entry.timestamp
        elif entry.event == SyncEventType.DLQ:
            self._stats.total_dlq += 1
        
        # Update by_agent stats
        agent_key = f"{entry.source_agent}->{entry.target_agent}"
        self._stats.by_agent[agent_key][entry.event.value] += 1
        
        # Update by_message_type stats
        self._stats.by_message_type[entry.message_type][entry.event.value] += 1
    
    def log_send(
        self,
        message: AgentMessage,
        status: str = "success",
        attempt: int = 1,
    ) -> None:
        """
        Log a message send event.
        
        Args:
            message: The message being sent
            status: Status of the send (success, pending, failed)
            attempt: Attempt number
        """
        entry = SyncLogEntry(
            event=SyncEventType.SEND,
            message_id=message.message_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value,
            message_type=message.message_type.value,
            status=SyncStatus(status),
            attempt=attempt,
        )
        self._write_entry(entry)
    
    def log_receive(
        self,
        message: AgentMessage,
        status: str = "success",
    ) -> None:
        """
        Log a message receive event.
        
        Args:
            message: The message received
            status: Status of the receive
        """
        entry = SyncLogEntry(
            event=SyncEventType.RECEIVE,
            message_id=message.message_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value,
            message_type=message.message_type.value,
            status=SyncStatus(status),
        )
        self._write_entry(entry)
    
    def log_retry(
        self,
        message: AgentMessage,
        attempt: int,
        delay: float,
    ) -> None:
        """
        Log a retry event.
        
        Args:
            message: The message being retried
            attempt: Current attempt number
            delay: Delay before retry in seconds
        """
        entry = SyncLogEntry(
            event=SyncEventType.RETRY,
            message_id=message.message_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value,
            message_type=message.message_type.value,
            status=SyncStatus.PENDING,
            attempt=attempt,
            delay_ms=int(delay * 1000),
        )
        self._write_entry(entry)
    
    def log_failure(
        self,
        message: AgentMessage,
        error: str,
        attempt: int = 1,
    ) -> None:
        """
        Log a failure event.
        
        Args:
            message: The message that failed
            error: Error message
            attempt: Number of attempts made
        """
        entry = SyncLogEntry(
            event=SyncEventType.FAILURE,
            message_id=message.message_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value,
            message_type=message.message_type.value,
            status=SyncStatus.FAILED,
            attempt=attempt,
            error=error,
        )
        self._write_entry(entry)
    
    def log_dlq(
        self,
        message: AgentMessage,
        error: str,
        attempts: int,
    ) -> None:
        """
        Log a dead letter queue event.
        
        Args:
            message: The message added to DLQ
            error: Error that caused the failure
            attempts: Number of retry attempts made
        """
        entry = SyncLogEntry(
            event=SyncEventType.DLQ,
            message_id=message.message_id,
            source_agent=message.source_agent.value,
            target_agent=message.target_agent.value,
            message_type=message.message_type.value,
            status=SyncStatus.FAILED,
            attempt=attempts,
            error=error,
        )
        self._write_entry(entry)
    
    def get_sync_stats(self) -> SyncStats:
        """
        Get current sync statistics.
        
        Returns:
            SyncStats with current counts
        """
        return self._stats
    
    def read_recent_entries(self, limit: int = 100) -> list[SyncLogEntry]:
        """
        Read recent log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of SyncLogEntry objects, most recent last
        """
        entries = []
        with self._lock:
            if not self.log_path.exists():
                return entries
            
            with open(self.log_path, "r") as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(SyncLogEntry.from_ndjson(line))
                        except (json.JSONDecodeError, ValueError):
                            continue
        
        return entries
    
    def clear_stats(self) -> None:
        """Reset in-memory statistics."""
        with self._lock:
            self._stats = SyncStats()
    
    def rotate_log(self, max_size_mb: float = 10.0) -> bool:
        """
        Rotate log file if it exceeds max size.
        
        Args:
            max_size_mb: Maximum file size in megabytes
            
        Returns:
            True if log was rotated
        """
        with self._lock:
            if not self.log_path.exists():
                return False
            
            size_mb = self.log_path.stat().st_size / (1024 * 1024)
            if size_mb < max_size_mb:
                return False
            
            # Rename current log with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            rotated_path = self.log_path.with_suffix(f".{timestamp}.ndjson")
            self.log_path.rename(rotated_path)
            
            # Create new empty log
            self.log_path.touch()
            
            return True


# Module-level logger instance
_sync_logger: Optional[SyncLogger] = None


def get_sync_logger(log_path: Optional[str] = None) -> SyncLogger:
    """
    Get the singleton sync logger instance.
    
    Args:
        log_path: Optional path to log file
        
    Returns:
        SyncLogger instance
    """
    global _sync_logger
    if _sync_logger is None:
        _sync_logger = SyncLogger(log_path)
    return _sync_logger


def reset_sync_logger() -> None:
    """Reset the singleton sync logger (for testing)."""
    global _sync_logger
    _sync_logger = None
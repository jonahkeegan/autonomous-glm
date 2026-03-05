"""
Dead Letter Queue for permanently failed messages.

Stores messages that have exceeded retry limits for later analysis
and potential replay.
"""

import json
import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.protocol.message import AgentMessage, AgentType, MessageType
from src.protocol.sync import SyncLogger, get_sync_logger


class DeadLetterEntry(BaseModel):
    """Entry in the dead letter queue."""
    entry_id: str = Field(default_factory=lambda: str(uuid4()))
    message: AgentMessage
    error: str = Field(..., description="Error that caused the failure")
    attempts: int = Field(default=1, ge=1, description="Number of retry attempts")
    first_error: Optional[str] = Field(default=None, description="Original error message")
    first_failure_at: datetime = Field(default_factory=datetime.utcnow)
    last_failure_at: datetime = Field(default_factory=datetime.utcnow)
    added_to_dlq_at: datetime = Field(default_factory=datetime.utcnow)
    replayed: bool = Field(default=False)
    replayed_at: Optional[datetime] = None
    replay_result: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "message_id": self.message.message_id,
            "source_agent": self.message.source_agent.value,
            "target_agent": self.message.target_agent.value,
            "message_type": self.message.message_type.value,
            "error": self.error,
            "attempts": self.attempts,
            "first_error": self.first_error,
            "first_failure_at": self.first_failure_at.isoformat() + "Z",
            "last_failure_at": self.last_failure_at.isoformat() + "Z",
            "added_to_dlq_at": self.added_to_dlq_at.isoformat() + "Z",
            "replayed": self.replayed,
            "replayed_at": self.replayed_at.isoformat() + "Z" if self.replayed_at else None,
            "replay_result": self.replay_result,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        data = self.to_dict()
        data["message"] = self.message.model_dump()
        return json.dumps(data, default=str)


class DeadLetterQueue:
    """
    Dead Letter Queue for failed messages.
    
    Stores messages that have permanently failed (exceeded retry limits)
    for later analysis, replay, or manual intervention.
    
    Features:
    - In-memory storage with size limits
    - JSON file persistence for durability
    - Replay capability for failed messages
    - Automatic purging of old entries
    """
    
    DEFAULT_MAX_SIZE = 1000
    DEFAULT_PERSIST_PATH = "data/dlq.json"
    
    def __init__(
        self,
        max_size: int = DEFAULT_MAX_SIZE,
        persist_path: Optional[str] = None,
        sync_logger: Optional[SyncLogger] = None,
    ):
        """
        Initialize the dead letter queue.
        
        Args:
            max_size: Maximum number of entries before oldest is evicted
            persist_path: Path to persist DLQ state (None for no persistence)
            sync_logger: Optional sync logger for logging DLQ events
        """
        self.max_size = max_size
        self.persist_path = Path(persist_path) if persist_path else None
        self.sync_logger = sync_logger or get_sync_logger()
        self._queue: OrderedDict[str, DeadLetterEntry] = OrderedDict()
        self._lock = threading.Lock()
        
        # Load persisted state if available
        if self.persist_path:
            self._load_from_disk()
    
    def _load_from_disk(self) -> None:
        """Load DLQ state from disk."""
        if not self.persist_path or not self.persist_path.exists():
            return
        
        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)
            
            for entry_data in data.get("entries", []):
                message = AgentMessage(**entry_data["message"])
                entry = DeadLetterEntry(
                    entry_id=entry_data["entry_id"],
                    message=message,
                    error=entry_data["error"],
                    attempts=entry_data["attempts"],
                    first_error=entry_data.get("first_error"),
                    first_failure_at=datetime.fromisoformat(entry_data["first_failure_at"].rstrip("Z")),
                    last_failure_at=datetime.fromisoformat(entry_data["last_failure_at"].rstrip("Z")),
                    added_to_dlq_at=datetime.fromisoformat(entry_data["added_to_dlq_at"].rstrip("Z")),
                    replayed=entry_data.get("replayed", False),
                    replayed_at=datetime.fromisoformat(entry_data["replayed_at"].rstrip("Z")) if entry_data.get("replayed_at") else None,
                    replay_result=entry_data.get("replay_result"),
                )
                self._queue[entry.entry_id] = entry
        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted file, start fresh
            pass
    
    def _save_to_disk(self) -> None:
        """Persist DLQ state to disk."""
        if not self.persist_path:
            return
        
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "entries": [json.loads(entry.to_json()) for entry in self._queue.values()],
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        
        # Write to temp file then rename for atomicity
        temp_path = self.persist_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        temp_path.rename(self.persist_path)
    
    def add_to_dlq(
        self,
        message: AgentMessage,
        error: str,
        attempts: int = 1,
        first_error: Optional[str] = None,
    ) -> DeadLetterEntry:
        """
        Add a failed message to the dead letter queue.
        
        Args:
            message: The failed message
            error: The error that caused the failure
            attempts: Number of retry attempts made
            first_error: Original error if different from final error
            
        Returns:
            The created DeadLetterEntry
        """
        with self._lock:
            # Check if we need to evict oldest
            while len(self._queue) >= self.max_size:
                self._queue.popitem(last=False)
            
            entry = DeadLetterEntry(
                message=message,
                error=error,
                attempts=attempts,
                first_error=first_error or error,
            )
            
            self._queue[entry.entry_id] = entry
            self._save_to_disk()
            
            # Log to sync logger
            self.sync_logger.log_dlq(message, error, attempts)
            
            return entry
    
    def get_dlq_entries(self, limit: int = 100) -> list[DeadLetterEntry]:
        """
        Get entries from the dead letter queue.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of DeadLetterEntry objects (most recent first)
        """
        with self._lock:
            entries = list(self._queue.values())
            return entries[-limit:][::-1]  # Most recent first
    
    def get_entry(self, entry_id: str) -> Optional[DeadLetterEntry]:
        """
        Get a specific entry by ID.
        
        Args:
            entry_id: The entry ID
            
        Returns:
            DeadLetterEntry if found, None otherwise
        """
        with self._lock:
            return self._queue.get(entry_id)
    
    def replay_dlq_entry(self, entry_id: str) -> bool:
        """
        Mark an entry as replayed (for manual replay tracking).
        
        Note: This doesn't actually resend the message - that's handled
        by the calling code. This just tracks the replay status.
        
        Args:
            entry_id: The entry ID to mark as replayed
            
        Returns:
            True if entry was found and marked
        """
        with self._lock:
            if entry_id not in self._queue:
                return False
            
            entry = self._queue[entry_id]
            entry.replayed = True
            entry.replayed_at = datetime.utcnow()
            entry.replay_result = "replayed"
            
            self._save_to_disk()
            return True
    
    def mark_replay_failed(self, entry_id: str, reason: str) -> bool:
        """
        Mark a replay attempt as failed.
        
        Args:
            entry_id: The entry ID
            reason: Why the replay failed
            
        Returns:
            True if entry was found and updated
        """
        with self._lock:
            if entry_id not in self._queue:
                return False
            
            entry = self._queue[entry_id]
            entry.replay_result = f"failed: {reason}"
            
            self._save_to_disk()
            return True
    
    def remove_entry(self, entry_id: str) -> bool:
        """
        Remove an entry from the queue.
        
        Args:
            entry_id: The entry ID to remove
            
        Returns:
            True if entry was found and removed
        """
        with self._lock:
            if entry_id not in self._queue:
                return False
            
            del self._queue[entry_id]
            self._save_to_disk()
            return True
    
    def purge_dlq(self, before: Optional[datetime] = None) -> int:
        """
        Purge entries from the dead letter queue.
        
        Args:
            before: Purge entries added before this datetime (None for all)
            
        Returns:
            Number of entries purged
        """
        with self._lock:
            if before is None:
                count = len(self._queue)
                self._queue.clear()
            else:
                to_remove = [
                    entry_id for entry_id, entry in self._queue.items()
                    if entry.added_to_dlq_at < before
                ]
                for entry_id in to_remove:
                    del self._queue[entry_id]
                count = len(to_remove)
            
            self._save_to_disk()
            return count
    
    def purge_replayed(self, older_than_hours: int = 24) -> int:
        """
        Purge replayed entries older than threshold.
        
        Args:
            older_than_hours: Purge replayed entries older than this
            
        Returns:
            Number of entries purged
        """
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
            to_remove = [
                entry_id for entry_id, entry in self._queue.items()
                if entry.replayed and entry.replayed_at and entry.replayed_at < cutoff
            ]
            
            for entry_id in to_remove:
                del self._queue[entry_id]
            
            self._save_to_disk()
            return len(to_remove)
    
    def get_size(self) -> int:
        """Get current queue size."""
        with self._lock:
            return len(self._queue)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        with self._lock:
            total = len(self._queue)
            replayed = sum(1 for e in self._queue.values() if e.replayed)
            
            by_agent: dict[str, int] = {}
            by_type: dict[str, int] = {}
            
            for entry in self._queue.values():
                target = entry.message.target_agent.value
                by_agent[target] = by_agent.get(target, 0) + 1
                
                msg_type = entry.message.message_type.value
                by_type[msg_type] = by_type.get(msg_type, 0) + 1
            
            return {
                "total_entries": total,
                "replayed_count": replayed,
                "pending_replay": total - replayed,
                "max_size": self.max_size,
                "by_target_agent": by_agent,
                "by_message_type": by_type,
            }
    
    def get_entries_by_agent(self, target_agent: AgentType) -> list[DeadLetterEntry]:
        """Get all entries for a specific target agent."""
        with self._lock:
            return [
                e for e in self._queue.values()
                if e.message.target_agent == target_agent
            ]
    
    def get_entries_by_type(self, message_type: MessageType) -> list[DeadLetterEntry]:
        """Get all entries for a specific message type."""
        with self._lock:
            return [
                e for e in self._queue.values()
                if e.message.message_type == message_type
            ]


# Module-level DLQ instance
_dlq: Optional[DeadLetterQueue] = None


def get_dead_letter_queue(
    max_size: int = DeadLetterQueue.DEFAULT_MAX_SIZE,
    persist_path: Optional[str] = None,
) -> DeadLetterQueue:
    """
    Get the singleton dead letter queue instance.
    
    Args:
        max_size: Maximum queue size (only used on first call)
        persist_path: Path to persist DLQ (only used on first call)
        
    Returns:
        DeadLetterQueue instance
    """
    global _dlq
    if _dlq is None:
        _dlq = DeadLetterQueue(max_size=max_size, persist_path=persist_path)
    return _dlq


def reset_dead_letter_queue() -> None:
    """Reset the singleton DLQ (for testing)."""
    global _dlq
    _dlq = None


def add_to_dlq(
    message: AgentMessage,
    error: str,
    attempts: int = 1,
) -> DeadLetterEntry:
    """
    Add a failed message to the singleton DLQ.
    
    Args:
        message: The failed message
        error: The error message
        attempts: Number of attempts made
        
    Returns:
        The created DeadLetterEntry
    """
    return get_dead_letter_queue().add_to_dlq(message, error, attempts)
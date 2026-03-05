"""
Message deduplication for idempotent message processing.

Provides an in-memory LRU cache for tracking processed message IDs
to prevent duplicate message processing.
"""

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CacheEntry:
    """Entry in the deduplication cache."""
    message_id: str
    processed_at: float  # Unix timestamp
    ttl: int  # Time-to-live in seconds
    
    @property
    def expires_at(self) -> float:
        """When this entry expires."""
        return self.processed_at + self.ttl
    
    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Check if this entry has expired."""
        current = current_time or time.time()
        return current > self.expires_at


class DeduplicationCache:
    """
    Thread-safe LRU cache for message deduplication.
    
    Uses OrderedDict for O(1) lookups and LRU eviction.
    Supports TTL-based expiration for memory management.
    """
    
    DEFAULT_MAX_SIZE = 10000
    DEFAULT_TTL = 3600  # 1 hour
    
    def __init__(
        self,
        max_size: int = DEFAULT_MAX_SIZE,
        default_ttl: int = DEFAULT_TTL,
    ):
        """
        Initialize the deduplication cache.
        
        Args:
            max_size: Maximum number of entries before LRU eviction
            default_ttl: Default time-to-live in seconds for entries
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._expirations = 0
    
    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if a message ID has already been processed.
        
        Args:
            message_id: The message ID to check
            
        Returns:
            True if the message has been processed (is a duplicate)
        """
        with self._lock:
            # Check if entry exists
            if message_id not in self._cache:
                self._misses += 1
                return False
            
            entry = self._cache[message_id]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[message_id]
                self._expirations += 1
                self._misses += 1
                return False
            
            # Move to end (most recently used)
            self._cache.move_to_end(message_id)
            self._hits += 1
            return True
    
    def mark_processed(
        self,
        message_id: str,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Mark a message as processed.
        
        Args:
            message_id: The message ID to mark
            ttl: Optional TTL override in seconds
        """
        with self._lock:
            current_time = time.time()
            entry_ttl = ttl if ttl is not None else self.default_ttl
            
            # If already exists, update it
            if message_id in self._cache:
                self._cache[message_id] = CacheEntry(
                    message_id=message_id,
                    processed_at=current_time,
                    ttl=entry_ttl,
                )
                self._cache.move_to_end(message_id)
                return
            
            # Check if we need to evict
            while len(self._cache) >= self.max_size:
                # Remove oldest (first) entry
                self._cache.popitem(last=False)
                self._evictions += 1
            
            # Add new entry
            self._cache[message_id] = CacheEntry(
                message_id=message_id,
                processed_at=current_time,
                ttl=entry_ttl,
            )
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_ids = [
                msg_id for msg_id, entry in self._cache.items()
                if entry.is_expired(current_time)
            ]
            
            for msg_id in expired_ids:
                del self._cache[msg_id]
                self._expirations += 1
            
            return len(expired_ids)
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
    
    def get_size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "expirations": self._expirations,
            }
    
    def get_entry(self, message_id: str) -> Optional[CacheEntry]:
        """
        Get a cache entry if it exists and hasn't expired.
        
        Args:
            message_id: The message ID to look up
            
        Returns:
            CacheEntry if found and valid, None otherwise
        """
        with self._lock:
            if message_id not in self._cache:
                return None
            
            entry = self._cache[message_id]
            if entry.is_expired():
                del self._cache[message_id]
                self._expirations += 1
                return None
            
            return entry
    
    def contains(self, message_id: str) -> bool:
        """
        Check if a message ID is in the cache (without counting as hit/miss).
        
        Args:
            message_id: The message ID to check
            
        Returns:
            True if in cache and not expired
        """
        with self._lock:
            if message_id not in self._cache:
                return False
            
            entry = self._cache[message_id]
            if entry.is_expired():
                return False
            
            return True


# Module-level cache instance
_dedup_cache: Optional[DeduplicationCache] = None


def get_dedup_cache(
    max_size: int = DeduplicationCache.DEFAULT_MAX_SIZE,
    ttl: int = DeduplicationCache.DEFAULT_TTL,
) -> DeduplicationCache:
    """
    Get the singleton deduplication cache instance.
    
    Args:
        max_size: Maximum cache size (only used on first call)
        ttl: Default TTL in seconds (only used on first call)
        
    Returns:
        DeduplicationCache instance
    """
    global _dedup_cache
    if _dedup_cache is None:
        _dedup_cache = DeduplicationCache(max_size=max_size, default_ttl=ttl)
    return _dedup_cache


def reset_dedup_cache() -> None:
    """Reset the singleton deduplication cache (for testing)."""
    global _dedup_cache
    _dedup_cache = None


def is_duplicate(message_id: str) -> bool:
    """
    Check if a message ID is a duplicate using the singleton cache.
    
    Args:
        message_id: The message ID to check
        
    Returns:
        True if the message has been processed
    """
    return get_dedup_cache().is_duplicate(message_id)


def mark_processed(message_id: str, ttl: Optional[int] = None) -> None:
    """
    Mark a message as processed using the singleton cache.
    
    Args:
        message_id: The message ID to mark
        ttl: Optional TTL override
    """
    get_dedup_cache().mark_processed(message_id, ttl)
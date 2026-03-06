"""
Event debouncer for watch mode.

Prevents duplicate processing of rapid file system events.
"""

import time
import threading
from pathlib import Path
from typing import Optional

from .models import WatchConfig


class EventDebouncer:
    """Debounces rapid file system events.
    
    Uses time-based debouncing to prevent duplicate processing of
    file events that occur within a configurable window.
    
    Example:
        >>> debouncer = EventDebouncer(window_seconds=2.0)
        >>> 
        >>> # First event should process
        >>> debouncer.should_process(Path("/data/test.png"), "created")
        True
        >>> 
        >>> # Immediate duplicate should be debounced
        >>> debouncer.should_process(Path("/data/test.png"), "created")
        False
        >>> 
        >>> # After window expires, same file can process again
        >>> time.sleep(2.0)
        >>> debouncer.should_process(Path("/data/test.png"), "created")
        True
    """
    
    def __init__(
        self,
        window_seconds: Optional[float] = None,
        config: Optional[WatchConfig] = None,
    ):
        """Initialize debouncer.
        
        Args:
            window_seconds: Debounce window in seconds (default from config)
            config: WatchConfig to use (alternative to window_seconds)
        """
        if config is not None:
            self.window = config.debounce_window_seconds
        elif window_seconds is not None:
            self.window = window_seconds
        else:
            self.window = 2.0  # Default fallback
        
        # Thread-safe storage for seen events: key -> timestamp
        self._seen_events: dict[str, float] = {}
        self._lock = threading.Lock()
    
    def _make_key(self, path: Path, event_type: str) -> str:
        """Create unique key for path and event type.
        
        Args:
            path: File path
            event_type: Event type string
            
        Returns:
            Unique key string
        """
        return f"{str(path)}:{event_type}"
    
    def should_process(self, path: Path, event_type: str) -> bool:
        """Check if event should be processed (not debounced).
        
        Args:
            path: File path that triggered event
            event_type: Event type (e.g., "created", "modified", "moved")
            
        Returns:
            True if event should be processed, False if debounced
        """
        key = self._make_key(path, event_type)
        now = time.time()
        
        with self._lock:
            if key in self._seen_events:
                elapsed = now - self._seen_events[key]
                if elapsed < self.window:
                    # Still within debounce window, skip this event
                    return False
            
            # Record this event
            self._seen_events[key] = now
            return True
    
    def record_event(self, path: Path, event_type: str) -> None:
        """Record an event manually (without checking).
        
        Useful for recording events that were processed externally.
        
        Args:
            path: File path
            event_type: Event type
        """
        key = self._make_key(path, event_type)
        now = time.time()
        
        with self._lock:
            self._seen_events[key] = now
    
    def cleanup_expired(self, max_age: Optional[float] = None) -> int:
        """Remove expired entries from the seen events cache.
        
        Args:
            max_age: Maximum age in seconds (default: 10x debounce window)
            
        Returns:
            Number of entries removed
        """
        if max_age is None:
            max_age = self.window * 10
        
        now = time.time()
        removed = 0
        
        with self._lock:
            expired_keys = [
                key for key, timestamp in self._seen_events.items()
                if now - timestamp > max_age
            ]
            
            for key in expired_keys:
                del self._seen_events[key]
                removed += 1
        
        return removed
    
    def clear(self) -> None:
        """Clear all recorded events."""
        with self._lock:
            self._seen_events.clear()
    
    @property
    def event_count(self) -> int:
        """Get number of tracked events."""
        with self._lock:
            return len(self._seen_events)
    
    def is_recent(self, path: Path, event_type: str) -> bool:
        """Check if an event was seen recently (within debounce window).
        
        Unlike should_process, this doesn't record the event.
        
        Args:
            path: File path
            event_type: Event type
            
        Returns:
            True if event was seen recently, False otherwise
        """
        key = self._make_key(path, event_type)
        now = time.time()
        
        with self._lock:
            if key in self._seen_events:
                elapsed = now - self._seen_events[key]
                return elapsed < self.window
            return False
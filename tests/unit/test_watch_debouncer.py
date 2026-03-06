"""Unit tests for watch mode debouncer."""

import pytest
import time
from pathlib import Path

from src.cli.watch.debouncer import EventDebouncer
from src.cli.watch.models import WatchConfig


class TestEventDebouncer:
    """Tests for EventDebouncer."""
    
    def test_default_window(self):
        """Test default debounce window."""
        debouncer = EventDebouncer()
        assert debouncer.window == 2.0
    
    def test_custom_window(self):
        """Test custom debounce window."""
        debouncer = EventDebouncer(window_seconds=5.0)
        assert debouncer.window == 5.0
    
    def test_config_initialization(self):
        """Test initialization from config."""
        config = WatchConfig(debounce_window_seconds=3.0)
        debouncer = EventDebouncer(config=config)
        assert debouncer.window == 3.0
    
    def test_first_event_processes(self):
        """Test that first event should process."""
        debouncer = EventDebouncer(window_seconds=1.0)
        
        assert debouncer.should_process(Path("/test.png"), "created") is True
    
    def test_duplicate_event_debounced(self):
        """Test that duplicate events within window are debounced."""
        debouncer = EventDebouncer(window_seconds=1.0)
        
        # First event processes
        assert debouncer.should_process(Path("/test.png"), "created") is True
        
        # Immediate duplicate is debounced
        assert debouncer.should_process(Path("/test.png"), "created") is False
    
    def test_different_events_process(self):
        """Test that different events process independently."""
        debouncer = EventDebouncer(window_seconds=1.0)
        
        assert debouncer.should_process(Path("/test.png"), "created") is True
        assert debouncer.should_process(Path("/test.png"), "modified") is True
        assert debouncer.should_process(Path("/other.png"), "created") is True
    
    def test_expired_event_processes(self):
        """Test that events after window expiry process again."""
        debouncer = EventDebouncer(window_seconds=0.1)
        
        # First event processes
        assert debouncer.should_process(Path("/test.png"), "created") is True
        
        # Wait for window to expire
        time.sleep(0.15)
        
        # Same event should now process
        assert debouncer.should_process(Path("/test.png"), "created") is True
    
    def test_record_event(self):
        """Test manual event recording."""
        debouncer = EventDebouncer(window_seconds=1.0)
        
        debouncer.record_event(Path("/test.png"), "created")
        
        # Should now be debounced
        assert debouncer.should_process(Path("/test.png"), "created") is False
    
    def test_is_recent(self):
        """Test is_recent check without recording."""
        debouncer = EventDebouncer(window_seconds=1.0)
        
        # Not recorded yet
        assert debouncer.is_recent(Path("/test.png"), "created") is False
        
        # Record event
        debouncer.record_event(Path("/test.png"), "created")
        
        # Now should be recent
        assert debouncer.is_recent(Path("/test.png"), "created") is True
    
    def test_event_count(self):
        """Test event count tracking."""
        debouncer = EventDebouncer(window_seconds=1.0)
        
        assert debouncer.event_count == 0
        
        debouncer.should_process(Path("/test.png"), "created")
        assert debouncer.event_count == 1
        
        debouncer.should_process(Path("/other.png"), "created")
        assert debouncer.event_count == 2
    
    def test_clear(self):
        """Test clearing all events."""
        debouncer = EventDebouncer(window_seconds=1.0)
        
        debouncer.should_process(Path("/test.png"), "created")
        assert debouncer.event_count == 1
        
        debouncer.clear()
        assert debouncer.event_count == 0
        
        # Should process again after clear
        assert debouncer.should_process(Path("/test.png"), "created") is True
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        debouncer = EventDebouncer(window_seconds=0.1)
        
        # Add some events
        debouncer.should_process(Path("/test1.png"), "created")
        debouncer.should_process(Path("/test2.png"), "created")
        
        assert debouncer.event_count == 2
        
        # Wait for events to expire (default max_age is 10x window)
        time.sleep(0.2)
        
        # Cleanup with small max_age
        removed = debouncer.cleanup_expired(max_age=0.05)
        
        assert removed == 2
        assert debouncer.event_count == 0
    
    def test_thread_safety(self):
        """Test thread-safe operations."""
        import threading
        
        debouncer = EventDebouncer(window_seconds=10.0)
        results = []
        
        def process_events(prefix: str, count: int):
            for i in range(count):
                path = Path(f"/{prefix}_{i}.png")
                result = debouncer.should_process(path, "created")
                results.append(result)
        
        threads = [
            threading.Thread(target=process_events, args=("thread1", 100)),
            threading.Thread(target=process_events, args=("thread2", 100)),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All events should have processed (different paths)
        assert all(results)
        assert debouncer.event_count == 200
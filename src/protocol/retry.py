"""
Exponential backoff retry logic for agent message delivery.

Implements full jitter exponential backoff with configurable parameters
to handle transient failures in agent communication.
"""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel, Field

from src.protocol.message import AgentMessage, MessageAck


T = TypeVar("T")


class RetryableError(Exception):
    """Error that can be retried."""
    pass


class PermanentError(Exception):
    """Error that should not be retried."""
    pass


class ErrorType(str, Enum):
    """Classification of error types for retry decisions."""
    TRANSIENT = "transient"  # Network timeout, temporary unavailable
    RATE_LIMIT = "rate_limit"  # Too many requests
    PERMANENT = "permanent"  # Invalid message, authentication failure
    UNKNOWN = "unknown"  # Unclassified error


@dataclass
class RetryConfig:
    """
    Configuration for exponential backoff retry.
    
    Default values align with PRD requirements:
    - max_delay: 1800s (30 minutes) per PRD
    - Full jitter to prevent thundering herd
    """
    max_retries: int = 5
    base_delay: float = 1.0  # seconds
    max_delay: float = 1800.0  # seconds (30 min per PRD)
    jitter: bool = True
    exponential_base: float = 2.0
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.max_delay <= 0:
            raise ValueError("max_delay must be positive")
        if self.exponential_base <= 1:
            raise ValueError("exponential_base must be greater than 1")


class RetryState(BaseModel):
    """State tracking for a single message's retry attempts."""
    message_id: str = Field(..., description="ID of the message being retried")
    attempt: int = Field(default=0, ge=0, description="Current attempt number")
    next_delay: float = Field(default=0.0, ge=0, description="Delay before next retry")
    last_error: Optional[str] = Field(default=None, description="Last error message")
    last_attempt_time: Optional[datetime] = Field(default=None, description="Time of last attempt")
    total_delay: float = Field(default=0.0, ge=0, description="Total delay accumulated")
    
    def increment(self, delay: float, error: Optional[str] = None) -> "RetryState":
        """Return a new state with incremented attempt."""
        return RetryState(
            message_id=self.message_id,
            attempt=self.attempt + 1,
            next_delay=delay,
            last_error=error,
            last_attempt_time=datetime.utcnow(),
            total_delay=self.total_delay + delay,
        )


class RetryManager:
    """
    Manages retry state and backoff calculations.
    
    Implements full jitter exponential backoff:
    delay = min(max_delay, base_delay * exponential_base^attempt)
    jittered_delay = random(0, delay)
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize with optional config."""
        self.config = config or RetryConfig()
        self._states: dict[str, RetryState] = {}
    
    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate backoff delay for a given attempt number.
        
        Uses full jitter: random value between 0 and calculated delay.
        
        Args:
            attempt: The attempt number (0-indexed)
            
        Returns:
            Delay in seconds before next retry
        """
        # Calculate base exponential delay
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        # Apply full jitter if enabled
        if self.config.jitter:
            delay = random.uniform(0, delay)
        
        return delay
    
    def should_retry(self, error: Exception) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if the error is retryable
        """
        # Permanent errors should never be retried
        if isinstance(error, PermanentError):
            return False
        
        # Retryable errors should be retried
        if isinstance(error, RetryableError):
            return True
        
        # Classify by error type
        error_type = self.classify_error(error)
        return error_type in (ErrorType.TRANSIENT, ErrorType.RATE_LIMIT)
    
    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify an error into a type for retry decision.
        
        Args:
            error: The exception to classify
            
        Returns:
            ErrorType classification
        """
        error_str = str(error).lower()
        
        # Check for rate limit indicators
        rate_limit_indicators = ["rate limit", "too many requests", "429", "throttl"]
        if any(indicator in error_str for indicator in rate_limit_indicators):
            return ErrorType.RATE_LIMIT
        
        # Check for permanent error indicators
        permanent_indicators = [
            "invalid", "unauthorized", "forbidden", "not found",
            "bad request", "schema", "validation", "401", "403", "404", "400"
        ]
        if any(indicator in error_str for indicator in permanent_indicators):
            return ErrorType.PERMANENT
        
        # Check for transient error indicators
        transient_indicators = [
            "timeout", "connection", "network", "unavailable", "503", "502", "500",
            "reset", "broken pipe", "temporarily"
        ]
        if any(indicator in error_str for indicator in transient_indicators):
            return ErrorType.TRANSIENT
        
        return ErrorType.UNKNOWN
    
    def get_state(self, message_id: str) -> RetryState:
        """Get or create retry state for a message."""
        if message_id not in self._states:
            self._states[message_id] = RetryState(message_id=message_id)
        return self._states[message_id]
    
    def update_state(self, message_id: str, error: Optional[str] = None) -> RetryState:
        """
        Update retry state after an attempt.
        
        Args:
            message_id: The message ID
            error: Optional error message from the attempt
            
        Returns:
            Updated RetryState
        """
        state = self.get_state(message_id)
        next_delay = self.calculate_backoff(state.attempt)
        new_state = state.increment(next_delay, error)
        self._states[message_id] = new_state
        return new_state
    
    def can_retry(self, message_id: str) -> bool:
        """
        Check if a message can be retried.
        
        Args:
            message_id: The message ID
            
        Returns:
            True if retries remaining
        """
        state = self.get_state(message_id)
        return state.attempt < self.config.max_retries
    
    def clear_state(self, message_id: str) -> None:
        """Clear retry state for a message."""
        self._states.pop(message_id, None)
    
    async def execute_with_retry(
        self,
        func: Callable[[], T],
        message: AgentMessage,
        on_retry: Optional[Callable[[int, float, Exception], None]] = None,
    ) -> T:
        """
        Execute a function with automatic retry on failure.
        
        Args:
            func: Async function to execute
            message: The message being sent
            on_retry: Optional callback for retry events (attempt, delay, error)
            
        Returns:
            Result of the function
            
        Raises:
            PermanentError: If a permanent error occurs
            RetryableError: If max retries exceeded
        """
        message_id = message.message_id
        
        while True:
            state = self.get_state(message_id)
            
            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = func()
                
                # Success - clear state and return
                self.clear_state(message_id)
                return result
                
            except PermanentError:
                # Don't retry permanent errors
                self.clear_state(message_id)
                raise
                
            except Exception as e:
                # Check if we should retry
                if not self.should_retry(e):
                    self.clear_state(message_id)
                    raise PermanentError(str(e)) from e
                
                # Check if we have retries remaining
                if not self.can_retry(message_id):
                    self.clear_state(message_id)
                    raise RetryableError(
                        f"Max retries ({self.config.max_retries}) exceeded: {e}"
                    ) from e
                
                # Update state and calculate delay
                new_state = self.update_state(message_id, str(e))
                delay = new_state.next_delay
                
                # Call retry callback if provided
                if on_retry:
                    on_retry(new_state.attempt, delay, e)
                
                # Wait before retry
                await asyncio.sleep(delay)


def create_retry_config_from_dict(config: dict[str, Any]) -> RetryConfig:
    """
    Create RetryConfig from a configuration dictionary.
    
    Args:
        config: Dictionary with retry settings
        
    Returns:
        RetryConfig instance
    """
    return RetryConfig(
        max_retries=config.get("max_retries", 5),
        base_delay=config.get("base_delay", 1.0),
        max_delay=config.get("max_delay", 1800.0),
        jitter=config.get("jitter", True),
        exponential_base=config.get("exponential_base", 2.0),
    )
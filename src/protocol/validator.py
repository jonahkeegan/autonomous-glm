"""
Schema validation for agent messages.

Validates messages against JSON schemas in /interfaces/ directory.
"""

import json
from pathlib import Path
from typing import Optional

import jsonschema
from jsonschema import ValidationError as JsonSchemaValidationError

from src.protocol.message import (
    AgentMessage,
    AgentType,
    MessageType,
)


class ValidationError(Exception):
    """Raised when message validation fails."""
    
    def __init__(self, message: str, errors: Optional[list[str]] = None):
        super().__init__(message)
        self.errors = errors or []
    
    def __str__(self) -> str:
        if self.errors:
            return f"{super().__str__()}\nDetails: {'; '.join(self.errors)}"
        return super().__str__()


# Mapping of message types to schema files
MESSAGE_TYPE_TO_SCHEMA = {
    MessageType.AUDIT_COMPLETE: "audit-complete.schema.json",
    MessageType.DESIGN_PROPOSAL: "design-proposal.schema.json",
    MessageType.DISPUTE: "dispute.schema.json",
    MessageType.HUMAN_REQUIRED: "human-required.schema.json",
}


class MessageValidator:
    """
    Validates agent messages against JSON schemas.
    
    Loads schemas from the /interfaces/ directory and caches them for performance.
    """
    
    def __init__(self, schema_dir: Optional[Path] = None):
        """
        Initialize the validator.
        
        Args:
            schema_dir: Directory containing JSON schemas. Defaults to interfaces/
        """
        self.schema_dir = schema_dir or Path("interfaces")
        self._schema_cache: dict[str, dict] = {}
    
    def _load_schema(self, schema_file: str) -> dict:
        """
        Load a JSON schema from disk, with caching.
        
        Args:
            schema_file: Name of the schema file
            
        Returns:
            Parsed JSON schema dict
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If schema file is invalid JSON
        """
        if schema_file in self._schema_cache:
            return self._schema_cache[schema_file]
        
        schema_path = self.schema_dir / schema_file
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, "r") as f:
            schema = json.load(f)
        
        self._schema_cache[schema_file] = schema
        return schema
    
    def _get_schema_for_message_type(self, message_type: MessageType) -> Optional[dict]:
        """
        Get the appropriate schema for a message type.
        
        Args:
            message_type: The type of message to validate
            
        Returns:
            JSON schema dict or None if no schema exists for this type
        """
        schema_file = MESSAGE_TYPE_TO_SCHEMA.get(message_type)
        if schema_file:
            return self._load_schema(schema_file)
        return None
    
    def validate_message(self, message: AgentMessage) -> tuple[bool, list[str]]:
        """
        Validate a message against its schema.
        
        Args:
            message: The message to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []
        
        # Get schema for this message type
        schema = self._get_schema_for_message_type(message.message_type)
        
        if schema is None:
            # No schema for this message type (e.g., HELLO, ACK, READY, ERROR)
            # Validate basic structure only
            return self._validate_basic_structure(message)
        
        # Convert message to dict for schema validation
        message_dict = message.model_dump()
        
        # Convert datetime to ISO string for schema validation
        if "timestamp" in message_dict and message_dict["timestamp"] is not None:
            message_dict["timestamp"] = message_dict["timestamp"].isoformat()
        
        try:
            jsonschema.validate(instance=message_dict, schema=schema)
            return True, []
        except JsonSchemaValidationError as e:
            errors.append(str(e.message))
            # Get path to the error
            if e.path:
                errors.append(f"Path: {'.'.join(str(p) for p in e.path)}")
            return False, errors
    
    def _validate_basic_structure(self, message: AgentMessage) -> tuple[bool, list[str]]:
        """
        Validate basic message structure for types without schemas.
        
        Args:
            message: The message to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []
        
        # Check required fields
        if not message.message_id:
            errors.append("message_id is required")
        
        if not message.source_agent:
            errors.append("source_agent is required")
        
        if not message.target_agent:
            errors.append("target_agent is required")
        
        if not message.message_type:
            errors.append("message_type is required")
        
        if message.payload is None:
            errors.append("payload is required")
        
        return len(errors) == 0, errors
    
    def validate_payload(
        self, 
        message_type: MessageType, 
        payload: dict
    ) -> tuple[bool, list[str]]:
        """
        Validate a payload against its schema.
        
        Args:
            message_type: The type of message this payload is for
            payload: The payload dict to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        schema = self._get_schema_for_message_type(message_type)
        
        if schema is None:
            # No schema for this message type
            return True, []
        
        # Extract payload schema from the message schema
        payload_schema = schema.get("properties", {}).get("payload", {})
        
        if not payload_schema:
            return True, []
        
        try:
            jsonschema.validate(instance=payload, schema=payload_schema)
            return True, []
        except JsonSchemaValidationError as e:
            return False, [str(e.message)]
    
    def validate_source_agent(
        self, 
        message: AgentMessage, 
        expected_source: AgentType
    ) -> bool:
        """
        Validate that a message comes from the expected source.
        
        Args:
            message: The message to validate
            expected_source: The expected source agent
            
        Returns:
            True if source matches, False otherwise
        """
        return message.source_agent == expected_source
    
    def validate_target_agent(
        self, 
        message: AgentMessage, 
        allowed_targets: list[AgentType]
    ) -> bool:
        """
        Validate that a message is targeted to an allowed agent.
        
        Args:
            message: The message to validate
            allowed_targets: List of allowed target agents
            
        Returns:
            True if target is allowed, False otherwise
        """
        return message.target_agent in allowed_targets
    
    def clear_cache(self) -> None:
        """Clear the schema cache."""
        self._schema_cache.clear()


# Convenience functions for quick validation

_default_validator: Optional[MessageValidator] = None


def _get_validator() -> MessageValidator:
    """Get or create the default validator instance."""
    global _default_validator
    if _default_validator is None:
        _default_validator = MessageValidator()
    return _default_validator


def validate_message(message: AgentMessage) -> tuple[bool, list[str]]:
    """
    Validate a message against its schema using the default validator.
    
    Args:
        message: The message to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    return _get_validator().validate_message(message)


def validate_message_schema(message: AgentMessage) -> None:
    """
    Validate a message and raise ValidationError if invalid.
    
    Args:
        message: The message to validate
        
    Raises:
        ValidationError: If validation fails
    """
    is_valid, errors = validate_message(message)
    if not is_valid:
        raise ValidationError(
            f"Message validation failed for {message.message_type}",
            errors=errors
        )
"""
Metadata parser for Autonomous-GLM artifacts.

Handles parsing of JSON and YAML metadata files and associating
metadata with ingested artifacts in the database.
"""

import json
from pathlib import Path
from typing import Optional, Union

import yaml

from .metadata_models import (
    ArtifactMetadata,
    ScreenMetadata,
    FlowMetadata,
    MetadataValidationResult,
    MetadataSource,
    ArtifactType,
)


class MetadataParseError(Exception):
    """Raised when metadata parsing fails."""
    
    def __init__(self, message: str, errors: Optional[list[str]] = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)


def parse_metadata(file_path: str) -> ArtifactMetadata:
    """
    Parse metadata from a JSON or YAML file.
    
    Args:
        file_path: Path to the metadata file
        
    Returns:
        Parsed ArtifactMetadata object
        
    Raises:
        MetadataParseError: If parsing fails
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {file_path}")
    
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        raise MetadataParseError(f"Failed to read file: {e}")
    
    # Determine format from extension
    suffix = path.suffix.lower()
    
    if suffix == ".json":
        return parse_metadata_json(content)
    elif suffix in (".yaml", ".yml"):
        return parse_metadata_yaml(content)
    else:
        # Try JSON first, then YAML
        try:
            return parse_metadata_json(content)
        except MetadataParseError:
            return parse_metadata_yaml(content)


def parse_metadata_json(content: str) -> ArtifactMetadata:
    """
    Parse metadata from JSON string.
    
    Args:
        content: JSON string content
        
    Returns:
        Parsed ArtifactMetadata object
        
    Raises:
        MetadataParseError: If parsing fails
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise MetadataParseError(
            f"Invalid JSON: {e}",
            errors=[f"Line {e.lineno}, column {e.colno}: {e.msg}"]
        )
    
    return parse_metadata_dict(data)


def parse_metadata_yaml(content: str) -> ArtifactMetadata:
    """
    Parse metadata from YAML string.
    
    Args:
        content: YAML string content
        
    Returns:
        Parsed ArtifactMetadata object
        
    Raises:
        MetadataParseError: If parsing fails
    """
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise MetadataParseError(
            f"Invalid YAML: {e}",
            errors=[str(e)]
        )
    
    if not isinstance(data, dict):
        raise MetadataParseError(
            "YAML must contain a mapping at the root level",
            errors=[f"Got {type(data).__name__} instead of dict"]
        )
    
    return parse_metadata_dict(data)


def parse_metadata_dict(data: dict) -> ArtifactMetadata:
    """
    Parse metadata from a dictionary.
    
    Determines the appropriate metadata type based on artifact_type field
    or defaults to base ArtifactMetadata.
    
    Args:
        data: Dictionary containing metadata
        
    Returns:
        Parsed metadata object (ArtifactMetadata, ScreenMetadata, or FlowMetadata)
        
    Raises:
        MetadataParseError: If validation fails
    """
    # Set source to file if not specified
    if "source" not in data:
        data["source"] = MetadataSource.FILE
    
    # Determine metadata type
    artifact_type = data.get("artifact_type", "").lower()
    
    try:
        if artifact_type == "screenshot":
            return ScreenMetadata.model_validate(data)
        elif artifact_type in ("video", "flow"):
            return FlowMetadata.model_validate(data)
        else:
            # Default to base metadata
            return ArtifactMetadata.model_validate(data)
    except Exception as e:
        raise MetadataParseError(
            f"Metadata validation failed: {e}",
            errors=[str(e)]
        )


def validate_metadata(data: dict) -> MetadataValidationResult:
    """
    Validate metadata without raising exceptions.
    
    Args:
        data: Dictionary containing metadata
        
    Returns:
        MetadataValidationResult with validation status
    """
    errors: list[str] = []
    warnings: list[str] = []
    
    # Check for required fields (none required, but warn on empty)
    if not data:
        return MetadataValidationResult(
            valid=True,
            warnings=["Empty metadata provided"],
            metadata=ArtifactMetadata()
        )
    
    # Set source if not specified
    if "source" not in data:
        data["source"] = MetadataSource.FILE
    
    # Determine metadata type
    artifact_type = data.get("artifact_type", "").lower()
    
    try:
        if artifact_type == "screenshot":
            metadata = ScreenMetadata.model_validate(data)
        elif artifact_type in ("video", "flow"):
            metadata = FlowMetadata.model_validate(data)
        else:
            metadata = ArtifactMetadata.model_validate(data)
        
        # Check for potentially useful missing fields
        if not metadata.project:
            warnings.append("No project specified")
        if not metadata.tags:
            warnings.append("No tags specified")
        
        return MetadataValidationResult(
            valid=True,
            warnings=warnings,
            metadata=metadata
        )
    except Exception as e:
        errors.append(str(e))
        return MetadataValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings
        )


def associate_metadata(
    artifact_id: str,
    metadata: ArtifactMetadata,
    artifact_type: ArtifactType,
    db_path: Optional[str] = None
) -> bool:
    """
    Associate metadata with an artifact in the database.
    
    Updates the metadata JSON field of the appropriate entity
    (Screen or Flow) with the provided metadata.
    
    Args:
        artifact_id: ID of the artifact (screen_id or flow_id)
        metadata: Metadata to associate
        artifact_type: Type of artifact
        db_path: Optional database path
        
    Returns:
        True if association was successful
        
    Raises:
        ValueError: If artifact not found or update fails
    """
    from ..db.database import get_connection
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    metadata_json = metadata.model_dump_json()
    
    if artifact_type == ArtifactType.SCREENSHOT:
        # Update Screen entity
        cursor.execute(
            """
            UPDATE screens 
            SET hierarchy = json_set(
                COALESCE(hierarchy, '{}'),
                '$.metadata', json(?)
            )
            WHERE id = ?
            """,
            (metadata_json, artifact_id)
        )
    elif artifact_type in (ArtifactType.VIDEO, ArtifactType.FLOW):
        # Update Flow entity
        cursor.execute(
            """
            UPDATE flows
            SET metadata = json(?)
            WHERE id = ?
            """,
            (metadata_json, artifact_id)
        )
    else:
        raise ValueError(f"Unknown artifact type: {artifact_type}")
    
    if cursor.rowcount == 0:
        conn.rollback()
        raise ValueError(f"Artifact not found: {artifact_id}")
    
    conn.commit()
    return True


def metadata_to_dict(metadata: ArtifactMetadata) -> dict:
    """
    Convert metadata object to dictionary.
    
    Args:
        metadata: Metadata object to convert
        
    Returns:
        Dictionary representation
    """
    return metadata.model_dump(mode="json")


def metadata_to_json(metadata: ArtifactMetadata) -> str:
    """
    Convert metadata object to JSON string.
    
    Args:
        metadata: Metadata object to convert
        
    Returns:
        JSON string representation
    """
    return metadata.model_dump_json()
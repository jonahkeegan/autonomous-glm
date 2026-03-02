"""
Unit tests for metadata parsing and validation.

Tests the metadata models, parser, and validation functions.
"""

import json
import pytest
import tempfile
from pathlib import Path

from src.ingest.metadata_models import (
    ArtifactMetadata,
    ScreenMetadata,
    FlowMetadata,
    MetadataValidationResult,
    MetadataSource,
    ArtifactType,
)
from src.ingest.metadata import (
    parse_metadata,
    parse_metadata_json,
    parse_metadata_yaml,
    parse_metadata_dict,
    validate_metadata,
    metadata_to_dict,
    metadata_to_json,
    MetadataParseError,
)


class TestArtifactMetadata:
    """Tests for base ArtifactMetadata model."""
    
    def test_empty_metadata(self):
        """Can create empty metadata."""
        metadata = ArtifactMetadata()
        
        assert metadata.project is None
        assert metadata.feature is None
        assert metadata.tags == []
        assert metadata.notes is None
        assert metadata.source == MetadataSource.API
    
    def test_full_metadata(self):
        """Can create metadata with all fields."""
        metadata = ArtifactMetadata(
            project="my-project",
            feature="login-flow",
            tags=["auth", "ui"],
            notes="Testing login screen",
            source=MetadataSource.MANUAL,
        )
        
        assert metadata.project == "my-project"
        assert metadata.feature == "login-flow"
        assert metadata.tags == ["auth", "ui"]
        assert metadata.notes == "Testing login screen"
        assert metadata.source == MetadataSource.MANUAL
    
    def test_extra_fields(self):
        """Can include extra custom fields."""
        metadata = ArtifactMetadata(
            extra={
                "browser": "Chrome",
                "viewport": "1920x1080",
            }
        )
        
        assert metadata.extra["browser"] == "Chrome"
        assert metadata.extra["viewport"] == "1920x1080"
    
    def test_project_max_length(self):
        """Project has max length constraint."""
        with pytest.raises(Exception):
            ArtifactMetadata(project="x" * 300)
    
    def test_notes_max_length(self):
        """Notes has max length constraint."""
        with pytest.raises(Exception):
            ArtifactMetadata(notes="x" * 2100)


class TestScreenMetadata:
    """Tests for ScreenMetadata model."""
    
    def test_screenshot_metadata(self):
        """Can create screenshot-specific metadata."""
        metadata = ScreenMetadata(
            project="web-app",
            screen_name="Login Page",
            url="https://example.com/login",
            viewport_width=1920,
            viewport_height=1080,
            device_type="desktop",
            browser="Chrome 120",
            os="macOS",
        )
        
        assert metadata.artifact_type == ArtifactType.SCREENSHOT
        assert metadata.screen_name == "Login Page"
        assert metadata.url == "https://example.com/login"
        assert metadata.viewport_width == 1920
        assert metadata.viewport_height == 1080
    
    def test_viewport_constraints(self):
        """Viewport has valid constraints."""
        # Valid viewport
        metadata = ScreenMetadata(viewport_width=800, viewport_height=600)
        assert metadata.viewport_width == 800
        
        # Invalid viewport (too small)
        with pytest.raises(Exception):
            ScreenMetadata(viewport_width=0)
        
        # Invalid viewport (too large)
        with pytest.raises(Exception):
            ScreenMetadata(viewport_width=20000)


class TestFlowMetadata:
    """Tests for FlowMetadata model."""
    
    def test_flow_metadata(self):
        """Can create flow-specific metadata."""
        metadata = FlowMetadata(
            project="web-app",
            flow_name="User Registration",
            user_journey="New user signs up for account",
            start_url="https://example.com/signup",
            end_url="https://example.com/welcome",
            duration_seconds=45.5,
            interaction_count=12,
        )
        
        assert metadata.artifact_type == ArtifactType.VIDEO
        assert metadata.flow_name == "User Registration"
        assert metadata.duration_seconds == 45.5
        assert metadata.interaction_count == 12
    
    def test_duration_constraints(self):
        """Duration must be non-negative."""
        metadata = FlowMetadata(duration_seconds=0)
        assert metadata.duration_seconds == 0
        
        with pytest.raises(Exception):
            FlowMetadata(duration_seconds=-1)


class TestMetadataSource:
    """Tests for MetadataSource enum."""
    
    def test_source_values(self):
        """Source enum has expected values."""
        assert MetadataSource.FILE == "file"
        assert MetadataSource.API == "api"
        assert MetadataSource.AGENT == "agent"
        assert MetadataSource.MANUAL == "manual"


class TestMetadataValidationResult:
    """Tests for MetadataValidationResult model."""
    
    def test_valid_result(self):
        """Can create valid result."""
        result = MetadataValidationResult(
            valid=True,
            metadata=ArtifactMetadata(),
        )
        
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []
    
    def test_invalid_result(self):
        """Can create invalid result."""
        result = MetadataValidationResult(
            valid=False,
            errors=["Invalid field: project"],
        )
        
        assert result.valid is False
        assert "Invalid field: project" in result.errors


class TestParseMetadataJSON:
    """Tests for JSON metadata parsing."""
    
    def test_parse_valid_json(self):
        """Can parse valid JSON."""
        content = json.dumps({
            "project": "test-project",
            "feature": "login",
            "tags": ["ui", "auth"],
        })
        
        metadata = parse_metadata_json(content)
        
        assert metadata.project == "test-project"
        assert metadata.feature == "login"
        assert metadata.tags == ["ui", "auth"]
    
    def test_parse_invalid_json(self):
        """Invalid JSON raises error."""
        content = "{not valid json"
        
        with pytest.raises(MetadataParseError) as exc_info:
            parse_metadata_json(content)
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_parse_screenshot_type(self):
        """Can parse screenshot-type metadata."""
        content = json.dumps({
            "artifact_type": "screenshot",
            "screen_name": "Dashboard",
            "viewport_width": 1920,
        })
        
        metadata = parse_metadata_json(content)
        
        assert isinstance(metadata, ScreenMetadata)
        assert metadata.screen_name == "Dashboard"
    
    def test_parse_video_type(self):
        """Can parse video-type metadata."""
        content = json.dumps({
            "artifact_type": "video",
            "flow_name": "Checkout",
            "duration_seconds": 30.0,
        })
        
        metadata = parse_metadata_json(content)
        
        assert isinstance(metadata, FlowMetadata)
        assert metadata.flow_name == "Checkout"


class TestParseMetadataYAML:
    """Tests for YAML metadata parsing."""
    
    def test_parse_valid_yaml(self):
        """Can parse valid YAML."""
        content = """
project: test-project
feature: login
tags:
  - ui
  - auth
"""
        
        metadata = parse_metadata_yaml(content)
        
        assert metadata.project == "test-project"
        assert metadata.feature == "login"
        assert metadata.tags == ["ui", "auth"]
    
    def test_parse_invalid_yaml(self):
        """Invalid YAML raises error."""
        content = ": invalid yaml: ["
        
        with pytest.raises(MetadataParseError) as exc_info:
            parse_metadata_yaml(content)
        
        assert "Invalid YAML" in str(exc_info.value)
    
    def test_parse_non_mapping_yaml(self):
        """Non-mapping YAML raises error."""
        content = "- item1\n- item2"
        
        with pytest.raises(MetadataParseError) as exc_info:
            parse_metadata_yaml(content)
        
        assert "mapping" in str(exc_info.value).lower()


class TestParseMetadataFile:
    """Tests for file-based metadata parsing."""
    
    def test_parse_json_file(self, tmp_path):
        """Can parse JSON file."""
        file_path = tmp_path / "metadata.json"
        file_path.write_text(json.dumps({
            "project": "json-project",
            "tags": ["a", "b"],
        }))
        
        metadata = parse_metadata(str(file_path))
        
        assert metadata.project == "json-project"
        assert metadata.tags == ["a", "b"]
    
    def test_parse_yaml_file(self, tmp_path):
        """Can parse YAML file."""
        file_path = tmp_path / "metadata.yaml"
        file_path.write_text("project: yaml-project\ntags:\n  - c\n  - d")
        
        metadata = parse_metadata(str(file_path))
        
        assert metadata.project == "yaml-project"
        assert metadata.tags == ["c", "d"]
    
    def test_parse_nonexistent_file(self):
        """Nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            parse_metadata("/nonexistent/path/metadata.json")


class TestValidateMetadata:
    """Tests for validate_metadata function."""
    
    def test_validate_empty_dict(self):
        """Empty dict returns valid result with warning."""
        result = validate_metadata({})
        
        assert result.valid is True
        assert "Empty" in result.warnings[0]
    
    def test_validate_valid_dict(self):
        """Valid dict returns valid result."""
        result = validate_metadata({
            "project": "test",
            "tags": ["a", "b"],
        })
        
        assert result.valid is True
        assert result.metadata is not None
        assert result.metadata.project == "test"
    
    def test_validate_invalid_dict(self):
        """Invalid dict returns invalid result."""
        result = validate_metadata({
            "project": "x" * 300,  # Too long
        })
        
        assert result.valid is False
        assert len(result.errors) > 0
    
    def test_validate_warnings_missing_project(self):
        """Missing project generates warning."""
        result = validate_metadata({"feature": "test"})
        
        assert result.valid is True
        assert any("project" in w.lower() for w in result.warnings)
    
    def test_validate_warnings_missing_tags(self):
        """Missing tags generates warning."""
        result = validate_metadata({"project": "test"})
        
        assert result.valid is True
        assert any("tags" in w.lower() for w in result.warnings)


class TestMetadataToDict:
    """Tests for metadata_to_dict function."""
    
    def test_to_dict(self):
        """Can convert metadata to dict."""
        metadata = ArtifactMetadata(
            project="test",
            feature="login",
            tags=["a"],
        )
        
        result = metadata_to_dict(metadata)
        
        assert isinstance(result, dict)
        assert result["project"] == "test"
        assert result["feature"] == "login"
        assert result["tags"] == ["a"]
    
    def test_to_dict_includes_source(self):
        """Dict includes source field."""
        metadata = ArtifactMetadata(source=MetadataSource.FILE)
        result = metadata_to_dict(metadata)
        
        assert result["source"] == "file"


class TestMetadataToJSON:
    """Tests for metadata_to_json function."""
    
    def test_to_json(self):
        """Can convert metadata to JSON."""
        metadata = ArtifactMetadata(
            project="test",
            feature="login",
        )
        
        result = metadata_to_json(metadata)
        
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["project"] == "test"
    
    def test_to_json_roundtrip(self):
        """JSON can be parsed back."""
        original = ArtifactMetadata(
            project="test",
            tags=["a", "b", "c"],
            extra={"key": "value"},
        )
        
        json_str = metadata_to_json(original)
        parsed = parse_metadata_json(json_str)
        
        assert parsed.project == original.project
        assert parsed.tags == original.tags
        assert parsed.extra == original.extra
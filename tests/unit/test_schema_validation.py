"""
Unit tests for Autonomous-GLM interface schema validation.

Tests validate all JSON schemas in /interfaces/ directory for:
- Valid JSON format
- Conformance to JSON Schema draft-07
- Required fields present
- Cross-schema consistency (agent names, message types)
"""

import json
from pathlib import Path

import pytest
import jsonschema
from jsonschema import validate, Draft7Validator, exceptions


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def interfaces_dir(project_root):
    """Get the interfaces directory."""
    return project_root / "interfaces"


@pytest.fixture
def schema_files(interfaces_dir):
    """Get list of all schema files."""
    return list(interfaces_dir.glob("*.schema.json"))


@pytest.fixture
def audit_complete_schema(interfaces_dir):
    """Load audit-complete schema."""
    schema_path = interfaces_dir / "audit-complete.schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def design_proposal_schema(interfaces_dir):
    """Load design-proposal schema."""
    schema_path = interfaces_dir / "design-proposal.schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def dispute_schema(interfaces_dir):
    """Load dispute schema."""
    schema_path = interfaces_dir / "dispute.schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def human_required_schema(interfaces_dir):
    """Load human-required schema."""
    schema_path = interfaces_dir / "human-required.schema.json"
    with open(schema_path) as f:
        return json.load(f)


# =============================================================================
# SCHEMA FILE TESTS
# =============================================================================

class TestSchemaFilesExist:
    """Tests for schema file existence."""
    
    def test_interfaces_directory_exists(self, interfaces_dir):
        """Interfaces directory exists."""
        assert interfaces_dir.exists()
        assert interfaces_dir.is_dir()
    
    def test_all_schema_files_exist(self, schema_files):
        """All expected schema files exist."""
        expected_schemas = [
            "audit-complete.schema.json",
            "design-proposal.schema.json",
            "dispute.schema.json",
            "handshake.schema.json",
            "human-required.schema.json",
        ]
        
        found_names = [f.name for f in schema_files]
        
        for expected in expected_schemas:
            assert expected in found_names, f"Missing schema: {expected}"
    
    def test_schema_count(self, schema_files):
        """Expected number of schema files."""
        assert len(schema_files) == 5


class TestSchemaValidJson:
    """Tests for valid JSON format."""
    
    @pytest.mark.parametrize("schema_name", [
        "audit-complete.schema.json",
        "design-proposal.schema.json",
        "dispute.schema.json",
        "human-required.schema.json",
    ])
    def test_schema_is_valid_json(self, interfaces_dir, schema_name):
        """Each schema file is valid JSON."""
        schema_path = interfaces_dir / schema_name
        
        with open(schema_path) as f:
            content = f.read()
        
        # Should not raise JSONDecodeError
        data = json.loads(content)
        assert isinstance(data, dict)
    
    @pytest.mark.parametrize("schema_name", [
        "audit-complete.schema.json",
        "design-proposal.schema.json",
        "dispute.schema.json",
        "human-required.schema.json",
    ])
    def test_schema_has_schema_declaration(self, interfaces_dir, schema_name):
        """Each schema has $schema declaration."""
        schema_path = interfaces_dir / schema_name
        
        with open(schema_path) as f:
            data = json.load(f)
        
        assert "$schema" in data
        assert "draft-07" in data["$schema"]


# =============================================================================
# JSON SCHEMA DRAFT-07 CONFORMANCE
# =============================================================================

class TestSchemaConformance:
    """Tests for JSON Schema draft-07 conformance."""
    
    @pytest.mark.parametrize("schema_name", [
        "audit-complete.schema.json",
        "design-proposal.schema.json",
        "dispute.schema.json",
        "human-required.schema.json",
    ])
    def test_schema_is_valid_draft7(self, interfaces_dir, schema_name):
        """Each schema is valid JSON Schema draft-07."""
        schema_path = interfaces_dir / schema_name
        
        with open(schema_path) as f:
            schema = json.load(f)
        
        # Check that the schema is valid draft-07
        # This will raise an exception if the schema itself is invalid
        Draft7Validator.check_schema(schema)
    
    def test_audit_complete_schema_structure(self, audit_complete_schema):
        """Audit complete schema has correct structure."""
        assert audit_complete_schema["type"] == "object"
        assert "required" in audit_complete_schema
        assert "properties" in audit_complete_schema
        
        # Check required fields
        required = audit_complete_schema["required"]
        assert "message_id" in required
        assert "source_agent" in required
        assert "target_agent" in required
        assert "message_type" in required
        assert "payload" in required
        assert "timestamp" in required
    
    def test_design_proposal_schema_structure(self, design_proposal_schema):
        """Design proposal schema has correct structure."""
        assert design_proposal_schema["type"] == "object"
        
        properties = design_proposal_schema["properties"]
        assert "message_type" in properties
        assert properties["message_type"]["const"] == "DESIGN_PROPOSAL"
    
    def test_dispute_schema_structure(self, dispute_schema):
        """Dispute schema has correct structure."""
        assert dispute_schema["type"] == "object"
        
        properties = dispute_schema["properties"]
        assert "message_type" in properties
        assert properties["message_type"]["const"] == "DISPUTE"
    
    def test_human_required_schema_structure(self, human_required_schema):
        """Human required schema has correct structure."""
        assert human_required_schema["type"] == "object"
        
        properties = human_required_schema["properties"]
        assert "message_type" in properties
        assert properties["message_type"]["const"] == "HUMAN_REQUIRED"
        
        # Target must be human
        assert properties["target_agent"]["const"] == "human"


# =============================================================================
# CROSS-SCHEMA CONSISTENCY
# =============================================================================

class TestCrossSchemaConsistency:
    """Tests for consistency across schemas."""
    
    def test_agent_names_consistent(self, audit_complete_schema, design_proposal_schema, 
                                    dispute_schema, human_required_schema):
        """Agent names are consistent across schemas."""
        # All schemas should support the same agent names in target_agent
        # (except human-required which only targets human)
        
        audit_targets = audit_complete_schema["properties"]["target_agent"]["enum"]
        proposal_targets = design_proposal_schema["properties"]["target_agent"]["enum"]
        dispute_targets = dispute_schema["properties"]["target_agent"]["enum"]
        
        # Core agents should be in all enums
        core_agents = ["claude", "minimax", "codex", "human"]
        
        for agent in core_agents:
            assert agent in audit_targets, f"Missing agent {agent} in audit-complete"
            assert agent in proposal_targets, f"Missing agent {agent} in design-proposal"
    
    def test_source_agent_autonomous_glm(self, audit_complete_schema, design_proposal_schema,
                                         human_required_schema):
        """autonomous-glm is source agent for outbound messages."""
        # These schemas originate from autonomous-glm
        assert audit_complete_schema["properties"]["source_agent"]["const"] == "autonomous-glm"
        assert design_proposal_schema["properties"]["source_agent"]["const"] == "autonomous-glm"
        assert human_required_schema["properties"]["source_agent"]["const"] == "autonomous-glm"
    
    def test_dispute_source_can_be_any_agent(self, dispute_schema):
        """Dispute can originate from any agent."""
        source_enum = dispute_schema["properties"]["source_agent"]["enum"]
        
        expected_sources = ["autonomous-glm", "claude", "minimax", "codex"]
        for source in expected_sources:
            assert source in source_enum
    
    def test_message_types_unique(self, audit_complete_schema, design_proposal_schema,
                                  dispute_schema, human_required_schema):
        """Each schema has unique message type."""
        message_types = [
            audit_complete_schema["properties"]["message_type"]["const"],
            design_proposal_schema["properties"]["message_type"]["const"],
            dispute_schema["properties"]["message_type"]["const"],
            human_required_schema["properties"]["message_type"]["const"],
        ]
        
        # All message types should be unique
        assert len(message_types) == len(set(message_types))
    
    def test_timestamp_format_consistent(self, audit_complete_schema, design_proposal_schema,
                                         dispute_schema, human_required_schema):
        """Timestamp format is consistent across schemas."""
        schemas = [
            audit_complete_schema,
            design_proposal_schema,
            dispute_schema,
            human_required_schema,
        ]
        
        for schema in schemas:
            timestamp = schema["properties"]["timestamp"]
            assert timestamp["type"] == "string"
            assert timestamp["format"] == "date-time"
    
    def test_requires_response_field(self, audit_complete_schema, design_proposal_schema,
                                     dispute_schema, human_required_schema):
        """requires_response field exists in all schemas."""
        schemas = [
            audit_complete_schema,
            design_proposal_schema,
            dispute_schema,
            human_required_schema,
        ]
        
        for schema in schemas:
            assert "requires_response" in schema["properties"]
            assert schema["properties"]["requires_response"]["type"] == "boolean"


# =============================================================================
# PAYLOAD VALIDATION
# =============================================================================

class TestPayloadValidation:
    """Tests for payload structure validation."""
    
    def test_audit_complete_payload_required_fields(self, audit_complete_schema):
        """Audit complete payload has required fields."""
        payload = audit_complete_schema["properties"]["payload"]
        required = payload["required"]
        
        assert "artifact_id" in required
        assert "audit_id" in required
        assert "findings_count" in required
        assert "phases" in required
    
    def test_design_proposal_payload_required_fields(self, design_proposal_schema):
        """Design proposal payload has required fields."""
        payload = design_proposal_schema["properties"]["payload"]
        required = payload["required"]
        
        assert "proposal_id" in required
        assert "proposal_type" in required
        assert "changes" in required
        assert "human_approval_required" in required
    
    def test_dispute_payload_required_fields(self, dispute_schema):
        """Dispute payload has required fields."""
        payload = dispute_schema["properties"]["payload"]
        required = payload["required"]
        
        assert "dispute_id" in required
        assert "audit_id" in required
        assert "finding_id" in required
        assert "dispute_reason" in required
    
    def test_human_required_payload_required_fields(self, human_required_schema):
        """Human required payload has required fields."""
        payload = human_required_schema["properties"]["payload"]
        required = payload["required"]
        
        assert "review_type" in required
        assert "reason" in required
        assert "blocking" in required
    
    def test_phases_enum_values(self, audit_complete_schema):
        """Phases enum has expected values."""
        phases_items = audit_complete_schema["properties"]["payload"]["properties"]["phases"]["items"]
        phases_enum = phases_items["enum"]
        
        assert "Critical" in phases_enum
        assert "Refinement" in phases_enum
        assert "Polish" in phases_enum
    
    def test_proposal_type_enum_values(self, design_proposal_schema):
        """Proposal type enum has expected values."""
        proposal_type = design_proposal_schema["properties"]["payload"]["properties"]["proposal_type"]
        enum_values = proposal_type["enum"]
        
        expected_types = [
            "token_addition",
            "token_modification",
            "component_addition",
            "component_modification",
            "standard_update",
        ]
        
        for expected in expected_types:
            assert expected in enum_values
    
    def test_review_type_enum_values(self, human_required_schema):
        """Review type enum has expected values."""
        review_type = human_required_schema["properties"]["payload"]["properties"]["review_type"]
        enum_values = review_type["enum"]
        
        expected_types = [
            "design_system_change",
            "disputed_finding",
            "critical_severity",
            "subjective_polish",
            "complex_aria",
            "novel_component",
            "cross_agent_impact",
        ]
        
        for expected in expected_types:
            assert expected in enum_values


# =============================================================================
# SCHEMA VALIDATION EXAMPLES
# =============================================================================

class TestSchemaValidationExamples:
    """Test that schemas validate example messages correctly."""
    
    def test_valid_audit_complete_message(self, audit_complete_schema):
        """Valid audit complete message passes validation."""
        message = {
            "message_id": "550e8400-e29b-41d4-a716-446655440000",
            "source_agent": "autonomous-glm",
            "target_agent": "claude",
            "message_type": "AUDIT_COMPLETE",
            "payload": {
                "artifact_id": "550e8400-e29b-41d4-a716-446655440001",
                "audit_id": "550e8400-e29b-41d4-a716-446655440002",
                "findings_count": 5,
                "critical_count": 1,
                "phases": ["Critical", "Refinement"],
                "report_path": "/output/reports/audit-001.md"
            },
            "timestamp": "2026-03-01T12:00:00Z",
            "requires_response": False
        }
        
        # Should not raise exception
        validate(instance=message, schema=audit_complete_schema)
    
    def test_invalid_audit_complete_missing_required(self, audit_complete_schema):
        """Invalid audit complete message fails validation."""
        message = {
            "message_id": "550e8400-e29b-41d4-a716-446655440000",
            "source_agent": "autonomous-glm",
            # Missing target_agent
            "message_type": "AUDIT_COMPLETE",
            "payload": {
                "artifact_id": "550e8400-e29b-41d4-a716-446655440001",
                "audit_id": "550e8400-e29b-41d4-a716-446655440002",
                "findings_count": 5,
                "phases": ["Critical"]
            },
            "timestamp": "2026-03-01T12:00:00Z"
        }
        
        with pytest.raises(exceptions.ValidationError):
            validate(instance=message, schema=audit_complete_schema)
    
    def test_valid_human_required_message(self, human_required_schema):
        """Valid human required message passes validation."""
        message = {
            "message_id": "550e8400-e29b-41d4-a716-446655440000",
            "source_agent": "autonomous-glm",
            "target_agent": "human",
            "message_type": "HUMAN_REQUIRED",
            "payload": {
                "review_type": "design_system_change",
                "reason": "Adding new primary color token requires human approval",
                "blocking": True,
                "options": [
                    {
                        "label": "Approve",
                        "description": "Accept the proposed token",
                        "action": "approve"
                    }
                ]
            },
            "timestamp": "2026-03-01T12:00:00Z",
            "requires_response": True
        }
        
        # Should not raise exception
        validate(instance=message, schema=human_required_schema)
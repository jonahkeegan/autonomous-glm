"""
JSON output generation for agent consumption.

Provides generators for creating JSON payloads from audit results,
implementation plans, and design system proposals. Validates output
against interface schemas for agent compatibility.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

# Schema validation is optional - gracefully handle missing jsonschema
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# =============================================================================
# SCHEMA PATHS
# =============================================================================

INTERFACE_DIR = Path(__file__).parent.parent.parent / "interfaces"

AUDIT_COMPLETE_SCHEMA_PATH = INTERFACE_DIR / "audit-complete.schema.json"
DESIGN_PROPOSAL_SCHEMA_PATH = INTERFACE_DIR / "design-proposal.schema.json"


# =============================================================================
# JSON GENERATOR
# =============================================================================

class JsonGenerator:
    """Generator for JSON output consumed by other agents.
    
    Creates JSON payloads that validate against interface schemas.
    Provides methods for generating agent-compatible messages and
    structured data exports.
    """
    
    def __init__(
        self,
        validate_schemas: bool = True,
        schema_dir: Optional[Path] = None,
    ):
        """Initialize the JSON generator.
        
        Args:
            validate_schemas: Whether to validate against interface schemas
            schema_dir: Optional override for interface schema directory
        """
        self.validate_schemas = validate_schemas and HAS_JSONSCHEMA
        self.schema_dir = schema_dir or INTERFACE_DIR
        self._schemas: dict[str, dict] = {}
        
        if self.validate_schemas:
            self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load JSON schemas for validation."""
        schemas_to_load = [
            ("audit_complete", AUDIT_COMPLETE_SCHEMA_PATH),
            ("design_proposal", DESIGN_PROPOSAL_SCHEMA_PATH),
        ]
        
        for name, path in schemas_to_load:
            if path.exists():
                with open(path, "r") as f:
                    self._schemas[name] = json.load(f)
    
    def _validate_against_schema(
        self,
        data: dict[str, Any],
        schema_name: str
    ) -> tuple[bool, Optional[str]]:
        """Validate data against a loaded schema.
        
        Args:
            data: Data to validate
            schema_name: Name of schema to validate against
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.validate_schemas:
            return True, None
        
        schema = self._schemas.get(schema_name)
        if not schema:
            return True, f"Schema '{schema_name}' not loaded"
        
        try:
            jsonschema.validate(data, schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, str(e)
        except jsonschema.SchemaError as e:
            return False, f"Schema error: {e}"
    
    # =========================================================================
    # AGENT PAYLOAD GENERATION
    # =========================================================================
    
    def generate_agent_payload(
        self,
        plan: Any,
        target_agent: str = "claude",
        message_type: str = "AUDIT_COMPLETE",
    ) -> dict[str, Any]:
        """Generate a complete agent message payload.
        
        Creates a message in the format defined by the agent communication
        protocol (AGENTS.md) that can be sent to other agents.
        
        Args:
            plan: Plan object with phases and summary
            target_agent: Target agent (claude, minimax, codex, human)
            message_type: Message type (AUDIT_COMPLETE, DESIGN_PROPOSAL, etc.)
        
        Returns:
            Dict containing the agent message payload
        """
        message_id = str(uuid4())
        timestamp = datetime.now().isoformat()
        
        # Extract payload data from plan
        payload = {
            "artifact_id": getattr(plan, "screen_id", "unknown"),
            "audit_id": getattr(plan, "audit_session_id", "unknown"),
            "findings_count": 0,
            "phases": [],
        }
        
        # Get findings count and phases from plan
        if hasattr(plan, "phases"):
            phases_with_findings = []
            total_findings = 0
            
            for phase in plan.phases:
                action_count = len(getattr(phase, "actions", []))
                total_findings += action_count
                if action_count > 0:
                    phase_name = phase.phase_type.value.title()
                    phases_with_findings.append(phase_name)
            
            payload["findings_count"] = total_findings
            payload["phases"] = phases_with_findings
        
        # Get critical count from summary
        if hasattr(plan, "summary") and plan.summary:
            payload["critical_count"] = getattr(plan.summary, "critical_count", 0)
        
        # Build complete message
        message = {
            "message_id": message_id,
            "source_agent": "autonomous-glm",
            "target_agent": target_agent,
            "message_type": message_type,
            "payload": payload,
            "timestamp": timestamp,
            "requires_response": message_type == "DESIGN_PROPOSAL",
        }
        
        return message
    
    def generate_design_proposal_payload(
        self,
        proposal: Any,
        target_agent: str = "claude",
    ) -> dict[str, Any]:
        """Generate a design proposal message payload.
        
        Creates a DESIGN_PROPOSAL message that validates against
        interfaces/design-proposal.schema.json.
        
        Args:
            proposal: DesignSystemProposal object
            target_agent: Target agent (claude, minimax, codex, human)
        
        Returns:
            Dict containing the design proposal message
        """
        message_id = str(uuid4())
        timestamp = datetime.now().isoformat()
        
        # Build changes list
        changes = []
        
        # Add token proposals as changes
        for tp in getattr(proposal, "token_proposals", []):
            changes.append({
                "target_file": "design_system/tokens.md",
                "change_type": "add",
                "old_value": "",
                "new_value": f"{tp.token_name}: {tp.proposed_value}",
                "rationale": tp.rationale,
            })
        
        # Add component proposals as changes
        for cp in getattr(proposal, "component_proposals", []):
            changes.append({
                "target_file": "design_system/components.md",
                "change_type": "add",
                "old_value": "",
                "new_value": f"{cp.component_type}-{cp.variant_name}",
                "rationale": cp.rationale,
            })
        
        # Determine proposal type
        proposal_type = "token_addition"
        if getattr(proposal, "component_proposals", None):
            if getattr(proposal, "token_proposals", None):
                proposal_type = "token_addition"  # Default to first
            else:
                proposal_type = "component_addition"
        
        # Build payload
        payload = {
            "proposal_id": str(getattr(proposal, "id", uuid4())),
            "proposal_type": proposal_type,
            "changes": changes,
            "human_approval_required": True,
        }
        
        # Add optional fields
        audit_source = getattr(proposal, "audit_session_id", None)
        if audit_source:
            payload["audit_source"] = audit_source
        
        affected = set()
        for tp in getattr(proposal, "token_proposals", []):
            affected.update(getattr(tp, "affected_screens", []))
        for cp in getattr(proposal, "component_proposals", []):
            affected.update(getattr(cp, "affected_screens", []))
        
        if affected:
            payload["affected_components"] = list(affected)
        
        # Build complete message
        message = {
            "message_id": message_id,
            "source_agent": "autonomous-glm",
            "target_agent": target_agent,
            "message_type": "DESIGN_PROPOSAL",
            "payload": payload,
            "timestamp": timestamp,
            "requires_response": True,
        }
        
        # Validate against schema
        is_valid, error = self._validate_against_schema(message, "design_proposal")
        if not is_valid:
            # Log warning but don't fail
            message["_validation_warning"] = error
        
        return message
    
    # =========================================================================
    # DATA EXPORT METHODS
    # =========================================================================
    
    def generate_findings_json(
        self,
        findings: list[Any]
    ) -> list[dict[str, Any]]:
        """Generate JSON array from audit findings.
        
        Args:
            findings: List of AuditFindingCreate objects
        
        Returns:
            List of finding dictionaries
        """
        result = []
        
        for finding in findings:
            if hasattr(finding, "model_dump"):
                finding_dict = finding.model_dump()
            else:
                finding_dict = dict(finding)
            
            # Ensure consistent structure
            result.append({
                "id": finding_dict.get("id", str(uuid4())),
                "entity_type": finding_dict.get("entity_type", "Screen"),
                "entity_id": finding_dict.get("entity_id", "unknown"),
                "dimension": finding_dict.get("dimension", "unknown"),
                "issue": finding_dict.get("issue", ""),
                "rationale": finding_dict.get("rationale"),
                "severity": finding_dict.get("severity", "medium"),
                "standards_refs": finding_dict.get("standards_refs", []),
                "jobs_filtered": finding_dict.get("jobs_filtered", False),
            })
        
        return result
    
    def generate_instructions_json(
        self,
        instructions: list[Any]
    ) -> list[dict[str, Any]]:
        """Generate JSON array from implementation instructions.
        
        Args:
            instructions: List of ImplementationInstruction objects
        
        Returns:
            List of instruction dictionaries
        """
        result = []
        
        for i, instruction in enumerate(instructions, 1):
            if hasattr(instruction, "model_dump"):
                inst_dict = instruction.model_dump()
            else:
                inst_dict = dict(instruction)
            
            # Ensure consistent structure
            result.append({
                "sequence": i,
                "target_file": inst_dict.get("target_file", "UNKNOWN"),
                "target_entity": inst_dict.get("component", {}).get("name", "unknown"),
                "property": inst_dict.get("property", ""),
                "old_value": inst_dict.get("old_value", ""),
                "new_value": inst_dict.get("new_value", ""),
                "description": inst_dict.get("description", ""),
                "rationale": inst_dict.get("rationale"),
                "confidence": inst_dict.get("confidence", 0.0),
                "phase": inst_dict.get("phase", "refinement"),
                "issue_type": inst_dict.get("issue_type", "generic"),
                "requires_inspection": inst_dict.get("requires_inspection", False),
            })
        
        return result
    
    def generate_proposals_json(
        self,
        proposals: Any
    ) -> dict[str, Any]:
        """Generate JSON from design system proposals.
        
        Args:
            proposals: DesignSystemProposal object
        
        Returns:
            Dict containing proposal data
        """
        if hasattr(proposals, "to_json_dict"):
            return proposals.to_json_dict()
        
        if hasattr(proposals, "model_dump"):
            return proposals.model_dump()
        
        return dict(proposals)
    
    def generate_full_report_json(
        self,
        report: Any
    ) -> dict[str, Any]:
        """Generate complete JSON from a FullReport.
        
        Args:
            report: FullReport object
        
        Returns:
            Dict containing the full report data
        """
        if hasattr(report, "to_json_dict"):
            return report.to_json_dict()
        
        if hasattr(report, "model_dump"):
            return report.model_dump()
        
        return dict(report)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_agent_payload(plan: Any, **kwargs) -> dict[str, Any]:
    """Generate agent message payload from a Plan.
    
    Args:
        plan: Plan object
        **kwargs: Additional arguments for JsonGenerator
    
    Returns:
        Dict containing the agent message
    """
    generator = JsonGenerator(**kwargs)
    return generator.generate_agent_payload(plan)


def generate_findings_json(findings: list[Any]) -> list[dict[str, Any]]:
    """Generate JSON from findings list.
    
    Args:
        findings: List of findings
    
    Returns:
        List of finding dictionaries
    """
    generator = JsonGenerator()
    return generator.generate_findings_json(findings)


def generate_instructions_json(
    instructions: list[Any]
) -> list[dict[str, Any]]:
    """Generate JSON from instructions list.
    
    Args:
        instructions: List of instructions
    
    Returns:
        List of instruction dictionaries
    """
    generator = JsonGenerator()
    return generator.generate_instructions_json(instructions)


def generate_proposals_json(proposals: Any) -> dict[str, Any]:
    """Generate JSON from design system proposals.
    
    Args:
        proposals: DesignSystemProposal object
    
    Returns:
        Dict containing proposals
    """
    generator = JsonGenerator()
    return generator.generate_proposals_json(proposals)


def validate_agent_message(message: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate an agent message against interface schemas.
    
    Args:
        message: Message dict to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not HAS_JSONSCHEMA:
        return True, "jsonschema not installed - skipping validation"
    
    generator = JsonGenerator(validate_schemas=True)
    
    message_type = message.get("message_type", "")
    
    if message_type == "AUDIT_COMPLETE":
        return generator._validate_against_schema(message, "audit_complete")
    elif message_type == "DESIGN_PROPOSAL":
        return generator._validate_against_schema(message, "design_proposal")
    else:
        return True, f"No schema for message type: {message_type}"
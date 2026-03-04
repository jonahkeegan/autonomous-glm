"""
Instruction formatter for transforming audit findings into executable instructions.

Main formatting logic that converts AuditFindingCreate objects into
ImplementationInstruction objects with actionable, unambiguous guidance.
"""

from typing import Any, Optional

from src.audit.models import AuditFindingCreate, AuditDimension
from src.db.models import EntityType, Severity
from src.plan.instruction_models import (
    ComponentInfo,
    ImplementationInstruction,
    InstructionResult,
    BatchInstructionResult,
    IssueType,
    PropertyChange,
    ValidationResult,
)
from src.plan.templates import InstructionTemplateRegistry, get_default_registry
from src.plan.models import Plan, PlanActionCreate


# =============================================================================
# COMPONENT MAPPING
# =============================================================================

def map_to_component(
    finding: AuditFindingCreate,
    component_registry: Optional[dict[str, Any]] = None
) -> ComponentInfo:
    """Map a finding to component information.
    
    Uses entity_id from the finding to look up component details.
    Falls back to placeholder info if component data unavailable.
    
    Args:
        finding: Audit finding with entity_id
        component_registry: Optional dict mapping entity_id to component data
        
    Returns:
        ComponentInfo for the target component
    """
    entity_id = finding.entity_id
    entity_type = finding.entity_type
    
    # Try to get component data from registry
    component_data = None
    if component_registry and entity_id in component_registry:
        component_data = component_registry[entity_id]
    
    if component_data:
        return ComponentInfo(
            component_id=entity_id,
            component_type=component_data.get("type", entity_type.value),
            bounding_box=component_data.get("bounding_box"),
            selector=component_data.get("selector"),
        )
    
    # Fallback: use entity type as component type
    return ComponentInfo(
        component_id=entity_id,
        component_type=entity_type.value,
        bounding_box=None,
        selector=None,
    )


def determine_file_path(
    screen_id: Optional[str] = None,
    screen_metadata: Optional[dict] = None
) -> tuple[str, bool]:
    """Determine file path for an instruction.
    
    Attempts to get file path from screen metadata. Returns placeholder
    if path cannot be determined.
    
    Args:
        screen_id: Screen identifier
        screen_metadata: Optional metadata dict with file_path key
        
    Returns:
        Tuple of (file_path, is_placeholder)
    """
    # Try to get from metadata
    if screen_metadata and "file_path" in screen_metadata:
        return screen_metadata["file_path"], False
    
    # Try to construct from screen_id
    if screen_id:
        # Check if screen_id looks like a path
        if "/" in screen_id or "\\" in screen_id:
            return screen_id, False
        
        # Use screen_id as component reference
        return f"UNKNOWN_FILE (screen: {screen_id})", True
    
    # Ultimate fallback
    return "UNKNOWN_FILE", True


# =============================================================================
# CHANGE GENERATION
# =============================================================================

def generate_changes(
    finding: AuditFindingCreate,
    issue_type: IssueType
) -> list[PropertyChange]:
    """Generate property changes from finding metadata.
    
    Extracts change information from finding.metadata or generates
    sensible defaults based on issue type.
    
    Args:
        finding: Source audit finding
        issue_type: Categorized issue type
        
    Returns:
        List of PropertyChange objects
    """
    changes = []
    metadata = finding.metadata or {}
    
    # Check for explicit changes in metadata
    if "changes" in metadata:
        for change in metadata["changes"]:
            changes.append(PropertyChange(
                property_name=change.get("property", "style"),
                old_value=change.get("old"),
                new_value=change.get("new", "REQUIRES_INSPECTION"),
                confidence=change.get("confidence", 1.0),
                requires_inspection=change.get("old") is None,
            ))
        return changes
    
    # Check for single property change in metadata
    if "property" in metadata:
        changes.append(PropertyChange(
            property_name=metadata["property"],
            old_value=metadata.get("old_value"),
            new_value=metadata.get("new_value", "REQUIRES_INSPECTION"),
            confidence=metadata.get("confidence", 1.0),
            requires_inspection=metadata.get("old_value") is None,
        ))
        return changes
    
    # Generate changes based on issue type
    if issue_type == IssueType.SPACING:
        changes.append(_generate_spacing_change(finding))
    elif issue_type == IssueType.COLOR_CONTRAST:
        changes.append(_generate_color_change(finding))
    elif issue_type == IssueType.TYPOGRAPHY:
        changes.append(_generate_typography_change(finding))
    elif issue_type == IssueType.ALIGNMENT:
        changes.append(_generate_alignment_change(finding))
    elif issue_type == IssueType.ACCESSIBILITY:
        changes.extend(_generate_accessibility_changes(finding))
    else:
        # Generic change
        changes.append(PropertyChange(
            property_name="style",
            old_value=None,
            new_value=_extract_proposed_value(finding),
            confidence=0.7,
            requires_inspection=True,
        ))
    
    return changes if changes else [
        PropertyChange(
            property_name="style",
            old_value=None,
            new_value="REQUIRES_INSPECTION",
            confidence=0.5,
            requires_inspection=True,
        )
    ]


def _generate_spacing_change(finding: AuditFindingCreate) -> PropertyChange:
    """Generate spacing-related property change."""
    metadata = finding.metadata or {}
    
    return PropertyChange(
        property_name=metadata.get("property", "margin"),
        old_value=metadata.get("current_spacing"),
        new_value=metadata.get("recommended_spacing", "16px"),
        confidence=metadata.get("confidence", 0.9),
        requires_inspection=metadata.get("current_spacing") is None,
    )


def _generate_color_change(finding: AuditFindingCreate) -> PropertyChange:
    """Generate color/contrast property change."""
    metadata = finding.metadata or {}
    
    property_name = "color"
    if metadata.get("is_background"):
        property_name = "background-color"
    
    return PropertyChange(
        property_name=property_name,
        old_value=metadata.get("current_color"),
        new_value=metadata.get("recommended_color", "var(--color-text-primary)"),
        confidence=metadata.get("confidence", 0.9),
        requires_inspection=metadata.get("current_color") is None,
    )


def _generate_typography_change(finding: AuditFindingCreate) -> PropertyChange:
    """Generate typography property change."""
    metadata = finding.metadata or {}
    
    return PropertyChange(
        property_name=metadata.get("property", "font-size"),
        old_value=metadata.get("current_value"),
        new_value=metadata.get("recommended_value", "16px"),
        confidence=metadata.get("confidence", 0.9),
        requires_inspection=metadata.get("current_value") is None,
    )


def _generate_alignment_change(finding: AuditFindingCreate) -> PropertyChange:
    """Generate alignment property change."""
    metadata = finding.metadata or {}
    
    return PropertyChange(
        property_name=metadata.get("property", "margin-left"),
        old_value=metadata.get("current_value"),
        new_value=metadata.get("recommended_value", "auto"),
        confidence=metadata.get("confidence", 0.8),
        requires_inspection=metadata.get("current_value") is None,
    )


def _generate_accessibility_changes(finding: AuditFindingCreate) -> list[PropertyChange]:
    """Generate accessibility-related property changes."""
    metadata = finding.metadata or {}
    changes = []
    
    # Touch target
    if metadata.get("issue_type") == "touch_target":
        changes.append(PropertyChange(
            property_name="min-height",
            old_value=metadata.get("current_height"),
            new_value="44px",
            confidence=0.95,
            requires_inspection=False,
        ))
        changes.append(PropertyChange(
            property_name="min-width",
            old_value=metadata.get("current_width"),
            new_value="44px",
            confidence=0.95,
            requires_inspection=False,
        ))
    
    # Focus indicator
    elif metadata.get("issue_type") == "focus":
        changes.append(PropertyChange(
            property_name="outline",
            old_value=metadata.get("current_outline", "none"),
            new_value="2px solid var(--color-focus)",
            confidence=0.9,
            requires_inspection=False,
        ))
    
    # ARIA
    elif metadata.get("issue_type") == "aria":
        changes.append(PropertyChange(
            property_name=f"aria-{metadata.get('aria_attr', 'label')}",
            old_value=None,
            new_value=metadata.get("aria_value", "REQUIRES_INSPECTION"),
            confidence=0.85,
            requires_inspection=True,
        ))
    
    # Default accessibility change
    else:
        changes.append(PropertyChange(
            property_name="accessibility",
            old_value=None,
            new_value=_extract_proposed_value(finding),
            confidence=0.8,
            requires_inspection=True,
        ))
    
    return changes


def _extract_proposed_value(finding: AuditFindingCreate) -> str:
    """Extract proposed value from finding."""
    metadata = finding.metadata or {}
    
    # Check common keys
    for key in ["recommended_value", "new_value", "proposed", "suggested"]:
        if key in metadata:
            return str(metadata[key])
    
    # Check rationale for hints
    if finding.rationale:
        # Look for quoted values
        import re
        matches = re.findall(r"'([^']+)'|\"([^\"]+)\"", finding.rationale)
        if matches:
            return matches[0][0] or matches[0][1]
    
    return "REQUIRES_INSPECTION"


# =============================================================================
# RATIONALE GENERATION
# =============================================================================

def generate_rationale(
    finding: AuditFindingCreate,
    issue_type: IssueType,
    registry: Optional[InstructionTemplateRegistry] = None
) -> str:
    """Generate rationale text for an instruction.
    
    Uses templates when possible, falls back to finding.rationale
    or generates from issue type.
    
    Args:
        finding: Source audit finding
        issue_type: Categorized issue type
        registry: Optional template registry
        
    Returns:
        Rationale string
    """
    # Use finding's rationale if available
    if finding.rationale:
        return finding.rationale
    
    # Use template registry
    if registry is None:
        registry = get_default_registry()
    
    # Build context from finding
    context = _build_template_context(finding)
    
    try:
        return registry.render_for_issue(issue_type, context)
    except ValueError:
        # Template rendering failed, use issue description
        return finding.issue


def _build_template_context(finding: AuditFindingCreate) -> dict:
    """Build template context from finding."""
    metadata = finding.metadata or {}
    
    return {
        "element": finding.entity_id,
        "property": metadata.get("property", "style"),
        "old": metadata.get("old_value", metadata.get("current_value", "current")),
        "new": metadata.get("new_value", metadata.get("recommended_value", "proposed")),
        "rationale": finding.issue,
        "criterion": "2.1",
        "level": "AA",
        "grid": "8px",
        **metadata,  # Include all metadata as potential context
    }


# =============================================================================
# INSTRUCTION FORMATTER
# =============================================================================

class InstructionFormatter:
    """Main formatter for converting findings to instructions.
    
    Orchestrates the transformation of AuditFindingCreate objects into
    ImplementationInstruction objects with all required context.
    """
    
    def __init__(
        self,
        template_registry: Optional[InstructionTemplateRegistry] = None,
        component_registry: Optional[dict[str, Any]] = None,
        screen_metadata: Optional[dict] = None,
        placeholder_path_threshold: float = 0.8,
    ):
        """Initialize formatter.
        
        Args:
            template_registry: Custom template registry
            component_registry: Dict mapping entity_id to component data
            screen_metadata: Metadata for current screen
            placeholder_path_threshold: Confidence threshold for using placeholder paths
        """
        self._template_registry = template_registry or get_default_registry()
        self._component_registry = component_registry
        self._screen_metadata = screen_metadata
        self._placeholder_threshold = placeholder_path_threshold
    
    def format_instruction(
        self,
        finding: AuditFindingCreate,
        screen_id: Optional[str] = None,
    ) -> InstructionResult:
        """Format a single finding into an instruction.
        
        Args:
            finding: Audit finding to format
            screen_id: Optional screen ID for file path resolution
            
        Returns:
            InstructionResult with instruction or validation errors
        """
        original_finding_id = finding.entity_id
        
        try:
            # Determine issue type
            issue_type = IssueType.from_dimension(finding.dimension)
            
            # Map to component
            component = map_to_component(finding, self._component_registry)
            
            # Determine file path
            file_path, is_placeholder = determine_file_path(
                screen_id, 
                self._screen_metadata
            )
            
            # Generate property changes
            changes = generate_changes(finding, issue_type)
            
            # Generate rationale
            rationale = generate_rationale(
                finding, 
                issue_type, 
                self._template_registry
            )
            
            # Calculate confidence
            avg_confidence = sum(c.confidence for c in changes) / len(changes)
            
            # Determine if manual review needed
            requires_review = (
                is_placeholder or
                avg_confidence < self._placeholder_threshold or
                any(c.requires_inspection for c in changes)
            )
            
            # Create instruction
            instruction = ImplementationInstruction(
                finding_id=original_finding_id,
                file_path=file_path,
                component=component,
                changes=changes,
                rationale=rationale,
                standards_refs=finding.standards_refs,
                dimension=finding.dimension,
                severity=finding.severity,
                issue_type=issue_type,
                confidence=avg_confidence,
                requires_manual_review=requires_review,
                is_placeholder_path=is_placeholder,
                metadata=finding.metadata,
            )
            
            return InstructionResult(
                instruction=instruction,
                validation=ValidationResult(is_valid=True, errors=[], warnings=[]),
                original_finding_id=original_finding_id,
            )
            
        except Exception as e:
            # Formatting failed
            return InstructionResult(
                instruction=None,
                validation=ValidationResult(
                    is_valid=False,
                    errors=[f"Formatting error: {str(e)}"],
                    warnings=[],
                ),
                original_finding_id=original_finding_id,
            )
    
    def format_all(
        self,
        findings: list[AuditFindingCreate],
        screen_id: Optional[str] = None,
    ) -> BatchInstructionResult:
        """Format multiple findings into instructions.
        
        Args:
            findings: List of audit findings to format
            screen_id: Optional screen ID for all findings
            
        Returns:
            BatchInstructionResult with all results
        """
        result = BatchInstructionResult()
        
        for finding in findings:
            instruction_result = self.format_instruction(finding, screen_id)
            result = result.add_result(instruction_result)
        
        return result
    
    def format_plan_actions(
        self,
        plan: Plan,
        screen_id: Optional[str] = None,
    ) -> BatchInstructionResult:
        """Format plan actions into instructions.
        
        Converts PlanActionCreate objects from a Plan into instructions.
        
        Args:
            plan: Plan with actions to format
            screen_id: Optional screen ID
            
        Returns:
            BatchInstructionResult with all results
        """
        result = BatchInstructionResult()
        
        for phase in plan.phases:
            for action in phase.actions:
                # Convert PlanActionCreate to AuditFindingCreate
                finding = self._action_to_finding(action)
                instruction_result = self.format_instruction(finding, screen_id)
                result = result.add_result(instruction_result)
        
        return result
    
    def _action_to_finding(self, action: PlanActionCreate) -> AuditFindingCreate:
        """Convert PlanActionCreate to AuditFindingCreate for formatting."""
        return AuditFindingCreate(
            entity_type=EntityType.COMPONENT,
            entity_id=action.target_entity,
            dimension=action.dimension,
            issue=action.description,
            rationale=action.rationale,
            severity=action.severity,
            metadata={
                "property": action.target_property,
                "old_value": action.current_value,
                "new_value": action.proposed_value,
                **(action.metadata or {}),
            },
        )
    
    def set_screen_metadata(self, metadata: dict) -> None:
        """Update screen metadata for file path resolution."""
        self._screen_metadata = metadata
    
    def set_component_registry(self, registry: dict[str, Any]) -> None:
        """Update component registry for component mapping."""
        self._component_registry = registry


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def format_finding(
    finding: AuditFindingCreate,
    screen_id: Optional[str] = None,
) -> InstructionResult:
    """Format a single finding using default configuration.
    
    Convenience function for quick formatting without explicit formatter setup.
    
    Args:
        finding: Audit finding to format
        screen_id: Optional screen ID
        
    Returns:
        InstructionResult
    """
    formatter = InstructionFormatter()
    return formatter.format_instruction(finding, screen_id)


def format_findings(
    findings: list[AuditFindingCreate],
    screen_id: Optional[str] = None,
) -> BatchInstructionResult:
    """Format multiple findings using default configuration.
    
    Args:
        findings: List of audit findings
        screen_id: Optional screen ID for all findings
        
    Returns:
        BatchInstructionResult
    """
    formatter = InstructionFormatter()
    return formatter.format_all(findings, screen_id)
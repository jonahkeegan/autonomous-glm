"""
Audit command for CLI.

Provides the `glm audit` command to run audits on UI artifacts.
"""

import click
from rich.console import Console

from ..errors import (
    ArtifactNotFoundError,
    AuditFailedError,
    InvalidArgumentsError,
)
from ..formatters import (
    format_audit_summary,
    format_findings_table,
    output_json,
    print_error,
    print_info,
    print_success,
)
from ..progress import spinner_progress


console = Console()


@click.command()
@click.argument("artifact_id")
@click.option(
    "--dimensions",
    "-d",
    multiple=True,
    help="Specific dimensions to audit (can be used multiple times).",
)
@click.option(
    "--json",
    "output_json_flag",
    is_flag=True,
    help="Output results in JSON format.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output with detailed findings.",
)
@click.option(
    "--save",
    "-s",
    is_flag=True,
    help="Save audit results to database.",
)
@click.pass_context
def audit(
    ctx: click.Context,
    artifact_id: str,
    dimensions: tuple[str, ...],
    output_json_flag: bool,
    verbose: bool,
    save: bool,
) -> None:
    """Run an audit on a UI artifact (screenshot or video frame).
    
    ARTIFACT_ID is the identifier of the screen or frame to audit.
    
    Examples:
        glm audit screen_abc123
        glm audit screen_abc123 --dimensions typography spacing_rhythm
        glm audit screen_abc123 --json
        glm audit screen_abc123 --verbose --save
    """
    # Get global options from context
    global_json = ctx.obj.get("output_json", False)
    global_verbose = ctx.obj.get("verbose", False)
    
    # Combine local and global flags
    use_json = output_json_flag or global_json
    use_verbose = verbose or global_verbose
    
    # Convert dimensions tuple to list
    dimension_list = list(dimensions) if dimensions else None
    
    # Validate dimensions if provided
    if dimension_list:
        valid_dimensions = _get_valid_dimensions()
        invalid = [d for d in dimension_list if d not in valid_dimensions]
        if invalid:
            raise InvalidArgumentsError(
                f"Invalid dimension(s): {', '.join(invalid)}",
                details=f"Valid dimensions: {', '.join(valid_dimensions)}",
            )
    
    try:
        # Run the audit
        result = _run_audit(
            artifact_id=artifact_id,
            dimensions=dimension_list,
            save=save,
            verbose=use_verbose,
        )
        
        # Output results
        if use_json:
            output_json(result)
        else:
            _display_audit_result(result, verbose=use_verbose)
            
    except ArtifactNotFoundError:
        raise
    except Exception as e:
        raise AuditFailedError(
            f"Audit failed: {str(e)}",
            screen_id=artifact_id,
            details=str(e) if use_verbose else None,
        )


def _run_audit(
    artifact_id: str,
    dimensions: list[str] | None,
    save: bool,
    verbose: bool,
) -> dict:
    """Run the audit and return results.
    
    Args:
        artifact_id: Screen or frame identifier
        dimensions: Optional list of dimensions to audit
        save: Whether to save results to database
        verbose: Whether to enable verbose output
        
    Returns:
        Dictionary with audit results
    """
    # Import here to avoid circular imports
    from src.audit.orchestrator import AuditOrchestrator
    from src.db.crud import get_screen
    
    with spinner_progress(f"Running audit on {artifact_id}..."):
        # Verify artifact exists
        screen = get_screen(artifact_id)
        if screen is None:
            raise ArtifactNotFoundError("Screen", artifact_id)
        
        # Create orchestrator and run audit
        orchestrator = AuditOrchestrator()
        
        # Run the audit
        audit_result = orchestrator.run_audit(
            screen_id=artifact_id,
            dimensions=dimensions,
        )
        
        # Save if requested
        if save:
            from src.audit.persistence import save_audit_result
            save_audit_result(audit_result)
    
    # Convert to dict for output
    return _audit_result_to_dict(audit_result)


def _audit_result_to_dict(result: Any) -> dict:
    """Convert audit result to dictionary.
    
    Args:
        result: AuditResult object
        
    Returns:
        Dictionary representation
    """
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif hasattr(result, "__dict__"):
        data = result.__dict__
    else:
        data = dict(result) if result else {}
    
    # Ensure we have required fields
    return {
        "audit_id": data.get("id", data.get("audit_id", "unknown")),
        "screen_id": data.get("screen_id", "unknown"),
        "status": data.get("status", "completed"),
        "total_findings": data.get("total_findings", 0),
        "by_severity": data.get("by_severity", {}),
        "findings": data.get("findings", []),
        "duration_ms": data.get("duration_ms"),
        "created_at": data.get("created_at"),
    }


def _display_audit_result(result: dict, verbose: bool) -> None:
    """Display audit result in the console.
    
    Args:
        result: Audit result dictionary
        verbose: Whether to show detailed findings
    """
    # Display summary table
    summary_table = format_audit_summary(
        audit_id=result.get("audit_id", "unknown"),
        screen_id=result.get("screen_id", "unknown"),
        status=result.get("status", "completed"),
        total_findings=result.get("total_findings", 0),
        by_severity=result.get("by_severity", {}),
        duration_ms=result.get("duration_ms"),
    )
    console.print(summary_table)
    console.print()
    
    # Display findings if verbose
    if verbose and result.get("findings"):
        findings_table = format_findings_table(result["findings"])
        console.print(findings_table)
    elif result.get("total_findings", 0) > 0:
        print_info(f"Use --verbose to see detailed findings")


def _get_valid_dimensions() -> list[str]:
    """Get list of valid audit dimensions.
    
    Returns:
        List of valid dimension names
    """
    return [
        "visual_hierarchy",
        "spacing_rhythm",
        "typography",
        "color",
        "alignment_grid",
        "components",
        "iconography",
        "motion_transitions",
        "empty_states",
        "loading_states",
        "error_states",
        "dark_mode_theming",
        "density",
        "responsiveness",
        "accessibility",
    ]
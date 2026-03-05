"""
Output formatters for CLI commands.

Provides Rich-based table formatting and JSON output utilities.
"""

import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


console = Console()


# =============================================================================
# BASE FORMATTERS
# =============================================================================

def format_json(data: Any, indent: int = 2) -> str:
    """Format data as JSON string.
    
    Args:
        data: Data to format
        indent: Indentation level
        
    Returns:
        JSON string
    """
    def json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for non-serializable types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)
    
    return json.dumps(data, indent=indent, default=json_serializer)


def output_json(data: Any) -> None:
    """Output data as JSON to console.
    
    Args:
        data: Data to output
    """
    console.print(format_json(data))


# =============================================================================
# TABLE BUILDERS
# =============================================================================

def create_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
    show_header: bool = True,
    show_lines: bool = False,
) -> Table:
    """Create a Rich table with the given data.
    
    Args:
        title: Table title
        columns: Column headers
        rows: Table rows
        show_header: Whether to show column headers
        show_lines: Whether to show row separator lines
        
    Returns:
        Rich Table object
    """
    table = Table(
        title=title,
        show_header=show_header,
        show_lines=show_lines,
        header_style="bold cyan",
    )
    
    for col in columns:
        table.add_column(col)
    
    for row in rows:
        table.add_row(*[str(cell) if cell is not None else "-" for cell in row])
    
    return table


# =============================================================================
# AUDIT FORMATTERS
# =============================================================================

def format_audit_summary(
    audit_id: str,
    screen_id: str,
    status: str,
    total_findings: int,
    by_severity: dict[str, int],
    duration_ms: float | None = None,
) -> Table:
    """Format an audit summary as a table.
    
    Args:
        audit_id: Audit identifier
        screen_id: Screen identifier
        status: Audit status
        total_findings: Total number of findings
        by_severity: Findings count by severity level
        duration_ms: Optional duration in milliseconds
        
    Returns:
        Rich Table with audit summary
    """
    table = Table(title="Audit Summary", header_style="bold cyan")
    
    table.add_column("Field", style="bold")
    table.add_column("Value")
    
    table.add_row("Audit ID", audit_id)
    table.add_row("Screen ID", screen_id)
    table.add_row("Status", _format_status(status))
    table.add_row("Total Findings", str(total_findings))
    table.add_row("Critical", str(by_severity.get("critical", 0)), style="red")
    table.add_row("High", str(by_severity.get("high", 0)), style="orange1")
    table.add_row("Medium", str(by_severity.get("medium", 0)), style="yellow")
    table.add_row("Low", str(by_severity.get("low", 0)), style="green")
    
    if duration_ms is not None:
        table.add_row("Duration", f"{duration_ms:.1f}ms")
    
    return table


def format_findings_table(findings: list[dict[str, Any]]) -> Table:
    """Format a list of findings as a table.
    
    Args:
        findings: List of finding dictionaries
        
    Returns:
        Rich Table with findings
    """
    table = Table(
        title="Audit Findings",
        header_style="bold cyan",
        show_lines=True,
    )
    
    table.add_column("ID", style="dim", width=12)
    table.add_column("Dimension", width=20)
    table.add_column("Severity", width=10)
    table.add_column("Title", width=40)
    
    for finding in findings:
        severity = finding.get("severity", "unknown")
        severity_style = _get_severity_style(severity)
        
        table.add_row(
            str(finding.get("id", "-"))[:12],
            str(finding.get("dimension", "-"))[:20],
            f"[{severity_style}]{severity}[/{severity_style}]",
            str(finding.get("title", "-"))[:40],
        )
    
    return table


# =============================================================================
# REPORT FORMATTERS
# =============================================================================

def format_report_summary(
    report_id: str,
    audit_id: str,
    phases: dict[str, int],
    created_at: str,
    output_path: str | None = None,
) -> Table:
    """Format a report summary as a table.
    
    Args:
        report_id: Report identifier
        audit_id: Associated audit identifier
        phases: Action counts by phase
        created_at: Creation timestamp
        output_path: Optional file output path
        
    Returns:
        Rich Table with report summary
    """
    table = Table(title="Report Summary", header_style="bold cyan")
    
    table.add_column("Field", style="bold")
    table.add_column("Value")
    
    table.add_row("Report ID", report_id)
    table.add_row("Audit ID", audit_id)
    table.add_row("Created", created_at)
    
    for phase, count in phases.items():
        table.add_row(f"{phase} Actions", str(count))
    
    if output_path:
        table.add_row("Output Path", output_path)
    
    return table


def format_reports_table(reports: list[dict[str, Any]]) -> Table:
    """Format a list of reports as a table.
    
    Args:
        reports: List of report dictionaries
        
    Returns:
        Rich Table with reports
    """
    table = Table(
        title="Reports",
        header_style="bold cyan",
    )
    
    table.add_column("Report ID", width=12)
    table.add_column("Audit ID", width=12)
    table.add_column("Total Actions", width=12)
    table.add_column("Created", width=20)
    
    for report in reports:
        table.add_row(
            str(report.get("id", "-"))[:12],
            str(report.get("audit_id", "-"))[:12],
            str(report.get("total_actions", 0)),
            str(report.get("created_at", "-"))[:20],
        )
    
    return table


# =============================================================================
# PROPOSAL FORMATTERS
# =============================================================================

def format_proposals_table(proposals: list[dict[str, Any]]) -> Table:
    """Format a list of proposals as a table.
    
    Args:
        proposals: List of proposal dictionaries
        
    Returns:
        Rich Table with proposals
    """
    table = Table(
        title="Design System Proposals",
        header_style="bold cyan",
    )
    
    table.add_column("ID", width=12)
    table.add_column("Type", width=15)
    table.add_column("Token/Component", width=25)
    table.add_column("Status", width=10)
    table.add_column("Priority", width=10)
    
    for proposal in proposals:
        status = proposal.get("status", "pending")
        status_style = _get_status_style(status)
        
        table.add_row(
            str(proposal.get("id", "-"))[:12],
            str(proposal.get("change_type", "-"))[:15],
            str(proposal.get("target", "-"))[:25],
            f"[{status_style}]{status}[/{status_style}]",
            str(proposal.get("priority", "-"))[:10],
        )
    
    return table


def format_proposal_detail(proposal: dict[str, Any]) -> Panel:
    """Format a single proposal with full details.
    
    Args:
        proposal: Proposal dictionary
        
    Returns:
        Rich Panel with proposal details
    """
    title = f"Proposal: {proposal.get('id', 'Unknown')}"
    
    lines = []
    lines.append(f"[bold]Type:[/bold] {proposal.get('change_type', '-')}")
    lines.append(f"[bold]Target:[/bold] {proposal.get('target', '-')}")
    lines.append(f"[bold]Status:[/bold] {_format_status(proposal.get('status', 'unknown'))}")
    lines.append(f"[bold]Priority:[/bold] {proposal.get('priority', '-')}")
    
    if "rationale" in proposal:
        lines.append(f"\n[bold]Rationale:[/bold]\n{proposal['rationale']}")
    
    if "before" in proposal:
        lines.append(f"\n[bold red]Before:[/bold red]\n{proposal['before']}")
    
    if "after" in proposal:
        lines.append(f"\n[bold green]After:[/bold green]\n{proposal['after']}")
    
    content = "\n".join(lines)
    
    return Panel(content, title=title, border_style="cyan")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_status(status: str) -> str:
    """Format a status with appropriate styling.
    
    Args:
        status: Status string
        
    Returns:
        Styled status string
    """
    status_styles = {
        "completed": "green",
        "success": "green",
        "running": "yellow",
        "in_progress": "yellow",
        "pending": "dim",
        "failed": "red",
        "error": "red",
    }
    
    style = status_styles.get(status.lower(), "white")
    return f"[{style}]{status}[/{style}]"


def _get_severity_style(severity: str) -> str:
    """Get the style for a severity level.
    
    Args:
        severity: Severity level string
        
    Returns:
        Rich style string
    """
    severity_styles = {
        "critical": "bold red",
        "high": "red",
        "medium": "yellow",
        "low": "green",
        "info": "dim",
    }
    return severity_styles.get(severity.lower(), "white")


def _get_status_style(status: str) -> str:
    """Get the style for a status.
    
    Args:
        status: Status string
        
    Returns:
        Rich style string
    """
    status_styles = {
        "approved": "green",
        "pending": "yellow",
        "rejected": "red",
        "implemented": "cyan",
        "draft": "dim",
    }
    return status_styles.get(status.lower(), "white")


def print_error(message: str, details: str | None = None) -> None:
    """Print an error message.
    
    Args:
        message: Error message
        details: Optional error details
    """
    console.print(f"[red bold]Error:[/red bold] {message}")
    if details:
        console.print(f"[dim]{details}[/dim]")


def print_success(message: str) -> None:
    """Print a success message.
    
    Args:
        message: Success message
    """
    console.print(f"[green]✓[/green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message.
    
    Args:
        message: Warning message
    """
    console.print(f"[yellow]![/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message.
    
    Args:
        message: Info message
    """
    console.print(f"[blue]ℹ[/blue] {message}")
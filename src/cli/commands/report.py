"""
Report command for CLI.

Provides the `glm report` command to view and export audit reports.
"""

import click
from rich.console import Console

from ..errors import (
    ArtifactNotFoundError,
    ReportNotFoundError,
    InvalidArgumentsError,
)
from ..formatters import (
    format_report_summary,
    format_reports_table,
    output_json,
    print_info,
    print_success,
)
from ..progress import spinner_progress


console = Console()


@click.command()
@click.argument("audit_id", required=False)
@click.option(
    "--latest",
    "-l",
    is_flag=True,
    help="Show the most recent report.",
)
@click.option(
    "--full",
    "-f",
    is_flag=True,
    help="Show full report with all actions.",
)
@click.option(
    "--json",
    "output_json_flag",
    is_flag=True,
    help="Output results in JSON format.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="Export report to file (markdown or json based on extension).",
)
@click.option(
    "--list",
    "list_reports",
    is_flag=True,
    help="List all available reports.",
)
@click.pass_context
def report(
    ctx: click.Context,
    audit_id: str | None,
    latest: bool,
    full: bool,
    output_json_flag: bool,
    output: str | None,
    list_reports: bool,
) -> None:
    """View or export audit reports.
    
    AUDIT_ID is the identifier of the audit to get the report for.
    
    Examples:
        glm report audit_abc123
        glm report --latest
        glm report audit_abc123 --full
        glm report audit_abc123 --json
        glm report audit_abc123 --output report.md
        glm report --list
    """
    # Get global options from context
    global_json = ctx.obj.get("output_json", False)
    use_json = output_json_flag or global_json
    
    # Validate options
    if audit_id is None and not latest and not list_reports:
        raise InvalidArgumentsError(
            "AUDIT_ID is required unless --latest or --list is specified",
            details="Use 'glm report --list' to see available reports, or 'glm report --latest' for the most recent.",
        )
    
    if list_reports:
        _list_reports(use_json)
        return
    
    if latest:
        audit_id = _get_latest_audit_id()
        if audit_id is None:
            print_info("No reports found")
            return
    
    # Get and display the report
    report_data = _get_report(audit_id, include_full=full or (output is not None))
    
    if output:
        _export_report(report_data, output)
        print_success(f"Report exported to {output}")
    elif use_json:
        output_json(report_data)
    else:
        _display_report(report_data, verbose=full)


def _get_report(audit_id: str, include_full: bool) -> dict:
    """Get report data for an audit.
    
    Args:
        audit_id: Audit identifier
        include_full: Whether to include full details
        
    Returns:
        Report dictionary
    """
    from src.db.crud import list_audit_findings, get_audit
    
    with spinner_progress(f"Fetching report for audit {audit_id}..."):
        # Get audit record
        audit = get_audit(audit_id)
        if audit is None:
            raise ReportNotFoundError(audit_id)
        
        # Get findings
        findings = list_audit_findings(entity_id=audit_id)
        
        # Build report data
        report = _build_report_data(audit, findings, include_full)
    
    return report


def _build_report_data(audit: Any, findings: list, include_full: bool) -> dict:
    """Build report dictionary from audit and findings.
    
    Args:
        audit: Audit record
        findings: List of findings
        include_full: Whether to include full details
        
    Returns:
        Report dictionary
    """
    # Convert audit to dict
    if hasattr(audit, "model_dump"):
        audit_data = audit.model_dump()
    elif hasattr(audit, "__dict__"):
        audit_data = audit.__dict__
    else:
        audit_data = dict(audit) if audit else {}
    
    # Convert findings to list of dicts
    findings_data = []
    for f in findings:
        if hasattr(f, "model_dump"):
            findings_data.append(f.model_dump())
        elif hasattr(f, "__dict__"):
            findings_data.append(f.__dict__)
        else:
            findings_data.append(dict(f))
    
    # Count by severity
    by_severity = {}
    for f in findings_data:
        severity = f.get("severity", "unknown")
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    # Count by phase
    by_phase = {}
    for f in findings_data:
        phase = f.get("phase", "unknown")
        by_phase[phase] = by_phase.get(phase, 0) + 1
    
    return {
        "report_id": f"report_{audit_data.get('id', 'unknown')}",
        "audit_id": audit_data.get("id", "unknown"),
        "screen_id": audit_data.get("screen_id"),
        "status": audit_data.get("status", "completed"),
        "total_findings": len(findings_data),
        "by_severity": by_severity,
        "by_phase": by_phase,
        "created_at": audit_data.get("created_at"),
        "findings": findings_data if include_full else [],
    }


def _get_latest_audit_id() -> str | None:
    """Get the ID of the most recent audit.
    
    Returns:
        Audit ID or None if no audits exist
    """
    from src.db.crud import list_audits
    
    audits = list_audits(limit=1)
    if not audits:
        return None
    
    audit = audits[0]
    if hasattr(audit, "id"):
        return audit.id
    return audit.get("id")


def _list_reports(use_json: bool) -> None:
    """List all available reports.
    
    Args:
        use_json: Whether to output as JSON
    """
    from src.db.crud import list_audits
    
    with spinner_progress("Fetching reports..."):
        audits = list_audits(limit=100)
    
    # Convert to report summaries
    reports = []
    for audit in audits:
        if hasattr(audit, "model_dump"):
            data = audit.model_dump()
        elif hasattr(audit, "__dict__"):
            data = audit.__dict__
        else:
            data = dict(audit)
        
        reports.append({
            "id": f"report_{data.get('id', 'unknown')}",
            "audit_id": data.get("id", "unknown"),
            "total_actions": data.get("total_findings", 0),
            "created_at": str(data.get("created_at", "-"))[:19],
        })
    
    if use_json:
        output_json(reports)
    else:
        if reports:
            table = format_reports_table(reports)
            console.print(table)
        else:
            print_info("No reports found")


def _display_report(report: dict, verbose: bool) -> None:
    """Display report in the console.
    
    Args:
        report: Report dictionary
        verbose: Whether to show detailed findings
    """
    # Display summary table
    summary_table = format_report_summary(
        report_id=report.get("report_id", "unknown"),
        audit_id=report.get("audit_id", "unknown"),
        phases=report.get("by_phase", {}),
        created_at=str(report.get("created_at", "-"))[:19],
    )
    console.print(summary_table)
    
    # Display findings if verbose
    if verbose and report.get("findings"):
        console.print()
        from ..formatters import format_findings_table
        findings_table = format_findings_table(report["findings"])
        console.print(findings_table)


def _export_report(report: dict, output_path: str) -> None:
    """Export report to a file.
    
    Args:
        report: Report dictionary
        output_path: Output file path
    """
    import json
    from pathlib import Path
    
    path = Path(output_path)
    ext = path.suffix.lower()
    
    if ext == ".json":
        content = json.dumps(report, indent=2, default=str)
    else:
        # Default to markdown
        content = _report_to_markdown(report)
    
    path.write_text(content)


def _report_to_markdown(report: dict) -> str:
    """Convert report to markdown format.
    
    Args:
        report: Report dictionary
        
    Returns:
        Markdown string
    """
    lines = [
        f"# Audit Report: {report.get('report_id', 'Unknown')}",
        "",
        f"**Audit ID:** {report.get('audit_id', '-')}",
        f"**Created:** {report.get('created_at', '-')}",
        f"**Total Findings:** {report.get('total_findings', 0)}",
        "",
        "## Summary by Severity",
        "",
    ]
    
    by_severity = report.get("by_severity", {})
    for severity in ["critical", "high", "medium", "low"]:
        count = by_severity.get(severity, 0)
        lines.append(f"- **{severity.title()}:** {count}")
    
    lines.extend([
        "",
        "## Summary by Phase",
        "",
    ])
    
    by_phase = report.get("by_phase", {})
    for phase, count in by_phase.items():
        lines.append(f"- **{phase}:** {count} actions")
    
    if report.get("findings"):
        lines.extend([
            "",
            "## Findings",
            "",
        ])
        
        for i, finding in enumerate(report["findings"], 1):
            lines.extend([
                f"### {i}. {finding.get('title', 'Untitled')}",
                "",
                f"- **Dimension:** {finding.get('dimension', '-')}",
                f"- **Severity:** {finding.get('severity', '-')}",
                f"- **Phase:** {finding.get('phase', '-')}",
                "",
            ])
            
            if finding.get("description"):
                lines.extend([
                    finding["description"],
                    "",
                ])
    
    return "\n".join(lines)
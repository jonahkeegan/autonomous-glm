"""
Dashboard renderer for autonomous-glm CLI.

Renders dashboard output in terminal (Rich), HTML, and JSON formats.
"""

import json
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .metrics import DashboardMetrics, Period


# Severity colors for terminal display
SEVERITY_COLORS = {
    "critical": "red",
    "high": "orange1",
    "medium": "yellow",
    "low": "green",
}

# Period labels
PERIOD_LABELS = {
    Period.DAY: "Last 24 Hours",
    Period.WEEK: "Last 7 Days",
    Period.MONTH: "Last 30 Days",
    Period.ALL: "All Time",
}


class DashboardRenderer:
    """Renders dashboard metrics in various formats.
    
    Example:
        >>> renderer = DashboardRenderer()
        >>> output = renderer.render_terminal(metrics)
        >>> print(output)
    """
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize the renderer.
        
        Args:
            console: Optional Rich console instance
        """
        self.console = console or Console()
    
    def render_terminal(self, metrics: DashboardMetrics) -> str:
        """Render dashboard as Rich terminal output.
        
        Args:
            metrics: Dashboard metrics to render
            
        Returns:
            Rendered string (also prints to console)
        """
        # Main title
        period_label = PERIOD_LABELS.get(metrics.period, str(metrics.period))
        title = Text()
        title.append("AUTONOMOUS-GLM DASHBOARD", style="bold cyan")
        title.append(f"\n{period_label}", style="dim")
        
        # Build sections
        sections = []
        
        # Audits section
        audits_table = Table(show_header=False, box=None, padding=(0, 2))
        audits_table.add_column("label", style="dim")
        audits_table.add_column("value", justify="right")
        
        total = metrics.total_audits
        successful = metrics.successful_audits
        failed = metrics.failed_audits
        success_pct = (successful / total * 100) if total > 0 else 0
        fail_pct = (failed / total * 100) if total > 0 else 0
        
        audits_table.add_row("Total:", str(total))
        audits_table.add_row("Successful:", f"{successful} ({success_pct:.0f}%)")
        audits_table.add_row("Failed:", f"{failed} ({fail_pct:.0f}%)")
        
        sections.append(Panel(
            audits_table,
            title="[bold]AUDITS[/bold]",
            border_style="blue",
        ))
        
        # Findings by severity section
        severity_table = Table(show_header=False, box=None, padding=(0, 2))
        severity_table.add_column("severity", style="dim")
        severity_table.add_column("count", justify="right")
        
        for severity, color in SEVERITY_COLORS.items():
            count = getattr(metrics.findings_summary, severity, 0)
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            severity_table.add_row(
                f"{emoji} {severity.title()}:",
                f"[{color}]{count}[/{color}]"
            )
        
        sections.append(Panel(
            severity_table,
            title="[bold]FINDINGS BY SEVERITY[/bold]",
            border_style="blue",
        ))
        
        # Top dimensions section
        if metrics.dimension_breakdown:
            dim_table = Table(show_header=False, box=None, padding=(0, 2))
            dim_table.add_column("dimension", style="dim")
            dim_table.add_column("count", justify="right")
            
            for item in metrics.dimension_breakdown[:5]:  # Top 5
                dim_table.add_row(
                    f"{item.dimension}:",
                    f"{item.count} ({item.percentage}%)"
                )
            
            sections.append(Panel(
                dim_table,
                title="[bold]TOP DIMENSIONS[/bold]",
                border_style="blue",
            ))
        
        # Artifacts section
        artifacts_table = Table(show_header=False, box=None, padding=(0, 2))
        artifacts_table.add_column("label", style="dim")
        artifacts_table.add_column("value", justify="right")
        
        artifacts_table.add_row("Screens:", str(metrics.artifact_stats.total_screens))
        artifacts_table.add_row("Flows:", str(metrics.artifact_stats.total_flows))
        artifacts_table.add_row("Components:", str(metrics.artifact_stats.total_components))
        artifacts_table.add_row("Tokens:", str(metrics.artifact_stats.total_tokens))
        
        sections.append(Panel(
            artifacts_table,
            title="[bold]ARTIFACTS[/bold]",
            border_style="blue",
        ))
        
        # Combine all sections into columns
        from rich.columns import Columns
        layout = Columns(sections, equal=True, expand=True)
        
        # Render to string
        from io import StringIO
        string_console = Console(file=StringIO(), force_terminal=True, width=120)
        string_console.print(Panel(title, expand=False))
        string_console.print(layout)
        
        return string_console.file.getvalue()
    
    def render_html(self, metrics: DashboardMetrics) -> str:
        """Render dashboard as HTML.
        
        Args:
            metrics: Dashboard metrics to render
            
        Returns:
            HTML string
        """
        period_label = PERIOD_LABELS.get(metrics.period, str(metrics.period))
        
        # Build severity bars
        severity_bars = []
        for severity, color in SEVERITY_COLORS.items():
            count = getattr(metrics.findings_summary, severity, 0)
            total = metrics.findings_summary.total or 1
            pct = (count / total) * 100
            severity_bars.append(f"""
                <div class="severity-item">
                    <span class="severity-label">{severity.title()}</span>
                    <div class="severity-bar">
                        <div class="severity-fill severity-{severity}" style="width: {pct:.1f}%"></div>
                    </div>
                    <span class="severity-count">{count}</span>
                </div>
            """)
        
        # Build dimension list
        dimension_items = []
        for item in metrics.dimension_breakdown[:10]:
            dimension_items.append(f"""
                <li class="dimension-item">
                    <span class="dimension-name">{item.dimension}</span>
                    <span class="dimension-count">{item.count}</span>
                    <span class="dimension-pct">{item.percentage}%</span>
                </li>
            """)
        
        # Build trend data
        trend_rows = []
        for point in metrics.trend_data.points[-7:]:  # Last 7 days
            trend_rows.append(f"""
                <tr>
                    <td>{point.date}</td>
                    <td>{point.audits}</td>
                    <td>{point.findings}</td>
                </tr>
            """)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous-GLM Dashboard</title>
    <style>
        :root {{
            --critical: #dc3545;
            --high: #fd7e14;
            --medium: #ffc107;
            --low: #28a745;
            --primary: #007bff;
            --dark: #343a40;
            --light: #f8f9fa;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: var(--light);
        }}
        .dashboard {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: var(--primary);
            margin: 0;
        }}
        .header .period {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .card h2 {{
            margin: 0 0 15px 0;
            font-size: 1.1em;
            color: var(--dark);
            border-bottom: 2px solid var(--primary);
            padding-bottom: 10px;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .stat-label {{
            color: #6c757d;
        }}
        .stat-value {{
            font-weight: 600;
        }}
        .severity-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
        }}
        .severity-label {{
            width: 80px;
            color: #6c757d;
        }}
        .severity-bar {{
            flex: 1;
            height: 20px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }}
        .severity-fill {{
            height: 100%;
            border-radius: 4px;
        }}
        .severity-critical {{ background: var(--critical); }}
        .severity-high {{ background: var(--high); }}
        .severity-medium {{ background: var(--medium); }}
        .severity-low {{ background: var(--low); }}
        .severity-count {{
            width: 40px;
            text-align: right;
            font-weight: 600;
        }}
        .dimension-item {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #eee;
        }}
        .dimension-name {{
            flex: 1;
        }}
        .dimension-count {{
            font-weight: 600;
            margin: 0 15px;
        }}
        .dimension-pct {{
            color: #6c757d;
            width: 50px;
            text-align: right;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            color: #6c757d;
            font-weight: 600;
        }}
        @media print {{
            body {{ background: white; }}
            .card {{ box-shadow: none; border: 1px solid #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Autonomous-GLM Dashboard</h1>
            <div class="period">{period_label}</div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Audits</h2>
                <div class="stat-row">
                    <span class="stat-label">Total</span>
                    <span class="stat-value">{metrics.total_audits}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Successful</span>
                    <span class="stat-value">{metrics.successful_audits}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Failed</span>
                    <span class="stat-value">{metrics.failed_audits}</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Findings by Severity</h2>
                {''.join(severity_bars)}
            </div>
            
            <div class="card">
                <h2>Artifacts</h2>
                <div class="stat-row">
                    <span class="stat-label">Screens</span>
                    <span class="stat-value">{metrics.artifact_stats.total_screens}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Flows</span>
                    <span class="stat-value">{metrics.artifact_stats.total_flows}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Components</span>
                    <span class="stat-value">{metrics.artifact_stats.total_components}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Tokens</span>
                    <span class="stat-value">{metrics.artifact_stats.total_tokens}</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Top Dimensions</h2>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    {''.join(dimension_items)}
                </ul>
            </div>
            
            <div class="card" style="grid-column: span 2;">
                <h2>Recent Trend</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Audits</th>
                            <th>Findings</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(trend_rows)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def render_json(self, metrics: DashboardMetrics) -> str:
        """Render dashboard as JSON.
        
        Args:
            metrics: Dashboard metrics to render
            
        Returns:
            JSON string with pretty formatting
        """
        return json.dumps(metrics.model_dump(), indent=2, default=str)


def render_dashboard(
    metrics: DashboardMetrics,
    format: str = "terminal",
    output_path: Optional[str] = None,
) -> str:
    """Render dashboard in the specified format.
    
    Args:
        metrics: Dashboard metrics to render
        format: Output format ("terminal", "html", "json")
        output_path: Optional path to save output
        
    Returns:
        Rendered output string
    """
    renderer = DashboardRenderer()
    
    if format == "html":
        output = renderer.render_html(metrics)
    elif format == "json":
        output = renderer.render_json(metrics)
    else:
        output = renderer.render_terminal(metrics)
    
    if output_path:
        from pathlib import Path
        Path(output_path).write_text(output)
    
    return output
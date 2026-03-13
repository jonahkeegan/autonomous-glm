"""
Dashboard command for CLI.

Provides the `glm dashboard` command to display audit metrics.
"""

import click
from rich.console import Console

from ..errors import InvalidArgumentsError
from ..formatters import output_json, print_info, print_success
from ..progress import spinner_progress
from ..dashboard.metrics import MetricsAggregator, Period
from ..dashboard.renderer import DashboardRenderer, render_dashboard


console = Console()


@click.command()
@click.option(
    "--html",
    is_flag=True,
    help="Output dashboard as HTML.",
)
@click.option(
    "--json",
    "output_json_flag",
    is_flag=True,
    help="Output dashboard as JSON.",
)
@click.option(
    "--pdf",
    is_flag=True,
    help="Export dashboard as PDF.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="Save output to file.",
)
@click.option(
    "--period",
    "-p",
    type=click.Choice(["day", "week", "month", "all"], case_sensitive=False),
    default="week",
    help="Time period for metrics (default: week).",
)
@click.pass_context
def dashboard(
    ctx: click.Context,
    html: bool,
    output_json_flag: bool,
    pdf: bool,
    output: str | None,
    period: str,
) -> None:
    """Display audit metrics dashboard.
    
    Shows aggregate statistics about audits, findings, and artifacts.
    
    Examples:
        glm dashboard
        glm dashboard --period month
        glm dashboard --html --output dashboard.html
        glm dashboard --pdf --output dashboard.pdf
        glm dashboard --json
    """
    # Get global options from context
    global_json = ctx.obj.get("output_json", False)
    use_json = output_json_flag or global_json
    
    # Convert period string to enum
    period_enum = Period(period.lower())
    
    # Determine output format
    if pdf:
        format_type = "pdf"
    elif html:
        format_type = "html"
    elif use_json:
        format_type = "json"
    else:
        format_type = "terminal"
    
    # Get metrics
    with spinner_progress(f"Aggregating metrics for {period}..."):
        aggregator = MetricsAggregator()
        metrics = aggregator.get_metrics(period_enum)
    
    # Check for empty data
    if metrics.total_audits == 0 and metrics.artifact_stats.total_screens == 0:
        print_info("No data available. Run some audits first with 'glm audit <artifact_id>'")
        return
    
    # Handle PDF export
    if pdf:
        from pathlib import Path
        from ..export.pdf import PDFGenerator
        
        pdf_generator = PDFGenerator()
        output_path = Path(output) if output else Path("dashboard.pdf")
        
        with spinner_progress("Generating PDF..."):
            pdf_generator.generate_from_dashboard(metrics, output_path)
        
        print_success(f"Dashboard exported to {output_path}")
        return
    
    # Render output
    if output:
        rendered = render_dashboard(metrics, format=format_type, output_path=output)
        print_success(f"Dashboard saved to {output}")
    elif format_type == "terminal":
        renderer = DashboardRenderer(console)
        renderer.render_terminal(metrics)
    elif use_json:
        output_json(metrics.model_dump())
    elif html:
        # Print HTML to stdout
        rendered = render_dashboard(metrics, format="html")
        console.print(rendered)
    else:
        # Default terminal output
        renderer = DashboardRenderer(console)
        renderer.render_terminal(metrics)

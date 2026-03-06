"""
Watch command for automatic artifact detection and processing.

Provides the 'glm watch' CLI command for directory watching.
"""

import logging
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.live import Live

from ...config.loader import load_config
from ..watch.models import WatchConfig, ArtifactType
from ..watch.manager import WatchManager
from ..watch.logger import WatchEventLogger

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="watch")
def watch():
    """Watch directories for new artifacts and process automatically.
    
    The watch command monitors specified directories for new screenshots
    and videos, automatically triggering the audit pipeline when artifacts
    are detected.
    
    Examples:
        # Watch default artifact directories
        glm watch start
        
        # Watch specific directory
        glm watch start --directory ./screenshots
        
        # Watch with dry-run (no processing)
        glm watch start --dry-run
        
        # Check watch status
        glm watch status
        
        # View recent events
        glm watch events
    """
    pass


@watch.command(name="start")
@click.option(
    "--directory", "-d",
    "directories",
    multiple=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Directory to watch (can specify multiple times)",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Watch subdirectories recursively",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Detect artifacts but don't process them",
)
@click.option(
    "--process-existing",
    is_flag=True,
    help="Process existing artifacts on start",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output",
)
def start(
    directories: tuple[Path, ...],
    recursive: bool,
    dry_run: bool,
    process_existing: bool,
    verbose: bool,
):
    """Start watching directories for new artifacts.
    
    Monitors specified directories and automatically processes new
    screenshots and videos through the audit pipeline.
    
    Press Ctrl+C to stop watching.
    """
    # Load configuration
    config = load_config()
    watch_config = WatchConfig(
        debounce_window_seconds=config.watch.debounce_window_seconds,
        max_queue_size=config.watch.max_queue_size,
        processing_interval_seconds=config.watch.processing_interval_seconds,
        event_log_path=config.watch.event_log_path,
        screenshot_extensions=config.watch.screenshot_extensions,
        video_extensions=config.watch.video_extensions,
    )
    
    # Determine directories to watch
    if not directories:
        # Use default artifact directories
        directories = (
            Path(config.paths.screenshots_dir),
            Path(config.paths.videos_dir),
        )
    
    # Create process callback (integrates with audit pipeline)
    def process_artifact(path: Path, artifact_type: ArtifactType) -> tuple[str, str]:
        """Process artifact through audit pipeline."""
        # Import here to avoid circular imports
        from ...audit.orchestrator import AuditOrchestrator
        from ...plan.report_writer import ReportWriter
        
        # Create orchestrator
        orchestrator = AuditOrchestrator(config=config)
        
        # Run audit
        audit_result = orchestrator.run_audit(str(path))
        
        # Generate report
        report_writer = ReportWriter(config=config)
        report_path = report_writer.write_report(audit_result)
        
        return audit_result.audit_id, str(report_path)
    
    # Create manager
    manager = WatchManager(
        config=watch_config,
        process_callback=process_artifact if not dry_run else None,
        dry_run=dry_run,
    )
    
    # Add directories
    valid_dirs = []
    for directory in directories:
        if manager.add_directory(directory, recursive=recursive):
            valid_dirs.append(directory)
    
    if not valid_dirs:
        console.print("[red]Error:[/red] No valid directories to watch")
        raise SystemExit(1)
    
    # Display startup info
    console.print("\n[bold cyan]Starting Watch Mode[/bold cyan]")
    console.print(f"  Directories: {', '.join(str(d) for d in valid_dirs)}")
    console.print(f"  Recursive: {recursive}")
    console.print(f"  Dry Run: {dry_run}")
    console.print(f"  Process Existing: {process_existing}")
    console.print("\n[dim]Press Ctrl+C to stop[/dim]\n")
    
    # Process existing artifacts if requested
    if process_existing:
        console.print("[yellow]Processing existing artifacts...[/yellow]")
        count = manager.process_existing()
        console.print(f"[green]Queued {count} existing artifact(s)[/green]\n")
    
    # Start status display (non-blocking)
    if verbose:
        manager.start_async()
        try:
            with Live(generate_status_table(manager), refresh_per_second=2) as live:
                while manager.is_running:
                    live.update(generate_status_table(manager))
                    time.sleep(0.5)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping watch...[/yellow]")
            manager.stop()
    else:
        # Blocking mode with simple status
        try:
            manager.start()
        except KeyboardInterrupt:
            console.print("\n[yellow]Watch stopped[/yellow]")


@watch.command(name="status")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def status(output_json: bool):
    """Show current watch status.
    
    Displays the status of any running watch session and queue state.
    """
    config = load_config()
    watch_config = WatchConfig(
        debounce_window_seconds=config.watch.debounce_window_seconds,
        max_queue_size=config.watch.max_queue_size,
        processing_interval_seconds=config.watch.processing_interval_seconds,
        event_log_path=config.watch.event_log_path,
        screenshot_extensions=config.watch.screenshot_extensions,
        video_extensions=config.watch.video_extensions,
    )
    
    # Check for event log
    event_logger = WatchEventLogger(watch_config.event_log_path)
    recent_events = event_logger.read_recent_events(count=10)
    
    if output_json:
        import json
        data = {
            "recent_events": [e.model_dump(mode="json") for e in recent_events],
            "event_count": len(recent_events),
        }
        console.print_json(json.dumps(data, indent=2, default=str))
    else:
        console.print("\n[bold cyan]Watch Status[/bold cyan]")
        
        if recent_events:
            # Show last event
            last_event = recent_events[-1]
            console.print(f"  Last Event: {last_event.event_type.value}")
            console.print(f"  Last Event Time: {last_event.timestamp.isoformat()}")
            console.print(f"  Total Recent Events: {len(recent_events)}")
        else:
            console.print("  [dim]No events recorded[/dim]")
        
        console.print(f"\n  Event Log: {watch_config.event_log_path}")


@watch.command(name="events")
@click.option(
    "--count", "-n",
    default=20,
    help="Number of events to show",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def events(count: int, output_json: bool):
    """Show recent watch events.
    
    Displays events from the watch event log.
    """
    config = load_config()
    watch_config = WatchConfig(
        debounce_window_seconds=config.watch.debounce_window_seconds,
        max_queue_size=config.watch.max_queue_size,
        processing_interval_seconds=config.watch.processing_interval_seconds,
        event_log_path=config.watch.event_log_path,
        screenshot_extensions=config.watch.screenshot_extensions,
        video_extensions=config.watch.video_extensions,
    )
    
    event_logger = WatchEventLogger(watch_config.event_log_path)
    recent_events = event_logger.read_recent_events(count=count)
    
    if output_json:
        import json
        data = {
            "events": [e.model_dump(mode="json") for e in recent_events],
            "count": len(recent_events),
        }
        console.print_json(json.dumps(data, indent=2, default=str))
    else:
        console.print(f"\n[bold cyan]Recent Watch Events ({len(recent_events)})[/bold cyan]\n")
        
        if not recent_events:
            console.print("[dim]No events recorded[/dim]")
            return
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Time", style="dim")
        table.add_column("Event", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Details")
        
        for event in recent_events:
            time_str = event.timestamp.strftime("%H:%M:%S")
            event_str = event.event_type.value
            
            # Color code event types
            if event.event_type.value == "detected":
                event_str = f"[blue]{event_str}[/blue]"
            elif event.event_type.value == "processing_completed":
                event_str = f"[green]{event_str}[/green]"
            elif event.event_type.value == "processing_failed":
                event_str = f"[red]{event_str}[/red]"
            
            path_str = str(event.path) if event.path else "-"
            
            details = ""
            if event.audit_id:
                details = f"audit: {event.audit_id}"
            elif event.error:
                details = f"[red]{event.error[:50]}[/red]"
            
            table.add_row(time_str, event_str, path_str[-40:], details)
        
        console.print(table)


def generate_status_table(manager: WatchManager) -> Table:
    """Generate status table for Live display.
    
    Args:
        manager: WatchManager instance
        
    Returns:
        Rich Table with current status
    """
    status = manager.get_status_display()
    
    table = Table(title="Watch Status", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in status.items():
        if key == "---":
            table.add_row("─" * 20, "─" * 20)
        else:
            table.add_row(key, str(value))
    
    return table
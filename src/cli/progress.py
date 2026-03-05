"""
Progress indicators for CLI commands.

Provides Rich-based progress bars and spinners for long-running operations.
"""

from contextlib import contextmanager
from typing import Generator, Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.spinner import Spinner


console = Console()


# =============================================================================
# SPINNER PROGRESS
# =============================================================================

@contextmanager
def spinner_progress(
    message: str,
    success_message: str | None = None,
    error_message: str | None = None,
) -> Generator[None, Any, None]:
    """Context manager for spinner-based progress indicator.
    
    Args:
        message: Message to display while spinning
        success_message: Message to display on success (default: message + "done")
        error_message: Message to display on error (default: message + "failed")
        
    Yields:
        None
        
    Example:
        with spinner_progress("Running audit..."):
            # Do work
            pass
    """
    if success_message is None:
        success_message = f"{message.rstrip('.')}... done"
    if error_message is None:
        error_message = f"{message.rstrip('.')}... failed"
    
    with console.status(message, spinner="dots"):
        try:
            yield
            console.print(f"[green]✓[/green] {success_message}")
        except Exception:
            console.print(f"[red]✗[/red] {error_message}")
            raise


# =============================================================================
# PROGRESS BAR
# =============================================================================

def create_progress_bar(
    description: str = "Processing",
    transient: bool = True,
) -> Progress:
    """Create a progress bar instance.
    
    Args:
        description: Description for the progress bar
        transient: Whether to remove the bar after completion
        
    Returns:
        Rich Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=transient,
    )


@contextmanager
def progress_bar(
    description: str,
    total: int,
    transient: bool = True,
) -> Generator[Progress, Any, None]:
    """Context manager for a progress bar.
    
    Args:
        description: Description for the progress bar
        total: Total number of items to process
        transient: Whether to remove the bar after completion
        
    Yields:
        Rich Progress instance
        
    Example:
        with progress_bar("Processing items", 100) as progress:
            task = progress.add_task("Processing", total=100)
            for item in items:
                # Process item
                progress.update(task, advance=1)
    """
    progress = create_progress_bar(description, transient)
    with progress:
        yield progress


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_step(step: int, total: int, message: str) -> None:
    """Print a step progress message.
    
    Args:
        step: Current step number
        total: Total number of steps
        message: Step description
    """
    console.print(f"[dim][{step}/{total}][/dim] {message}")


def print_subtask(message: str) -> None:
    """Print a subtask message.
    
    Args:
        message: Subtask description
    """
    console.print(f"  [dim]→[/dim] {message}")
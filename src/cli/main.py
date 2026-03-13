"""
Main CLI entry point for autonomous-glm.

Provides the root Click command group and version display.
"""

import click
from rich.console import Console

from .errors import CLIError, ExitCode
from .commands import audit, report, propose, watch, dashboard

# Version will be read from package metadata
__version__ = "0.1.0"

console = Console()


# =============================================================================
# VERSION DISPLAY
# =============================================================================

def get_version() -> str:
    """Get the current version string."""
    return __version__


def print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Print version and exit."""
    if not value or ctx.resilient_parsing:
        return
    console.print(f"glm version {get_version()}")
    ctx.exit()


# =============================================================================
# ROOT COMMAND GROUP
# =============================================================================

@click.group()
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show the version and exit.",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to custom configuration file.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output results in JSON format.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    config: str | None,
    verbose: bool,
    output_json: bool,
) -> None:
    """Autonomous GLM - UI/UX Design Audit Agent.
    
    Run audits on UI screenshots and generate design system proposals.
    
    Examples:
        glm audit <artifact_id>          Run an audit
        glm report <audit_id>            View a report
        glm propose                      List design system proposals
    """
    # Ensure context object exists for storing options
    ctx.ensure_object(dict)
    
    # Store global options in context
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["output_json"] = output_json
    
    # Load configuration if specified
    if config:
        try:
            from src.config.loader import load_config
            ctx.obj["loaded_config"] = load_config(config)
        except Exception as e:
            raise CLIError(
                f"Failed to load configuration: {e}",
                exit_code=ExitCode.CONFIGURATION_ERROR,
            )


# =============================================================================
# REGISTER COMMANDS
# =============================================================================

cli.add_command(audit)
cli.add_command(report)
cli.add_command(propose)
cli.add_command(watch)
cli.add_command(dashboard)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        cli(standalone_mode=False)
        return ExitCode.SUCCESS
    except CLIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        if e.details:
            console.print(f"[dim]{e.details}[/dim]")
        return e.exit_code
    except click.ClickException as e:
        e.show()
        return ExitCode.GENERAL_ERROR
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return ExitCode.GENERAL_ERROR
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        return ExitCode.GENERAL_ERROR


if __name__ == "__main__":
    exit(main())
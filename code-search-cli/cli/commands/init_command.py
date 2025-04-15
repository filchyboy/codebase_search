"""Initialization command for setting up the code search CLI."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from cli.managers.config_manager import ConfigManager
from ..logger import setup_logger

logger = setup_logger()
console = Console()

@click.command()
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for code search.",
    required=True,
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force initialization even if already initialized.",
)
def init(base_dir: Path, force: bool):
    """Initialize the code search CLI with a base directory."""
    try:
        config = ConfigManager()
        current_base_dir = Path(config.get_base_dir())

        if current_base_dir.exists() and not force:
            console.print(
                Panel(
                    f"[yellow]Already initialized with base directory:[/yellow]\n"
                    f"[blue]{current_base_dir}[/blue]\n\n"
                    "Use [green]--force[/green] to reinitialize.",
                    title="⚠️ Already Initialized",
                )
            )
            return

        # Set the new base directory
        config.set_base_dir(str(base_dir.resolve()))
        
        # Log the initialization
        logger.info(f"Initialized with base directory: {base_dir}")

        # Display success message
        console.print(
            Panel(
                f"[green]Successfully initialized code search CLI![/green]\n\n"
                f"Base directory: [blue]{base_dir.resolve()}[/blue]\n"
                f"Config directory: [blue]{config.config_dir}[/blue]\n\n"
                "You can now use the following commands:\n"
                "• [yellow]code-search search[/yellow] - Search through your codebase\n"
                "• [yellow]code-search exclusions[/yellow] - Manage search exclusions\n"
                "• [yellow]code-search help[/yellow] - Show detailed help",
                title="🎉 Initialization Complete",
                border_style="green",
            )
        )

    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()

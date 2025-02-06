"""Initialization command for setting up the code search CLI."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ..config_manager import ConfigManager
from ..logger import setup_logger

logger = setup_logger()
console = Console()

def init(args=None):
    """Initialize or change the root directory."""
    config = ConfigManager()
    current_root = Path(config.get_base_dir()).resolve()
    
    console.print("\n[bold]Configure Root Directory[/bold]")
    console.print(f"\nCurrent root directory: [blue]{current_root}[/blue]")
    
    if click.confirm("\nWould you like to change the current root directory?", default=False):
        current_dir = Path.cwd().resolve()
        console.print(f"\nCurrent working directory: [blue]{current_dir}[/blue]")
        
        if click.confirm("Use this directory?", default=True):
            new_root = current_dir
        else:
            new_root = Path(click.prompt(
                "Enter new root directory path",
                type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
                default=str(current_dir)
            ))
        
        config.set_base_dir(str(new_root))
        console.print(f"\n[green]✓ Root directory updated to: [blue]{new_root}[/blue][/green]")
    else:
        console.print("\n[green]✓ Root directory unchanged[/green]")

@click.command()
def init_command():
    """Initialize the code search CLI."""
    try:
        init()
        
        # Log the initialization
        logger.info(f"Initialized with base directory: {ConfigManager().get_base_dir()}")

        # Display success message
        console.print(
            Panel(
                f"[green]Successfully initialized code search CLI![/green]\n\n"
                f"Base directory: [blue]{ConfigManager().get_base_dir()}[/blue]\n"
                f"Config directory: [blue]{ConfigManager().config_dir}[/blue]\n\n"
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

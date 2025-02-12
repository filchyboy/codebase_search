"""Command for managing search exclusions."""

import click
from rich.console import Console
from rich.table import Table

from ..config_manager import ConfigManager
from ..logger import setup_logger

logger = setup_logger()
console = Console()

@click.group()
def exclusions():
    """Manage search exclusions."""
    pass

@exclusions.command()
@click.argument("pattern")
def add(pattern: str):
    """Add a new exclusion pattern."""
    try:
        config = ConfigManager()
        current_exclusions = config.get_exclusions()

        if pattern in current_exclusions:
            console.print(f"[yellow]Pattern '{pattern}' is already excluded.[/yellow]")
            return

        config.add_exclusion(pattern)
        logger.info(f"Added exclusion pattern: {pattern}")
        console.print(f"[green]Successfully added exclusion pattern: [blue]{pattern}[/blue][/green]")

    except Exception as e:
        logger.error(f"Failed to add exclusion: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()

@exclusions.command()
@click.argument("pattern")
def remove(pattern: str):
    """Remove an exclusion pattern."""
    try:
        config = ConfigManager()
        current_exclusions = config.get_exclusions()

        if pattern not in current_exclusions:
            console.print(f"[yellow]Pattern '{pattern}' is not in exclusions.[/yellow]")
            return

        config.remove_exclusion(pattern)
        logger.info(f"Removed exclusion pattern: {pattern}")
        console.print(f"[green]Successfully removed exclusion pattern: [blue]{pattern}[/blue][/green]")

    except Exception as e:
        logger.error(f"Failed to remove exclusion: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()

@exclusions.command()
def list():
    """List all current exclusion patterns."""
    try:
        config = ConfigManager()
        patterns = config.get_exclusions()

        if not patterns:
            console.print("[yellow]No exclusion patterns configured.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Exclusion Patterns")
        
        for pattern in sorted(patterns):
            table.add_row(pattern)

        console.print("\n[bold]Current Exclusion Patterns:[/bold]")
        console.print(table)

    except Exception as e:
        logger.error(f"Failed to list exclusions: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()

"""Search command implementation."""

import click
from rich.console import Console
from rich.table import Table

from ..config_manager import ConfigManager
from ..logger import setup_logger

logger = setup_logger()
console = Console()

@click.command()
@click.argument("query")
@click.option(
    "--context",
    "-c",
    default=2,
    help="Number of context lines to show around matches.",
)
@click.option(
    "--ignore-case",
    "-i",
    is_flag=True,
    help="Perform case-insensitive search.",
)
def search(query: str, context: int, ignore_case: bool):
    """Search through the codebase for the given query."""
    try:
        config = ConfigManager()
        base_dir = config.get_base_dir()
        exclusions = config.get_exclusions()

        # Log the search attempt
        logger.info(f"Search initiated - Query: {query}, Context: {context}, Ignore case: {ignore_case}")

        # TODO: Implement actual search logic here
        # This is a placeholder that shows how results would be displayed
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File")
        table.add_column("Line")
        table.add_column("Content")

        # Example result display
        table.add_row(
            "example.py",
            "42",
            "def example_function():  # Example match"
        )

        console.print(table)

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()

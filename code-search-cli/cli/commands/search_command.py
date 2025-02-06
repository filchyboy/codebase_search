"""Interactive search command implementation."""

import click
from rich.console import Console
from rich.table import Table
import subprocess
import shlex
from pathlib import Path

from ..config_manager import ConfigManager
from ..logger import setup_logger

logger = setup_logger()
console = Console()

def interactive_search(base_dir: Path):
    """Run an interactive search loop."""
    console.print("\n[bold green]Code Search CLI[/bold green]. Type your search term and press Enter.")
    console.print("Press [bold red]Ctrl+C[/bold red] to exit.\n")

    while True:
        try:
            # Get user input for the search term
            search_term = console.input("[bold blue]Search:[/bold blue] ").strip()
            if not search_term:
                continue  # Skip empty inputs

            # Escape special characters in the search term
            safe_search_term = shlex.quote(search_term)

            # Default exclusions
            exclusions = "--exclude-dir={.git,node_modules,venv,__pycache__} --exclude='*.pyc'"

            # Construct the grep command
            command = f'grep -rHn {safe_search_term} {exclusions} {base_dir}'

            # Execute the command
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=True
                )

                # Display the results
                if result.stdout:
                    console.print(result.stdout)
                else:
                    console.print("[yellow]No results found[/yellow]")

            except subprocess.CalledProcessError as e:
                console.print(f"[red]Search error: {str(e)}[/red]")

        except KeyboardInterrupt:
            console.print("\n[green]Exiting Code Search CLI.[/green]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

@click.command()
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for code search.",
)
@click.argument("query", required=False)
def search(base_dir: Path = None, query: str = None):
    """Search through the codebase. If no query is provided, enters interactive mode."""
    try:
        config = ConfigManager()
        search_dir = base_dir or Path(config.get_base_dir())

        if not query:
            # Interactive mode
            interactive_search(search_dir)
            return

        # Single search mode
        safe_query = shlex.quote(query)
        exclusions = "--exclude-dir={.git,node_modules,venv,__pycache__} --exclude='*.pyc'"
        command = f'grep -rHn {safe_query} {exclusions} {search_dir}'

        try:
            result = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True
            )

            if result.stdout:
                console.print(result.stdout)
            else:
                console.print("[yellow]No results found[/yellow]")

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Search error: {str(e)}[/red]")

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()

#!/usr/bin/env python3
"""Main entry point for the code search CLI."""

import click
from rich.console import Console
import shlex
import subprocess
from pathlib import Path

from .commands.search_command import search
from .commands.exclusions_command import exclusions
from .commands.init_command import init
from .commands.help_command import show_help
from .config_manager import ConfigManager
from .logger import setup_logger

console = Console()
logger = setup_logger()

def handle_command(ctx, command_input: str):
    """Handle a CLI command within the REPL context."""
    try:
        # Split the command into args
        args = shlex.split(command_input)
        
        # Create a new context for the command
        with ctx.scope(cleanup=False):
            # Invoke the CLI command with the given args
            ctx.command.main(args=args, prog_name=ctx.command.name)
    except click.exceptions.Exit:
        # Ignore exit attempts - we want to stay in the REPL
        pass
    except Exception as e:
        console.print(f"[red]Command error: {str(e)}[/red]")

def interactive_repl(ctx):
    """Run the interactive REPL."""
    config = ConfigManager()
    base_dir = Path(config.get_base_dir())

    console.print("\n[bold green]Code Search CLI[/bold green] - Interactive Mode")
    console.print("• Enter search terms directly to search")
    console.print("• Use [bold blue]cs: command[/bold blue] for CLI commands (e.g. [bold blue]cs: --help[/bold blue])")
    console.print("• Press [bold red]Ctrl+C[/bold red] to exit\n")

    while True:
        try:
            # Get user input
            user_input = console.input("[bold blue]>>[/bold blue] ").strip()
            if not user_input:
                continue

            # Check if this is a command or a search
            if user_input.startswith("cs:"):
                # Handle as CLI command
                command = user_input[3:].strip()
                handle_command(ctx, command)
            else:
                # Handle as search
                safe_term = shlex.quote(user_input)
                exclusions = "--exclude-dir={.git,node_modules,venv,__pycache__} --exclude='*.pyc'"
                command = f'grep -rHn {safe_term} {exclusions} {base_dir}'

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

        except KeyboardInterrupt:
            console.print("\n[green]Exiting Code Search CLI.[/green]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Code Search CLI - Search through your codebase with ease."""
    pass

@cli.command()
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for code search.",
)
def repl(base_dir: Path = None):
    """Start the interactive REPL mode."""
    if base_dir:
        config = ConfigManager()
        config.set_base_dir(str(base_dir))

    # Get the Click context
    ctx = click.get_current_context()
    
    # Start the REPL
    interactive_repl(ctx)

# Register all commands
cli.add_command(search)
cli.add_command(exclusions)
cli.add_command(init)
cli.add_command(show_help)

if __name__ == "__main__":
    cli()

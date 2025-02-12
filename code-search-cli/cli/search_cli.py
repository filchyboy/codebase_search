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
from .theme_manager import ThemeManager
from .logger import setup_logger

console = Console()
logger = setup_logger()

def handle_command(
    ctx,
    command_input: str,
    base_dir: Path
):
    """Process and execute a CLI command within the REPL context."""
    try:
        # Split command into arguments
        args = shlex.split(command_input)

        if not args:
            return
        
        command = args[0]
        subcommand = args[1:] if len(args) > 1 else None

        # Command Routing Table
        command_map = {
            "search": lambda: handle_search_command(" ".join(subcommand), base_dir) if subcommand else console.print("[red]Error: Missing search query.[/red]"),
            "exclusions": lambda: exclusions(subcommand),
            "init": lambda: init(subcommand),
            "help": lambda: show_help(),
            "theme": lambda: handle_theme_command(subcommand),
        }

        if command in command_map:
            command_map[command]()
        else:
            console.print(f"[red]Unknown command: {command}[/red]")

    except Exception as e:
        console.print(f"[red]Command error: {str(e)}[/red]")

def handle_search_command(query: str, base_dir: Path):
    """Handles executing a search query within the codebase, applying theme colors."""

    theme = ThemeManager.get_theme()

    if not query:
        console.print("[{theme['error']}]Error: Search query cannot be empty.[/]")
        return
    safe_term = shlex.quote(query)
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
            console.print(f"[{theme['highlight']}]Search results for:[/] [{theme['success']}]{query}[/]\n")
            console.print(result.stdout)
        else:
            console.print(f"[{theme['warning']}]No results found for:[/] [{theme['error']}]{query}[/]")

    except subprocess.CalledProcessError as e:
        console.print(f"[{theme['error']}]Search error: {str(e)}[/]")

def handle_theme_command(args):
    """Handles theme switching commands."""
    if not args or args[0] != "set" or len(args) < 2:
        console.print("[yellow]Usage: theme set [light|dark][/yellow]")
        return

    theme_name = args[1]
    if theme_name in ThemeManager.THEMES:
        ThemeManager.set_theme(theme_name)
        console.print(f"[{theme['success']}]Theme set to {theme_name}[/]")
    else:
        console.print("[{theme['error']}]Invalid theme. Use 'light' or 'dark'.[/]")

def interactive_repl(ctx):
    """Run the interactive REPL."""
    config = ConfigManager()
    base_dir = Path(config.get_base_dir())
    theme = ThemeManager.get_theme()

    console.print(f"\n[{theme['highlight']}]Code Search CLI[/] - Interactive Mode")
    console.print(f"• Enter search terms directly to search")
    console.print(f"• Use [{theme['highlight']}]cs: command[/] for CLI commands (e.g. [{theme['highlight']}]cs: --help[/])")
    console.print(f"• Press [{theme['error']}]Ctrl+C[/] to exit\n")

    while True:
        try:
            # Get user input
            user_input = console.input(f"[{theme['highlight']}]>>[/] ").strip()
            if not user_input:
                continue

            # Check if this is a command or a search
            if user_input.startswith("cs:"):
                command = user_input[3:].strip()
                handle_command(ctx, command, base_dir)
            else:
                handle_command(ctx, f"search {user_input}", base_dir)


        except KeyboardInterrupt:
            console.print("\n[green]Exiting Code Search CLI.[/green]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx):
    """Code Search CLI - Search through your codebase with ease."""
    if not ctx.invoked_subcommand:
        ctx.invoke(repl)

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

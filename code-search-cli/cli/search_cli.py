#!/usr/bin/env python3
"""Main entry point for the code search CLI."""
import re
import click
from rich.console import Console
import shlex
import subprocess
from pathlib import Path

from .commands.search_command import search
from .commands.exclusions_command import list_exclusions, add_exclusion, remove_exclusion
from .managers.exclusions_manager import ExclusionsManager
from .commands.init_command import init
from .commands.help_command import show_help
from .config_manager import ConfigManager
from .theme_manager import ThemeManager
from .logger import setup_logger

console = Console()
logger = setup_logger()
theme = ThemeManager.get_theme()
config = ConfigManager()

# ✅ Check if settings.yaml exists. If not, trigger first-time setup.
if not config.get_base_dir():
    console.print("\n[{theme['warning']}]First-time setup required.[/{theme['warning']}]")
    config._first_time_setup()

def handle_command(
    ctx,
    command_input: str,
    base_dir: Path
):
    """Process and execute a CLI command within the REPL context."""
    try:
        # Split command into arguments
        command_input = command_input.lstrip(":").strip()
        args = shlex.split(command_input)

        if not args:
            return
        
        command = args[0]
        if not base_dir or not base_dir.exists():
            console.print("\nError: No base directory set. Please run `: init` first.")
            return

        # Command Routing Table
        command_map = {
            "": lambda: ctx.invoke(show_help),  # `:` triggers help
            "init": lambda: handle_init_command(),  # `: init` resets root dir
            "list": lambda: ctx.invoke(list_exclusions),  # `: exc` lists exclusions
            "add": lambda: ctx.invoke(add_exclusion),  # `: exc+` starts exclusion addition
            "rm": lambda: ctx.invoke(remove_exclusion),  # `: exc-` starts exclusion removal
            "theme": lambda: handle_theme_command(),  # ✅ `: theme` starts user flow
        }

        if command in command_map:
            command_map[command]()
        else:
            console.print(f"Unknown command: {command}")

    except Exception as e:
        console.print(f"Command error: {str(e)}")

def handle_init_command():
    """Handles initialization by showing the current base directory and allowing the user to change it."""
    config = ConfigManager()
    exclusions_manager = ExclusionsManager()
    
    current_base_dir = config.get_base_dir()

    # ✅ Step 1: Show the current base directory if it exists
    if current_base_dir:
        console.print(f"\n[{theme['highlight']}]The existing root directory is:[/] {current_base_dir}")

        # ✅ Step 2: Ask the user if they want to change it
        console.print(f"\n[{theme['warning']}]Would you like to change it? [Y,n] [/]", end="")
        change_dir = input().strip().lower() or "y"

        if change_dir != "y":
            console.print(f"[{theme['success']}]No changes made to the search directory.[/]")
            return

    # ✅ Step 3: Prompt for a new root directory
    new_base_dir = ""
    while not new_base_dir or not Path(new_base_dir).exists():
        console.print(f"\n[{theme['highlight']}]Enter new root directory:[/] ", end="")
        new_base_dir = input().strip()

        # ✅ Strip out unwanted escape sequences from pasted input
        new_base_dir = re.sub(r"^\x1b\[200~|\x1b\[201~$", "", new_base_dir).strip()

        # ✅ Validate new directory
        if not new_base_dir or not Path(new_base_dir).exists():
            console.print(f"[{theme['error']}]Invalid directory path. Please enter a valid path.[/]")
            new_base_dir = ""

    # ✅ Step 4: Ask for confirmation before saving
    console.print(f"\n[{theme['highlight']}]Please confirm new root directory: {new_base_dir} [Y,n][/] ", end="")
    confirm = input().strip().lower() or "y"

    if confirm != "y":
        console.print(f"[{theme['warning']}]Setup aborted. No changes were made.[/]")
        return

    # ✅ Step 5: Save the new base directory
    config.set_base_dir(new_base_dir)
    new_base_dir_path = Path(config.get_base_dir())

    if not new_base_dir_path or not new_base_dir_path.exists():
        console.print(f"[{theme['error']}]Failed to set base directory. Please try again.[/]")
        return

    # ✅ Update exclusions based on detected codebase type
    console.print(f"[{theme['highlight']}]Detected codebase type:[/] {exclusions_manager.language}")
    config.set_exclusions(exclusions_manager.get_combined_exclusions())

    console.print(f"[{theme['success']}]Updated search directory and exclusions list based on detected codebase.[/]")

def handle_search_command(query: str, base_dir: Path):
    """Handles executing a search query within the codebase, applying theme colors."""


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

def handle_theme_command():
    """Initiates the user flow for changing the theme."""
    console.print(f"\n[{theme['highlight']}]Select a theme:[/]")
    console.print(f"[1] Light Mode")
    console.print(f"[2] Dark Mode")

    choice = click.prompt(
        "\nEnter your choice (1 or 2)",
        type=click.Choice(["1", "2"]),
        show_choices=False
    )

    theme_name = "light" if choice == "1" else "dark"
    ThemeManager.set_theme(theme_name)
    
    console.print(f"[{theme['success']}]Theme set to {theme_name.capitalize()}[/]")


def interactive_repl(ctx):
    """Run the interactive REPL."""
    config = ConfigManager()
    base_dir = Path(config.get_base_dir())


    console.print(f"\n[{theme['highlight']}]Code Search CLI[/] - Interactive Mode")
    console.print(f"• Enter search terms directly to search")
    console.print(f"• Use [{theme['highlight']}]: command[/] for CLI commands (e.g. [{theme['highlight']}]: --help[/{theme['highlight']}])")
    console.print(f"• Press [{theme['error']}]Ctrl+C[/] to exit\n")

    try:
        while True:
            try:
                # Get user input
                user_input = input(f"\n>> ").strip()
                if not user_input:
                    continue

                if user_input == ":":
                    ctx.invoke(show_help)
                    continue

                # Check if this is a command or a search
                if user_input.startswith(":"):
                    command = user_input.lstrip(":").strip()
                    handle_command(ctx, command, base_dir)
                else:
                    handle_command(ctx, f"search {user_input}", base_dir)


            except KeyboardInterrupt:
                console.print("\n\nExiting Code Search CLI.\n")
                return
            except Exception as e:
                console.print(f"Error: {str(e)}")

    except KeyboardInterrupt:
        console.print("\n\nGoodbye!")
        return

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



if __name__ == "__main__":
    cli()

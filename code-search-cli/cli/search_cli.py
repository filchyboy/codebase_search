#!/usr/bin/env python3
"""Main entry point for the code search CLI."""

import click
from rich.console import Console
import shlex
import subprocess
from pathlib import Path
import os

from .commands.search_command import search
from .commands.exclusions_command import exclusions
from .commands.init_command import init
from .commands.help_command import show_help
from .config_manager import ConfigManager
from .logger import setup_logger

console = Console()
logger = setup_logger()

def detect_project_type(root_dir: Path) -> list:
    """Detect project type and return appropriate exclusions."""
    # Common exclusions for all projects
    common_exclusions = [
        ".git",
        ".svn",
        ".hg",
        ".idea",
        ".vscode",
        ".DS_Store",
        "*.swp",
        "*.bak",
        "*.tmp",
        "*.log"
    ]
    
    language_exclusions = []
    
    # Python
    if list(root_dir.glob("*.py")) or \
       (root_dir / "requirements.txt").exists() or \
       (root_dir / "setup.py").exists() or \
       (root_dir / "Pipfile").exists():
        language_exclusions.extend([
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "env/",
            "venv/",
            ".env",
            "dist/",
            "build/",
            "*.egg-info/",
            ".tox/",
            ".coverage",
            "htmlcov/"
        ])
    
    # JavaScript/Node.js
    if (root_dir / "package.json").exists() or \
       (root_dir / "node_modules").exists():
        language_exclusions.extend([
            "node_modules/",
            "npm-debug.log",
            "yarn-debug.log*",
            "yarn-error.log*",
            ".npm",
            ".yarn",
            "*.min.js",
            "bundle.js",
            "coverage/",
            ".next/",
            "out/"
        ])
    
    # PHP
    if list(root_dir.glob("*.php")) or \
       (root_dir / "composer.json").exists() or \
       (root_dir / "composer.lock").exists():
        language_exclusions.extend([
            "vendor/",
            "composer.phar",
            ".phpunit.result.cache",
            "*.cache",
            "wp-content/uploads/",  # WordPress specific
            "wp-content/cache/",    # WordPress specific
            ".php_cs.cache",
            "*.log",
            "storage/logs/",        # Laravel specific
            "storage/framework/",    # Laravel specific
            "bootstrap/cache/",     # Laravel specific
            "node_modules/"         # Many PHP projects use Node.js for frontend
        ])
    
    # Java
    if list(root_dir.glob("*.java")) or \
       (root_dir / "pom.xml").exists() or \
       (root_dir / "build.gradle").exists():
        language_exclusions.extend([
            "*.class",
            "*.jar",
            "*.war",
            "target/",
            "build/",
            ".gradle/",
            "gradle-app.setting",
            "local.properties"
        ])
    
    # Ruby
    if list(root_dir.glob("*.rb")) or \
       (root_dir / "Gemfile").exists():
        language_exclusions.extend([
            "*.gem",
            ".bundle/",
            "vendor/bundle",
            "coverage/",
            "tmp/"
        ])
    
    return list(set(common_exclusions + language_exclusions))

def initial_setup():
    """Perform first-time setup of the CLI."""
    config = ConfigManager()
    current_dir = Path(os.getcwd()).resolve()
    
    console.print("\n[bold green]Code Search CLI - First Time Setup[/bold green]")
    
    # Set up root directory
    console.print("\n[bold]Step 1: Configure Root Directory[/bold]")
    console.print(f"Detected root directory: [blue]{current_dir}[/blue]")
    
    if click.confirm("Is this the root directory of your codebase?", default=True):
        root_dir = current_dir
    else:
        root_dir = Path(click.prompt(
            "Please enter the root directory of your codebase",
            type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
            default=str(current_dir)
        ))
    
    config.set_base_dir(str(root_dir))
    
    # Set up exclusions
    console.print("\n[bold]Step 2: Configure Search Exclusions[/bold]")
    
    # Detect project type and get appropriate exclusions
    detected_exclusions = detect_project_type(root_dir)
    
    console.print("\nDetected project exclusions:")
    for excl in detected_exclusions:
        console.print(f"• {excl}")
    
    if click.confirm("\nWould you like to use these exclusions?", default=True):
        exclusions = detected_exclusions
    else:
        exclusions = []
    
    if click.confirm("Would you like to add any additional exclusions?", default=False):
        while True:
            pattern = click.prompt("Enter exclusion pattern (or empty to finish)")
            if not pattern:
                break
            exclusions.append(pattern)
    
    config.set_exclusions(exclusions)
    
    # Mark setup as complete
    config.mark_setup_complete()
    
    console.print("\n[green]✓ Setup complete![/green]")
    console.print(f"Root directory: [blue]{root_dir}[/blue]")
    console.print("Exclusions:", style="bold")
    for excl in config.get_exclusions():
        console.print(f"• {excl}")
    
    return root_dir

def needs_setup() -> bool:
    """Check if initial setup is needed."""
    config = ConfigManager()
    try:
        if not config.is_setup_complete():
            return True
        base_dir = Path(config.get_base_dir())
        return not base_dir.exists()
    except:
        return True

def verify_setup():
    """Verify or perform first-time setup."""
    if needs_setup():
        return initial_setup()
    
    config = ConfigManager()
    return Path(config.get_base_dir())

def handle_command(ctx, command_input: str):
    """Handle a CLI command within the REPL context."""
    try:
        # Split the command into args
        args = shlex.split(command_input)
        
        # Map commands to functions
        commands = {
            '--help': show_help,
            'help': show_help,
            'init': init,
            'exclusions': exclusions
        }
        
        cmd = args[0]
        if cmd in commands:
            try:
                if len(args) > 1:
                    commands[cmd](args[1:])
                else:
                    commands[cmd]()
            except click.exceptions.Exit:
                # Ignore Click's exit attempts
                pass
        else:
            console.print("[yellow]Unknown command. Type 'cs: --help' for usage information.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Command error: {str(e)}[/red]")

def interactive_repl():
    """Run the interactive REPL."""
    config = ConfigManager()
    
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
                handle_command(None, command)
            else:
                # Handle as search
                safe_term = shlex.quote(user_input)
                base_dir = config.get_base_dir()
                exclusions = " ".join(f'--exclude="{e}"' for e in config.get_exclusions())
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

@click.command(context_settings={"ignore_unknown_options": True})
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.version_option(version="0.1.0")
def cli(args=None):
    """Code Search CLI - Search through your codebase with ease."""
    # If help is explicitly requested, show it
    if args and '--help' in args:
        show_help()
        return

    # Verify/perform first-time setup if needed
    verify_setup()
    
    # Start the REPL
    interactive_repl()

if __name__ == "__main__":
    cli()

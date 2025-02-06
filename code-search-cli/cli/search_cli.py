#!/usr/bin/env python3
"""Main entry point for the code search CLI."""

import click
from rich.console import Console

from .commands.search_command import search
from .commands.exclusions_command import exclusions
from .commands.init_command import init
from .commands.help_command import show_help
from .config_manager import ConfigManager
from .logger import setup_logger

console = Console()
logger = setup_logger()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Code Search CLI - Search through your codebase with ease."""
    pass

cli.add_command(search)
cli.add_command(exclusions)
cli.add_command(init)
cli.add_command(show_help)

if __name__ == "__main__":
    cli()

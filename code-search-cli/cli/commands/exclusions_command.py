"""Exclusions command implementation."""
import sys
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table

from ..config_manager import ConfigManager
from ..managers.exclusions_manager import ExclusionsManager
from ..theme_manager import ThemeManager

console = Console()
theme = ThemeManager.get_theme()

def list_exclusions():
    """List all current exclusions."""
    exclusions_manager = ExclusionsManager()
    exclusions = exclusions_manager.get_combined_exclusions()
    
    if not exclusions:
        console.print(f"[{theme['warning']}]No exclusions configured.[/{theme['warning']}]")
        return
    
    header_color = theme.get("header", "cyan")
    title_color = theme.get("title", "bold magenta")
    
    table = Table(
        title=f"[{title_color}]Current Exclusions[/{title_color}]",
        show_header=True,
        header_style=f"bold {header_color}"
    )
    table.add_column("Pattern", style=theme['highlight'])
    
    for pattern in sorted(exclusions):
        table.add_row(pattern)
    
    console.print(table)

def add_exclusion():
    """Prompt user to add an exclusion pattern."""
    try:
        console.print(f"\n[{theme['input']}]Enter exclusion pattern:[/{theme['input']}] ", end="")
        pattern = click.get_text_stream("stdin").readline().strip()

        if not pattern:
            console.print(f"[{theme['warning']}]No pattern entered. Operation cancelled.[/{theme['warning']}]")
            return

        exclusions_manager = ExclusionsManager()

        if pattern in exclusions_manager.get_combined_exclusions():
            console.print(f"[{theme['warning']}]Pattern '{pattern}' is already excluded.[/{theme['warning']}]")
            return

        exclusions_manager.add_exclusion(pattern)
        console.print(f"[{theme['success']}]Successfully added exclusion pattern: [/{theme['success']}] [{theme['highlight']}]{pattern}[/{theme['highlight']}]")

        # ✅ Show updated exclusion list
        list_exclusions()

    except Exception as e:
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")


def remove_exclusion():
    """Prompt user to remove an exclusion pattern."""
    try:
        exclusions_manager = ExclusionsManager()
        exclusions = exclusions_manager.get_combined_exclusions()
        
        if not exclusions:
            console.print(f"[{theme['warning']}]No exclusions to remove.[/{theme['warning']}]")
            return
        
        console.print(f"\n[{theme['highlight']}]Current exclusions:[/{theme['highlight']}]")
        for i, excl in enumerate(exclusions, 1):
            list_item_color = theme.get("list_item", "blue")
            console.print(f"[{theme['list_item']}]{i}. {excl}[/{theme['list_item']}]")
        
        console.print(f"\n[{theme['input']}]Enter number to remove (or empty to cancel):[/{theme['input']}] ", end="")
        choice = click.get_text_stream("stdin").readline().strip()

        if not choice or not choice.isdigit():
            console.print(f"[{theme['warning']}]Invalid selection. Operation cancelled.[/{theme['warning']}]")
            return

        index = int(choice) - 1
        if index < 0 or index >= len(exclusions):
            console.print(f"[{theme['error']}]Invalid selection. No exclusion removed.[/{theme['error']}]")
            return

        pattern = exclusions[index]
        exclusions_manager.remove_exclusion(pattern)

        console.print(f"[{theme['success']}]Successfully removed exclusion pattern: [/{theme['success']}] [{theme['highlight']}]{pattern}[/{theme['highlight']}]")

        # ✅ Show updated exclusion list
        list_exclusions()

    except Exception as e:
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")
        raise click.Abort()   
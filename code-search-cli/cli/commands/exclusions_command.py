"""Exclusions command implementation."""

from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table

from ..config_manager import ConfigManager

console = Console()

def list_exclusions():
    """List all current exclusions."""
    config = ConfigManager()
    exclusions = config.get_exclusions()
    
    if not exclusions:
        console.print("[yellow]No exclusions configured.[/yellow]")
        return
    
    table = Table(title="Current Exclusions")
    table.add_column("Pattern", style="blue")
    
    for pattern in sorted(exclusions):
        table.add_row(pattern)
    
    console.print(table)

def add_exclusion(pattern: Optional[str] = None):
    """Add a new exclusion pattern."""
    if not pattern:
        pattern = click.prompt("Enter exclusion pattern")
    
    config = ConfigManager()
    config.add_exclusion(pattern)
    console.print(f"[green]Added exclusion pattern: [blue]{pattern}[/blue][/green]")

def remove_exclusion(pattern: Optional[str] = None):
    """Remove an exclusion pattern."""
    config = ConfigManager()
    exclusions = config.get_exclusions()
    
    if not exclusions:
        console.print("[yellow]No exclusions to remove.[/yellow]")
        return
    
    if not pattern:
        console.print("\nCurrent exclusions:")
        for i, excl in enumerate(exclusions, 1):
            console.print(f"{i}. {excl}")
        
        choice = click.prompt(
            "\nEnter number to remove (or empty to cancel)",
            type=click.Choice([str(i) for i in range(1, len(exclusions) + 1)]),
            show_choices=False,
            default="",
            show_default=False
        )
        
        if not choice:
            return
        
        pattern = exclusions[int(choice) - 1]
    
    config.remove_exclusion(pattern)
    console.print(f"[green]Removed exclusion pattern: [blue]{pattern}[/blue][/green]")

def exclusions(args: Optional[List[str]] = None):
    """Manage exclusion patterns for code search."""
    if not args or not args[0]:
        list_exclusions()
        return
    
    command = args[0]
    pattern = args[1] if len(args) > 1 else None
    
    commands = {
        "list": list_exclusions,
        "add": add_exclusion,
        "remove": remove_exclusion
    }
    
    if command not in commands:
        console.print("[red]Invalid command. Use: list, add, or remove[/red]")
        return
    
    if pattern:
        commands[command](pattern)
    else:
        commands[command]()

@click.group()
def exclusions_cli():
    """Manage search exclusions."""
    pass

@exclusions_cli.command()
@click.argument("args", nargs=-1)
def exclusions(args):
    exclusions(args)

if __name__ == "__main__":
    exclusions_cli()

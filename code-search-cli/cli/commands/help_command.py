"""Help command implementation."""

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

HELP_TEXT = """
# Code Search CLI Help

## Overview
Code Search CLI is a powerful tool for searching through your codebase efficiently.

## Commands

### Initialize
```bash
code-search init --base-dir /path/to/your/code
```
Initialize the tool with your codebase directory.

### Search
```bash
code-search search "your query" [options]
```
Options:
- `--context, -c`: Number of context lines (default: 2)
- `--ignore-case, -i`: Case-insensitive search

### Manage Exclusions
```bash
code-search exclusions add "*.pyc"    # Add exclusion pattern
code-search exclusions remove "*.pyc"  # Remove exclusion pattern
code-search exclusions list           # List all exclusions
```

### Examples

Search for a function definition:
```bash
code-search search "def process_data"
```

Case-insensitive search with more context:
```bash
code-search search -i -c 5 "error handling"
```

## Configuration

Configuration is stored in:
- `~/.code-search-cli/settings.yaml`
- Environment variables can be set in `~/.code-search-cli/.env`

## Tips
- Use quotes around search queries with spaces
- Add common build and cache directories to exclusions
- Use case-insensitive search for broader matches
"""

@click.command()
def show_help():
    """Show detailed help and usage information."""
    console.print(
        Panel(
            Markdown(HELP_TEXT),
            title="📚 Code Search CLI Help",
            border_style="green",
        )
    )

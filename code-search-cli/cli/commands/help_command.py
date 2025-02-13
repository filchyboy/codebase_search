"""Help command implementation."""

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

HELP_TEXT = """
# Code Search CLI Help

## Interactive REPL Mode

Start the interactive REPL:
```bash
code-search repl --base-dir /path/to/search
```
In REPL mode:
- Type search terms directly to search
- Use `:` prefix for CLI commands (e.g. `: --help`)
- Press Ctrl+C to exit

## Available Commands

### Initialize
```bash
cs: init --base-dir /path/to/your/code
```
Initialize the tool with your codebase directory.

### Search
Just type your search term in the REPL:
```bash
>> your search term
```
Or use the search command:
```bash
: search "your query"
```

### Manage Exclusions
```bash
: exclusions add "*.pyc"    # Add exclusion pattern
: exclusions remove "*.pyc"  # Remove exclusion pattern
: exclusions list           # List all exclusions
```

## Configuration

Configuration is stored in:
- `~/.code-search-cli/settings.yaml`
- Environment variables can be set in `~/.code-search-cli/.env`

## Tips
- Use quotes around search queries with spaces
- Add common build and cache directories to exclusions
- Use grep regular expressions for advanced searches
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

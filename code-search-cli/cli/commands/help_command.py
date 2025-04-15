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
- Use `:` prefix for CLI commands (e.g. `: help`)
- Press Ctrl+C to exit

## Available Commands

### Initialize
```bash
: init
```
Initialize or change the tool's search directory.

### Search
Just type your search term in the REPL:
```bash
>> your search term
```
For regex search, use slashes:
```bash
>> /pattern\\w+/
```
For case-insensitive regex search:
```bash
>> /pattern\\w+/i
```

### Manage Exclusions
```bash
: list           # List all exclusions
: add "*.pyc"    # Add exclusion pattern
: rm             # Remove exclusion pattern (interactive)
```

### Index Management
```bash
: index          # Manage search index
```
The search index speeds up searches and runs in the background without blocking searches.

### Theme Settings
```bash
: theme          # Change between light/dark mode
```

### Editor Settings
```bash
: editor         # Configure your preferred editor for opening files
: open <number>  # Open a file from search results by its number
```

## Performance Features

- **Progress Indicators**: Shows search progress in real-time
- **Background Indexing**: Indexes files without blocking searches
- **Multithreaded Search**: Utilizes multiple CPU cores for better performance
- **Smart Exclusions**: Automatically detects and excludes vendor directories

## Tips
- Use the indexing feature for faster searches in large codebases
- The index automatically updates when files change
- Add common build and cache directories to exclusions
- Use regex for advanced searches
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

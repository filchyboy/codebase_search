"""Help command implementation."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

HELP_TEXT = """
# Code Search CLI Help

## Overview
Code Search CLI is a simple tool for searching through your codebase. It's designed to be installed and used within a single codebase.

## First Time Setup
On first run, the CLI will:
1. Detect the current directory
2. Ask you to confirm if it's your codebase root directory
3. Save this configuration for future use

## Usage

Start the CLI:
```bash
code-search
```

In the interactive mode:
- Type search terms directly to search
- Use `cs: --help` to see this help
- Press Ctrl+C to exit

## Available Commands

### Search
Just type your search term:
```bash
>> def process_data
```

### Change Root Directory
```bash
cs: init
```

### Manage Exclusions
```bash
cs: exclusions list    # List current exclusions
cs: exclusions add     # Add new exclusion
cs: exclusions remove  # Remove an exclusion
```

## Tips
- Use quotes around search queries with spaces
- Use grep regular expressions for advanced searches
- The CLI automatically excludes common directories like .git, node_modules, etc.
"""

def show_help():
    """Show detailed help and usage information."""
    console.print(
        Panel(
            Markdown(HELP_TEXT),
            title="📚 Code Search CLI Help",
            border_style="green",
        )
    )

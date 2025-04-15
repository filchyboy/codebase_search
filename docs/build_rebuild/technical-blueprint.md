# Technical Blueprint

This blueprint outlines the minimal set of components, data models, and commands needed to rapidly recreate `codebase_search` as a functional CLI tool.

## Essential Components (Implement in Order)
1. **CLI Entry Point**
   - Use `Click` to define the `code-search` command group and subcommands (`init`, `search`, `exclusions`, `help`).
2. **Configuration Manager**
   - Store config in a single YAML file (e.g., `config/settings.yaml`).
   - Track at minimum: `base_dir` (search root), `exclusions` (patterns).
3. **Search Engine**
   - Recursively walk the `base_dir` using `os.walk`.
   - Match lines using regex or simple substring search.
   - Respect exclusion patterns from config.
4. **Exclusions Manager**
   - Add/remove exclusion patterns via CLI.
   - Persist to config YAML.
5. **Rich Output & Logging**
   - Use `rich` for colored output.
   - Use `loguru` for logging to file/console.
6. **REPL/Interactive Mode** (optional for MVP)
   - Use `click-repl` to provide an interactive shell.

## Simplified Data Models
```yaml
# config/settings.yaml
base_dir: /path/to/codebase
exclusions:
  - '*.pyc'
  - '.git'
  - 'node_modules'
```

## Core CLI Commands (API)
- `code-search init --base-dir /path/to/codebase`
- `code-search search "query"`
- `code-search exclusions add "pattern"`
- `code-search exclusions remove "pattern"`
- `code-search help`

## Minimal Viable Features per Milestone
### Milestone 1: CLI + Search
- CLI entry point
- Basic search through files
- Print matching lines with file and line number

### Milestone 2: Config + Exclusions
- Persist base_dir and exclusions
- Exclude files/dirs during search

### Milestone 3: Output + Logging
- Pretty terminal output (Rich)
- Logging (Loguru)

### Milestone 4: REPL (Optional)
- Interactive shell for running commands

---

## Skeleton Code Example
```python
import click

@click.group()
def cli():
    pass

@cli.command()
def init():
    # Set up config
    pass

@cli.command()
def search(query):
    # Walk files and search
    pass

if __name__ == "__main__":
    cli()
```

This blueprint gives a clear, minimal path to a working CLI code search tool.

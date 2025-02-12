# Code Search CLI

A powerful command-line tool for searching through codebases efficiently.

## Features

- Fast code search across your codebase
- Configurable file/directory exclusions
- Search history and audit logging
- YAML-based configuration
- Rich terminal output

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/code-search-cli.git
cd code-search-cli

# Install using pipenv (recommended)
pipenv install --dev

# Or install using pip
pip install -e .
```

## Usage

Initialize the tool:
```bash
code-search init --base-dir /path/to/your/codebase
```

Search through your codebase:
```bash
code-search search "your search query"
```

Manage exclusions:
```bash
code-search exclusions add "*.pyc"
code-search exclusions remove "*.pyc"
code-search exclusions list
```

Get help:
```bash
code-search --help
```

## Development

1. Install development dependencies:
```bash
pipenv install --dev
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

3. Run tests:
```bash
pipenv run pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

# CLAUDE.md - Development Guidelines

## Build & Test Commands
- Setup: `pipenv install` or `pip install -e .`
- Run application: `python -m code_search_cli.search_cli`
- Run tests: `pytest`
- Run single test: `pytest tests/test_file.py::test_function`
- Lint code: `flake8`
- Format code: `black .`

## Code Style Guidelines
- **Formatting**: Use Black formatter
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Imports**: Group in order: standard library, third-party, local (absolute imports preferred)
- **Documentation**: Triple quotes docstrings with descriptions for modules/functions
- **Error Handling**: Use specific exceptions, log errors before handling
- **Commands**: Use Click library for CLI commands in search_cli.py
- **Configuration**: Store in YAML files under config directory
- **Logging**: Use logger.py for consistent log formatting
- **Testing**: Use pytest fixtures and parametrization where appropriate

## Architecture
Commands → Managers → Core Logic pattern, with configuration files in YAML format
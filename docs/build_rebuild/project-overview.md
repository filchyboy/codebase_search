# Project Overview

## What is codebase_search?

`codebase_search` is a command-line tool designed for fast, efficient searching through large codebases. It provides developers with powerful search capabilities, configurable exclusions, search history, YAML-based configuration, and rich terminal output for a streamlined developer experience.

## Key Technologies & Frameworks
- **Python 3.8+**
- **Click**: For building the CLI interface
- **PyYAML**: For YAML-based configuration
- **python-dotenv**: For environment variable management
- **Rich**: For enhanced terminal output
- **Loguru**: For logging

## Project Organization
- Root directory contains utility scripts and a main `code-search-cli` package
- `code-search-cli/` contains:
  - CLI logic and entry point
  - Configuration and documentation
  - Logs and test suite

## Critical Architectural Decisions
- **CLI-first design**: All functionality is exposed via a single command-line tool (`code-search`)
- **YAML configuration**: Enables flexible and human-readable project settings
- **Modular structure**: CLI, configuration, and logging are separated for maintainability
- **Rich terminal output**: Enhances usability and readability for developers

---

This overview provides the foundation for understanding and rapidly rebuilding the project. See the following docs for step-by-step implementation guidance and technical blueprints.

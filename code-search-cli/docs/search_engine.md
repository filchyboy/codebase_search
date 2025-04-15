# Search Engine Documentation

## Overview

The `SearchEngine` class provides a native Python implementation for searching code repositories. It replaces the previous grep-based implementation with a more robust, cross-platform solution that properly integrates with the exclusions system.

## Features

- **Pure Python Implementation**: Works on all platforms without relying on external tools
- **Smart Exclusions**: Respects all exclusion rules (language-specific, framework-specific, and user-defined)
- **Binary File Detection**: Automatically skips binary files to avoid corrupting output
- **Regex Support**: Supports both plain text and regular expression searches
- **Case Sensitivity Control**: Allows case-sensitive or case-insensitive searches
- **Detailed Results**: Provides detailed search results including file paths, line numbers, and match positions
- **Error Handling**: Robust error handling for file access issues and malformed regex patterns

## Usage

### Basic Usage

```python
from cli.managers.search_engine import SearchEngine
from cli.managers.config_manager import ConfigManager

# Create a search engine
config = ConfigManager()
search_engine = SearchEngine("/path/to/codebase", config)

# Perform a simple text search
results = search_engine.search("function")

# Process results
for result in results:
    print(f"{result.file_path}:{result.line_number}: {result.line_content}")
```

### Advanced Usage

```python
# Regular expression search
results = search_engine.search(r"function\s+\w+\(", use_regex=True)

# Case-insensitive search
results = search_engine.search("ERROR", case_sensitive=False)

# Combined options
results = search_engine.search(r"class\s+\w+", use_regex=True, case_sensitive=False)
```

## Command-Line Interface

The search engine can be used through the CLI in both interactive and single-search modes:

### Single Search

```
code-search-cli search "pattern"  # Plain text search
code-search-cli search -r "pattern"  # Regex search
code-search-cli search -i "pattern"  # Case-insensitive search
```

### Interactive Mode

In interactive mode, you can use the following syntax:

- `term` - Plain text search
- `/pattern/` - Regex search
- `/pattern/i` - Case-insensitive regex search

## Integration with Exclusions System

The search engine automatically integrates with the `ExclusionsManager` to respect all exclusion patterns, including:

- Language-specific exclusions (e.g., `*.pyc`, `node_modules/` for JavaScript)
- Framework-specific exclusions (e.g., `migrations/` for Django)
- User-defined exclusions added via the CLI

## Performance Considerations

The native Python implementation offers consistent behavior across platforms but may be slower than grep for very large codebases. Performance optimizations include:

1. Early directory filtering to avoid walking excluded directories
2. Quick binary file detection to skip non-text files
3. Efficient file reading with error handling

## Development and Testing

The search engine includes a comprehensive test suite that verifies:

- Basic text search functionality
- Regular expression support
- Case sensitivity options
- Exclusion pattern handling

Run the tests with:

```
pytest -xvs tests/test_search_engine.py
```
"""Utility functions for the code search CLI."""

import os
from pathlib import Path
from typing import List, Set

def normalize_path(path: str) -> Path:
    """Convert a string path to a resolved Path object."""
    return Path(os.path.expanduser(path)).resolve()

def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary."""
    try:
        with open(file_path, 'tr') as check_file:
            check_file.read(1024)
            return False
    except UnicodeDecodeError:
        return True

def get_file_type(file_path: str) -> str:
    """Get the type of a file based on its extension."""
    ext = Path(file_path).suffix.lower()
    
    # Map of common file extensions to their types
    extension_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.rs': 'Rust',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.cs': 'C#',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.m': 'Objective-C',
        '.mm': 'Objective-C++',
    }
    
    return extension_map.get(ext, 'Unknown')

def filter_files(
    base_dir: Path,
    exclusions: List[str],
    allowed_extensions: Set[str] = None
) -> List[Path]:
    """
    Get a list of files to search through, respecting exclusions.
    
    Args:
        base_dir: Base directory to search in
        exclusions: List of glob patterns to exclude
        allowed_extensions: Set of allowed file extensions (optional)
    
    Returns:
        List of Path objects for files to search
    """
    from pathlib import Path
    import fnmatch
    
    def is_excluded(path: Path) -> bool:
        """Check if a path matches any exclusion pattern."""
        path_str = str(path.relative_to(base_dir))
        return any(fnmatch.fnmatch(path_str, pattern) for pattern in exclusions)
    
    files = []
    for path in base_dir.rglob('*'):
        if not path.is_file():
            continue
            
        if is_excluded(path):
            continue
            
        if allowed_extensions and path.suffix.lower() not in allowed_extensions:
            continue
            
        if is_binary_file(str(path)):
            continue
            
        files.append(path)
    
    return files

def highlight_match(line: str, query: str, ignore_case: bool = False) -> str:
    """
    Highlight the matching part of a line using ANSI color codes.
    
    Args:
        line: The line of text to highlight
        query: The search query to highlight
        ignore_case: Whether to ignore case when highlighting
    
    Returns:
        The line with the matching part highlighted
    """
    if not query:
        return line
        
    if ignore_case:
        import re
        pattern = re.compile(re.escape(query), re.IGNORECASE)
    else:
        pattern = re.compile(re.escape(query))
        
    return pattern.sub(lambda m: f"\033[1;31m{m.group(0)}\033[0m", line)

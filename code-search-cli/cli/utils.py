"""Utility functions for the code search CLI."""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import List, Set, Optional

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

def open_file_in_editor(file_path: str, line_number: Optional[int] = None, editor_config: Optional[dict] = None) -> bool:
    """
    Attempt to open a file in the user's preferred editor/IDE.
    This function will use the settings defined through the `: editor` command.
    
    Args:
        file_path: The path to the file to open
        line_number: Optional line number to navigate to
        editor_config: Optional editor configuration from config_manager
    
    Returns:
        True if successful, False otherwise
    """
    if not editor_config:
        # Use system default if no editor config provided
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
                return True
            elif system == "Windows":
                os.startfile(file_path)
                return True
            elif system == "Linux":
                subprocess.run(["xdg-open", file_path])
                return True
        except Exception as e:
            print(f"Error opening file with system default: {e}")
            return False
    else:
        try:
            editor_name = editor_config.get("name", "default")
            command = editor_config.get("command", "")
            args = editor_config.get("args", [])
            
            if not command:  # Use system default
                return open_file_in_editor(file_path, line_number)
                
            cmd_args = [command]
            
            # Handle different editor formats for line numbers
            for arg in args:
                if "%line%" in arg and line_number:
                    cmd_args.append(arg.replace("%line%", str(line_number)))
                else:
                    cmd_args.append(arg)
            
            # Handle special cases for common editors
            if editor_name == "vscode":
                cmd_args.append(f"{file_path}:{line_number}" if line_number else file_path)
            elif editor_name == "jetbrains":
                cmd_args.append(f"{file_path}")
                if line_number:
                    cmd_args.append(str(line_number))
            elif editor_name == "custom":
                # For custom command, replace placeholders directly in the command
                custom_cmd = command.replace("%file%", file_path)
                if line_number:
                    custom_cmd = custom_cmd.replace("%line%", str(line_number))
                else:
                    custom_cmd = custom_cmd.replace("%line%", "1")
                # Split custom command into args
                cmd_args = custom_cmd.split()
            else:
                # Default case
                cmd_args.append(file_path)
            
            # Execute the command
            subprocess.run(cmd_args)
            return True
            
        except Exception as e:
            print(f"Error opening file with configured editor: {e}")
            return False
    
    return False

def create_clickable_link(file_path: str, line_number: Optional[int] = None, 
                      base_dir: Optional[str] = None, display_path: Optional[str] = None,
                      editor_config: Optional[dict] = None) -> str:
    """
    Create a clickable link using the appropriate format for the terminal.
    
    Args:
        file_path: Path to the file
        line_number: Optional line number
        base_dir: Optional base directory to create relative paths
        display_path: Optional custom path to display instead of the actual path
        editor_config: Optional editor configuration for custom URL schemes
    
    Returns:
        String containing a clickable link or formatted file path
    """
    from cli.managers.config_manager import ConfigManager
    
    system = platform.system()
    
    # Get the absolute normalized path
    norm_path = str(Path(file_path).resolve())
    
    # Determine the visible text (what the user sees)
    if display_path:
        visible_text = display_path
    elif base_dir:
        # If base_dir is provided, show path relative to it
        try:
            rel_path = os.path.relpath(norm_path, base_dir)
            visible_text = rel_path
        except:
            visible_text = os.path.basename(norm_path)
    else:
        visible_text = os.path.basename(norm_path)
    
    # Add line number to the visible text
    if line_number:
        visible_text = f"{visible_text}:{line_number}"
    
    # Determine URI based on editor config (if provided)
    if not editor_config:
        # Try to get editor config from settings
        try:
            config = ConfigManager()
            editor_config = config.get_editor_config()
        except:
            editor_config = {"name": "default"}
    
    # Create URI based on editor
    editor_name = editor_config.get("name", "default").lower()
    
    if editor_name == "vscode":
        # Use vscode:// protocol for VS Code
        if system == "Windows":
            uri = f"vscode://file/{norm_path.replace('\\', '/')}"
        else:
            uri = f"vscode://file/{norm_path}"
        
        # Add line number
        if line_number:
            uri += f":{line_number}"
            
    elif editor_name == "jetbrains":
        # IntelliJ-based IDEs
        if system == "Windows":
            uri = f"idea://open?file={norm_path.replace('\\', '/')}"
        else:
            uri = f"idea://open?file={norm_path}"
        
        # Add line number
        if line_number:
            uri += f"&line={line_number}"
            
    elif editor_name == "sublime":
        # Sublime Text
        if system == "Windows":
            norm_path_slash = norm_path.replace('\\', '/')
            uri = f"subl://open?url=file:///{norm_path_slash}"
        else:
            uri = f"subl://open?url=file://{norm_path}"
        
        # Add line number
        if line_number:
            uri += f":{line_number}"
            
    else:
        # Use standard file:// URI for default and other editors
        if system == "Windows":
            uri = f"file:///{norm_path.replace('\\', '/')}"
        else:
            uri = f"file://{norm_path}"
            
        # Some terminal handlers can understand line numbers in file:// URIs
        if line_number:
            uri += f":{line_number}"
    
    try:
        # Use OSC 8 terminal link escape sequence compatible with many terminals
        # Format: \033]8;;URI\033\\VISIBLE TEXT\033]8;;\033\\
        # This creates a hyperlink in many modern terminals
        return f"\033]8;;{uri}\033\\{visible_text}\033]8;;\033\\"
    except:
        # Fall back to plain text if any issues
        return visible_text

#!/usr/bin/env python3
"""Main entry point for the code search CLI."""
import os
import re
import click
import time
from pathlib import Path

from cli.commands.exclusions_command import (
    list_exclusions, add_exclusion, remove_exclusion,
    add_exclusion_interactive, remove_exclusion_interactive
)
from cli.commands.init_command import init
from cli.commands.help_command import show_help
import platform
import subprocess
from cli.managers.config_manager import ConfigManager
from cli.managers.theme_manager import ThemeManager
from cli.logger import setup_logger

logger = setup_logger()

# Create a console with just print function
class SimpleConsole:
    def print(self, text, **kwargs):
        # Strip rich formatting
        text = re.sub(r'\[.*?\]', '', text)
        print(text)

console = SimpleConsole()
theme = ThemeManager.get_theme()
config = ConfigManager()

# Global variable to store file commands between searches
file_open_commands = {}

def handle_search_command(query, base_dir):
    """Perform a direct search without threading."""
    # Ensure we're using the latest base_dir from config
    config = ConfigManager()
    current_base_dir = Path(config.get_base_dir())
    
    # Use the freshly fetched base_dir instead of the passed one
    print(f"\nSearching for '{query}' in {current_base_dir}...")
    
    # Basic search implementation
    matches = []
    files_searched = 0
    files_with_matches = 0
    
    # Walk the directory tree
    for root, dirs, files in os.walk(current_base_dir):
        # Skip common excluded directories
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "vendor"]]
        
        for file in files:
            # Skip binary and non-text files
            if any(file.endswith(ext) for ext in [".pyc", ".pyo", ".exe", ".dll", ".jpg", ".png"]):
                continue
                
            file_path = os.path.join(root, file)
            
            # Skip large files
            try:
                if os.path.getsize(file_path) > 1000000:  # 1MB
                    continue
            except:
                continue
                
            files_searched += 1
            
            # Try to read the file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_has_match = False
                    for i, line in enumerate(f, 1):
                        # Use a simple substring search for consistent behavior
                        if query in line:
                            matches.append((file_path, i, line.strip()))
                            file_has_match = True
                    
                    if file_has_match:
                        files_with_matches += 1
            except:
                pass
    
    # Print results
    print(f"\n=====================================")
    print(f"SEARCH REPORT: '{query}'")
    print(f"• Files searched:              {files_searched}")
    print(f"• Files with matches:          {files_with_matches}")
    print(f"• Total matches found:         {len(matches)}")
    print("=====================================\n")
    
    # Group matches by file and show one entry per file
    if matches:
        # Group matches by file path
        files_with_matches = {}
        for file_path, line_num, content in matches:
            rel_path = os.path.relpath(file_path, current_base_dir)
            if rel_path not in files_with_matches:
                files_with_matches[rel_path] = {"path": file_path, "matches": []}
            files_with_matches[rel_path]["matches"].append((line_num, content))
        
        # Get the user's editor config
        config = ConfigManager()
        editor_config = config.get_editor_config()
        editor_name = editor_config.get("name", "default")
        
        # Display results with file paths and match counts
        print(f"Found matches in {len(files_with_matches)} files:")
        
        # Generate clickable links for terminal based on editor preference
        for i, (rel_path, file_data) in enumerate(list(files_with_matches.items())[:10]):
            match_count = len(file_data["matches"])
            abs_path = file_data["path"]
            
            # Get first match line number for better navigation
            first_line = file_data["matches"][0][0] if file_data["matches"] else 1
            
            # Create command for opening with the configured editor
            if editor_name == "vscode":
                cmd = f"code --goto {abs_path}:{first_line}"
            elif editor_name == "jetbrains":
                cmd = f"idea {abs_path}:{first_line}"
            elif editor_name == "sublime":
                cmd = f"subl {abs_path}:{first_line}"
            elif editor_name == "vim":
                cmd = f"vim +{first_line} {abs_path}"
            elif editor_name == "emacs":
                cmd = f"emacs +{first_line} {abs_path}"
            elif editor_name == "custom":
                custom_cmd = editor_config.get("command", "")
                cmd = custom_cmd.replace("%file%", abs_path).replace("%line%", str(first_line))
            else:
                # Default to just opening the file with system default
                if platform.system() == "Darwin":  # macOS
                    cmd = f"open {abs_path}"
                elif platform.system() == "Windows":
                    cmd = f"start {abs_path}"
                else:
                    cmd = f"xdg-open {abs_path}"
            
            # Create VS Code clickable link (works in iTerm2)
            vscode_url = f"vscode://file/{abs_path}:{first_line}"
            
            # Format with the exact escape sequence for iTerm2
            # Format: \033]8;;vscode://file/path:line\033\\link text\033]8;;\033\\
            clickable_link = f"\033]8;;{vscode_url}\033\\{rel_path}:{first_line}\033]8;;\033\\"
            
            # Print the result with clickable link and match count
            print(f"{i+1}. {clickable_link} ({match_count} {'match' if match_count == 1 else 'matches'})")
        
        # Store file paths for the open command
        global file_open_commands
        file_open_commands.clear()  # Clear previous results
        
        for i, (rel_path, file_data) in enumerate(list(files_with_matches.items())[:10]):
            abs_path = file_data["path"]
            first_line = file_data["matches"][0][0] if file_data["matches"] else 1
            
            # Store the file info for later use with the open command
            file_open_commands[i+1] = {
                "abs_path": abs_path,
                "rel_path": rel_path,
                "line": first_line
            }
            
        # Add tip for using clickable links or opening files with command
        print(f"\nTip: File paths are clickable in iTerm2 (Command+click opens in VS Code) or use `: open <number>`")
        
        if len(files_with_matches) > 10:
            print(f"\n... and {len(files_with_matches) - 10} more files")
    else:
        print("No matches found.")
        
    # Add a blank line to separate from next prompt
    print("")

def handle_open_command(file_num):
    """Handle opening a file from search results by number."""
    global file_open_commands
    
    try:
        file_num = int(file_num)
        if not file_open_commands:
            print("\nNo recent search results to open. Run a search first.")
            return
            
        if file_num not in file_open_commands:
            print(f"\nInvalid file number. Please use a number between 1 and {len(file_open_commands)}.")
            return
            
        file_info = file_open_commands[file_num]
        abs_path = file_info["abs_path"]
        rel_path = file_info["rel_path"]
        line_num = file_info["line"]
        
        # Get the editor config
        config = ConfigManager()
        editor_config = config.get_editor_config()
        editor_name = editor_config.get("name", "default")
        
        # Create command based on the configured editor
        if editor_name == "vscode":
            cmd = f"code --goto {abs_path}:{line_num}"
        elif editor_name == "jetbrains":
            cmd = f"idea {abs_path}:{line_num}"
        elif editor_name == "sublime":
            cmd = f"subl {abs_path}:{line_num}"
        elif editor_name == "vim":
            cmd = f"vim +{line_num} {abs_path}"
        elif editor_name == "emacs":
            cmd = f"emacs +{line_num} {abs_path}"
        elif editor_name == "custom":
            custom_cmd = editor_config.get("command", "")
            cmd = custom_cmd.replace("%file%", abs_path).replace("%line%", str(line_num))
        else:
            # Default to system default
            if platform.system() == "Darwin":  # macOS
                cmd = f"open {abs_path}"
            elif platform.system() == "Windows":
                cmd = f"start {abs_path}"
            else:
                cmd = f"xdg-open {abs_path}"
                
        print(f"\nOpening {rel_path}:{line_num}...")
        
        # Execute the command
        try:
            # Use subprocess.Popen to avoid waiting for the process to complete
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            print(f"Error opening file: {e}")
            
    except ValueError:
        print("\nInvalid file number. Please provide a number (e.g. `: open 1`).")
    except Exception as e:
        print(f"\nError opening file: {e}")

def handle_command(ctx, command_input, base_dir):
    """Process and execute a CLI command within the REPL context."""
    try:
        # Split command into arguments
        command_input = command_input.lstrip(":").strip()
        args = command_input.split()

        if not args:
            return
        
        command = args[0]
        if not base_dir or not base_dir.exists():
            console.print("\nError: No base directory set. Please run `: init` first.")
            return

        # Handle open command separately
        if command == "open" and len(args) > 1:
            handle_open_command(args[1])
            return

        # Command Routing Table
        command_map = {
            "": lambda: ctx.invoke(show_help),  # `:` triggers help
            "help": lambda: ctx.invoke(show_help),  # `: help` shows help
            "init": lambda: handle_init_command(),  # `: init` resets root dir
            "list": lambda: ctx.invoke(list_exclusions),  # `: list` lists exclusions
            "add": lambda: ctx.invoke(add_exclusion),  # `: add` starts exclusion addition
            "add-path": lambda: ctx.invoke(add_exclusion_interactive, exclusion_type="path"),
            "add-string": lambda: ctx.invoke(add_exclusion_interactive, exclusion_type="string"),
            "rm": lambda: ctx.invoke(remove_exclusion),  # `: rm` starts exclusion removal
            "rm-path": lambda: ctx.invoke(remove_exclusion_interactive, exclusion_type="path"),
            "rm-string": lambda: ctx.invoke(remove_exclusion_interactive, exclusion_type="string"),
            "theme": lambda: handle_theme_command(),  # `: theme` starts theme selection
            "editor": lambda: handle_editor_command(),  # `: editor` configures preferred editor
            "index": lambda: handle_index_command(),  # `: index` rebuilds the search index
        }

        if command in command_map:
            command_map[command]()
        else:
            console.print(f"Unknown command: {command}")

    except Exception as e:
        console.print(f"Command error: {str(e)}")

def handle_init_command():
    """Initialize the search directory."""
    config = ConfigManager()
    current_base_dir = config.get_base_dir()

    if current_base_dir:
        print(f"\nThe existing root directory is: {current_base_dir}")
        print(f"\nWould you like to change it? [Y,n] ", end="")
        change_dir = input().strip().lower() or "y"

        if change_dir != "y":
            print(f"No changes made to the search directory.")
            return

    new_base_dir = ""
    while not new_base_dir or not Path(new_base_dir).exists():
        print(f"\nEnter new root directory: ", end="")
        new_base_dir = input().strip()
        if not new_base_dir or not Path(new_base_dir).exists():
            print(f"Invalid directory path. Please enter a valid path.")
            new_base_dir = ""

    print(f"\nPlease confirm new root directory: {new_base_dir} [Y,n] ", end="")
    confirm = input().strip().lower() or "y"

    if confirm != "y":
        print(f"Setup aborted. No changes were made.")
        return

    config.set_base_dir(new_base_dir)
    print(f"Updated search directory.")

def handle_theme_command():
    """Handle theme selection."""
    print(f"\nSelect a theme:")
    print(f"[1] Light Mode")
    print(f"[2] Dark Mode")

    choice = input("\nEnter your choice (1 or 2): ").strip() or "1"
    theme_name = "light" if choice == "1" else "dark"
    ThemeManager.set_theme(theme_name)
    
    print(f"Theme set to {theme_name.capitalize()}")

def handle_editor_command():
    """Handle editor configuration."""
    config = ConfigManager()
    current_editor = config.get_editor_config()
    print(f"\nCurrent editor: {current_editor.get('name', 'default')}")
    
    print("\nWhat editor/IDE would you like to use for opening files?")
    print("[1] Visual Studio Code (code)")
    print("[2] JetBrains IDEs (IntelliJ, PyCharm, etc.)")
    print("[3] Sublime Text")
    print("[4] Vim")
    print("[5] Emacs")
    print("[6] Use system default")
    print("[7] Custom command")
    
    choice = input("\nEnter your choice (1-7): ").strip() or "1"
    
    editor_configs = {
        "1": {"name": "vscode", "command": "code", "args": ["--goto"]},
        "2": {"name": "jetbrains", "command": "idea", "args": ["--line"]},
        "3": {"name": "sublime", "command": "subl", "args": []},
        "4": {"name": "vim", "command": "vim", "args": ["+%line%"]},
        "5": {"name": "emacs", "command": "emacs", "args": ["+%line%"]},
        "6": {"name": "default", "command": "", "args": []},
    }
    
    if choice in editor_configs:
        config.set_editor_config(editor_configs[choice])
        print(f"\nEditor set to {editor_configs[choice]['name']}")
    elif choice == "7":
        custom_command = input("Enter custom command (use %file% and %line% placeholders): ").strip()
        editor_config = {"name": "custom", "command": custom_command, "args": []}
        config.set_editor_config(editor_config)
        print(f"\nCustom editor command set")
    else:
        print(f"\nInvalid choice - keeping current editor")
        
def handle_index_command():
    """Handle index command - we'll just inform the user it's disabled."""
    print("\nIndexing is currently disabled to avoid stalling issues.")
    print("The search now works directly without an index.")
    print("Type a search term to search files directly.")

def interactive_repl(ctx):
    """Run the interactive REPL."""
    config = ConfigManager()
    
    print(f"\nCode Search CLI - Interactive Mode\n")
    print(f"• Enter search terms directly to search. REPL will return results.")
    print(f"• Use : command for CLI commands (e.g. : init)")
    print(f"• Type : or : help for help")
    print(f"• Press Ctrl+C to exit")

    try:
        while True:
            try:
                # Get the current base directory (refresh for each command in case it changed)
                base_dir = Path(config.get_base_dir())
                
                # Get user input
                user_input = input(f"\n>> ").strip()
                if not user_input:
                    continue

                if user_input == ":":
                    ctx.invoke(show_help)
                    continue

                # Check if this is a command or a search
                if user_input.startswith(":"):
                    command = user_input.lstrip(":").strip()
                    handle_command(ctx, command, base_dir)
                    continue

                # Otherwise, treat input as a search term
                handle_search_command(user_input, base_dir)

            except KeyboardInterrupt:
                print("\n\nExiting Code Search CLI.\n")
                return
            except Exception as e:
                print(f"Error: {str(e)}")

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        return

@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx):
    """Code Search CLI - Search through your codebase with ease."""
    if not ctx.invoked_subcommand:
        ctx.invoke(repl)

@cli.command()
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for code search.",
)
def repl(base_dir: Path = None):
    """Start the interactive REPL mode."""
    if base_dir:
        config = ConfigManager()
        config.set_base_dir(str(base_dir))

    # Get the Click context
    ctx = click.get_current_context()
    
    # Start the REPL
    interactive_repl(ctx)

if __name__ == "__main__":
    cli()

#!/usr/bin/env python3
"""
Simple fix to make search work directly without threading.
This bypasses the original search logic to use a direct approach.
"""
import os
import sys
import shutil

def fix_search_cli():
    """Replace the search command implementation with a direct version."""
    print("Fixing search command...")
    
    # Path to the search_cli.py file
    cli_path = os.path.join(os.getcwd(), "code-search-cli/cli/search_cli.py")
    
    if not os.path.exists(cli_path):
        print(f"Error: File not found: {cli_path}")
        return False
    
    print(f"Found file: {cli_path}")
    
    # Create a backup
    backup_path = cli_path + ".search.bak"
    shutil.copy2(cli_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        # Write a completely new search_cli.py file
        new_content = """#!/usr/bin/env python3
\"\"\"Main entry point for the code search CLI.\"\"\"
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
from cli.managers.config_manager import ConfigManager
from cli.managers.theme_manager import ThemeManager
from cli.logger import setup_logger

logger = setup_logger()

# Create a console with just print function
class SimpleConsole:
    def print(self, text, **kwargs):
        # Strip rich formatting
        text = re.sub(r'\\[.*?\\]', '', text)
        print(text)

console = SimpleConsole()
theme = ThemeManager.get_theme()
config = ConfigManager()

def handle_search_command(query, base_dir):
    \"\"\"Perform a direct search without threading.\"\"\"
    print(f"\\nSearching for '{query}' in {base_dir}...")
    
    # Basic search implementation
    matches = []
    files_searched = 0
    files_with_matches = 0
    
    # Walk the directory tree
    for root, dirs, files in os.walk(base_dir):
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
                        if query in line:
                            matches.append((file_path, i, line.strip()))
                            file_has_match = True
                    
                    if file_has_match:
                        files_with_matches += 1
            except:
                pass
    
    # Print results
    print(f"\\n=====================================")
    print(f"SEARCH REPORT: '{query}'")
    print(f"• Files searched:              {files_searched}")
    print(f"• Files with matches:          {files_with_matches}")
    print(f"• Total matches found:         {len(matches)}")
    print("=====================================\\n")
    
    # Show first 10 matches
    if matches:
        print("First 10 matches:")
        for i, (file_path, line_num, content) in enumerate(matches[:10]):
            rel_path = os.path.relpath(file_path, base_dir)
            if len(content) > 80:
                content = content[:77] + "..."
            print(f"{i+1}. {rel_path}:{line_num} - {content}")
        
        if len(matches) > 10:
            print(f"\\n... and {len(matches) - 10} more matches")
    else:
        print("No matches found.")
        
    # Add a blank line to separate from next prompt
    print("")

def handle_command(ctx, command_input, base_dir):
    \"\"\"Process and execute a CLI command within the REPL context.\"\"\"
    try:
        # Split command into arguments
        command_input = command_input.lstrip(":").strip()
        args = command_input.split()

        if not args:
            return
        
        command = args[0]
        if not base_dir or not base_dir.exists():
            console.print("\\nError: No base directory set. Please run `: init` first.")
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
            "index": lambda: handle_index_command(),  # `: index` rebuilds the search index
        }

        if command in command_map:
            command_map[command]()
        else:
            console.print(f"Unknown command: {command}")

    except Exception as e:
        console.print(f"Command error: {str(e)}")

def handle_init_command():
    \"\"\"Initialize the search directory.\"\"\"
    config = ConfigManager()
    current_base_dir = config.get_base_dir()

    if current_base_dir:
        print(f"\\nThe existing root directory is: {current_base_dir}")
        print(f"\\nWould you like to change it? [Y,n] ", end="")
        change_dir = input().strip().lower() or "y"

        if change_dir != "y":
            print(f"No changes made to the search directory.")
            return

    new_base_dir = ""
    while not new_base_dir or not Path(new_base_dir).exists():
        print(f"\\nEnter new root directory: ", end="")
        new_base_dir = input().strip()
        if not new_base_dir or not Path(new_base_dir).exists():
            print(f"Invalid directory path. Please enter a valid path.")
            new_base_dir = ""

    print(f"\\nPlease confirm new root directory: {new_base_dir} [Y,n] ", end="")
    confirm = input().strip().lower() or "y"

    if confirm != "y":
        print(f"Setup aborted. No changes were made.")
        return

    config.set_base_dir(new_base_dir)
    print(f"Updated search directory.")

def handle_theme_command():
    \"\"\"Handle theme selection.\"\"\"
    print(f"\\nSelect a theme:")
    print(f"[1] Light Mode")
    print(f"[2] Dark Mode")

    choice = input("\\nEnter your choice (1 or 2): ").strip() or "1"
    theme_name = "light" if choice == "1" else "dark"
    ThemeManager.set_theme(theme_name)
    
    print(f"Theme set to {theme_name.capitalize()}")

def handle_index_command():
    \"\"\"Handle index command - we'll just inform the user it's disabled.\"\"\"
    print("\\nIndexing is currently disabled to avoid stalling issues.")
    print("The search now works directly without an index.")
    print("Type a search term to search files directly.")

def interactive_repl(ctx):
    \"\"\"Run the interactive REPL.\"\"\"
    config = ConfigManager()
    base_dir = Path(config.get_base_dir())

    print(f"\\nCode Search CLI - Interactive Mode\\n")
    print(f"• Enter search terms directly to search. REPL will return results.")
    print(f"• Use : command for CLI commands (e.g. : init)")
    print(f"• Type : or : help for help")
    print(f"• Press Ctrl+C to exit")

    try:
        while True:
            try:
                # Get user input
                user_input = input(f"\\n>> ").strip()
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
                print("\\n\\nExiting Code Search CLI.\\n")
                return
            except Exception as e:
                print(f"Error: {str(e)}")

    except KeyboardInterrupt:
        print("\\n\\nGoodbye!")
        return

@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx):
    \"\"\"Code Search CLI - Search through your codebase with ease.\"\"\"
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
    \"\"\"Start the interactive REPL mode.\"\"\"
    if base_dir:
        config = ConfigManager()
        config.set_base_dir(str(base_dir))

    # Get the Click context
    ctx = click.get_current_context()
    
    # Start the REPL
    interactive_repl(ctx)

if __name__ == "__main__":
    cli()
"""
        
        # Write the new content
        with open(cli_path, 'w') as f:
            f.write(new_content)
            
        print("Successfully replaced search_cli.py with simplified version")
        return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, cli_path)
            print("Restored backup due to error")
        return False

if __name__ == "__main__":
    print("=== Simple Search Fix ===")
    print("This tool will replace the search implementation with a direct approach")
    
    # Fix the search CLI
    result = fix_search_cli()
    
    if result:
        print("\nFix applied successfully!")
        print("The search CLI has been replaced with a simplified version")
        print("that doesn't use threading or complex formatting.")
        print("\nTry running 'code-search' again and search for 'match'")
    else:
        print("\nFix could not be applied. Check the errors above.")
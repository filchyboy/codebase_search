"""Exclusions command implementation."""
import sys
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table

from cli.managers.config_manager import ConfigManager
from cli.managers.exclusions_manager import ExclusionsManager
from cli.managers.exclusions_updater import handle_exclusion_update
from cli.managers.theme_manager import ThemeManager

console = Console()
theme = ThemeManager.get_theme()

def list_exclusions():
    """List all current exclusions."""
    config = ConfigManager()
    exclusions_manager = ExclusionsManager(config.get_base_dir(), config)
    theme = ThemeManager.get_theme()

    exclusions = exclusions_manager.get_combined_exclusions()
    
    if not any(exclusions.values()):
        console.print(f"[{theme['warning']}]No exclusions configured.[/{theme['warning']}]")
        return
    
    # Ensure all colors come from the theme
    title_color = theme["title"]
    header_color = theme["header"]
    highlight_color = theme["highlight"]

    output = []

    # Framework-Specific Exclusions
    if exclusions.get("framework"):
        framework_name = next(iter(exclusions_manager.detected_frameworks), "Unknown")
        output.append(f"\n\n[{header_color}]{framework_name} Framework-Specific Exclusions (Path)[/{header_color}]\n")

        for pattern in sorted(exclusions["framework"]):
            output.append(f"- [{highlight_color}]{pattern}[/{highlight_color}]")

        output.append("\n___\n")  # Section divider

    # Language-Specific Exclusions
    language_name = "Unknown"
    for detected_framework in exclusions_manager.detected_frameworks:
        if detected_framework in exclusions_manager.EXCLUSIONS_BY_LANGUAGE:
            language_name = detected_framework

    if exclusions.get("language"):
        output.append(f"[{header_color}]{language_name} Language-Specific Exclusions (Path)[/{header_color}]\n")

        for pattern in sorted(exclusions["language"]):
            output.append(f"- [{highlight_color}]{pattern}[/{highlight_color}]")

        output.append("\n___\n")  # Section divider

    # User-Defined Path Exclusions
    if exclusions.get("user_path"):
        output.append(f"[{header_color}]User-Defined Path Exclusions[/{header_color}]\n")

        for pattern in sorted(exclusions["user_path"]):
            output.append(f"- [{highlight_color}]{pattern}[/{highlight_color}]")

        output.append("\n___\n")  # Section divider
        
    # User-Defined String Exclusions
    if exclusions.get("user_string"):
        output.append(f"[{header_color}]User-Defined String Exclusions[/{header_color}]\n")

        for pattern in sorted(exclusions["user_string"]):
            output.append(f"- [{highlight_color}]{pattern}[/{highlight_color}]")

        output.append("\n___\n")  # Section divider
        
    # If no user exclusions
    if not exclusions.get("user_path") and not exclusions.get("user_string"):
        output.append(f"[{header_color}]No current user-added exclusions.[/{header_color}]\n")

    # Print final output
    console.print("\n".join(output).strip())

def update_exclusions():
    """Manually trigger exclusion updates based on the detected frameworks."""
    try:
        config = ConfigManager()
        base_dir = config.get_base_dir()

        if not base_dir:
            console.print(f"[{theme['error']}]Error: No base directory set. Run `: init` first.[/{theme['error']}]")
            return

        from ..managers.exclusions_updater import handle_exclusion_update  # ✅ Import the bridge function

        handle_exclusion_update(base_dir)

        console.print(f"[{theme['success']}]Exclusions successfully updated.[/{theme['success']}]")

        # ✅ Show updated exclusion list
        list_exclusions()

    except Exception as e:
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")

def add_exclusion_interactive(exclusion_type="path"):
    """Prompt user to add an exclusion pattern with type."""
    try:
        console.print(f"\n[{theme['input']}]Enter {exclusion_type} exclusion pattern:[/{theme['input']}]")
        pattern = input().strip()

        if not pattern:
            console.print(f"[{theme['warning']}]No pattern entered. Operation cancelled.[/{theme['warning']}]")
            return

        config = ConfigManager()
        exclusions_manager = ExclusionsManager(config.get_base_dir(), config)

        # ✅ Ensure system-defined exclusions (language/framework) cannot be manually added
        system_exclusions = exclusions_manager.get_language_exclusions().union(exclusions_manager.get_framework_exclusions())
        if pattern in system_exclusions:
            console.print(f"[{theme['error']}]Cannot manually add system-defined exclusion: {pattern}[/{theme['error']}]")
            return

        # ✅ Add to user-defined exclusions via ExclusionsManager with type
        exclusions_manager.add_exclusion(pattern, exclusion_type)

        # ✅ Show updated exclusion list
        list_exclusions()

    except Exception as e:
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")
        
def add_exclusion():
    """Prompt user to choose exclusion type and add a pattern."""
    try:
        console.print(f"\n[{theme['input']}]Exclusion type (1=path, 2=string):[/{theme['input']}]")
        type_choice = input().strip()
        
        if not type_choice or type_choice not in ["1", "2"]:
            console.print(f"[{theme['warning']}]Invalid type. Using default (path).[/{theme['warning']}]")
            exclusion_type = "path"
        else:
            exclusion_type = "path" if type_choice == "1" else "string"
            
        add_exclusion_interactive(exclusion_type)

    except Exception as e:
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")


def remove_exclusion_interactive(exclusion_type="path"):
    """Prompt user to remove an exclusion pattern of specific type."""
    try:
        config = ConfigManager()
        exclusions_manager = ExclusionsManager(config.get_base_dir(), config)
        user_exclusions = exclusions_manager.get_user_exclusions()
        
        # Get the exclusions of the specified type
        type_exclusions = user_exclusions.get(exclusion_type, set())

        if not type_exclusions:
            console.print(f"[{theme['warning']}]No user-added {exclusion_type} exclusions to remove.[/{theme['warning']}]")
            return

        console.print(f"\n[{theme['highlight']}]User-Added {exclusion_type.capitalize()} Exclusions:[/{theme['highlight']}]")
        for i, excl in enumerate(sorted(type_exclusions), 1):
            console.print(f"[{theme['list_item']}]{i}. {excl}[/{theme['list_item']}]")

        console.print(f"\n[{theme['input']}]Enter number to remove (or empty to cancel):[/{theme['input']}]")
        choice = input().strip()

        if not choice or not choice.isdigit():
            console.print(f"[{theme['warning']}]Invalid selection. Operation cancelled.[/{theme['warning']}]")
            return

        index = int(choice) - 1
        exclusion_list = sorted(type_exclusions)

        if index < 0 or index >= len(exclusion_list):
            console.print(f"[{theme['error']}]Invalid selection. No exclusion removed.[/{theme['error']}]")
            return

        pattern = exclusion_list[index]
        exclusions_manager.remove_exclusion(pattern, exclusion_type)

        console.print(f"[{theme['success']}]Successfully removed {exclusion_type} exclusion pattern: [{theme['highlight']}]{pattern}[/{theme['highlight']}]")

        # ✅ Automatically trigger full exclusion update
        handle_exclusion_update(exclusions_manager.base_dir)

        # ✅ Show updated exclusion list
        list_exclusions()

    except Exception as e:
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")
        
def remove_exclusion():
    """Prompt user to choose which type of exclusion to remove."""
    try:
        console.print(f"\n[{theme['input']}]Exclusion type to remove (1=path, 2=string):[/{theme['input']}]")
        type_choice = input().strip()
        
        if not type_choice or type_choice not in ["1", "2"]:
            console.print(f"[{theme['warning']}]Invalid type. Using default (path).[/{theme['warning']}]")
            exclusion_type = "path"
        else:
            exclusion_type = "path" if type_choice == "1" else "string"
            
        remove_exclusion_interactive(exclusion_type)

    except Exception as e:
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")
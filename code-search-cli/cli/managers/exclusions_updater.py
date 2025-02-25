"""Handles exclusion updates by bridging ExclusionsManager and ConfigManager."""

from rich.console import Console

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli.managers.config_manager import ConfigManager

console = Console()

def handle_exclusion_update(
    base_dir: str,
    config_manager: "ConfigManager"
):
    """Detect frameworks, generate exclusions, and update settings.yaml."""
    from cli.managers.exclusions_manager import ExclusionsManager

    config_manager.base_dir = base_dir
    config_manager._load_config()
    exclusions_manager = ExclusionsManager(base_dir, config_manager)

    detected_frameworks = exclusions_manager.detect_codebase_type()
    exclusions_manager.update_exclusions()

    # Only log the detected frameworks, we'll only show this once during setup
    if not config_manager.config.get("detected_frameworks"):
        console.print(f"[green]Detected codebase types: {', '.join(detected_frameworks)}[/green]")
        
        # Add default path exclusions during initial setup
        ensure_default_exclusions(config_manager)

    config_manager.update_frameworks(detected_frameworks)
    
    # Get the exclusions from the ExclusionsManager
    exclusions = config_manager.get_exclusions()
    
    # Update the exclusions in the config - use the new format
    # Get user_path and user_string exclusions
    user_path_exclusions = exclusions.get("user_path", [])
    user_string_exclusions = exclusions.get("user_string", [])
    
    # For backward compatibility
    if "user_added" in exclusions:
        # Migrate old exclusions to new format
        user_path_exclusions.extend([x for x in exclusions.get("user_added", []) if x not in user_path_exclusions])
    
    # Update config with both path and string exclusions
    config_manager.set_exclusions({
        "system_generated": exclusions.get("system_generated", []),
        "user_path": user_path_exclusions,
        "user_string": user_string_exclusions
    })
    
def ensure_default_exclusions(config_manager: "ConfigManager"):
    """Add default path exclusions if they don't already exist."""
    from cli.managers.exclusions_manager import ExclusionsManager
    from cli.managers.theme_manager import ThemeManager
    
    # Common directories that should be excluded by default
    default_path_exclusions = [".git", "js"]
    
    # Get current exclusions
    exclusions = config_manager.get_exclusions()
    current_path_exclusions = set(exclusions.get("user_path", []))
    
    # Add any missing default exclusions
    for exclusion in default_path_exclusions:
        if exclusion not in current_path_exclusions:
            # Add to user_path exclusions
            if "user_path" not in exclusions:
                exclusions["user_path"] = []
            exclusions["user_path"].append(exclusion)
            
            theme = ThemeManager.get_theme()
            console.print(f"Added default path exclusion: [{theme['highlight']}]{exclusion}[/{theme['highlight']}]")
    
    # Update the config file
    config_manager.set_exclusions(exclusions)
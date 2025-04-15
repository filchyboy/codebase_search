"""Configuration management for the code search CLI."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv
from rich.console import Console
from cli.managers.theme_manager import ThemeManager
from cli.managers.exclusions_updater import handle_exclusion_update

console = Console()
global theme
theme = ThemeManager.get_theme()

class ConfigManager:
    """Manages configuration for the code search CLI."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the config manager, ensuring the settings file exists."""
        self.app_root = Path(__file__).resolve().parent.parent
        self.config_dir = self.app_root / "config"
        self.config_file = self.config_dir / "settings.yaml"
        self.env_file = self.config_dir / ".env"

        # ✅ Ensure the config directory exists
        self._ensure_config_dir()
        self.config = self._load_config()

        # ✅ If settings.yaml is missing or base_dir is empty, force setup
        if not self.config or not self.config.get("base_dir"):
            console.print(
                f"First-time setup required."
            )
            self._first_time_setup()
        else:
            # ✅ Ensure exclusions are properly set up even after initialization
            handle_exclusion_update(self.config["base_dir"], self)

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.env_file.exists():
            load_dotenv(self.env_file)

    def _load_config(self) -> Dict:
        """Load the configuration from file. If missing, return an empty dict."""
        if not self.config_file.exists():
            self.save_config({})
            return {}

        try:
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[red]Failed to load config: {str(e)}[/red]")
            return {}

    def save_config(self, config: Dict) -> None:
        """Save the configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(config, f)
            # Don't print success message to avoid cluttering the output
        except Exception as e:
            console.print(f"[{theme['error']}]Failed to save config: {str(e)}[/]")


    def _first_time_setup(self):
        """Prompt the user to set up the application on first launch."""
        try:
            theme = ThemeManager.get_theme()
            console.print(f"\nIt looks like you're starting Code Search CLI for the first time. [{theme['highlight']}]Let's set things up![/{theme['highlight']}]")

            base_dir = self._prompt_for_directory()
            selected_theme = self._prompt_for_theme()
            preferred_editor = self._prompt_for_editor()

            self.config = {
                "base_dir": base_dir,
                "detected_frameworks": [],
                "exclusions": {
                    "system_generated": [],
                    "user_path": [],
                    "user_string": []
                },
                "theme": selected_theme,
                "editor": preferred_editor
            }
            self.save_config(self.config)
            handle_exclusion_update(self.config["base_dir"], self)

            console.print(f"\nSetup complete! Code Search CLI is now ready to use.\n")
        except KeyboardInterrupt:
            console.print(f"\n[{theme['error']}]Setup interrupted. Exiting...[/]")
            raise SystemExit(1)
            
    def _prompt_for_editor(self) -> dict:
        """Prompt the user for their preferred editor/IDE."""
        console.print("\nWhat editor/IDE would you like to use for opening files?")
        console.print("[1] Visual Studio Code (code)")
        console.print("[2] JetBrains IDEs (IntelliJ, PyCharm, etc.)")
        console.print("[3] Sublime Text")
        console.print("[4] Vim")
        console.print("[5] Emacs")
        console.print("[6] Use system default")
        console.print("[7] Custom command")
        
        choice = input("Enter your choice (1-7): ").strip() or "1"
        
        editor_configs = {
            "1": {"name": "vscode", "command": "code", "args": ["--goto"]},
            "2": {"name": "jetbrains", "command": "idea", "args": ["--line"]},
            "3": {"name": "sublime", "command": "subl", "args": []},
            "4": {"name": "vim", "command": "vim", "args": ["+%line%"]},
            "5": {"name": "emacs", "command": "emacs", "args": ["+%line%"]},
            "6": {"name": "default", "command": "", "args": []},
        }
        
        if choice in editor_configs:
            return editor_configs[choice]
        elif choice == "7":
            custom_command = input("Enter custom command (use %file% and %line% placeholders): ").strip()
            return {"name": "custom", "command": custom_command, "args": []}
        else:
            return editor_configs["1"]  # Default to VS Code

    def _prompt_for_directory(self) -> str:
        """Prompt the user for the codebase root directory."""
        while True:
            console.print(f"\nEnter the directory where your codebase is located: ", end="")
            base_dir = input().strip()
            base_dir = re.sub(r"^\x1b\[200~|\x1b\[201~$", "", base_dir).strip()

            if Path(base_dir).exists():
                return base_dir
            console.print(f"[{theme['error']}]Invalid directory path. Please enter a valid path.[/]")

    def _prompt_for_theme(self) -> str:
        """Prompt the user for the CLI theme preference."""
        console.print("\nSelect a theme:")
        console.print("[1] Light Mode")
        console.print("[2] Dark Mode")

        theme_choice = input("Enter your choice (1 or 2): ").strip() or "1"
        return "light" if theme_choice == "1" else "dark"

    def get_base_dir(self) -> str:
        """Get the base directory for code search."""
        return self.config.get("base_dir", "")

    def set_base_dir(self, base_dir: str) -> None:
        """Set the base directory for code search."""
        self.config["base_dir"] = str(Path(base_dir).resolve())
        self.save_config(self.config)
        handle_exclusion_update(base_dir, self)
        
    def get_editor_config(self) -> dict:
        """Get the configured editor settings."""
        default_editor = {"name": "vscode", "command": "code", "args": ["--goto"]}
        return self.config.get("editor", default_editor)
        
    def set_editor_config(self, editor_config: dict) -> None:
        """Set the editor configuration."""
        self.config["editor"] = editor_config
        self.save_config(self.config)

    def get_frameworks(self) -> List[str]:
        """Get detected frameworks from config."""
        return self.config.get("detected_frameworks", [])

    def update_frameworks(self, frameworks: List[str]) -> None:
        """Update detected frameworks in the config."""
        self.config["detected_frameworks"] = sorted(frameworks)
        self.save_config(self.config)

    def set_exclusions(self, exclusions: Dict[str, List[str]]):
        """Set the exclusions in the config and save it."""
        # Ensure backward compatibility
        if "user_added" in exclusions and ("user_path" not in exclusions or "user_string" not in exclusions):
            # Migrate old format to new format
            exclusions["user_path"] = exclusions.get("user_added", [])
            if "user_string" not in exclusions:
                exclusions["user_string"] = []
        
        self.config["exclusions"] = exclusions
        self.save_config(self.config)

    def get_exclusions(self) -> Dict[str, List[str]]:
        """Get exclusions by category."""
        exclusions = self.config.get("exclusions", {
            "system_generated": [],
            "user_path": [],
            "user_string": []
        })
        
        # For backward compatibility
        if "user_added" in exclusions and "user_path" not in exclusions:
            exclusions["user_path"] = exclusions["user_added"]
            exclusions["user_string"] = []
            
        return exclusions

    def update_exclusions(self, system_exclusions: List[str], user_exclusions: Optional[List[str]] = None):
        """Update exclusions in settings.yaml while preserving system and user-defined exclusions.
        
        Note: This method is maintained for backward compatibility but you should prefer
        using set_exclusions() which supports the new format with user_path and user_string categories.
        """
        if not isinstance(system_exclusions, list):
            system_exclusions = list(system_exclusions)

        # Retrieve existing exclusions in the new format
        exclusions = self.get_exclusions()
        
        # Get existing path and string exclusions
        user_path = set(exclusions.get("user_path", []))
        user_string = set(exclusions.get("user_string", []))
        
        # For backward compatibility - merge any provided user_added exclusions into user_path
        if user_exclusions:
            user_path.update(user_exclusions)

        # Update with the new format
        self.config["exclusions"] = {
            "system_generated": sorted(set(system_exclusions)),
            "user_path": sorted(user_path),
            "user_string": sorted(user_string)
        }

        self.save_config(self.config)


    def add_exclusion(self, pattern: str, exclusion_type: str = "path") -> None:
        """Add a user-defined exclusion pattern of the specified type."""
        exclusions = self.get_exclusions()
        
        # Map type to config key
        type_key = f"user_{exclusion_type}"
        
        if type_key not in exclusions:
            exclusions[type_key] = []
            
        if pattern not in exclusions[type_key]:
            exclusions[type_key].append(pattern)
            
        # Update config
        self.set_exclusions(exclusions)

    def remove_exclusion(self, pattern: str, exclusion_type: str = "path") -> None:
        """Remove a user-defined exclusion pattern of the specified type."""
        exclusions = self.get_exclusions()
        
        # Map type to config key
        type_key = f"user_{exclusion_type}"
        
        if type_key in exclusions and pattern in exclusions[type_key]:
            exclusions[type_key].remove(pattern)
            
        # Update config
        self.set_exclusions(exclusions)

"""Configuration management for the code search CLI."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv
from rich.console import Console
from .theme_manager import ThemeManager

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

        console.print(f"Config directory: {self.config_dir}")
        console.print(f"Config file: {self.config_file}")


        self._ensure_config_dir()
        self.config = self._load_config()

        # ✅ Debugging output
        if not self.config:
            console.print("No config found, triggering first-time setup.")

        # ✅ If settings.yaml is missing or base_dir is empty, force setup
        if not self.config or not self.config.get("base_dir"):
            console.print("First-time setup needed.")
            self._first_time_setup()

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if self.env_file.exists():
            load_dotenv(self.env_file)

    def _load_config(self) -> Dict:
        """Load the configuration from file. If missing, return an empty dict."""
        if not self.config_file.exists():
            console.print("Config file does not exist.")
            return {}

        try:
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"Failed to load config: {str(e)}")
            return {}

    def save_config(self, config: Dict) -> None:
        """Save the configuration to file."""
        console.print(f"Saving config: {self.config}") 
        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

    def _first_time_setup(self):
        theme = ThemeManager.get_theme()
        """Prompt the user to set up the application on first launch."""
        console.print(f"\n[{theme['warning']}]It looks like you're starting Code Search CLI for the first time.[/]")
        console.print(f"[{theme['highlight']}]Let's set things up![/]")

        # ✅ Prompt user for base directory
        console.print(f"\nPlease enter the directory where your codebase is located: ", end="")
        base_dir = input().strip()
        base_dir = re.sub(r"^\x1b\[200~|\x1b\[201~$", "", base_dir).strip()

        while not base_dir or not Path(base_dir).exists():
            console.print(f"[{theme['error']}]Invalid directory path. Please enter a valid path:[/] ", end="")
            base_dir = input().strip()

        # ✅ Apply default exclusions based on detected code type
        default_exclusions = [
            "*.pyc", "__pycache__", "*.git", "*.svn", "node_modules", "venv", ".env"
        ]

        # ✅ Prompt user to select theme
        console.print("\nSelect a theme:")
        console.print("[1] Light Mode")
        console.print("[2] Dark Mode")

        theme_choice = input("Enter your choice (1 or 2): ").strip() or "1"
        selected_theme = "light" if theme_choice == "1" else "dark"

        # ✅ Save settings.yaml with user input
        self.config = {
            "base_dir": base_dir,
            "exclusions": default_exclusions,
            "theme": selected_theme,
        }
        self.save_config(self.config)

        console.print(f"\n[{theme['success']}]Setup complete! Code Search CLI is now ready to use.[/]\n")

    def get_base_dir(self) -> str:
        """Get the base directory for code search."""
        return self.config.get("base_dir", "")

    def set_base_dir(self, base_dir: str) -> None:
        """Set the base directory for code search."""
        self.config["base_dir"] = str(Path(base_dir).resolve())
        self.save_config(self.config)

    def get_exclusions(self) -> List[str]:
        """Get the list of exclusion patterns."""
        return self.config.get("exclusions", [])

    def add_exclusion(self, pattern: str) -> None:
        """Add an exclusion pattern."""
        if pattern not in self.config["exclusions"]:
            self.config["exclusions"].append(pattern)
            self.save_config(self.config)

    def remove_exclusion(self, pattern: str) -> None:
        """Remove an exclusion pattern."""
        if pattern in self.config["exclusions"]:
            self.config["exclusions"].remove(pattern)
            self.save_config(self.config)
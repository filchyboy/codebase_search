"""Configuration management for the code search CLI."""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

class ConfigManager:
    """Manages configuration for the code search CLI."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the config manager."""
        self.config_dir = Path(config_dir or Path.home() / ".code-search-cli")
        self.config_file = self.config_dir / "settings.yaml"
        self.env_file = self.config_dir / ".env"
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self._create_default_config()
        if self.env_file.exists():
            load_dotenv(self.env_file)

    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "setup_complete": False,
            "base_dir": str(Path.home()),
            "exclusions": []
        }
        self.save_config(default_config)

    def _load_config(self) -> Dict:
        """Load the configuration from file."""
        try:
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    def save_config(self, config: Dict) -> None:
        """Save the configuration to file."""
        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

    def is_setup_complete(self) -> bool:
        """Check if initial setup has been completed."""
        config = self._load_config()
        return config.get("setup_complete", False)

    def mark_setup_complete(self) -> None:
        """Mark the setup as complete."""
        config = self._load_config()
        config["setup_complete"] = True
        self.save_config(config)

    def get_base_dir(self) -> str:
        """Get the base directory for code search."""
        config = self._load_config()
        return config.get("base_dir", str(Path.home()))

    def set_base_dir(self, base_dir: str) -> None:
        """Set the base directory for code search."""
        config = self._load_config()
        config["base_dir"] = str(Path(base_dir).resolve())
        self.save_config(config)

    def get_exclusions(self) -> List[str]:
        """Get the list of exclusion patterns."""
        config = self._load_config()
        return config.get("exclusions", [])

    def set_exclusions(self, exclusions: List[str]) -> None:
        """Set the list of exclusion patterns."""
        config = self._load_config()
        config["exclusions"] = exclusions
        self.save_config(config)

    def add_exclusion(self, pattern: str) -> None:
        """Add an exclusion pattern."""
        config = self._load_config()
        if "exclusions" not in config:
            config["exclusions"] = []
        if pattern not in config["exclusions"]:
            config["exclusions"].append(pattern)
            self.save_config(config)

    def remove_exclusion(self, pattern: str) -> None:
        """Remove an exclusion pattern."""
        config = self._load_config()
        if "exclusions" in config and pattern in config["exclusions"]:
            config["exclusions"].remove(pattern)
            self.save_config(config)

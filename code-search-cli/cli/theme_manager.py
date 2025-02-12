import yaml
from pathlib import Path

class ThemeManager:
    """Manages the global CLI theme (light or dark mode)."""

    THEME_FILE = Path.home() / ".code-search-cli/theme.yaml"

    DEFAULT_THEME = "light"
    THEMES = {
        "light": {
            "primary": "black",
            "secondary": "dim",
            "highlight": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green",
        },
        "dark": {
            "primary": "white",
            "secondary": "bright_black",
            "highlight": "cyan",
            "warning": "bright_yellow",
            "error": "bright_red",
            "success": "bright_green",
        },
    }

    _current_theme = DEFAULT_THEME

    @classmethod
    def load_theme(cls):
        """Loads the theme from disk or sets default."""
        if cls.THEME_FILE.exists():
            try:
                with open(cls.THEME_FILE, "r") as f:
                    theme_data = yaml.safe_load(f)
                    cls._current_theme = theme_data.get("theme", cls.DEFAULT_THEME)
            except Exception:
                cls._current_theme = cls.DEFAULT_THEME
        else:
            cls.save_theme(cls.DEFAULT_THEME)

    @classmethod
    def save_theme(cls, theme: str):
        """Saves the selected theme to disk."""
        if theme not in cls.THEMES:
            raise ValueError(f"Invalid theme: {theme}")
        cls._current_theme = theme
        with open(cls.THEME_FILE, "w") as f:
            yaml.safe_dump({"theme": theme}, f)

    @classmethod
    def get_theme(cls):
        """Returns the current theme's color settings."""
        return cls.THEMES.get(cls._current_theme, cls.THEMES[cls.DEFAULT_THEME])

    @classmethod
    def set_theme(cls, theme: str):
        """Sets the theme globally and persists it."""
        cls.save_theme(theme)

# Load theme on startup
ThemeManager.load_theme()
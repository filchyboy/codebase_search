import yaml
from pathlib import Path

class ThemeManager:
    """Manages the global CLI theme (light or dark mode)."""

    THEME_FILE = Path.home() / ".code-search-cli/theme.yaml"

    DEFAULT_THEME = "light"
    THEMES = {
        "light": {
            "primary": "#333333",
            "secondary": "#666666",
            "highlight": "#0057B8",
            "warning": "#FFAA00",
            "error": "#B00020",
            "success": "#007A33",
        },
        "dark": {
            "primary": "#DDDDDD",
            "secondary": "#AAAAAA",
            "highlight": "#00A3E0",
            "warning": "#FFC107",
            "error": "#FF4D4D",
            "success": "#32CD32",
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
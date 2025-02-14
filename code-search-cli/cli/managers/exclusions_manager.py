import os
import re
from pathlib import Path
from typing import List, Dict, Set
from ..config_manager import ConfigManager
from ..theme_manager import ThemeManager
from rich.console import Console
console = Console()

class ExclusionsManager:
    """Handles exclusion logic including language-based and user-defined exclusions."""
    theme = ThemeManager.get_theme()
    # Standard exclusions by language
    EXCLUSIONS_BY_LANGUAGE: Dict[str, List[str]] = {
        "Python": ["*.pyc", "__pycache__", "venv", ".pytest_cache", "*.pyo", "*.pyd", "*.whl",
                   ".tox", ".mypy_cache", "pip-wheel-metadata", ".coverage", "nosetests.xml",
                   "*.egg-info", "*.eggs", "htmlcov", ".pytype", "*.log"],
        "JavaScript": ["node_modules", "dist", "build", ".npm", ".yarn", "coverage",
                       "jspm_packages", ".eslintcache", ".cache", "*.log", "bower_components"],
        "Java": ["target", "bin", ".gradle", ".idea", "*.iml", "*.ipr", "*.iws", ".classpath",
                 ".project", ".settings", "*.class", "out", ".mvn", "*.log"],
        "Go": ["bin", "pkg", "*.exe", "*.test", "*.out", "*.mod", "*.sum", ".vscode",
               ".idea", "*.log", ".DS_Store", "vendor"],
        "Rust": ["target", "Cargo.lock", "debug", "release", "incremental", "*.log"],
        "C++": ["*.o", "*.obj", "*.exe", "*.dll", "*.dylib", "*.so", "build", "cmake-build-debug",
                "cmake-build-release", "Makefile", "*.log", "Debug", "Release"],
        "C#": ["bin", "obj", "*.suo", "*.user", "*.csproj.user", "*.dll", "*.exe",
               "*.pdb", "*.appx", "AppPackages", "node_modules", "*.log"],
        "Ruby": ["*.gem", ".bundle", ".yardoc", "coverage", "tmp", "vendor/bundle",
                 "log", "node_modules", "*.log"],
        "PHP": [
            "vendor",
            "*.log",
            "composer.lock",
            "composer.phar",
            ".phpunit.result.cache",
            "node_modules",
            "coverage",
            "cache",
            "*.tar.gz",
        ],
        "Laravel": [
            "storage",
            "bootstrap/cache",
            "node_modules",
            "vendor",
            ".env",
            "composer.lock",
            "public/storage",
            "tests",
            "phpunit.xml",
            "coverage",
            "dist",
        ],
    }

    def __init__(self):
        """Initialize the ExclusionsManager with stored exclusions."""
        self.config = ConfigManager()
        self.base_dir = Path(self.config.get_base_dir())
        self.language = self.detect_codebase_type()
        # ✅ Ensure system_exclusions is initialized
        self.system_exclusions = set()
        self.user_exclusions = set(self.config.get_exclusions())

        # ✅ Ensure exclusions are updated when a new base_dir is set
        if self.base_dir:
            self.update_exclusions()
    def detect_codebase_type(self) -> Set[str]:
        """Detect all applicable frameworks in the codebase instead of returning just one."""

        detected_frameworks = set()

        # ✅ Prioritize Laravel over generic PHP
        if (self.base_dir / "artisan").exists() and (self.base_dir / "composer.json").exists():
            detected_frameworks.add("Laravel")

        if (self.base_dir / "composer.json").exists():
            detected_frameworks.add("PHP")

        if (self.base_dir / "package.json").exists():
            detected_frameworks.add("JavaScript")

        language_signatures = {
            "Python": ["requirements.txt", "setup.py", "Pipfile", "__init__.py"],
            "Java": ["pom.xml", "build.gradle"],
            "Go": ["go.mod", "main.go"],
            "Rust": ["Cargo.toml"],
            "C++": ["CMakeLists.txt", ".cpp", ".h"],
            "C#": [".csproj", "Program.cs"],
            "Ruby": ["Gemfile"],
        }

        for language, signatures in language_signatures.items():
            if any((self.base_dir / signature).exists() for signature in signatures):
                detected_frameworks.add(language)

        if detected_frameworks:
            # console.print(f"Detected codebase types: {', '.join(detected_frameworks)}")
            return detected_frameworks

        return {"Unknown"}

    def update_exclusions(self):
        """Updates exclusions based on all detected frameworks in the codebase."""
        theme = ThemeManager.get_theme()

        # ✅ Detect all relevant frameworks ONCE
        if not hasattr(self, "_cached_frameworks"):
            self._cached_frameworks = self.detect_codebase_type()

        detected_frameworks = self._cached_frameworks
        console.print(f"\nDetected codebase types: [{theme['highlight']}]{', '.join(detected_frameworks)}[/{theme['highlight']}]\n")

        # ✅ Get exclusions for all detected frameworks
        all_exclusions = set()
        for framework in detected_frameworks:
            all_exclusions.update(self.EXCLUSIONS_BY_LANGUAGE.get(framework, []))

        # ✅ Merge with user-defined exclusions
        self.system_exclusions = all_exclusions
        updated_exclusions = sorted(self.system_exclusions | self.user_exclusions)

        # ✅ Save exclusions only if they changed
        current_exclusions = set(self.config.get_exclusions())
        if current_exclusions != set(updated_exclusions):
            self.config.set_exclusions(updated_exclusions)
            console.print(f"\nExclusions updated for detected frameworks: [{theme['success']}]{', '.join(detected_frameworks)}[/{theme['success']}]")
            console.print(f"\nUpdated Exclusions List:\n [{theme['highlight']}]{updated_exclusions}[/{theme['highlight']}]")

    def get_combined_exclusions(self) -> Set[str]:
        """Returns a complete set of exclusions (system + user)."""
        return self.system_exclusions | self.user_exclusions

    def add_exclusion(self, pattern: str):
        """Adds a user-defined exclusion pattern."""
        self.user_exclusions.add(pattern)
        self.config.add_exclusion(pattern)

    def remove_exclusion(self, pattern: str):
        """Removes a user-defined exclusion pattern."""
        if pattern in self.user_exclusions:
            self.user_exclusions.remove(pattern)
            self.config.remove_exclusion(pattern)

    def generate_search_exclusion_regex(self) -> str:
        """Generates a regex pattern for search filtering based on exclusions."""
        combined_exclusions = self.get_combined_exclusions()
        escaped_patterns = [re.escape(pattern).replace("\\*", ".*") for pattern in combined_exclusions]
        return "|".join(escaped_patterns) if escaped_patterns else "(?!)"

    def get_exclusion_summary(self) -> str:
        """Returns a formatted string of exclusions for display."""
        exclusions_list = sorted(self.get_combined_exclusions())
        return "\n".join(exclusions_list) if exclusions_list else "No exclusions configured."
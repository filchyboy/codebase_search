import os
import re
from pathlib import Path
from typing import List, Dict, Set
from ..config_manager import ConfigManager

class ExclusionsManager:
    """Handles exclusion logic including language-based and user-defined exclusions."""

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
        "PHP": ["vendor", "*.log", "composer.lock", "composer.phar", ".phpunit.result.cache",
                "node_modules", "coverage", "cache", "*.tar.gz"],
    }

    def __init__(self):
        """Initialize the ExclusionsManager with stored exclusions."""
        self.config = ConfigManager()
        self.base_dir = Path(self.config.get_base_dir())
        self.language = self.detect_codebase_type()
        self.system_exclusions = set(self.EXCLUSIONS_BY_LANGUAGE.get(self.language, []))
        self.user_exclusions = set(self.config.get_exclusions())

    def detect_codebase_type(self) -> str:
        """Detects the primary codebase language based on project files."""
        language_signatures = {
            "Python": ["requirements.txt", "setup.py", "Pipfile", "__init__.py"],
            "JavaScript": ["package.json", "yarn.lock"],
            "Java": ["pom.xml", "build.gradle"],
            "Go": ["go.mod", "main.go"],
            "Rust": ["Cargo.toml"],
            "C++": ["CMakeLists.txt", ".cpp", ".h"],
            "C#": [".csproj", "Program.cs"],
            "Ruby": ["Gemfile"],
            "PHP": ["composer.json", "index.php"],
        }

        for language, signatures in language_signatures.items():
            if any((self.base_dir / signature).exists() for signature in signatures):
                return language
        return "Unknown"

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
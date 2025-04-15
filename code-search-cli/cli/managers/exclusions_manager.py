import os
import re
from pathlib import Path
from typing import List, Dict, Set
from cli.managers.config_manager import ConfigManager
from cli.managers.theme_manager import ThemeManager
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
        "JavaScript": ["node_modules", "node_modules/", "dist", "build", ".npm", ".yarn", "coverage",
                       "jspm_packages", ".eslintcache", ".cache", "*.log", "bower_components"],
        "Java": ["target", "bin", ".gradle", ".idea", "*.iml", "*.ipr", "*.iws", ".classpath",
                 ".project", ".settings", "*.class", "out", ".mvn", "*.log"],
        "Go": ["bin", "pkg", "*.exe", "*.test", "*.out", "*.mod", "*.sum", ".vscode",
               ".idea", "*.log", ".DS_Store", "vendor", "vendor/"],
        "Rust": ["target", "Cargo.lock", "debug", "release", "incremental", "*.log"],
        "C++": ["*.o", "*.obj", "*.exe", "*.dll", "*.dylib", "*.so", "build", "cmake-build-debug",
                "cmake-build-release", "Makefile", "*.log", "Debug", "Release"],
        "C#": ["bin", "obj", "*.suo", "*.user", "*.csproj.user", "*.dll", "*.exe",
               "*.pdb", "*.appx", "AppPackages", "node_modules", "*.log"],
        "Ruby": ["*.gem", ".bundle", ".yardoc", "coverage", "tmp", "vendor/bundle",
                 "log", "node_modules", "*.log"],
        "PHP": ["vendor", "vendor/", "*.log", "composer.lock", "composer.phar", ".phpunit.result.cache",
                "node_modules", "coverage", "cache", "*.tar.gz"],
    }

    # Standard exclusions by framework
    EXCLUSIONS_BY_FRAMEWORK: Dict[str, List[str]] = {
        "Laravel": ["storage", "bootstrap/cache", "node_modules", "node_modules/", 
                   "vendor", "vendor/", ".env", "composer.lock", "public/storage", 
                   "tests", "phpunit.xml", "coverage", "dist"],
        "Node.js": ["node_modules", "node_modules/", "dist", "dist/", "coverage", "coverage/"],
        "Django": ["db.sqlite3", "migrations", "migrations/", "__pycache__", "__pycache__/"],
        "Spring Boot": ["target", "target/", ".gradle", ".gradle/", ".mvn", ".mvn/"],
        "Ruby on Rails": ["log", "log/", "tmp", "tmp/", ".bundle", ".bundle/"],
    }

    def __init__(
        self,
        base_dir: str,
        config_manager: ConfigManager
    ):
        """Initialize the ExclusionsManager with stored exclusions."""
        self.config = config_manager
        self.base_dir = Path(base_dir).resolve()
        self.detected_frameworks = self.detect_codebase_type()

        # Ensure system/user exclusions are initialized properly with separate types
        self.system_path_exclusions = set()
        self.user_path_exclusions = set()
        self.user_string_exclusions = set()
        
        # Load exclusions from config
        self._load_exclusions_from_config()

        # Ensure exclusions are updated when a new base_dir is set
        if self.base_dir:
            self.update_exclusions()

    def detect_codebase_type(self) -> Set[str]:
        """Detect all applicable frameworks in the codebase instead of returning just one."""
        detected_frameworks = set()
        base_dir = Path(self.base_dir)

        if (base_dir / "artisan").exists() and (base_dir / "composer.json").exists():
            detected_frameworks.add("Laravel")
        if (base_dir / "composer.json").exists():
            detected_frameworks.add("PHP")
        if (base_dir / "package.json").exists():
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

        return detected_frameworks if detected_frameworks else {"Unknown"}


    def _load_exclusions_from_config(self):
        """Load exclusions from config file with type separation."""
        config_exclusions = self.config.get_exclusions()
        
        # System exclusions are always path-based
        self.system_path_exclusions = set(config_exclusions.get("system_generated", []))
        
        # User exclusions are separated by type
        self.user_path_exclusions = set(config_exclusions.get("user_path", []))
        self.user_string_exclusions = set(config_exclusions.get("user_string", []))
        
        # For backward compatibility - migrate existing user_added to path_exclusions
        if "user_added" in config_exclusions:
            self.user_path_exclusions.update(config_exclusions.get("user_added", []))
    
    def update_exclusions(self):
        """Updates exclusions based on all detected frameworks in the codebase."""
        theme = ThemeManager.get_theme()
        current_base_dir = Path(self.config.get_base_dir())

        # If root directory changed, reset cached framework detection
        if not hasattr(self, "_cached_frameworks") or self.base_dir != current_base_dir:
            self.base_dir = current_base_dir
            self._cached_frameworks = self.detect_codebase_type()

        detected_frameworks = self._cached_frameworks

        # Get exclusions for all detected frameworks
        all_exclusions = set()
        for framework in detected_frameworks:
            all_exclusions.update(self.EXCLUSIONS_BY_LANGUAGE.get(framework, []))
            all_exclusions.update(self.EXCLUSIONS_BY_FRAMEWORK.get(framework, []))

        self.system_path_exclusions = all_exclusions

        # Save exclusions only if they changed
        current_exclusions = set(self.config.get_exclusions().get("system_generated", []))
        if current_exclusions != set(all_exclusions):
            self.config.set_exclusions({
                "system_generated": sorted(self.system_path_exclusions),
                "user_path": sorted(self.user_path_exclusions),
                "user_string": sorted(self.user_string_exclusions)
            })

    def get_language_exclusions(self) -> Set[str]:
        """Retrieve language-specific exclusions based on detected languages."""
        return {
            exclusion for framework in self.detected_frameworks
            for exclusion in self.EXCLUSIONS_BY_LANGUAGE.get(framework, [])
        }

    def get_framework_exclusions(self) -> Set[str]:
        """Retrieve framework-specific exclusions based on detected frameworks."""
        return {
            exclusion for framework in self.detected_frameworks
            for exclusion in self.EXCLUSIONS_BY_FRAMEWORK.get(framework, [])
        }

    def get_user_exclusions(self) -> Dict[str, Set[str]]:
        """Retrieve user-defined exclusions by type."""
        return {
            "path": self.user_path_exclusions,
            "string": self.user_string_exclusions
        }

    def get_combined_exclusions(self) -> Dict[str, Set[str]]:
        """Returns exclusions grouped by type."""
        return {
            "language": self.get_language_exclusions(),
            "framework": self.get_framework_exclusions(),
            "user_path": self.user_path_exclusions,
            "user_string": self.user_string_exclusions
        }

    def add_exclusion(self, pattern: str, exclusion_type: str = "path"):
        """Adds a user-defined exclusion pattern with type specification."""
        if exclusion_type not in ["path", "string"]:
            console.print(f"[{self.theme['error']}]Invalid exclusion type: {exclusion_type}[/{self.theme['error']}]")
            return
            
        # Check if pattern already exists in appropriate collection
        if exclusion_type == "path" and pattern in self.user_path_exclusions:
            console.print(f"[{self.theme['warning']}]Pattern '{pattern}' is already excluded as a path.[/{self.theme['warning']}]")
            return
        elif exclusion_type == "string" and pattern in self.user_string_exclusions:
            console.print(f"[{self.theme['warning']}]Pattern '{pattern}' is already excluded as a string.[/{self.theme['warning']}]")
            return

        # Add to the appropriate collection
        if exclusion_type == "path":
            self.user_path_exclusions.add(pattern)
        else:
            self.user_string_exclusions.add(pattern)
            
        # Save to config
        self.config.add_exclusion(pattern, exclusion_type)
        console.print(f"Successfully added {exclusion_type} exclusion: [{self.theme['highlight']}]{pattern}[/{self.theme['highlight']}]")

    def remove_exclusion(self, pattern: str, exclusion_type: str = "path"):
        """Removes a user-defined exclusion pattern with type specification."""
        if exclusion_type not in ["path", "string"]:
            console.print(f"[{self.theme['error']}]Invalid exclusion type: {exclusion_type}[/{self.theme['error']}]")
            return
            
        # Check if pattern exists in appropriate collection
        if exclusion_type == "path" and pattern not in self.user_path_exclusions:
            console.print(f"[{self.theme['warning']}]Pattern '{pattern}' is not in path exclusions.[/{self.theme['warning']}]")
            return
        elif exclusion_type == "string" and pattern not in self.user_string_exclusions:
            console.print(f"[{self.theme['warning']}]Pattern '{pattern}' is not in string exclusions.[/{self.theme['warning']}]")
            return

        # Remove from appropriate collection
        if exclusion_type == "path":
            self.user_path_exclusions.remove(pattern)
        else:
            self.user_string_exclusions.remove(pattern)
            
        # Save to config
        self.config.remove_exclusion(pattern, exclusion_type)
        console.print(f"Successfully removed {exclusion_type} exclusion: [{self.theme['highlight']}]{pattern}[/{self.theme['highlight']}]")

    def generate_path_exclusion_regex(self) -> str:
        """Generates a regex pattern for filtering paths based on exclusions."""
        combined_exclusions = self.system_path_exclusions | self.user_path_exclusions
        
        # Ensure exclusions apply correctly to full paths
        escaped_patterns = [
            re.escape(pattern).replace("\\*", ".*").replace("\\/", "/")  # Fix slashes for cross-platform compatibility
            for pattern in combined_exclusions
        ]
        
        return "|".join(escaped_patterns) if escaped_patterns else "(?!)"
        
    def generate_string_exclusion_regex(self) -> str:
        """Generates a regex pattern for filtering content based on exclusions."""
        if not self.user_string_exclusions:
            return ""
            
        # String exclusions are simple pattern matches
        escaped_patterns = [re.escape(pattern) for pattern in self.user_string_exclusions]
        return "|".join(escaped_patterns)
        
    def generate_search_exclusion_regex(self) -> Dict[str, str]:
        """Generates regex patterns for both path and string filtering."""
        return {
            "path": self.generate_path_exclusion_regex(),
            "string": self.generate_string_exclusion_regex()
        }

    def get_exclusion_summary(self) -> str:
        """Returns a formatted string of exclusions for display."""
        exclusions = self.get_combined_exclusions()
        
        formatted_sections = []
        
        # Display language exclusions
        if exclusions.get("language"):
            formatted_sections.append(
                f"[{self.theme['highlight']}]Language exclusions (path):[/{self.theme['highlight']}]\n"
                + "\n".join(sorted(exclusions["language"]))
            )
            
        # Display framework exclusions
        if exclusions.get("framework"):
            formatted_sections.append(
                f"[{self.theme['highlight']}]Framework exclusions (path):[/{self.theme['highlight']}]\n"
                + "\n".join(sorted(exclusions["framework"]))
            )
            
        # Display user path exclusions
        if exclusions.get("user_path"):
            formatted_sections.append(
                f"[{self.theme['highlight']}]User-defined path exclusions:[/{self.theme['highlight']}]\n"
                + "\n".join(sorted(exclusions["user_path"]))
            )
            
        # Display user string exclusions
        if exclusions.get("user_string"):
            formatted_sections.append(
                f"[{self.theme['highlight']}]User-defined string exclusions:[/{self.theme['highlight']}]\n"
                + "\n".join(sorted(exclusions["user_string"]))
            )

        return "\n\n".join(formatted_sections) if formatted_sections else f"[{self.theme['warning']}]No exclusions configured.[/{self.theme['warning']}]"
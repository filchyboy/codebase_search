"""Tests for the search engine."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.managers.search_engine import SearchEngine, SearchResult

@pytest.fixture
def mock_config_manager():
    """Create a mock config manager."""
    config = MagicMock()
    config.get_exclusions.return_value = {"system_generated": [], "user_added": []}
    return config

@pytest.fixture
def test_directory():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        test_files = {
            "file1.txt": "This is a test file with some test content.",
            "file2.py": "def test_function():\n    return 'test'",
            "dir1/file3.js": "function test() {\n    console.log('test');\n}",
            "dir1/dir2/file4.md": "# Test Markdown\nThis is a test markdown file.",
            "node_modules/ignored.js": "This should be ignored",
            ".git/ignored.txt": "This should also be ignored",
        }
        
        # Create the files
        for file_path, content in test_files.items():
            file_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        
        yield Path(temp_dir)

class TestSearchEngine:
    """Tests for the SearchEngine class."""
    
    @patch('cli.managers.exclusions_manager.ExclusionsManager')
    def test_search_plain_text(self, mock_exclusions_manager, test_directory, mock_config_manager):
        """Test plain text search."""
        # Mock the exclusions manager
        mock_exclusions_manager.return_value.get_combined_exclusions.return_value = {
            "language": set(["node_modules/", ".git/"]),
            "framework": set(),
            "user": set(),
        }
        
        # Create the search engine
        search_engine = SearchEngine(test_directory, mock_config_manager)
        
        # Test plain text search
        results = search_engine.search("test")
        
        # Verify results
        assert len(results) == 5  # 5 instances of "test" in non-excluded files
        assert all(isinstance(result, SearchResult) for result in results)
        
        # Check that excluded files aren't in results
        assert not any("node_modules" in str(result.file_path) for result in results)
        assert not any(".git" in str(result.file_path) for result in results)
    
    @patch('cli.managers.exclusions_manager.ExclusionsManager')
    def test_search_regex(self, mock_exclusions_manager, test_directory, mock_config_manager):
        """Test regex search."""
        # Mock the exclusions manager
        mock_exclusions_manager.return_value.get_combined_exclusions.return_value = {
            "language": set(["node_modules/", ".git/"]),
            "framework": set(),
            "user": set(),
        }
        
        # Create the search engine
        search_engine = SearchEngine(test_directory, mock_config_manager)
        
        # Test regex search
        results = search_engine.search(r"def\s+\w+", use_regex=True)
        
        # Verify results
        assert len(results) == 1  # Should match 'def test_function'
        assert "def test_function" in results[0].line_content
    
    @patch('cli.managers.exclusions_manager.ExclusionsManager')
    def test_search_case_insensitive(self, mock_exclusions_manager, test_directory, mock_config_manager):
        """Test case-insensitive search."""
        # Mock the exclusions manager
        mock_exclusions_manager.return_value.get_combined_exclusions.return_value = {
            "language": set(["node_modules/", ".git/"]),
            "framework": set(),
            "user": set(),
        }
        
        # Create the search engine
        search_engine = SearchEngine(test_directory, mock_config_manager)
        
        # Test case-insensitive search (TEST instead of test)
        results = search_engine.search("TEST", case_sensitive=False)
        
        # Verify results
        assert len(results) == 5  # Should find all instances of "test" ignoring case
    
    @patch('cli.managers.exclusions_manager.ExclusionsManager')
    def test_exclusions(self, mock_exclusions_manager, test_directory, mock_config_manager):
        """Test exclusion patterns."""
        # Mock the exclusions manager with custom exclusions
        mock_exclusions_manager.return_value.get_combined_exclusions.return_value = {
            "language": set(),
            "framework": set(),
            "user": set(["*.py", "dir1/"]),  # Exclude Python files and dir1 directory
        }
        
        # Create the search engine
        search_engine = SearchEngine(test_directory, mock_config_manager)
        
        # Run search
        results = search_engine.search("test")
        
        # Verify results
        assert len(results) == 1  # Only file1.txt should be included
        assert "file1.txt" in str(results[0].file_path)
        
        # Check that excluded files aren't in results
        assert not any(".py" in str(result.file_path) for result in results)
        assert not any("dir1" in str(result.file_path) for result in results)
"""Tests for search functionality and directory switching."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from cli.managers.config_manager import ConfigManager
from cli.search_cli import handle_search_command, handle_init_command, interactive_repl


@pytest.fixture
def temp_dirs():
    """Create two temporary directories for testing directory switching."""
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        # Create test file in dir1
        test_file1 = Path(dir1) / "test_file1.txt"
        with open(test_file1, "w") as f:
            f.write("This is a test file with a search term: testpattern here")
            
        # Create test file in dir2
        test_file2 = Path(dir2) / "test_file2.txt"
        with open(test_file2, "w") as f:
            f.write("This file has different content: another_test_pattern here")
            
        yield (dir1, dir2)


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager that allows base_dir to be changed."""
    mock_config = MagicMock(spec=ConfigManager)
    base_dir = None
    
    def get_base_dir():
        return base_dir
    
    def set_base_dir(new_dir):
        nonlocal base_dir
        base_dir = new_dir
    
    mock_config.get_base_dir.side_effect = get_base_dir
    mock_config.set_base_dir.side_effect = set_base_dir
    
    return mock_config


def test_handle_search_directory_switching(temp_dirs, capsys):
    """Test that handle_search_command uses the latest directory from config."""
    dir1, dir2 = temp_dirs
    
    # Mock ConfigManager to return dir1
    with patch('cli.search_cli.ConfigManager') as mock_config:
        config_instance = MagicMock()
        config_instance.get_base_dir.return_value = dir1
        mock_config.return_value = config_instance
        
        # Search for "testpattern" which is in dir1
        handle_search_command("testpattern", "dummy_dir")
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify dir1 is used and testpattern is found
        assert dir1 in captured.out
        assert "testpattern" in captured.out
        assert "Total matches found:         1" in captured.out
        
    # Now mock ConfigManager to return dir2
    with patch('cli.search_cli.ConfigManager') as mock_config:
        config_instance = MagicMock()
        config_instance.get_base_dir.return_value = dir2
        mock_config.return_value = config_instance
        
        # Search again with the same pattern
        handle_search_command("testpattern", "dummy_dir")
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify dir2 is used and testpattern is not found (it's only in dir1)
        assert dir2 in captured.out
        assert "Total matches found:         0" in captured.out
        
        # Search for "another_test_pattern" which is in dir2
        handle_search_command("another_test_pattern", "dummy_dir")
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify dir2 is used and another_test_pattern is found
        assert dir2 in captured.out
        assert "another_test_pattern" in captured.out
        assert "Total matches found:         1" in captured.out


@pytest.mark.parametrize("init_input, expected_dir", [
    # Test case: User selects "n" to not change directory
    (["n"], "initial_dir"),
    # Test case: User selects "y" to change directory, enters new dir, confirms with "y"
    (["y", "new_dir", "y"], "new_dir"),
    # Test case: User selects "y", enters new dir, but cancels with "n"
    (["y", "new_dir", "n"], "initial_dir"),
])
def test_init_command_directory_change(init_input, expected_dir, monkeypatch):
    """Test the init command's directory changing functionality."""
    # Setup test paths
    initial_dir = "initial_dir"
    
    # Mock Path.exists to always return True for our test paths
    def mock_exists(self):
        return True
    
    with patch('cli.search_cli.Path.exists', mock_exists):
        with patch('cli.search_cli.ConfigManager') as mock_config:
            # Setup config manager
            config_instance = MagicMock()
            config_instance.get_base_dir.return_value = initial_dir
            mock_config.return_value = config_instance
            
            # Mock the input function to return our predefined inputs
            input_values = iter(init_input)
            monkeypatch.setattr('builtins.input', lambda *args: next(input_values))
            
            # Run the init command
            try:
                handle_init_command()
            except StopIteration:
                # This can happen if we run out of input values, which is fine
                pass
            
            # If expected_dir is initial_dir, then set_base_dir should not be called
            # Otherwise, it should be called with the new dir
            if expected_dir != initial_dir:
                config_instance.set_base_dir.assert_called_once_with(expected_dir)
            elif expected_dir == initial_dir and "y" in init_input:
                # We entered "y" to change, but then canceled
                config_instance.set_base_dir.assert_not_called()
            else:
                # We entered "n" to not change
                config_instance.set_base_dir.assert_not_called()
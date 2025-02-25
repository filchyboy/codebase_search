"""Test script to verify the directory switching functionality."""

import os
import tempfile
from pathlib import Path

from code_search_cli.cli.search_cli import handle_search_command

def test_directory_switching():
    """Test that handle_search_command uses the latest directory from config."""
    # Create two temporary directories
    with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
        # Create test file in dir1
        test_file1 = Path(dir1) / "test_file1.txt"
        with open(test_file1, "w") as f:
            f.write("This is a test file with a search term: testpattern")
        
        # Create test file in dir2
        test_file2 = Path(dir2) / "test_file2.txt"
        with open(test_file2, "w") as f:
            f.write("This is another test file with a different search term: anothertestpattern")
        
        print(f"\n----- Testing directory switching -----")
        print(f"Created test files in:")
        print(f"  Directory 1: {dir1}")
        print(f"  Directory 2: {dir2}")
        
        # Test with manually patched directories
        from unittest.mock import patch, MagicMock
        
        # Test with dir1
        print(f"\n----- Testing search in Directory 1 -----")
        with patch('code_search_cli.cli.search_cli.ConfigManager') as mock_config:
            config_instance = MagicMock()
            config_instance.get_base_dir.return_value = dir1
            mock_config.return_value = config_instance
            
            # Search for testpattern which is in dir1
            handle_search_command("testpattern", "dummy_dir")
        
        # Test with dir2
        print(f"\n----- Testing search in Directory 2 -----")
        with patch('code_search_cli.cli.search_cli.ConfigManager') as mock_config:
            config_instance = MagicMock()
            config_instance.get_base_dir.return_value = dir2
            mock_config.return_value = config_instance
            
            # Search for testpattern which is not in dir2
            handle_search_command("testpattern", "dummy_dir")
            
            # Search for anothertestpattern which is in dir2
            handle_search_command("anothertestpattern", "dummy_dir")
        
        print(f"\n----- Test completed -----")
        print(f"If the search reports show the correct directories, the fix is working.")

if __name__ == "__main__":
    test_directory_switching()
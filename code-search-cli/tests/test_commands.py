"""Tests for CLI commands."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.commands.init_command import init
from cli.commands.exclusions_command import exclusions
from cli.config_manager import ConfigManager

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_init_command(runner, temp_config_dir):
    """Test the init command."""
    with runner.isolated_filesystem():
        # Create a test directory to initialize with
        test_dir = Path("test_dir")
        test_dir.mkdir()
        
        result = runner.invoke(init, ["--base-dir", str(test_dir)])
        assert result.exit_code == 0
        assert "Successfully initialized" in result.output

def test_init_command_nonexistent_dir(runner, temp_config_dir):
    """Test init command with non-existent directory."""
    result = runner.invoke(init, ["--base-dir", "nonexistent"])
    assert result.exit_code != 0
    assert "Error" in result.output

def test_exclusions_add_command(runner, temp_config_dir):
    """Test adding exclusion patterns."""
    config = ConfigManager(temp_config_dir)
    result = runner.invoke(exclusions, ["add", "*.test"])
    
    assert result.exit_code == 0
    assert "*.test" in config.get_exclusions()

def test_exclusions_remove_command(runner, temp_config_dir):
    """Test removing exclusion patterns."""
    config = ConfigManager(temp_config_dir)
    
    # First add a pattern
    runner.invoke(exclusions, ["add", "*.test"])
    
    # Then remove it
    result = runner.invoke(exclusions, ["remove", "*.test"])
    assert result.exit_code == 0
    assert "*.test" not in config.get_exclusions()

def test_exclusions_list_command(runner, temp_config_dir):
    """Test listing exclusion patterns."""
    config = ConfigManager(temp_config_dir)
    
    # Add some patterns
    runner.invoke(exclusions, ["add", "*.test1"])
    runner.invoke(exclusions, ["add", "*.test2"])
    
    # List them
    result = runner.invoke(exclusions, ["list"])
    assert result.exit_code == 0
    assert "*.test1" in result.output
    assert "*.test2" in result.output

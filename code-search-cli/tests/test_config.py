"""Tests for the configuration manager."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from cli.config_manager import ConfigManager

@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_config_manager_initialization(temp_config_dir):
    """Test that ConfigManager initializes correctly."""
    config_manager = ConfigManager(temp_config_dir)
    assert Path(temp_config_dir).exists()
    assert (Path(temp_config_dir) / "settings.yaml").exists()

def test_default_config_creation(temp_config_dir):
    """Test that default configuration is created correctly."""
    config_manager = ConfigManager(temp_config_dir)
    config_file = Path(temp_config_dir) / "settings.yaml"
    
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    
    assert "base_dir" in config
    assert "exclusions" in config
    assert isinstance(config["exclusions"], list)

def test_add_remove_exclusion(temp_config_dir):
    """Test adding and removing exclusion patterns."""
    config_manager = ConfigManager(temp_config_dir)
    
    # Add new exclusion
    test_pattern = "*.test"
    config_manager.add_exclusion(test_pattern)
    assert test_pattern in config_manager.get_exclusions()
    
    # Remove exclusion
    config_manager.remove_exclusion(test_pattern)
    assert test_pattern not in config_manager.get_exclusions()

def test_base_dir_operations(temp_config_dir):
    """Test setting and getting base directory."""
    config_manager = ConfigManager(temp_config_dir)
    
    test_dir = "/test/path"
    config_manager.set_base_dir(test_dir)
    assert config_manager.get_base_dir() == test_dir

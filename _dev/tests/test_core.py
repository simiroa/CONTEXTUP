import sys
from pathlib import Path
import pytest

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.config import MenuConfig
from core.registry import RegistryManager

def test_config_loading():
    config = MenuConfig("menu_config.json")
    assert len(config.items) > 0
    
    item = config.get_item_by_id("image_format_convert")
    assert item is not None
    assert item['name'] == "Convert Image Format"

def test_registry_command_generation():
    config = MenuConfig("menu_config.json")
    manager = RegistryManager(config)
    
    cmd = manager._get_command("test_id")
    assert "pythonw.exe" in cmd
    assert "menu.py" in cmd
    assert "test_id" in cmd
    assert "%1" in cmd
    assert cmd.startswith('"')
    assert cmd.endswith('"')

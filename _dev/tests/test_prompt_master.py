import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch

# Add src/scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'scripts'))

# Mock customtkinter before importing prompt_master
sys.modules["customtkinter"] = MagicMock()
sys.modules["tkinter"] = MagicMock()

# Now import the module to test
# We need to expose the logic classes or refactor the script to be testable.
# Since the script is a single file with a GUI class, we can test the logic by instantiating the app 
# (with mocked GUI) or extracting the logic.
# For now, let's just verify we can import it and the paths are correct.

def test_paths():
    from prompt_master import PRESETS_DIR, TAGS_FILE
    assert os.path.exists(PRESETS_DIR)
    assert os.path.exists(TAGS_FILE)

def test_preset_loading():
    from prompt_master import PRESETS_DIR
    nanobanana_dir = os.path.join(PRESETS_DIR, "nanobanana")
    assert os.path.exists(nanobanana_dir)
    
    preset_file = os.path.join(nanobanana_dir, "gashapon.json")
    assert os.path.exists(preset_file)
    
    with open(preset_file, 'r') as f:
        data = json.load(f)
    
    assert data["engine"] == "nanobanana"
    assert "{name}" in data["template"]

def test_template_rendering_logic():
    # Simulate the logic used in update_output
    template = "Hello {name}, welcome to {place}."
    inputs = {"name": "World"}
    options = {"place": "ContextUp"}
    
    for key, val in inputs.items():
        template = template.replace(f"{{{key}}}", val)
        
    for key, val in options.items():
        template = template.replace(f"{{{key}}}", val)
        
    assert template == "Hello World, welcome to ContextUp."

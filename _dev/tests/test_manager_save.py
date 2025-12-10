import sys
import os
import json
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Setup paths
# We are in tests/, so parent is root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src" / "scripts"
sys.path.append(str(SRC_DIR))

# Mock ctk and tkinter before importing manager_gui
mock_ctk_module = types.ModuleType("customtkinter")

class MockCTk:
    def __init__(self, *args, **kwargs): pass
    def mainloop(self): pass
    def after(self, *args, **kwargs): pass
    def withdraw(self): pass
    def deiconify(self): pass
    def geometry(self, *args, **kwargs): pass
    def title(self, *args, **kwargs): pass
    def configure(self, *args, **kwargs): pass
    def protocol(self, *args, **kwargs): pass
    def bind(self, *args, **kwargs): pass
    def grid_columnconfigure(self, *args, **kwargs): pass
    def grid_rowconfigure(self, *args, **kwargs): pass

class MockWidget:
    def __init__(self, *args, **kwargs): pass
    def pack(self, *args, **kwargs): pass
    def grid(self, *args, **kwargs): pass
    def place(self, *args, **kwargs): pass
    def configure(self, *args, **kwargs): pass
    def bind(self, *args, **kwargs): pass
    def destroy(self): pass
    def winfo_children(self): return []
    def delete(self, *args): pass
    def insert(self, *args): pass
    def get(self): return ""
    def set(self, value): pass
    def add(self, *args): return self
    def grid_columnconfigure(self, *args, **kwargs): pass
    def grid_rowconfigure(self, *args, **kwargs): pass

mock_ctk_module.CTk = MockCTk
mock_ctk_module.CTkToplevel = MockCTk # Toplevel behaves like CTk for our purposes
mock_ctk_module.CTkButton = MockWidget
mock_ctk_module.CTkLabel = MockWidget
mock_ctk_module.CTkFrame = MockWidget
mock_ctk_module.CTkEntry = MockWidget
mock_ctk_module.CTkOptionMenu = MockWidget
mock_ctk_module.CTkComboBox = MockWidget
mock_ctk_module.CTkCheckBox = MockWidget
mock_ctk_module.CTkSwitch = MockWidget
mock_ctk_module.CTkScrollableFrame = MockWidget
mock_ctk_module.CTkTextbox = MockWidget
mock_ctk_module.CTkTabview = MockWidget
mock_ctk_module.CTkInputDialog = MockWidget
mock_ctk_module.CTkFont = MagicMock()
mock_ctk_module.CTkImage = MagicMock()
mock_ctk_module.set_appearance_mode = MagicMock()
mock_ctk_module.set_default_color_theme = MagicMock()
mock_ctk_module.filedialog = MagicMock()

class MockVar:
    def __init__(self, value=None): self._val = value
    def set(self, value): self._val = value
    def get(self): return self._val

mock_ctk_module.StringVar = MockVar
mock_ctk_module.BooleanVar = MockVar
mock_ctk_module.IntVar = MockVar

sys.modules["customtkinter"] = mock_ctk_module

sys.modules["tkinter"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["tkinter.filedialog"] = MagicMock()
sys.modules["tkinter.colorchooser"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()

# Import ManagerGUI
try:
    from manager_gui import ManagerGUI
except ImportError:
    print(f"SRC_DIR: {SRC_DIR}")
    print(f"sys.path: {sys.path}")
    raise

import traceback

def test_save_logic():
    print("Testing ManagerGUI save logic...")
    
    # Initialize ManagerGUI (mocked)
    # Patch ManagerGUI.__init__ to avoid UI setup
    with unittest.mock.patch('manager_gui.ManagerGUI.__init__', return_value=None) as mock_init:
        app = ManagerGUI()
        # Manually setup required attributes
        app.config_data = []
        app.settings = {"CATEGORY_COLORS": {}}
        app.config_path = PROJECT_ROOT / "config" / "menu_config.json"
        
        # Mock UI methods called by save_config
        app.refresh_list = MagicMock()
        app.refresh_group_list = MagicMock()
        
        # Create dummy config data
        app.config_data = [
            {
                "id": "test_ai_tool",
                "name": "Test AI Tool",
                "category": "AI",
                "command": "echo ai",
                "enabled": True
            },
            {
                "id": "test_video_tool",
                "name": "Test Video Tool",
                "category": "Video",
                "command": "echo video",
                "enabled": False
            }
        ]
        
        # Run save_config
        app.save_config()
    
    # Verify category files
    ai_path = PROJECT_ROOT / "config" / "menu_categories" / "ai.json"
    video_path = PROJECT_ROOT / "config" / "menu_categories" / "video.json"
    
    if not ai_path.exists():
        print("FAIL: ai.json not created.")
        return
    if not video_path.exists():
        print("FAIL: video.json not created.")
        return
        
    with open(ai_path, 'r') as f:
        data = json.load(f)
        if data[0]["id"] != "test_ai_tool":
            print("FAIL: ai.json content incorrect.")
            print(f"Expected test_ai_tool, got: {data[0]['id']}")
            print(f"Full content: {json.dumps(data, indent=2)}")
            return

    print("PASS: Category files created correctly.")
    
    # Verify menu_config.json regeneration
    menu_config_path = PROJECT_ROOT / "config" / "menu_config.json"
    if not menu_config_path.exists():
        print("FAIL: menu_config.json not regenerated.")
        return
        
    with open(menu_config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        ids = [item.get("id") for item in data]
        if "test_ai_tool" in ids and "test_video_tool" in ids:
            print("PASS: menu_config.json regenerated correctly.")
        else:
            print("FAIL: menu_config.json missing test items.")
            print(f"Found IDs: {ids}")

if __name__ == "__main__":
    test_save_logic()

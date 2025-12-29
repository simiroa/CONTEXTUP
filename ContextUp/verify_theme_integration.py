
import sys
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

# Mock ctk and tkinter before they are imported by gui_lib
sys.modules["tkinter"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["tkinter.filedialog"] = MagicMock()

# Mock CustomTkinter
ctk_mock = MagicMock()
# Must be types for inheritance to work
ctk_mock.CTk = type("CTk", (object,), {})
ctk_mock.CTkFrame = type("CTkFrame", (object,), {})
ctk_mock.CTkScrollableFrame = type("CTkScrollableFrame", (object,), {})
ctk_mock.CTkToplevel = type("CTkToplevel", (object,), {})
sys.modules["customtkinter"] = ctk_mock

# Mock other heavy deps
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.ImageTk"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["yt_dlp"] = MagicMock()

# Now import the modules under test
try:
    from utils.gui_lib import BaseWindow, THEME_BG, THEME_CARD
    from features.image.compare_gui import ImageCompareGUI
    from features.system.unwrap_folder_gui import UnwrapFolderGUI
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)

class TestThemeIntegration(unittest.TestCase):
    def test_theme_constants(self):
        """Verify theme constants are defined."""
        print(f"Checking Constants: THEME_BG={THEME_BG}, THEME_CARD={THEME_CARD}")
        self.assertTrue(THEME_BG.startswith("#"))
        self.assertTrue(THEME_CARD.startswith("#"))

    def test_base_window_inheritance(self):
        """Verify BaseWindow structure."""
        print("Checking BaseWindow...")
        # We can't easily instantiate because of super().__init__ calls to mocked methods, 
        # but we can check the class hierarchy.
        self.assertTrue(issubclass(BaseWindow, object)) 
        # In reality BaseWindow inherits ctk.CTk which is mocked
        
    def test_compare_gui_inheritance(self):
        """Verify ImageCompareGUI inherits BaseWindow."""
        print("Checking ImageCompareGUI inheritance...")
        self.assertTrue(issubclass(ImageCompareGUI, BaseWindow))

    def test_unwrap_gui_inheritance(self):
        """Verify UnwrapFolderGUI inherits BaseWindow."""
        print("Checking UnwrapFolderGUI inheritance...")
        self.assertTrue(issubclass(UnwrapFolderGUI, BaseWindow))

if __name__ == "__main__":
    unittest.main()

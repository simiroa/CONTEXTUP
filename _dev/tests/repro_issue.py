import sys
import types
from unittest.mock import MagicMock
from pathlib import Path

# Mocks
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
    def grid(self, *args, **kwargs):
        print(f"DEBUG: MockWidget.grid called on {self}")
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
mock_ctk_module.CTkToplevel = MockCTk
mock_ctk_module.CTkButton = MockWidget
mock_ctk_module.CTkLabel = MockWidget
print(f"DEBUG: mock_ctk_module.CTkLabel id: {id(mock_ctk_module.CTkLabel)}")
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
    def set(self, value):
        print(f"DEBUG: MockVar.set called with {value}")
        self._val = value
    def get(self): return self._val

mock_ctk_module.StringVar = MockVar
print(f"DEBUG: mock_ctk_module.StringVar id: {id(mock_ctk_module.StringVar)}")
mock_ctk_module.BooleanVar = MockVar
mock_ctk_module.IntVar = MockVar

sys.modules["customtkinter"] = mock_ctk_module
sys.modules["tkinter"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["tkinter.filedialog"] = MagicMock()
sys.modules["tkinter.colorchooser"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src" / "scripts"
sys.path.append(str(SRC_DIR))

try:
    from manager_gui import ManagerGUI
except ImportError:
    print("Import failed")
    raise

if __name__ == "__main__":
    print("Running repro with ManagerGUI...")
    app = ManagerGUI()
    print("ManagerGUI instantiated.")
    app.save_config()
    print("save_config called.")

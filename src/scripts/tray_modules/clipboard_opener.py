"""
Clipboard Opener Module.
Opens the folder path currently in the clipboard.
"""
import os
import pyperclip
from pathlib import Path
from pystray import MenuItem as item
from .base import TrayModule

class ClipboardOpener(TrayModule):
    def __init__(self, agent):
        super().__init__(agent)
        self.name = "Clipboard Opener"

    def open_clipboard_path(self):
        try:
            content = pyperclip.paste().strip()
            # Remove quotes if present
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            
            path = Path(content)
            if path.exists() and path.is_dir():
                os.startfile(str(path))
                self.agent.notify("Clipboard Opener", f"Opened: {path.name}")
            else:
                self.agent.notify("Clipboard Opener", "Clipboard does not contain a valid folder path.")
        except Exception as e:
            self.agent.notify("Error", str(e))

    def get_menu_items(self):
        return [item("Open Folder from Clipboard", lambda: self.open_clipboard_path())]

    def on_hotkey(self, key_combo):
        # Check if this module has a hotkey assigned in config
        # For now, we assume the agent handles hotkey mapping to commands
        # But if we want specific module hotkeys, we can check here.
        pass

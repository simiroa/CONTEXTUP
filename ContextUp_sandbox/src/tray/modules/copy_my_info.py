import json
import pystray
from pathlib import Path
import subprocess
import sys
import pyperclip

from core.paths import COPY_MY_INFO_FILE, SRC_DIR


class CopyMyInfoModule:
    def __init__(self, agent_wrapper):
        self.agent = agent_wrapper
        self.config_path = COPY_MY_INFO_FILE
        
    def start(self):
        pass # No background thread needed

    def _load_items(self):
        items = []
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items = data.get('items', [])
            except: pass
        return items

    def _copy_action(self, content):
        def action():
            try:
                pyperclip.copy(content)
                if self.agent:
                    self.agent.notify("Copy My Info", "Copied to clipboard")
            except Exception as e:
                print(f"Copy failed: {e}")
        return action

    def _open_manager_action(self):
        # Open sys_info_manager.py
        def action():
            script = SRC_DIR / "scripts" / "sys_info_manager.py"
            subprocess.Popen([sys.executable, str(script)], creationflags=0x08000000)
        return action

    def get_menu_items(self):
        info_items = self._load_items()
        
        submenu = []
        for item in info_items:
            label = item.get('label', 'Unknown')
            content = item.get('content', '')
            # Create a menu item for each
            # Label format: "Label: Content" (truncated?) or just "Label"
            display_text = f"{label}"
            submenu.append(pystray.MenuItem(display_text, self._copy_action(content)))
        
        submenu.append(pystray.Menu.SEPARATOR)
        submenu.append(pystray.MenuItem("Manage Info...", self._open_manager_action()))
        
        # Return as a submenu item
        return [pystray.MenuItem("Copy My Info", pystray.Menu(*submenu))]

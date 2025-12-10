"""
Base class for Tray Agent Modules.
"""
from abc import ABC, abstractmethod

class TrayModule(ABC):
    def __init__(self, agent):
        self.agent = agent
        self.name = "Base Module"

    @abstractmethod
    def get_menu_items(self):
        """Return a list of pystray.MenuItem objects or None."""
        return []

    def on_hotkey(self, key_combo):
        """Called when a global hotkey is triggered. Return True if handled."""
        return False

    def start(self):
        """Called when agent starts."""
        pass

    def stop(self):
        """Called when agent stops."""
        pass

"""
Recent Folders Module.
Tracks open Explorer windows using Windows Shell COM API.
"""
import time
import threading
import os
import subprocess
from collections import deque
from pathlib import Path
from pystray import MenuItem as item
from .base import TrayModule

try:
    import win32com.client
    SHELL_AVAILABLE = True
except ImportError:
    SHELL_AVAILABLE = False

import logging
import pythoncom
from core.paths import LOGS_DIR

logger = logging.getLogger("ContextUp")

class RecentFolders(TrayModule):
    def __init__(self, agent):
        super().__init__(agent)
        self.name = "Recent Folders"
        self.running = False
        self.log_file = LOGS_DIR / "recent_folders.log"
        self.open_folders = set()  # Set of currently open folder paths
        self.closed_history = deque(maxlen=10)  # Store last 10 closed folders (as batches)
        self._load_history_from_log()
        
    def start(self):
        self.running = True
        threading.Thread(target=self._poll_loop, daemon=True).start()
        logger.info("Recent Folders module started.")
        
    def stop(self):
        self.running = False

    def _get_explorer_paths(self):
        """Get paths of all open Explorer windows using Shell COM API."""
        paths = set()
        try:
            pythoncom.CoInitialize()
            shell = win32com.client.Dispatch("Shell.Application")
            windows = shell.Windows()
            
            for window in windows:
                try:
                    # Get the location URL
                    location = window.LocationURL
                    if not location:
                        continue
                    
                    # Convert file:/// URL to path
                    if location.startswith("file:///"):
                        # Remove file:/// prefix and decode URL encoding
                        import urllib.parse
                        path = urllib.parse.unquote(location[8:])
                        # Convert forward slashes to backslashes
                        path = path.replace("/", "\\")
                        
                        # Verify it's a valid directory
                        if os.path.isdir(path):
                            paths.add(path)
                except:
                    continue
                        
        except Exception as e:
            logger.error(f"Error getting Explorer paths: {e}")
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
        return paths

    def _poll_loop(self):
        """Poll for changes in open Explorer windows."""
        while self.running:
            try:
                current_folders = self._get_explorer_paths()
                
                # Detect closed folders
                closed = self.open_folders - current_folders
                if closed:
                    now = time.time()
                    valid_closed = [p for p in closed if self._is_valid_folder(p)]
                    
                    if valid_closed:
                        # Check if we can group with the last batch
                        if self.closed_history and (now - self.closed_history[-1][0] < 2.0):
                            # Add to existing batch
                            self.closed_history[-1][1].extend(valid_closed)
                            logger.info(f"Added to batch: {valid_closed}")
                        else:
                            # Create new batch
                            self.closed_history.append((now, list(valid_closed)))
                            logger.info(f"New batch: {valid_closed}")
                        self._log_closed(valid_closed)

                self.open_folders = current_folders
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
                
            time.sleep(0.5)  # Poll faster (0.5s) to catch batches better

    def _is_valid_folder(self, path):
        """Check if folder should be tracked."""
        # Ignore system folders and special paths
        ignore_patterns = [
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\ProgramData",
            "C:\\$Recycle.Bin",
            "System Volume Information",
        ]
        
        path_lower = path.lower()
        for pattern in ignore_patterns:
            if pattern.lower() in path_lower:
                return False
                
        return True

    def reopen_last(self):
        """Reopen the last closed folder(s)."""
        if not self.closed_history:
            self.agent.notify("Recent Folders", "No recently closed folders found.")
            return
            
        # Pop the last batch (timestamp, paths_list)
        _, last_batch = self.closed_history.pop()
        
        count = 0
        for folder_path in last_batch:
            try:
                # Open folder in Explorer
                subprocess.Popen(f'explorer "{folder_path}"')
                count += 1
            except Exception as e:
                logger.error(f"Failed to open {folder_path}: {e}")
                
        if count > 0:
            msg = f"Reopened {count} folder(s)"
            if count == 1:
                msg += f": {Path(last_batch[0]).name}"
            self.agent.notify("Recent Folders", msg)

    def _log_closed(self, folders):
        try:
            self.log_file.parent.mkdir(exist_ok=True, parents=True)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                for p in folders:
                    f.write(f"{timestamp}\t{p}\n")
        except Exception:
            pass

    def _load_history_from_log(self):
        """Load the last few closed folders from the log file at startup."""
        try:
            if self.log_file.exists():
                with open(self.log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # Take last 10 unique paths from the log
                unique_paths = []
                for line in reversed(lines):
                    if "\t" in line:
                        path = line.split("\t", 1)[1].strip()
                        if path and os.path.exists(path) and path not in unique_paths:
                            unique_paths.append(path)
                            if len(unique_paths) >= 10:
                                break
                
                # Add to history as individual "batches" (timestamp=0 since we don't care about grouping for old ones)
                for path in reversed(unique_paths):
                    self.closed_history.append((0, [path]))
                
                logger.info(f"Loaded {len(unique_paths)} recent folders from log.")
        except Exception as e:
            logger.error(f"Failed to load recent folders history: {e}")

    def get_menu_items(self):
        """Return dynamic menu items for this module."""
        from utils import i18n
        from pystray import Menu
        
        # 1. Reopen Last Closed Folder (Legacy simple behavior)
        reopen_last_text = i18n.t("features.system.reopen_last_folder", "🔄 Reopen Last Closed Folder")
        menu_items = [item(reopen_last_text, self.reopen_last)]
        
        # 2. Submenu for individual folders
        if not self.closed_history:
            return menu_items
        
        # Create a submenu of the last 10 folders
        recent_items = []
        
        # Flatten and keep unique recent folders
        flat_list = []
        seen = set()
        for _, paths in reversed(list(self.closed_history)):
            for p in reversed(paths):
                if p not in seen:
                    seen.add(p)
                    flat_list.append(p)
        
        for path in flat_list[:5]: # Show up to 5
            name = Path(path).name
            if not name: name = path # Handle drive roots
            recent_items.append(item(f"  {name}", lambda i, p=path: subprocess.Popen(f'explorer "{p}"')))
        
        recent_items.append(Menu.SEPARATOR)
        clear_text = i18n.t("common.clear_history", "Clear History")
        recent_items.append(item(f"  {clear_text}", self.clear_history))
        
        submenu_text = i18n.t("features.system.recent_folders", "📂 Recent Folders")
        menu_items.append(item(submenu_text, Menu(*recent_items)))
        
        return menu_items

    def clear_history(self):
        """Clear history and log file."""
        self.closed_history.clear()
        try:
            if self.log_file.exists():
                self.log_file.unlink()
            self.agent.notify("Recent Folders", "History cleared.")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")

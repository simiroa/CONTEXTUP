import os
import sys
import winreg
from pathlib import Path
from .config import MenuConfig
from .logger import setup_logger

logger = setup_logger("registry")

class RegistryManager:
    def __init__(self, config: MenuConfig):
        self.config = config
        self.root_key = "Software\\Classes"
        self.app_key = "CreatorTools_v2"
        # Use the currently running python executable (System Python)
        # Ensure we use pythonw.exe if available for no-console
        current_exe = Path(sys.executable)
        if current_exe.name.lower() == "python.exe":
            # Try to find pythonw.exe in the same dir
            pythonw = current_exe.parent / "pythonw.exe"
            if pythonw.exists():
                self.python_exe = pythonw
            else:
                self.python_exe = current_exe
        else:
            self.python_exe = current_exe
            
        self.menu_script = Path(__file__).parent / "menu.py"

    def _get_command(self, item_id: str, placeholder: str = "%1") -> str:
        """
        Constructs the command string: "pythonw.exe" "menu.py" "item_id" "placeholder"
        """
        # IMPORTANT: All paths must be quoted.
        cmd = f'"{self.python_exe}" "{self.menu_script}" "{item_id}" "{placeholder}"'
        return cmd

    def register_all(self):
        """
        Registers items based on their types and scope.
        """
        logger.info(f"Starting registration using {self.python_exe}...")
        try:
            # Group items by their registration target
            registry_map = {} # target_key -> list of items
            item_applies_to = {} # item_id -> AppliesTo string

            for item in self.config.items:
                if item.get('status') != 'COMPLETE':
                    continue
                
                if not item.get('enabled', True):
                    continue
                
                scope = item.get('scope', 'file')
                types = item.get('types', '*')
                
                # Determine targets based on scope
                if scope == 'folder' or scope == 'both':
                    # Directory (Folder selection) -> %1
                    if "Directory" not in registry_map: registry_map["Directory"] = []
                    registry_map["Directory"].append(item)
                    
                    # Directory\Background (Empty space) -> %V
                    # Only if NOT explicitly excluded? User said Rename exclude background.
                    # Current config 'both' implies background too.
                    # We'll stick to 'both' = Directory + Background for now.
                    # If user wants to exclude background, we might need a new scope 'selection' or 'folder_selection'.
                    # For now, let's keep it as is, but fix the File issue.
                    if "Directory\\Background" not in registry_map: registry_map["Directory\\Background"] = []
                    registry_map["Directory\\Background"].append(item)
                
                if scope == 'file' or scope == 'both':
                    # Always register to *
                    target = "*"
                    if target not in registry_map: registry_map[target] = []
                    registry_map[target].append(item)
                    
                    # If types is specific, create AppliesTo string
                    if types and types != "*":
                        exts = [t.strip() for t in types.split(';') if t.strip()]
                        # Format: System.FileExtension:=.jpg OR System.FileExtension:=.png
                        # Note: System.FileExtension matches extension.
                        conditions = []
                        for ext in exts:
                            if not ext.startswith('.'): ext = '.' + ext
                            conditions.append(f"System.FileExtension:={ext}")
                        
                        applies_to = " OR ".join(conditions)
                        item_applies_to[item['id']] = applies_to

            # Now register for each target
            for target, items in registry_map.items():
                # Use %V for Background, %1 for others
                placeholder = "%V" if target == "Directory\\Background" else "%1"
                self._register_menu(target, items, placeholder, item_applies_to)
            
            logger.info("Registration complete.")
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise

    def _register_menu(self, reg_class: str, items: list, placeholder: str = "%1", item_applies_to: dict = None):
        """
        Registers a list of items under a specific registry class.
        """
        key_path = f"{self.root_key}\\{reg_class}\\shell\\{self.app_key}"
        
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "Creator Tools")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "imageres.dll,203")
                winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "") # Enable subcommands
                winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Player") # Allow >15 items

            # Create 'shell' subkey
            shell_key_path = f"{key_path}\\shell"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, shell_key_path) as key:
                pass

            # Register items
            for item in items:
                item_id = item['id']
                item_name = item['name']
                item_icon = item.get('icon', '')
                
                if item_icon and ',' not in item_icon:
                    icon_path = Path(__file__).parent.parent.parent / item_icon
                    if icon_path.exists():
                        item_icon = str(icon_path)
                
                item_key_path = f"{shell_key_path}\\{item_id}"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, item_key_path) as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, item_name)
                    if item_icon:
                        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, item_icon)
                    
                    # AppliesTo
                    if item_applies_to and item_id in item_applies_to:
                        winreg.SetValueEx(key, "AppliesTo", 0, winreg.REG_SZ, item_applies_to[item_id])
                
                # Command
                command_key_path = f"{item_key_path}\\command"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
                    cmd = self._get_command(item_id, placeholder)
                    winreg.SetValue(key, "", winreg.REG_SZ, cmd)
                    
        except Exception as e:
            logger.warning(f"Failed to register for {reg_class}: {e}")

    def unregister_all(self):
        """
        Removes the registry keys.
        We need to clean up from all potential locations.
        Since we don't track exactly where we put them, we might need to iterate known possibilities
        OR just clean up the common ones and any SystemFileAssociations we know of.
        
        Actually, simpler approach:
        We know we use HKCU\Software\Classes\...\shell\CreatorTools_v2
        We can iterate HKCU\Software\Classes and look for CreatorTools_v2? 
        That's expensive.
        
        Better: Re-read config and derive targets, then delete.
        """
        logger.info("Unregistering...")
        
        # 1. Clean global and directory
        targets = ["*", "Directory", "Directory\\Background"]
        
        # 2. Clean extensions from config
        for item in self.config.items:
            types = item.get('types', '*')
            if types and types != "*":
                exts = [t.strip() for t in types.split(';') if t.strip()]
                for ext in exts:
                    if not ext.startswith('.'): ext = '.' + ext
                    targets.append(f"SystemFileAssociations\\{ext}")
        
        # Deduplicate
        targets = list(set(targets))
        
        for target in targets:
            key_path = f"{self.root_key}\\{target}\\shell\\{self.app_key}"
            self._delete_key_recursive(winreg.HKEY_CURRENT_USER, key_path)
            
        logger.info("Unregistration complete.")

    def _delete_key_recursive(self, root, key_path):
        try:
            with winreg.OpenKey(root, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
                while True:
                    try:
                        subkey = winreg.EnumKey(key, 0)
                        self._delete_key_recursive(root, f"{key_path}\\{subkey}")
                    except OSError:
                        break
            winreg.DeleteKey(root, key_path)
            logger.debug(f"Deleted {key_path}")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"Failed to delete {key_path}: {e}")

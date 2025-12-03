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
        self.app_key = "ContextUp"
        # Use the currently running python executable (System Python)
        # Ensure we use pythonw.exe if available for no-console
        current_exe = Path(sys.executable)
        # Check if we are already running pythonw
        if current_exe.name.lower() == "pythonw.exe":
            self.python_exe = current_exe
        else:
            # Try to find pythonw.exe in the same dir
            pythonw = current_exe.parent / "pythonw.exe"
            if pythonw.exists():
                self.python_exe = pythonw
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
        Registers items based on their types, scope, and submenu configuration.
        """
        logger.info(f"Starting registration using {self.python_exe}...")

        try:
            # Group items by their registration target AND submenu
            # registry_map: target_key -> { submenu_name -> list_of_items }
            registry_map = {} 
            item_applies_to = {} # item_id -> AppliesTo string

            for item in self.config.items:
                if item.get('status') != 'COMPLETE':
                    continue
                
                if not item.get('enabled', True):
                    continue
                
                scope = item.get('scope', 'file')
                types = item.get('types', '*')
                submenu = item.get('submenu', 'ContextUp')
                if not submenu: submenu = 'ContextUp' # Default
                
                # Determine targets based on scope
                targets = []
                if scope == 'folder' or scope == 'both':
                    targets.append("Directory")
                    targets.append("Directory\\Background")
                
                if scope == 'file' or scope == 'both':
                    targets.append("*")
                    
                    # If types is specific, create AppliesTo string
                    if types and types != "*":
                        exts = [t.strip() for t in types.split(';') if t.strip()]
                        conditions = []
                        for ext in exts:
                            if not ext.startswith('.'): ext = '.' + ext
                            conditions.append(f"System.FileExtension:={ext}")
                        
                        applies_to = " OR ".join(conditions)
                        item_applies_to[item['id']] = applies_to

                # Add to map
                for target in targets:
                    if target not in registry_map: registry_map[target] = {}
                    if submenu not in registry_map[target]: registry_map[target][submenu] = []
                    registry_map[target][submenu].append(item)

            # Now register for each target
            for target, submenus in registry_map.items():
                placeholder = "%V" if target == "Directory\\Background" else "%1"
                
                for submenu_name, items in submenus.items():
                    self._register_submenu_group(target, submenu_name, items, placeholder, item_applies_to)
            
            logger.info("Registration complete.")
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise

    def _register_submenu_group(self, reg_class: str, submenu_name: str, items: list, placeholder: str, item_applies_to: dict):
        """
        Registers a group of items under a specific submenu (or top level).
        """
        # If submenu is "(Top Level)", we register items directly under shell
        # If submenu is "ContextUp" or custom, we create a parent key first.
        
        base_key_path = f"{self.root_key}\\{reg_class}\\shell"
        
        if submenu_name == "(Top Level)":
            # Direct registration
            parent_key_path = base_key_path
        else:
            # Submenu registration
            # Sanitize submenu name for registry key (remove spaces/special chars for key, keep for display)
            safe_key_name = "".join(c for c in submenu_name if c.isalnum() or c in ('_', '-'))
            if not safe_key_name: safe_key_name = "ContextUp"
            
            parent_key_path = f"{base_key_path}\\{safe_key_name}"
            
            # Create the submenu parent
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, parent_key_path) as key:
                    winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, submenu_name)
                    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "imageres.dll,203") # Default icon
                    winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
                    winreg.SetValueEx(key, "MultiSelectModel", 0, winreg.REG_SZ, "Player")
                    # Marker to identify our keys
                    winreg.SetValueEx(key, "ContextUpManaged", 0, winreg.REG_SZ, "true")
                    
                    # --- Submenu Visibility Logic ---
                    # Calculate if we can restrict this submenu to specific file types
                    # If ALL items in this submenu have specific extensions, we can restrict the submenu itself.
                    # If ANY item has "*" or empty types, we must show it always (no AppliesTo).
                    
                    all_extensions = set()
                    has_wildcard = False
                    
                    for item in items:
                        types = item.get('types', '*')
                        if not types or types == '*':
                            has_wildcard = True
                            break
                        
                        # Parse extensions
                        exts = [t.strip() for t in types.split(';') if t.strip()]
                        for ext in exts:
                            if not ext.startswith('.'): ext = '.' + ext
                            all_extensions.add(ext)
                    
                    if not has_wildcard and all_extensions:
                        # Construct AppliesTo for the submenu
                        conditions = [f"System.FileExtension:={ext}" for ext in all_extensions]
                        applies_to = " OR ".join(conditions)
                        winreg.SetValueEx(key, "AppliesTo", 0, winreg.REG_SZ, applies_to)
                        
            except Exception as e:
                logger.warning(f"Failed to create submenu {submenu_name}: {e}")
                return

            # For submenus, items go into a 'shell' subkey
            parent_key_path = f"{parent_key_path}\\shell"
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, parent_key_path) as key:
                    pass
            except Exception:
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
            
            item_key_path = f"{parent_key_path}\\{item_id}"
            
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, item_key_path) as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, item_name)
                    if item_icon:
                        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, item_icon)
                    
                    if item_applies_to and item_id in item_applies_to:
                        winreg.SetValueEx(key, "AppliesTo", 0, winreg.REG_SZ, item_applies_to[item_id])
                    
                    # Marker for items too
                    winreg.SetValueEx(key, "ContextUpManaged", 0, winreg.REG_SZ, "true")
                
                # Command
                command_key_path = f"{item_key_path}\\command"
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
                    cmd = self._get_command(item_id, placeholder)
                    winreg.SetValue(key, "", winreg.REG_SZ, cmd)
            except Exception as e:
                logger.warning(f"Failed to register item {item_id}: {e}")

    def unregister_all(self):
        """
        Removes the registry keys.
        Scans for keys with 'ContextUpManaged' marker, known legacy names, 
        OR keys where the command executes our menu.py script.
        """
        logger.info("Unregistering...")
        
        targets = ["*", "Directory", "Directory\\Background"]
        legacy_keys = ["CreatorTools_v2", "ContextUp", "Image", "Video", "Audio", "3D", "Rename", "Sys", "Document", "Custom"]
        
        # We also want to check if the command points to our menu script
        menu_script_name = "menu.py"
        
        for target in targets:
            base_path = f"{self.root_key}\\{target}\\shell"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base_path, 0, winreg.KEY_ALL_ACCESS) as key:
                    # Iterate subkeys
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            full_subkey_path = f"{base_path}\\{subkey_name}"
                            
                            should_delete = False
                            
                            # Check 1: Known Legacy Name
                            if subkey_name in legacy_keys:
                                should_delete = True
                            
                            # Check 2: Managed Marker
                            if not should_delete:
                                try:
                                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, full_subkey_path) as subkey:
                                        try:
                                            val, _ = winreg.QueryValueEx(subkey, "ContextUpManaged")
                                            if val == "true": should_delete = True
                                        except FileNotFoundError: pass
                                except: pass
                                
                            # Check 3: Content Heuristic (Look for menu.py in command)
                            if not should_delete:
                                try:
                                    # Check direct command (for top level items)
                                    cmd_key_path = f"{full_subkey_path}\\command"
                                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cmd_key_path) as cmd_key:
                                        val, _ = winreg.QueryValueEx(cmd_key, "")
                                        if menu_script_name in val: should_delete = True
                                except:
                                    # Check submenu items (if it's a group)
                                    # We need to look deeper. If any child item points to menu.py, it's likely ours.
                                    # But be careful not to delete a container if it has mixed content (unlikely for us).
                                    # For now, let's assume if we find ONE item with menu.py in a shell subkey, it's ours.
                                    try:
                                        shell_path = f"{full_subkey_path}\\shell"
                                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, shell_path) as shell_key:
                                            j = 0
                                            while True:
                                                try:
                                                    item_name = winreg.EnumKey(shell_key, j)
                                                    item_cmd_path = f"{shell_path}\\{item_name}\\command"
                                                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, item_cmd_path) as item_cmd_key:
                                                        val, _ = winreg.QueryValueEx(item_cmd_key, "")
                                                        if menu_script_name in val: 
                                                            should_delete = True
                                                            break
                                                    j += 1
                                                except OSError: break
                                    except: pass

                            if should_delete:
                                self._delete_key_recursive(winreg.HKEY_CURRENT_USER, full_subkey_path)
                                # Reset index since we deleted a key
                                i = 0 
                            else:
                                i += 1
                        except OSError:
                            break # No more keys
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.warning(f"Error scanning {base_path}: {e}")

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

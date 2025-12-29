import os
import sys
import winreg
from pathlib import Path
from .config import MenuConfig
from .logger import setup_logger
from manager.mgr_core.packages import PackageManager
from utils import i18n

logger = setup_logger("registry")

class RegistryManager:
    def __init__(self, config: MenuConfig):
        self.config = config
        self.root_key = "Software\\Classes"
        self.app_key = "ContextUp"
        # Prefer embedded python, then configured PYTHON_PATH, then current interpreter
        embedded = Path(__file__).parent.parent.parent / "tools" / "python" / "pythonw.exe"
        if embedded.exists():
            self.embedded_python = embedded
        else:
            self.embedded_python = Path(sys.executable)

        # Determine System Python
        try:
            from core.settings import load_settings
            settings = load_settings()
            custom = settings.get("PYTHON_PATH")
            
            candidate = None
            if custom and Path(custom).exists():
                candidate = Path(custom)
            else:
                candidate = Path(sys.executable)
            
            # auto-switch to pythonw.exe if possible to hide console
            if candidate and candidate.name.lower() == 'python.exe':
                possible_w = candidate.parent / "pythonw.exe"
                if possible_w.exists():
                    candidate = possible_w
            
            self.system_python = candidate

        except Exception:
            self.system_python = "pythonw" # Try pythonw in PATH first, default loop will handle if fails? No, better safe.
            # actually if we fail to determine, just use "python" or sys.executable
            # But let's try to be smart.
            self.system_python = Path(sys.executable)
            
        self.menu_script = Path(__file__).parent / "menu.py"

    def _get_command(self, item_id: str, placeholder: str = "%1", env: str = "embedded") -> str:
        """
        Constructs the command string.
        """
        python_bin = self.embedded_python if env != "system" else self.system_python
        
        # If python_bin is a Path object, resolve strictly. If string, leave as is (command).
        if isinstance(python_bin, Path):
            cmd = f'"{python_bin}" "{self.menu_script}" "{item_id}" "{placeholder}"'
        else:
            # It's a command like "python"
            cmd = f'{python_bin} "{self.menu_script}" "{item_id}" "{placeholder}"'
            
        return cmd

    def register_all(self):
        """
        Registers items based on their types, scope, and submenu configuration.
        """
        logger.info(f"Starting registration using {self.embedded_python} (System: {self.system_python})...")

        try:
            # Group items by their registration target AND submenu
            # registry_map: target_key -> { submenu_name -> list_of_items }
            registry_map = {} 
            item_applies_to = {} # item_id -> AppliesTo string

            # Initialize Package Manager for checks
            pm = PackageManager(self.config.root_dir)
            # Clear cache to get fresh package list
            pm.refresh_package_cache()
            installed_packages = pm.get_installed_packages()

            for item in self.config.items:
                if not item.get('enabled', True):
                    continue
                
                # Check if item explicitly disables context menu
                if item.get('show_in_context_menu', True) == False:
                    logger.info(f"Skipping {item['id']} for context menu registration (show_in_context_menu=false)")
                    continue

                # Check Dependencies
                valid, missing = pm.check_dependencies(item, installed_packages)
                if not valid:
                    logger.warning(f"Skipping {item['id']} due to missing dependencies: {missing}")
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
                
                if scope == 'directory':
                    targets.append("Directory")
                    targets.append("Directory\\Background")

                if scope == 'file' or scope == 'both':
                    targets.append("*")

                if scope == 'items':
                    targets.append("*")
                    targets.append("Directory")

                if scope == 'background':
                    targets.append("Directory\\Background")
                    
                # If types is specific, create AppliesTo string
                # This should apply REGARDLESS of the scope, if it's targeted at files.
                applies_to_parts = []
                
                if types and types != "*":
                    exts = [t.strip() for t in types.split(';') if t.strip()]
                    conditions = []
                    for ext in exts:
                        if not ext.startswith('.'): ext = '.' + ext
                        conditions.append(f"System.FileExtension:={ext}")
                    
                    if conditions:
                        applies_to_parts.append("(" + " OR ".join(conditions) + ")")
                
                # Support exclude_types (e.g., exclude .lnk files)
                exclude_types = item.get('exclude_types', [])
                if exclude_types:
                    for ext in exclude_types:
                        if not ext.startswith('.'): ext = '.' + ext
                        applies_to_parts.append(f"NOT System.FileExtension:={ext}")
                
                if applies_to_parts:
                    item_applies_to[item['id']] = " AND ".join(applies_to_parts)

                # Add to map
                for target in targets:
                    if target not in registry_map: registry_map[target] = {}
                    if submenu not in registry_map[target]: registry_map[target][submenu] = []
                    registry_map[target][submenu].append(item)

            # Now register for each target
            for target, submenus in registry_map.items():
                placeholder = "%V" if target == "Directory\\Background" else "%1"
                
                for submenu_name, items in submenus.items():
                    # Stable sort by optional "order" field, then name/id for predictability
                    items = sorted(
                        items,
                        key=lambda it: (
                            it.get("order", 9999),
                            it.get("name", ""),
                            it.get("id", "")
                        )
                    )
                    self._register_submenu_group(target, submenu_name, items, placeholder, item_applies_to)
            
            self._bypass_selection_limit()
            logger.info("Registration complete.")
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise

    def _register_submenu_group(self, reg_class: str, submenu_name: str, items: list, placeholder: str, item_applies_to: dict):
        """
        Registers a group of items under a specific submenu (or top level).
        """
        # Localize submenu name if possible (only for MUIVerb, not key name)
        # Using a simple heuristic or mapping if needed, but 'submenu' is often user-defined or 'ContextUp'.
        # For 'ContextUp' specifically, we can try to translate it, but usually the Brand Name stays as is?
        # Let's assume submenu_name is the ID/English name for now.
        
        display_submenu_name = submenu_name
        if submenu_name == "ContextUp":
             # Optional: Translate Brand Name if strict localization required, 
             # but "ContextUp" is likely a proper noun.
             pass 

        base_key_path = f"{self.root_key}\\{reg_class}\\shell"
        
        if submenu_name == "(Top Level)":
            parent_key_path = base_key_path
        else:
            safe_key_name = "".join(c for c in submenu_name if c.isalnum() or c in ('_', '-'))
            
            # Check settings for position preference
            from core.settings import load_settings
            settings = load_settings()
            show_at_top = settings.get("MENU_POSITION_TOP", True)

            # Use the Position registry value to force menu to top instead of key name tricks
            # Prefix characters (space, numbers, etc.) break submenu expansion on Windows 11
            if not safe_key_name: 
                safe_key_name = "ContextUp"
            
            parent_key_path = f"{base_key_path}\\{safe_key_name}"
            
            try:
                # Use ContextUp.ico for all context menu icons
                contextup_icon = str(Path(__file__).parent.parent.parent / "assets" / "icons" / "ContextUp.ico")
                
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, parent_key_path) as key:
                    winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, submenu_name)
                    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, contextup_icon)
                    winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
                    winreg.SetValueEx(key, "ContextUpManaged", 0, winreg.REG_SZ, "true")
                    
                    # Force position to top (Windows 7+)
                    if show_at_top:
                        winreg.SetValueEx(key, "Position", 0, winreg.REG_SZ, "Top")
                    else:
                        # Remove Position if it exists (for toggle OFF)
                        try: winreg.DeleteValue(key, "Position")
                        except: pass
                    
                    # Logic for AppliesTo (omitted for brevity, relying on previous impl if needed, or simple pass)
            except Exception:
                pass

            parent_key_path = f"{parent_key_path}\\shell"
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, parent_key_path) as key:
                    pass
            except Exception:
                pass

        # Register items
        for item in items:
            item_id = item['id']
            # item_name_raw = item['name']
            
            # Localize Item Name
            if item.get("category"):
                i18n_key = f"features.{item['category'].lower()}.{item_id}"
            else:
                i18n_key = f"features.other.{item_id}"
                
            item_name = i18n.t(i18n_key, default=item['name'])

            item_icon = item.get('icon', '')
            
            if item_icon and ',' not in item_icon:
                icon_path = Path(__file__).parent.parent.parent / item_icon
                if icon_path.exists():
                    item_icon = str(icon_path)
            
            if item_id == 'copy_my_info' or item.get('dynamic_submenu') == 'copy_my_info':
                order_prefix = "9999"
            else:
                order_prefix = f"{item.get('order', 9999):04d}"
            item_key_path = f"{parent_key_path}\\{order_prefix}_{item_id}"
            
            # Check for dynamic submenu request
            dynamic_source = item.get('dynamic_submenu')
            
            try:
                if dynamic_source == "copy_my_info":
                    # --- Strategy: ExtendedSubCommandsKey (Robust) ---
                    # 1. Launcher Item (The visible menu item)
                    # It points to a separate "Class" where the items live.
                    class_id = "ContextUp.CopyInfoMenu"
                    
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, item_key_path) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, item_name) # MUIVerb (Default Value)
                        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, item_name) # Explicit MUIVerb just in case
                        if item_icon:
                            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, item_icon)
                        
                        # Point to the isolated menu definition
                        winreg.SetValueEx(key, "ExtendedSubCommandsKey", 0, winreg.REG_SZ, class_id)
                        winreg.SetValueEx(key, "ContextUpManaged", 0, winreg.REG_SZ, "true")
                        
                        # Clean up legacy attributes that might interfere
                        try: winreg.DeleteValue(key, "SubCommands")
                        except: pass

                    # 2. Define the Class and its Items
                    # Path: HKCU\Software\Classes\ContextUp.CopyInfoMenu\shell
                    class_shell_path = f"Software\\Classes\\{class_id}\\shell"
                    
                    # Ensure class exists
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, class_shell_path) as key:
                        pass
                        
                    # Load items
                    import json
                    config_path = Path(__file__).parent.parent.parent / "userdata" / "copy_my_info.json"
                    info_items = []
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            info_items = json.load(f).get('items', [])
                    except: pass
                    
                    if not info_items:
                        info_items = [{"label": "No items - Click Manage", "content": ""}]

                    # Register Info Items under the CLASS
                    python_bin = self.embedded_python
                    script = Path(__file__).parent.parent / "scripts" / "sys_copy_content.py"
                    
                    for i, info in enumerate(info_items):
                        label_raw = info.get('label', f'Item {i}')
                        # We don't have easy i18n keys for user content, so stick to raw
                        label = label_raw
                        
                        # Simple alphanumeric key
                        clean_label = "".join(c for c in label if c.isalnum())
                        if not clean_label: clean_label = f"Item{i}"
                        
                        child_key = f"{class_shell_path}\\{i:02d}_{clean_label}"
                        cmd = f'"{python_bin}" "{script}" "{label}"'
                        
                        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, child_key) as k:
                            winreg.SetValue(k, "", winreg.REG_SZ, label) # MUIVerb
                            winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, label)
                            # No icon for submenu items - cleaner look
                            
                            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{child_key}\\command") as ck:
                                winreg.SetValue(ck, "", winreg.REG_SZ, cmd)

                    # Add "Manage Info..." item at the bottom
                    manage_key = f"{class_shell_path}\\99_ManageInfo"
                    manage_cmd = f'"{python_bin}" "{script}" "--manage"'
                    
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, manage_key) as k:
                        manage_label = i18n.t("features.tools.manage_info", "Manage Info...")
                        winreg.SetValue(k, "", winreg.REG_SZ, manage_label)
                        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, manage_label)
                         # Use gear icon or similar if available, else generic shell32
                        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "shell32.dll,317") 
                        
                        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{manage_key}\\command") as ck:
                            winreg.SetValue(ck, "", winreg.REG_SZ, manage_cmd)
                        winreg.SetValue(k, "", winreg.REG_SZ, manage_label)
                        winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, manage_label)
                        winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, "imageres.dll,109")
                        
                        python_bin = self.embedded_python
                        script_mgr = Path(__file__).parent.parent / "scripts" / "sys_info_manager.py"
                        cmd = f'"{python_bin}" "{script_mgr}"'
                        
                        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{manage_key}\\command") as ck:
                            winreg.SetValue(ck, "", winreg.REG_SZ, cmd)
                            
                else:
                    # --- Standard Registration ---
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, item_key_path) as key:
                        winreg.SetValue(key, "", winreg.REG_SZ, item_name) # Default value = display name
                        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, item_name) # Explicit MUIVerb
                        if item_icon:
                            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, item_icon)
                        
                        # AppliesTo typically kills "Background" items because they don't have extensions.
                        # Only apply AppliesTo if we are NOT in Directory\Background, OR if the rule is generic enough.
                        # For now, simplistic rule: Don't apply file extensions checks to Background.
                        if item_applies_to and item_id in item_applies_to and reg_class != "Directory\\Background":
                            winreg.SetValueEx(key, "AppliesTo", 0, winreg.REG_SZ, item_applies_to[item_id])
                        
                        winreg.SetValueEx(key, "ContextUpManaged", 0, winreg.REG_SZ, "true")
                    
                    # Command
                    command_key_path = f"{item_key_path}\\command"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
                        cmd = self._get_command(item_id, placeholder, "embedded")
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
        legacy_keys = ["CreatorTools_v2", "ContextUp", " ContextUp"]
        
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

        # Cleanup CopyInfoMenu class (dynamic submenu holder)
        try:
            self._delete_key_recursive(winreg.HKEY_CURRENT_USER, "Software\\Classes\\ContextUp.CopyInfoMenu")
        except Exception as e:
            pass # Ignore if not found

        logger.info("Unregistration complete.")

    def _bypass_selection_limit(self):
        """
        Sets MultipleInvokePromptMinimum to avoids context menu disappearance 
        when selecting >15 files.
        """
        try:
            key_path = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                # Set to 500 (decimal)
                winreg.SetValueEx(key, "MultipleInvokePromptMinimum", 0, winreg.REG_DWORD, 500)
                logger.info("Set MultipleInvokePromptMinimum to 500")
        except Exception as e:
            logger.warning(f"Failed to set MultipleInvokePromptMinimum: {e}")


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

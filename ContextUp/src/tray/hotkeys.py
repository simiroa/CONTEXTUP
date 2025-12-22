"""
Tray Hotkey Management
Global hotkey registration and execution.
"""
import sys
import subprocess
from pathlib import Path

from core.paths import SRC_DIR
from core.logger import setup_logger
from tray.launchers import open_manager, open_translator

logger = setup_logger("tray_hotkeys")

src_dir = SRC_DIR


# Built-in hotkey handlers for items without 'command' field
BUILTIN_HOTKEY_HANDLERS = {
    "manager": lambda: open_manager(),
    "finder": lambda: subprocess.Popen(
        [sys.executable, str(src_dir / "features" / "finder" / "__init__.py")], 
        creationflags=0x08000000
    ),
    "translator": lambda: open_translator(),
    "vacance": lambda: subprocess.Popen(
        [sys.executable, str(src_dir / "features" / "vacance" / "gui.py")], 
        creationflags=0x08000000
    ),
}


def execute_hotkey_command(item: dict):
    """
    Execute a hotkey command from menu config.
    
    Args:
        item: Menu item dict with 'id', 'command', 'name' fields
    """
    item_id = item.get('id', '')
    cmd_str = item.get("command", "")
    logger.info(f"Hotkey triggered: {item.get('name')} (id={item_id}, command={cmd_str})")
    
    try:
        # 1. If no command, check built-in handlers by id
        if not cmd_str and item_id in BUILTIN_HOTKEY_HANDLERS:
            logger.info(f"Using built-in handler for: {item_id}")
            BUILTIN_HOTKEY_HANDLERS[item_id]()
            return
        
        # 2. Check if command is a script in src/scripts
        if cmd_str and "python" in cmd_str.lower():
            # Try to extract script path
            parts = cmd_str.split()
            for p in parts:
                if p.endswith(".py"):
                    script_path = Path(p.replace('"', ''))
                    if not script_path.is_absolute():
                        script_path = src_dir.parent / script_path
                    
                    if script_path.exists():
                        logger.info(f"Launching script: {script_path}")
                        subprocess.Popen(
                            [sys.executable, str(script_path)], 
                            creationflags=0x08000000
                        )
                        return

        # 3. Fallback: Run command as-is (subprocess)
        if cmd_str:
            subprocess.Popen(cmd_str, shell=True, creationflags=0x08000000)
        else:
            logger.warning(f"No command or built-in handler for hotkey: {item_id}")

    except Exception as e:
        logger.error(f"Global Hotkey Execution Failed: {e}")


def register_hotkeys(menu_config):
    """
    Register all hotkeys from menu config.
    
    Args:
        menu_config: MenuConfig instance with items
    
    Returns:
        Number of hotkeys registered
    """
    try:
        import keyboard
    except ImportError:
        logger.warning("keyboard module not found. Hotkeys disabled.")
        return 0
    
    count = 0
    
    for item in menu_config.items:
        hk = item.get("hotkey", "").strip()
        if hk:
            # Convert <ctrl> to ctrl, etc
            clean_hk = hk.replace("<", "").replace(">", "").lower()
            
            try:
                # Use closure to capture 'item'
                keyboard.add_hotkey(clean_hk, lambda x=item: execute_hotkey_command(x))
                count += 1
                logger.info(f"Registered Hotkey: {clean_hk} -> {item.get('name')}")
            except Exception as ex:
                logger.error(f"Failed to register hotkey '{clean_hk}': {ex}")
    
    logger.info(f"Total Hotkeys Registered: {count}")
    return count


def register_quick_menu_hotkey(show_menu_func, hotkey: str = "ctrl+shift+c"):
    """
    Register the global hotkey for quick menu.
    
    Args:
        show_menu_func: Function to show the quick menu
        hotkey: The hotkey combination (default: ctrl+shift+c)
    """
    try:
        import keyboard
        keyboard.add_hotkey(hotkey, show_menu_func)
        logger.info(f"Registered Global Context Menu Hotkey: {hotkey.upper()}")
    except ImportError:
        logger.warning("keyboard module not found. Quick menu hotkey disabled.")
    except Exception as e:
        logger.error(f"Failed to register popup menu hotkey: {e}")


def unregister_all():
    """Unregister all keyboard hotkeys."""
    try:
        import keyboard
        keyboard.unhook_all()
    except Exception:
        pass

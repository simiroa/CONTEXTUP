"""
Tray Hotkey Management
Global hotkey registration and execution.
"""
import sys
import subprocess
import threading
from pathlib import Path

from core.paths import SRC_DIR
from core.logger import setup_logger
from tray.launchers import open_manager, open_translator

logger = setup_logger("tray_hotkeys")

src_dir = SRC_DIR

_win32_hotkey_thread = None
_win32_hotkey_thread_id = None
_win32_hotkey_stop = threading.Event()


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


def _parse_hotkey(hotkey: str):
    parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
    if not parts:
        return None

    mod = 0
    key = None

    mod_map = {
        "alt": 0x0001,
        "ctrl": 0x0002,
        "control": 0x0002,
        "shift": 0x0004,
        "win": 0x0008,
    }

    key_map = {
        "space": 0x20,
        "tab": 0x09,
        "enter": 0x0D,
        "esc": 0x1B,
        "escape": 0x1B,
    }

    for part in parts:
        if part in mod_map:
            mod |= mod_map[part]
            continue
        if part in key_map:
            key = key_map[part]
            continue
        if part.startswith("f") and part[1:].isdigit():
            fn = int(part[1:])
            if 1 <= fn <= 24:
                key = 0x70 + (fn - 1)
                continue
        if len(part) == 1:
            key = ord(part.upper())

    if key is None:
        return None
    return mod, key


def _register_win32_hotkey(hotkey: str, show_menu_func):
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return False

    parsed = _parse_hotkey(hotkey)
    if not parsed:
        return False

    mod, key = parsed

    ready = threading.Event()
    result = {"ok": False}

    def _thread():
        global _win32_hotkey_thread_id
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        _win32_hotkey_thread_id = kernel32.GetCurrentThreadId()

        if not user32.RegisterHotKey(None, 1, mod, key):
            ready.set()
            return
        result["ok"] = True
        ready.set()

        msg = wintypes.MSG()
        while not _win32_hotkey_stop.is_set():
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res == 0:
                break
            if msg.message == 0x0312 and msg.wParam == 1:
                try:
                    show_menu_func()
                except Exception as exc:
                    logger.error(f"Quick menu hotkey handler failed: {exc}")

        user32.UnregisterHotKey(None, 1)

    _win32_hotkey_stop.clear()
    thread = threading.Thread(target=_thread, daemon=True)
    thread.start()
    ready.wait(1.0)
    return result["ok"]


def _unregister_win32_hotkey():
    global _win32_hotkey_thread_id
    if not _win32_hotkey_thread_id:
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        _win32_hotkey_stop.set()
        user32.PostThreadMessageW(_win32_hotkey_thread_id, 0x0012, 0, 0)
        _win32_hotkey_thread_id = None
    except Exception:
        pass


def register_quick_menu_hotkey(show_menu_func, hotkey: str = "ctrl+shift+c"):
    """
    Register the global hotkey for quick menu.
    
    Args:
        show_menu_func: Function to show the quick menu
        hotkey: The hotkey combination (default: ctrl+shift+c)
    """
    if _register_win32_hotkey(hotkey, show_menu_func):
        logger.info(f"Registered Global Context Menu Hotkey (Win32): {hotkey.upper()}")
        return
    logger.info("RegisterHotKey failed. Falling back to keyboard module.")

    try:
        import keyboard
        keyboard.add_hotkey(hotkey, show_menu_func)
        logger.info(f"Registered Global Context Menu Hotkey (keyboard): {hotkey.upper()}")
    except ImportError:
        logger.warning("keyboard module not found. Quick menu hotkey disabled.")
    except Exception as e:
        logger.error(f"Failed to register popup menu hotkey: {e}", exc_info=True)



def unregister_all():
    """Unregister all keyboard hotkeys."""
    _unregister_win32_hotkey()
    try:
        import keyboard
        keyboard.unhook_all()
    except Exception:
        pass

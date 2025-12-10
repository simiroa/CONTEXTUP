import sys
import os
import json
import subprocess
import socket
import threading
import time
import atexit
import argparse
import logging
from pathlib import Path
from PIL import Image, ImageDraw

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from core.logger import setup_logger

logger = setup_logger("tray_agent")

try:
    import pystray
except ImportError:
    # Minimal fallback logger if setup_logger failed or just stderr
    print("pystray not installed.")
    sys.exit(1)

PID_FILE = src_dir.parent / "logs" / "tray_agent.pid"
HANDSHAKE_FILE = src_dir.parent / "logs" / "tray_info.json"
LOG_FILE = src_dir.parent / "logs" / "tray_agent.log"



def kill_pid(pid: int):
    try:
        subprocess.run(f"taskkill /PID {pid} /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def pre_kill_existing():
    my_pid = os.getpid()
    
    # PID file first
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if old_pid != my_pid:
                 kill_pid(old_pid)
        except Exception as e:
            pass
        try:
            PID_FILE.unlink()
        except Exception:
            pass
    # Fallback: tasklist scan removed due to stability issues.
    # We rely on PID_FILE and Manager's stop() logic.






def build_icon_image():
    size = 64
    img = Image.new("RGBA", (size, size), (52, 152, 219, 255))
    dc = ImageDraw.Draw(img)
    dc.rectangle((18, 18, 46, 46), fill=(255, 255, 255, 255))
    return img


def setup_file_logging():
    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

def write_handshake(port):
    try:
        data = {
            "pid": os.getpid(),
            "port": port,
            "status": "ready",
            "timestamp": time.time()
        }
        with open(HANDSHAKE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        logger.info(f"Handshake written: {data}")
    except Exception as e:
        logger.error(f"Failed to write handshake: {e}")

def main():
    setup_file_logging()
    logger.info("Tray Agent Starting...")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=54321, help="UDP Port for listening")
    args = parser.parse_args()
    
    pre_kill_existing()

    # Write simple PID file as backup
    try:
        PID_FILE.parent.mkdir(exist_ok=True, parents=True)
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except Exception as e:
        logger.warning(f"PID write failed: {e}")


def open_translator():
    try:
        # Launch sys_translator.py directly
        translator_script = src_dir / "scripts" / "tool_translator.py"
        python_exe = sys.executable
        
        # Use simple python.exe with CREATE_NO_WINDOW
        cmd = [str(python_exe), str(translator_script)]
        logger.info(f"Opening Translator: {cmd}")
        
        creationflags = 0x08000000 # CREATE_NO_WINDOW
        subprocess.Popen(cmd, close_fds=True, creationflags=creationflags)
    except Exception as e:
        logger.error(f"Failed to open translator: {e}")

def open_manager():
    try:
        # Launch manager_gui.py directly
        manager_script = src_dir / "scripts" / "manager_gui.py"
        python_exe = sys.executable
        
        # Use simple python.exe with CREATE_NO_WINDOW
        cmd = [str(python_exe), str(manager_script)]
        logger.info(f"Opening Manager: {cmd}")
        
        creationflags = 0x08000000 # CREATE_NO_WINDOW
        subprocess.Popen(cmd, close_fds=True, creationflags=creationflags)
    except Exception as e:
        logger.error(f"Failed to open manager: {e}")

def main():
    setup_file_logging()
    logger.info("Tray Agent Starting...")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=54321, help="UDP Port for listening")
    args = parser.parse_args()
    
    pre_kill_existing()

    # Write simple PID file as backup
    try:
        PID_FILE.parent.mkdir(exist_ok=True, parents=True)
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except Exception as e:
        logger.warning(f"PID write failed: {e}")

    # No longer loading generic items from CONFIG_FILE
    # tray_items = load_tray_items() 

    def reload(icon, item):
        logger.info("Reloading tray...")
        icon.menu = pystray.Menu(*build_menu(icon))

    def exit_tray(icon, item):
        icon.stop()
    
    class TrayAgentWrapper:
        """Simple wrapper for icon to provide notify method for modules."""
        def __init__(self, icon):
            self._icon = icon
        
        def notify(self, title, message):
            try:
                self._icon.notify(f"{title}: {message}")
            except Exception as e:
                logger.error(f"Notify failed: {e}")

    def build_menu(icon_ref=None):
        menu_entries = []
        
        # 1. Recent Folders (Top)
        # 1. Recent Folders (Top)
        try:
            # sys.path has 'src', so we can import from scripts.tray_modules
            from scripts.tray_modules.recent_folders import RecentFolders
            from scripts.tray_modules.clipboard_opener import ClipboardOpener # Added

            # Create wrapper to provide notify method
            agent_wrapper = TrayAgentWrapper(icon_ref) if icon_ref else None
            
            # --- Recent Folders ---
            recent_module = RecentFolders(agent_wrapper)
            recent_module.start()
            
            # --- Clipboard Opener ---
            clip_module = ClipboardOpener(agent_wrapper)
            clip_module.start()
            
            # --- Copy My Info ---
            from scripts.tray_modules.copy_my_info import CopyMyInfoModule
            info_module = CopyMyInfoModule(agent_wrapper)
            info_module.start()
            
            # Store module reference to keep it alive
            if icon_ref:
                if not hasattr(icon_ref, '_modules'):
                    icon_ref._modules = []
                icon_ref._modules.append(recent_module)
                icon_ref._modules.append(clip_module) # Keep alive
                icon_ref._modules.append(info_module)
            
            # append items
            recent_items = recent_module.get_menu_items()
            if recent_items:
                menu_entries.extend(recent_items)
                menu_entries.append(pystray.Menu.SEPARATOR)
            
            info_items = info_module.get_menu_items()
            if info_items:
                menu_entries.extend(info_items)
                menu_entries.append(pystray.Menu.SEPARATOR)

            clip_items = clip_module.get_menu_items()
            if clip_items:
                menu_entries.extend(clip_items)
                menu_entries.append(pystray.Menu.SEPARATOR)

        except Exception as e:
            logger.error(f"Failed to load Tray Modules: {e}")
        
        # 2. Tools
        menu_entries.append(pystray.MenuItem("Translator", lambda: open_translator()))
        menu_entries.append(pystray.Menu.SEPARATOR)

        # 3. ContextUp Manager
        menu_entries.append(pystray.MenuItem("ContextUp Manager", lambda: open_manager()))
        menu_entries.append(pystray.Menu.SEPARATOR)

        # 4. System
        menu_entries.extend([
            pystray.MenuItem("Reload", reload),
            pystray.MenuItem("Exit", exit_tray)
        ])
        return menu_entries

    icon = pystray.Icon("ContextUp", build_icon_image(), "ContextUp Agent", pystray.Menu(*build_menu(None)))
    
    # Update menu with icon ref once created so modules can notify
    icon.menu = pystray.Menu(*build_menu(icon))

    def udp_listener():
        """Listen for exit signals from Manager."""
        UDP_IP = "127.0.0.1"
        UDP_PORT = args.port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((UDP_IP, UDP_PORT))
            logger.info(f"Tray Agent listening on UDP {UDP_IP}:{UDP_PORT} for exit")
            
            # Write handshake now that we are bound and ready
            write_handshake(UDP_PORT)
            
            while True:
                data, _ = sock.recvfrom(1024)
                if data and data.lower().startswith(b"exit"):
                    logger.info("Exit signal received, stopping tray icon.")
                    icon.stop()
                    break
        except Exception as e:
            logger.error(f"UDP listener failed: {e}")
        finally:
            try:
                sock.close()
            except Exception:
                pass
            # Cleanup handshake
            try:
                if HANDSHAKE_FILE.exists(): HANDSHAKE_FILE.unlink()
            except: pass

    threading.Thread(target=udp_listener, daemon=True).start()

    def cleanup():
        try:
            if PID_FILE.exists(): PID_FILE.unlink()
            if HANDSHAKE_FILE.exists(): HANDSHAKE_FILE.unlink()
        except Exception:
            pass
    atexit.register(cleanup)

    # Load Hotkeys using keyboard module
    try:
        import keyboard
        
        def execute_hotkey_command(item):
            logger.info(f"Hotkey triggered: {item.get('name')} -> {item.get('command')}")
            try:
                # 1. Check if command is a script in src/scripts
                cmd_str = item.get("command", "")
                
                # Check for "python " prefix
                if "python" in cmd_str.lower() and "src/scripts" in cmd_str.replace("\\", "/"):
                     # Attempt to run script directly
                     parts = cmd_str.split()
                     script_path = None
                     for p in parts:
                         if "src/scripts" in p.replace("\\", "/"):
                             script_path = p.replace('"', '')
                             break
                     
                     if script_path:
                         # Resolve absolute path
                         abs_script = src_dir / Path(script_path).name # Try direct name match first
                         if not abs_script.exists():
                             # Try relative trace
                             abs_script = src_dir.parent / Path(script_path)
                         
                         if abs_script.exists():
                             logger.info(f"Launching script: {abs_script}")
                             subprocess.Popen([sys.executable, str(abs_script)], creationflags=0x08000000)
                             return

                # 2. Fallback: Run command as-is (subprocess)
                # We need to handle arguments carefully, but for hotkeys usually 0 args
                subprocess.Popen(cmd_str, shell=True, creationflags=0x08000000)

            except Exception as e:
                logger.error(f"Global Hotkey Execution Failed: {e}")

        # Scan menu_config for hotkeys
        # Scan config for hotkeys using MenuConfig
        try:
            from core.config import MenuConfig
            menu_config = MenuConfig() # Loads from categories automatically
            menus = menu_config.items
            
            count = 0
            for m in menus:
                hk = m.get("hotkey", "").strip()
                if hk:
                    # Convert <ctrl> to ctrl, etc
                    clean_hk = hk.replace("<", "").replace(">", "").lower()
                    
                    # Register
                    try:
                        # Use closure to capture 'm'
                        keyboard.add_hotkey(clean_hk, lambda x=m: execute_hotkey_command(x))
                        count += 1
                        logger.info(f"Registered Hotkey: {clean_hk} -> {m.get('name')}")
                    except Exception as ex:
                        logger.error(f"Failed to register hotkey '{clean_hk}': {ex}")
            logger.info(f"Total Hotkeys Registered: {count}")

        except Exception as e:
            logger.error(f"Failed to load hotkeys from config: {e}")

    except ImportError:
        logger.warning("keyboard module not found. Hotkeys disabled.")

    logger.info("Tray Agent starting icon loop.")
    # Fire a small toast to confirm presence
    try:
        threading.Timer(1.0, lambda: icon.notify(f"ContextUp tray running (Port {args.port})")).start()
    except Exception:
        pass
    
    icon.run()
    
    # Cleanup
    try:
        import keyboard
        keyboard.unhook_all()
    except: pass
    
    logger.info("Tray Agent stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("startup_error.txt", "w") as f:
            import traceback
            traceback.print_exc(file=f)
        logger.error(f"Top level crash: {e}", exc_info=True)

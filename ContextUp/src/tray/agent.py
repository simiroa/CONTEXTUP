"""
ContextUp Tray Agent
Main entry point for the system tray application.

This module orchestrates the tray agent using separated components:
- tray.utils: Process management, logging
- tray.icon: Icon building
- tray.menu_builder: Menu construction
- tray.ipc: Inter-process communication
- tray.hotkeys: Global hotkey registration
"""
import sys
import os
import atexit
import argparse
import threading
from pathlib import Path

# Add src to path
current_file = Path(__file__).resolve()
# If executed as src/tray/agent.py, parent is src/tray, parent.parent is src
src_dir = current_file.parent.parent 

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Remove own directory to avoid package shadowing
if str(current_file.parent) in sys.path:
    sys.path.remove(str(current_file.parent))

from core.config import MenuConfig
from core.logger import setup_logger

# Import tray modules (using absolute imports for direct script execution)
from tray.agent_utils import (
    pre_kill_existing, 
    setup_file_logging, 
    write_pid, 
    cleanup_files,
    LOG_FILE
)
from tray.icon import build_icon_image
from tray.menu_builder import build_menu
from tray.ipc import create_udp_listener
from tray.hotkeys import register_hotkeys, register_quick_menu_hotkey, unregister_all

logger = setup_logger("tray_agent")

# Check pystray
try:
    import pystray
except ImportError:
    print("pystray not installed.")
    sys.exit(1)


def main():
    """Main entry point for tray agent."""
    setup_file_logging()
    logger.info("Tray Agent Starting...")
    logger.info(f"Running on Interpreter: {sys.executable}")
    
    # Set Windows AppUserModelID for proper notification icon/name
    try:
        import ctypes
        myappid = 'hg.contextup.tray.3.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        logger.info(f"Set AppUserModelID: {myappid}")
    except Exception as e:
        logger.warning(f"Failed to set AppUserModelID: {e}")
    
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=54321, help="UDP Port for listening")
    args = parser.parse_args()
    
    # Kill any existing instance and write PID
    pre_kill_existing()
    write_pid()
    
    # Menu callbacks (defined before build_menu to allow closure)
    def reload(icon, item):
        logger.info("Restarting tray...")
        try:
            # Re-register Quick Menu Hotkey cleanup (best effort)
            unregister_all()
            close_quick_menu_daemon()
            
            # Spawn new process
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv, creationflags=0x08000000)
            
            # Stop current icon (this exits the mainloop)
            icon.stop()
            
        except Exception as e:
            logger.error(f"Restart failed: {e}")
            # Fallback to old reload logic if restart fails?
            icon.menu = pystray.Menu(*build_menu(icon, reload, exit_tray))


    def exit_tray(icon, item):
        icon.stop()

    def close_quick_menu_daemon():
        """Best-effort cleanup for legacy quick menu daemon."""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.1)
            sock.sendto(b"quit", ("127.0.0.1", 54322))
            sock.close()
        except Exception:
            pass
    
    # Build initial menu and create icon
    icon = pystray.Icon(
        "ContextUp", 
        build_icon_image(), 
        "ContextUp Agent", 
        pystray.Menu(*build_menu(None, reload, exit_tray))
    )
    
    # Update menu with icon ref once created so modules can notify
    icon.menu = pystray.Menu(*build_menu(icon, reload, exit_tray))
    
    # Start UDP listener for IPC
    create_udp_listener(icon, args, lambda i: build_menu(i, reload, exit_tray))
    
    # Register cleanup
    atexit.register(cleanup_files)
    
    # Load and register hotkeys
    try:
        close_quick_menu_daemon()
        menu_config = MenuConfig()
        register_hotkeys(menu_config)
        
        # Register quick menu hotkey
        def show_popup_menu():
            try:
                from .quick_menu import show_quick_menu
                show_quick_menu()
            except Exception as e:
                logger.error(f"Quick menu failed: {e}")
        
        register_quick_menu_hotkey(show_popup_menu, "ctrl+shift+c")

    except Exception as e:
        logger.error(f"Failed to register hotkeys: {e}")
    
    # Start VRAM auto-unload timer if enabled
    def vram_auto_unload_timer():
        """Background thread to auto-unload VRAM when ComfyUI is idle."""
        from core.settings import load_settings
        import time
        import urllib.request
        
        last_activity_time = time.time()
        
        while True:
            try:
                settings = load_settings()
                gpu_options = settings.get("COMFYUI_GPU_OPTIONS", {})
                auto_unload_minutes = gpu_options.get("vram_auto_unload_minutes", 0)
                
                if auto_unload_minutes <= 0:
                    time.sleep(60)  # Check settings every minute
                    continue
                    
                # Check if ComfyUI is running
                from manager.helpers.comfyui_service import ComfyUIService
                service = ComfyUIService()
                running, port = service.is_running()
                
                if not running:
                    time.sleep(60)
                    continue
                
                # Check system status endpoint for queue length
                try:
                    if not port:
                        time.sleep(60)
                        continue

                    url = f"http://127.0.0.1:{port}/prompt"
                    # If queue is empty for auto_unload_minutes, unload VRAM
                    idle_seconds = auto_unload_minutes * 60
                    
                    # Basic idle detection: just wait for the configured time
                    time.sleep(idle_seconds)
                    
                    # After waiting, try to unload
                    unload_url = f"http://127.0.0.1:{port}/free"
                    urllib.request.urlopen(unload_url, timeout=5)
                    logger.info(f"VRAM auto-unloaded after {auto_unload_minutes} minutes idle")
                    
                except Exception as e:
                    logger.debug(f"VRAM auto-unload check: {e}")
                    
            except Exception as e:
                logger.debug(f"VRAM auto-unload error: {e}")
                time.sleep(60)
    
    # Start VRAM auto-unload in background
    vram_thread = threading.Thread(target=vram_auto_unload_timer, daemon=True)
    vram_thread.start()
    logger.info("VRAM auto-unload timer started")
    
    logger.info("Tray Agent starting icon loop.")
    
    # Fire a small toast to confirm presence
    try:
        threading.Timer(1.0, lambda: icon.notify(f"ContextUp tray running (Port {args.port})")).start()
    except Exception:
        pass
    
    # Run the icon (blocking)
    icon.run()
    
    # Cleanup
    unregister_all()
    
    # Kill Quick Menu daemon on exit
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.1)
        # Port match quick_menu.py
        sock.sendto(b"quit", ("127.0.0.1", 54322))
        sock.close()
    except:
        pass

    logger.info("Tray Agent stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("startup_error.txt", "w") as f:
            import traceback
            traceback.print_exc(file=f)
        logger.error(f"Top level crash: {e}", exc_info=True)

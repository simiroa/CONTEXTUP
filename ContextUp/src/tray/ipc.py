"""
Tray Agent IPC (Inter-Process Communication)
UDP listener for signals from Manager and handshake file management.
"""
import json
import socket
import time
import threading
from pathlib import Path

from core.paths import LOGS_DIR
from core.logger import setup_logger

logger = setup_logger("tray_ipc")

HANDSHAKE_FILE = LOGS_DIR / "tray_info.json"


def write_handshake(port: int):
    """
    Write handshake JSON file with connection info for Manager.
    
    Args:
        port: The UDP port the agent is listening on
    """
    import os
    try:
        data = {
            "pid": os.getpid(),
            "port": port,
            "status": "ready",
            "timestamp": time.time()
        }
        HANDSHAKE_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(HANDSHAKE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        logger.info(f"Handshake written: {data}")
    except Exception as e:
        logger.error(f"Failed to write handshake: {e}")


def create_udp_listener(icon, args, build_menu_func, reopen_handler=None):
    """
    Create and start the UDP listener thread.
    
    Args:
        icon: pystray Icon instance
        args: Parsed command line arguments with 'port' attribute
        build_menu_func: Function to rebuild menu (takes icon as argument)
        reopen_handler: Optional function to handle recent folder reopen
    
    Returns:
        The listener thread
    """
    import pystray
    
    def udp_listener():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Try to bind to requested port, fallback to any available
        current_port = args.port
        bound = False
        
        for p in [current_port, 0]:
            try:
                sock.bind(("127.0.0.1", p))
                current_port = sock.getsockname()[1]
                logger.info(f"UDP listener bound to port: {current_port}")
                bound = True
                break
            except Exception as e:
                logger.warning(f"Failed to bind UDP port {p}: {e}")
        
        if not bound:
            logger.error("Could not bind to any UDP port. IPC features disabled.")
            return
        
        # Write handshake with actual bound port
        write_handshake(current_port)
        
        sock.settimeout(1.0)
        try:
            while icon.visible:
                try:
                    data, addr = sock.recvfrom(1024)
                    msg = data.strip()
                except socket.timeout:
                    continue
                except Exception:
                    break
                
                if msg.startswith(b"quit"):
                    logger.info("Quit signal received via UDP")
                    icon.stop()
                    break
                elif msg.startswith(b"reload"):
                    logger.info("Reload signal received, rebuilding menu...")
                    try:
                        icon.menu = pystray.Menu(*build_menu_func(icon))
                        icon.update_menu()
                        logger.info("Menu reloaded successfully.")
                    except Exception as e:
                        logger.error(f"Menu reload failed: {e}")
                elif msg.startswith(b"reopen_recent"):
                    logger.info("Reopen recent signal received via UDP")
                    try:
                        if reopen_handler:
                            reopen_handler()
                        elif hasattr(icon, '_modules'):
                            for mod in icon._modules:
                                if hasattr(mod, 'reopen_last'):
                                    mod.reopen_last()
                                    break
                    except Exception as e:
                        logger.error(f"Reopen recent failed: {e}")
                        
        except Exception as e:
            logger.error(f"UDP listener failed: {e}")
        finally:
            try:
                sock.close()
            except Exception:
                pass
            try:
                if HANDSHAKE_FILE.exists():
                    HANDSHAKE_FILE.unlink()
            except Exception:
                pass
    
    thread = threading.Thread(target=udp_listener, daemon=True)
    thread.start()
    return thread

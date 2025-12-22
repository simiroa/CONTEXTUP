import os
import sys
import subprocess
import time
import psutil
from pathlib import Path

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from manager.helpers.comfyui_client import ComfyUIManager
from core.logger import setup_logger

logger = setup_logger("comfy_server_utils")

def is_comfy_running(port=8190):
    """Check if ComfyUI server is responding on the given port."""
    client = ComfyUIManager(port=port)
    return client.is_running()

def start_comfy(port=8190):
    """Start ComfyUI server in the background."""
    if is_comfy_running(port):
        logger.info(f"ComfyUI is already running on port {port}.")
        return True, "이미 실행 중입니다."

    client = ComfyUIManager(port=port)
    # The ComfyUIManager.start() method uses subprocess.Popen without creationflags.
    # To ensure it's hidden on Windows, we might need to monkeypatch or just use it as is if it's acceptable.
    # Actually, ComfyUIManager.start() has a commented out creationflags.
    
    success = client.start()
    if success:
        logger.info(f"ComfyUI started successfully on port {port}.")
        return True, "ComfyUI 서버가 시작되었습니다."
    else:
        logger.error(f"Failed to start ComfyUI on port {port}.")
        return False, "ComfyUI 서버 시작에 실패했습니다."

def stop_comfy(port=8190):
    """Stop ComfyUI server by terminating processes using the port."""
    logger.info(f"Stopping ComfyUI on port {port}...")
    
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info['connections']:
                if conn.laddr.port == port:
                    logger.info(f"Found process {proc.info['pid']} ({proc.info['name']}) using port {port}. Terminating...")
                    proc.terminate()
                    proc.wait(timeout=5)
                    found = True
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, Exception):
            continue
            
    if found:
        return True, "ComfyUI 서버가 종료되었습니다."
    else:
        # Check if it's still running (maybe terminated by name or already stopped)
        if not is_comfy_running(port):
            return True, "ComfyUI 서버가 이미 종료되었거나 실행 중이지 않습니다."
        return False, "ComfyUI 서버를 종료하지 못했습니다."

if __name__ == "__main__":
    # Test if run directly
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "start":
            print(start_comfy()[1])
        elif cmd == "stop":
            print(stop_comfy()[1])
        elif cmd == "status":
            print("Running" if is_comfy_running() else "Stopped")

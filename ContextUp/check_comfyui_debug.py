
import sys
import os
from pathlib import Path
import urllib.request
import time

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from manager.helpers.comfyui_client import ComfyUIManager
from manager.helpers.comfyui_service import ComfyUIService

def check_raw_params(host, port):
    url = f"http://{host}:{port}"
    print(f"Testing raw connection to {url}...")
    try:
        with urllib.request.urlopen(url, timeout=2.0) as response:
            print(f"  [SUCCESS] Status Code: {response.status}")
            return True
    except Exception as e:
        print(f"  [FAILED] {e}")
        return False

def check_manager_logic():
    print("\nTesting ComfyUIManager logic...")
    mgr = ComfyUIManager()
    print(f"  Manager Initial Port: {mgr.preferred_port}")
    print(f"  Manager Common Ports: {mgr.COMMON_PORTS}")
    
    is_running = mgr.is_running()
    print(f"  mgr.is_running() returned: {is_running}")
    print(f"  mgr.active_port: {mgr.active_port}")

def check_service_logic():
    print("\nTesting ComfyUIService logic...")
    svc = ComfyUIService()
    try:
        running, port, started = svc.ensure_running(start_if_missing=False)
        print(f"  ensure_running(start=False) returned: running={running}, port={port}, started={started}")
    except Exception as e:
        print(f"  [ERROR] Service check failed: {e}")

if __name__ == "__main__":
    print("=== ComfyUI Connection Diagnostic ===")
    
    # 1. Raw checks
    check_raw_params("127.0.0.1", 8188)
    check_raw_params("127.0.0.1", 8190)
    
    # 2. Manager checks
    check_manager_logic()
    
    # 3. Service checks
    check_service_logic()

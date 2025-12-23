
import sys
from pathlib import Path
import time

current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from manager.helpers.comfyui_service import ComfyUIService

print("Test: ensure_running(start_if_missing=True)...")
start_time = time.time()
svc = ComfyUIService()
try:
    running, port, started = svc.ensure_running(start_if_missing=True, wait_seconds=5)
    print(f"Result: running={running}, port={port}, started={started}")
except Exception as e:
    print(f"Exception: {e}")

print(f"Duration: {time.time() - start_time:.2f}s")

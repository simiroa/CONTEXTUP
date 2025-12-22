
from pathlib import Path
import sys

# Mock setup
project_root = Path.cwd()
SRC_DIR = project_root / "src"

def find_path(tool_script):
    parts = tool_script.replace("src.", "").split(".")
    print(f"Parts: {parts}")
    
    # Logic from launchers.py line 45
    path1 = SRC_DIR / "features" / "/".join(parts[:-1]) / f"{parts[-1]}.py"
    print(f"Path 1 (Wrong?): {path1}")
    print(f"Exists? {path1.exists()}")
    
    # Logic from launchers.py line 50
    path2 = SRC_DIR / f"{'/'.join(parts)}.py"
    print(f"Path 2 (Fallback): {path2}")
    print(f"Exists? {path2.exists()}")

print("Testing: src.features.comfyui.seedvr2_gui")
find_path("src.features.comfyui.seedvr2_gui")

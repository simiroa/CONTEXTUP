
import subprocess
import sys
import time
import os
import pygetwindow as gw
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
UNWRAP_SCRIPT = SRC_DIR / "features" / "system" / "unwrap_folder_gui.py"
TEMP_DIR = Path(os.environ.get("TEMP", ".")) / "debug_unwrap"

if not TEMP_DIR.exists():
    TEMP_DIR.mkdir(parents=True)

# Set env
env = os.environ.copy()
env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")

print(f"Launching {UNWRAP_SCRIPT}...")
cmd = [sys.executable, str(UNWRAP_SCRIPT), str(TEMP_DIR)]
proc = subprocess.Popen(cmd, env=env)

print("Waiting 5 seconds...")
time.sleep(5)

print("\nVisible Windows:")
titles = gw.getAllTitles()
for t in titles:
    if t.strip():
        print(f" - '{t}'")

print("\nTerminating...")
proc.kill()

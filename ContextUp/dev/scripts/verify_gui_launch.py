
import subprocess
import sys
import time
import os
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
EMBEDDED_PYTHON = PROJECT_ROOT / "tools" / "python" / "python.exe"

if not EMBEDDED_PYTHON.exists():
    EMBEDDED_PYTHON = Path(sys.executable)

GUI_LIST = [
    # Modified/Themed GUIs
    ("analysis", "features/video/sequence_analyze.py"),
    ("analyze_gui", "features/sequence/analyze_gui.py"),
    ("audio", "features/video/audio_gui.py"),
    ("normal", "features/image/normal.py"),
    ("leave_manager", "features/leave_manager/gui.py"),
    ("finder", "features/finder/ui.py"),
    ("gemini_tools", "features/ai/standalone/gemini_img_tools/gui.py"),
    
    # Files using Tabview/Treeview potentially affected
    ("rename", "features/system/rename.py"),
    
    # Previously modified
    ("image_convert", "features/image/convert_gui.py"),
    ("image_compare", "features/image/compare_gui.py"),
    ("merge_exr", "features/image/merge_exr.py"),
    ("split_exr", "features/image/split_exr.py"),
    ("resize", "features/image/resize_gui.py"),
    ("packer", "features/image/packer_gui.py"),
    ("video_convert", "features/video/convert_gui.py"),
    ("downloader", "features/video/downloader_gui.py"),
    ("to_video", "features/sequence/to_video_gui.py"),
    
    # Manager
    ("manager", "manager/main.py"),
]

def verify_gui(name, script_path):
    print(f"Testing {name} ({script_path})...", end="", flush=True)
    
    full_path = SRC_DIR / script_path
    if not full_path.exists():
        print(" [SKIP] File not found")
        return False

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    
    # Prepare dummy arguments to prevent internal checks from blocking
    args = []
    if "features" in script_path:
        # Some scripts expect a path argument
        pass

    cmd = [str(EMBEDDED_PYTHON), str(full_path)] + args
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            env=env
        )
        
        # Wait 4 seconds to see if it crashes
        time.sleep(4)
        
        ret = proc.poll()
        if ret is None:
            print(" [PASS]")
            proc.terminate()
            return True
        else:
            _, stderr = proc.communicate()
            print(f" [FAIL] Exit code {ret}")
            print(stderr.decode("utf-8", errors="replace"))
            return False
            
    except Exception as e:
        print(f" [ERROR] {e}")
        return False

def main():
    print(f"Verifying {len(GUI_LIST)} GUIs...")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, path in GUI_LIST:
        if verify_gui(name, path):
            passed += 1
        else:
            failed += 1
            
    print("="*60)
    print(f"Summary: {passed} PASS, {failed} FAIL")

if __name__ == "__main__":
    main()

import sys
import subprocess
import os
import urllib.request
import tarfile
import shutil
import json
from pathlib import Path

# ==========================================
# Core Installer (v2 Modular Architecture)
# Installs ONLY Manager, Tray, QuickMenu
# ==========================================

ROOT_DIR = Path(__file__).parent.parent.parent
TOOLS_DIR = ROOT_DIR / "tools"
PYTHON_DIR = TOOLS_DIR / "python"
SRC_DIR = ROOT_DIR / "src"

# Force encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 1. Base Core Dependencies ONLY
#    Removed: opencv, ffmpeg, scipy, heavy AI libs
BASE_CORE_PKGS = [
    "customtkinter",
    "psutil",
    "pystray",
    "packaging",
    "pywin32",
    "requests",
    "pynput",
    "keyboard",
    "send2trash",
    "piexif",
    "pyperclip",
    "xxhash",
    "Pillow",
    "numpy<2", # Kept for potential util usage, check transparency
    "tqdm",
    "holidays",
]

# Python Distro
PYTHON_URL = "https://github.com/indygreg/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-pc-windows-msvc-shared-install_only.tar.gz"
PYTHON_ARCHIVE_NAME = "python-standalone.tar.gz"

def download_file(url: str, dest: Path) -> bool:
    print(f"Downloading {url} -> {dest.name}")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False

def extract_tar_gz(tar_path: Path, dest_dir: Path) -> bool:
    print(f"Extracting {tar_path.name} ...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=dest_dir)
        return True
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
        return False

def setup_embedded_python() -> Path:
    py_exe = PYTHON_DIR / "python.exe"
    
    if py_exe.exists():
        # Simple check
        try:
            subprocess.check_call([str(py_exe), "-c", "import sys"], stdout=subprocess.DEVNULL)
            print(f"[INFO] Embedded Python found: {py_exe}")
            return py_exe
        except:
            print("[WARN] Existing Python broken, reinstalling...")

    print("[INFO] Setting up minimal Embedded Python...")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    tar_path = TOOLS_DIR / PYTHON_ARCHIVE_NAME
    
    if not tar_path.exists():
        if not download_file(PYTHON_URL, tar_path):
            return None
            
    if extract_tar_gz(tar_path, TOOLS_DIR):
        if py_exe.exists():
            return py_exe
            
    return None

def install_packages(py_exe: Path):
    print("\n--- Installing Core Dependencies ---")
    cmd = [str(py_exe), "-m", "pip", "install", "--no-warn-script-location"] + BASE_CORE_PKGS
    try:
        subprocess.check_call(cmd)
        print("[SUCCESS] Core packages installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Package installation failed: {e}")
        return False

def main():
    print("=== ContextUp Core Installer (Modular v2) ===\n")
    print("This will install ONLY the Manager and System Tray components.")
    print("Apps (Image, Video, AI) must be installed via the 'Store' later.\n")
    
    py_exe = setup_embedded_python()
    if not py_exe:
        print("[FATAL] Could not setup Python.")
        return
        
    if not install_packages(py_exe):
        print("[FATAL] Could not install core packages.")
        return

    print("\n[SUCCESS] Core System Ready.")
    print("Launch the Manager to install apps.")
    
    # Optional: Try to launch manager?
    # manager_script = SRC_DIR / "manager" / "main.py"
    # subprocess.Popen([str(py_exe), str(manager_script)], creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    main()

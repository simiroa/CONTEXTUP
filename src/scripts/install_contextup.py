import sys
import subprocess
import os
import urllib.request
import zipfile
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent # src/scripts/install_contextup.py -> ROOT
TOOLS_DIR = ROOT_DIR / "tools"
PYTHON_DIR = TOOLS_DIR / "python"
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"

# IndyGreg Python Build Standalone 3.11.9 (Shared Install Only)
# URL for x86_64-pc-windows-msvc-shared-install_only
PYTHON_URL = "https://github.com/indygreg/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-pc-windows-msvc-shared-install_only.tar.gz"

def download_file(url, dest):
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def extract_tar_gz(tar_path, dest_dir):
    print(f"Extracting {tar_path}...")
    try:
        import tarfile
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=dest_dir)
        return True
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False

def setup_embedded_python():
    if PYTHON_DIR.exists() and (PYTHON_DIR / "python.exe").exists():
        # Quick check if it works (optional)
        print("Local Python already exists.")
        return True
        
    print("--- Setting up Local Python (Unified Portable) ---")
    TOOLS_DIR.mkdir(exist_ok=True)
    
    # Check for pre-downloaded archive
    archive_name = "python-standalone.tar.gz"
    archive_path = TOOLS_DIR / archive_name
    
    # Look for common python archive names in tools/ if user copied it there
    found_archive = None
    for f in TOOLS_DIR.glob("cpython-3.11.*-install_only.tar.gz"):
        found_archive = f
        break
        
    if found_archive:
        print(f"Found pre-downloaded archive: {found_archive.name}")
        archive_path = found_archive
    elif archive_path.exists():
        print(f"Found existing {archive_name}")
    else:
        # Download if not found
        if not download_file(PYTHON_URL, archive_path):
            return False
            
    print("Installing Python locally...")
    
    # Extract
    # The IndyGreg archive usually extracts to a 'python' folder or similar.
    # We want it in tools/python.
    # If the tar contains a top-level dir, we might need to handle that.
    # Usually 'install_only' flavors extract everything flat or into strict structure.
    # Let's extract to tools/temp first to verify structure or just extract to tools/ and rename?
    # Actually, IndyGreg archives typically extract into a 'python' directory.
    # Let's extract to TOOLS_DIR. If it creates a 'python' dir, great.
    
    if not extract_tar_gz(archive_path, TOOLS_DIR):
        print("Failed to extract Python archive.")
        return False

    # Check if 'python' dir exists now
    if not PYTHON_DIR.exists():
        # Did it extract to 'python-build-standalone' or 'cpython...'?
        # Sometimes they extract to 'python'.
        # Let's try to interpret where it went.
        # But 'install_only' usually means the content of the installation prefix.
        # So it might dump bin/ lib/ include/ directly? 
        # Wait, 'install_only' usually behaves like an installation tree.
        # On Windows, it usually has python.exe at the root of the archive or in a subdir.
        # Let's assume it might have extracted to a subdir if not 'python'.
        
        # NOTE: For safety, let's look for python.exe in TOOLS_DIR and its subdirs
        found_py = list(TOOLS_DIR.rglob("python.exe"))
        if found_py:
            # Move the containing folder to 'python' if it's not already
            py_root = found_py[0].parent
            if py_root != PYTHON_DIR:
                print(f"Moving {py_root} to {PYTHON_DIR}...")
                shutil.move(str(py_root), str(PYTHON_DIR))
    
    # Verify installation actually worked
    py_exe = PYTHON_DIR / "python.exe"
    if not py_exe.exists():
        print(f"[ERROR] python.exe not found at: {py_exe}")
        print("Extraction seemed successful but python.exe is missing.")
        return False
        
    # Clean up archive if we downloaded it
    if archive_path.name == archive_name and archive_path.exists():
        os.remove(archive_path)

    print("Local Python setup complete.")
    return True

def install_core_dependencies():
    print("--- Installing Unified Dependencies ---")
    if not REQUIREMENTS_FILE.exists():
        print(f"Error: {REQUIREMENTS_FILE} not found.")
        return False
    
    py_exec = str(PYTHON_DIR / "python.exe")
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.run([py_exec, "-m", "pip", "install", "--upgrade", "pip"], check=False)
        
        # Install core requirements
        print("Installing dependencies from requirements_core.txt...")
        subprocess.check_call([py_exec, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
        
        print("All dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def check_clean_install():
    # Check for Core Python
    if PYTHON_DIR.exists():
        print(f"\n[!] Existing Local Python found at: {PYTHON_DIR}")
        choice = input("Do you want to perform a Clean Install (Delete existing)? (y/N): ").strip().lower()
        if choice == 'y':
            try:
                print("Removing existing Python...")
                shutil.rmtree(PYTHON_DIR)
                print("Deleted.")
            except Exception as e:
                print(f"Failed to delete: {e}")
                print("Please close any running ContextUp processes and try again.")
                return False
    return True

def main():
    print(f"ContextUp Installer (Unified Standalone)\n")
    print("This will install a portable Python environment with all AI dependencies included.")
    
    input("Press Enter to start installation...")
    
    if not check_clean_install():
        print("Installation Aborted.")
        input("Press Enter to exit...")
        return
    
    if setup_embedded_python():
        if install_core_dependencies():
            print("\n[SUCCESS] System Installed.")
            print("\nLaunching ContextUp Manager...")
            manager_bat = ROOT_DIR / "ContextUpManager.bat"
            if manager_bat.exists():
                try:
                    subprocess.Popen([str(manager_bat)], shell=True, cwd=str(ROOT_DIR))
                except Exception as e:
                    print(f"Failed to launch Manager: {e}")
            else:
                print("Manager batch file not found.")
        else:
             print("\n[FAILURE] Dependency Installation Failed.")
    else:
        print("\n[FAILURE] Local Python Setup Failed.")
    
    # Wait for user to see result
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()

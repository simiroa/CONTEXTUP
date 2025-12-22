import shutil
import subprocess
import sys
from pathlib import Path

# Paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
python_dir = project_root / "tools" / "python"
site_packages = python_dir / "Lib" / "site-packages"
requirements_file = project_root / "requirements.txt"

def reset_libs():
    print("WARNING: This will delete all installed libraries in the embedded Python environment.")
    print(f"Target: {site_packages}")
    confirm = input("Are you sure? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return

    # 1. Delete site-packages
    if site_packages.exists():
        print("Deleting site-packages...")
        try:
            shutil.rmtree(site_packages)
            print("Deleted.")
        except Exception as e:
            print(f"Error deleting site-packages: {e}")
            return
    else:
        print("site-packages not found, skipping deletion.")

    # 2. Re-install pip (ensure it exists)
    print("Ensuring pip is installed...")
    python_exe = python_dir / "python.exe"
    subprocess.call([str(python_exe), "-m", "ensurepip"])

    # 3. Install requirements
    if requirements_file.exists():
        print("Installing requirements...")
        subprocess.call([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)])
        print("Done.")
    else:
        print("requirements.txt not found. Please install libraries manually.")

if __name__ == "__main__":
    reset_libs()

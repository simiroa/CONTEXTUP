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
REQUIREMENTS_FILE = ROOT_DIR / "requirements_core.txt"

# Official Python 3.11.9 Installer (EXE)
PYTHON_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

def download_file(url, dest):
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def setup_embedded_python():
    if PYTHON_DIR.exists() and (PYTHON_DIR / "python.exe").exists():
        # Quick check if it works (optional)
        print("Local Python already exists.")
        return True
        
    print("--- Setting up Local Python (Core) ---")
    TOOLS_DIR.mkdir(exist_ok=True)
    
    # Check for pre-downloaded installer or renamed "python_installer.exe"
    installer_path = TOOLS_DIR / "python_installer.exe"
    
    # Look for common python installer names in tools/ if user copied it there
    # e.g. python-3.11.9-amd64.exe
    found_installer = None
    for f in TOOLS_DIR.glob("python-3.11.*-amd64.exe"):
        found_installer = f
        break
        
    if found_installer:
        print(f"Found pre-downloaded installer: {found_installer.name}")
        installer_path = found_installer
    elif installer_path.exists():
        print("Found existing python_installer.exe")
    else:
        # Download if not found
        if not download_file(PYTHON_URL, installer_path):
            return False
    
    print("Installing Python locally (This may ask for permission)...")
    # TargetDir must be absolute
    target_dir_abs = str(PYTHON_DIR.resolve())
    
    # Command Args: /quiet InstallAllUsers=0 TargetDir=... Include_tcltk=1 PrependPath=0
    cmd = [
        str(installer_path),
        "/quiet",
        "InstallAllUsers=0",
        f"TargetDir={target_dir_abs}",
        "Include_tcltk=1",  # CRITICAL: Needed for GUI
        "Include_pip=1",    # CRITICAL: Needed for requirements
        "PrependPath=0",
        "Shortcuts=0",
        "Include_test=0",
        "Include_doc=0",
        "Include_dev=0",
        "Include_launcher=0"
    ]
    
    try:
        print("Please wait... (Installing to tools/python)")
        subprocess.run(cmd, check=True)
        print("Local Python setup complete.")
        
        # Verify installation actually worked
        py_exe = PYTHON_DIR / "python.exe"
        if not py_exe.exists():
            print(f"[ERROR] python.exe not found at: {py_exe}")
            print("The installer exited successfully, but the file is missing.")
            print("Possible causes: Antivirus blocking, disk write delay, or installer failed silently.")
            return False

        # Only remove if we downloaded it as "python_installer.exe"
        if installer_path.name == "python_installer.exe" and installer_path.exists():
            os.remove(installer_path)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        print("Try running the installer manually if this persists.")
        return False

def install_core_dependencies():
    print("--- Installing Core Dependencies ---")
    if not REQUIREMENTS_FILE.exists():
        print(f"Error: {REQUIREMENTS_FILE} not found.")
        return False
    
    py_exec = str(PYTHON_DIR / "python.exe")
    
    try:
        # Install core requirements
        subprocess.check_call([py_exec, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
        print("Core dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def setup_ai_env():
    # We use the EMBEDDED python to launch the setup script? 
    # No, setup_ai_conda.py uses 'subprocess' to call 'conda'.
    # It just needs *a* python to run the script logic.
    # We can use our fresh Embedded Python to run it.
    
    ai_script = ROOT_DIR / "src" / "scripts" / "setup" / "setup_ai_conda.py"
    model_script = ROOT_DIR / "src" / "scripts" / "setup" / "download_ai_models.py"
    
    # Use Embedded Python to run these scripts
    py_exec = str(PYTHON_DIR / "python.exe")
    
    print("\n[Optional] AI Environment & Models Setup")
    print("This will:")
    print(" 1. Download & Install Miniconda + PyTorch (~2.5GB)")
    print(" 2. Configure 'ai_tools' environment")
    print(" 3. (Optional) Download AI Models (Marigold, Spleeter, etc.) (~4GB+)")
    print("    * Warning: This can take a long time.")
    
    choice = input("Install AI Environment now? (y/N): ").strip().lower()
    
    if choice == 'y':
        try:
            if not ai_script.exists():
                print(f"Script not found: {ai_script}")
                return

            print("Launching AI Environment Setup...")
            subprocess.run([py_exec, str(ai_script)], check=True)
            
            # Model Download
            model_choice = input("\nDownload AI Models now to skip waiting later? (y/N): ").strip().lower()
            if model_choice == 'y':
                if model_script.exists():
                    print("Launching Model Downloader...")
                    # setup_ai_conda.py writes env_info.txt. Read it to find Conda Python.
                    env_info_path = ROOT_DIR / "src" / "scripts" / "ai_standalone" / "env_info.txt"
                    if env_info_path.exists():
                        conda_python = None
                        with open(env_info_path, 'r') as f:
                            for line in f:
                                if line.startswith("PYTHON_EXE="):
                                    conda_python = line.strip().split("=", 1)[1]
                                    break
                        
                        if conda_python and Path(conda_python).exists():
                            subprocess.run([conda_python, str(model_script)], check=True)
                        else:
                             print("Could not find Conda Python executable to download models.")
                    else:
                        print("Env info file not found (AI setup might have failed). Skipping models.")
                else:
                    print("Model download script not found.")
            
        except Exception as e:
            print(f"AI Setup process failed: {e}")

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
    
    # Check for legacy Venv (if user upgraded from previous version)
    venv_dir = TOOLS_DIR / "contextup_venv"
    if venv_dir.exists():
        print(f"\n[!] Legacy Virtual Environment found at: {venv_dir}")
        choice = input("Delete legacy venv to free space? (Y/n): ").strip().lower()
        if choice != 'n':
             try:
                shutil.rmtree(venv_dir)
                print("Deleted.")
             except Exception as e:
                print(f"Failed to delete: {e}")

    return True

def main():
    print(f"ContextUp Installer (Hybrid Mode)\n")
    print("1. Core: Installs local Embedded Python 3.11 (Safe, Portable)")
    print("2. AI:   Optional Conda Environment (Heavy, GPU-enabled)\n")
    
    input("Press Enter to start installation...")
    
    if not check_clean_install():
        print("Installation Aborted.")
        input("Press Enter to exit...")
        return
    
    if setup_embedded_python():
        if install_core_dependencies():
            print("\n[SUCCESS] Core System Installed.")
            
            # Optional AI
            setup_ai_env()
            
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

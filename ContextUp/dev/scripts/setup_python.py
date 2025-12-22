```python
"""
Automatic setup script for the embedded Python runtime.
Downloads and configures the embeddable package in tools/python.
"""
import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

# Configuration
PYTHON_VERSION = "3.11.9"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

ROOT_DIR = Path(__file__).parent.parent
TOOLS_DIR = ROOT_DIR / "tools"
PYTHON_DIR = TOOLS_DIR / "python"
PYTHON_ZIP = TOOLS_DIR / f"python-{PYTHON_VERSION}-embed-amd64.zip"
PYTHON_EXE = PYTHON_DIR / "python.exe"

def download_file(url, dest):
    """Download a file with progress indication"""
    print(f"Downloading {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(dest, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print("\nDownload complete.")
        return True
    except Exception as e:
        print(f"\nDownload failed: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract a zip file"""
    print(f"Extracting {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("Extraction complete.")
        return True
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False

def create_pth_file():
    """Create python311._pth file to enable site-packages"""
    pth_file = PYTHON_DIR / "python311._pth"
    print(f"Creating {pth_file}...")
    
    content = """python311.zip
.
.\\Lib
.\\Lib\\site-packages

# Enable site module
import site
"""
    
    try:
        with open(pth_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("python311._pth created successfully.")
        return True
    except Exception as e:
        print(f"Failed to create python311._pth: {e}")
        return False

def install_pip():
    """Install pip in the embedded Python"""
    print("Installing pip...")
    
    get_pip_path = TOOLS_DIR / "get-pip.py"
    
    # Download get-pip.py
    if not download_file(GET_PIP_URL, get_pip_path):
        return False
    
    # Run get-pip.py
    try:
        import subprocess
        result = subprocess.run(
            [str(PYTHON_EXE), str(get_pip_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("pip installed successfully.")
        print(result.stdout)
        
        # Cleanup
        get_pip_path.unlink()
        return True
    except subprocess.CalledProcessError as e:
        print(f"pip installation failed: {e}")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Error installing pip: {e}")
        return False

def install_requirements():
    """Install packages from requirements.txt"""
    requirements_file = ROOT_DIR / "requirements.txt"
    
    if not requirements_file.exists():
        print("requirements.txt not found, skipping package installation.")
        return True
    
    print("Installing packages from requirements.txt...")
    
    try:
        import subprocess
        result = subprocess.run(
            [str(PYTHON_EXE), "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Packages installed successfully.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Package installation failed: {e}")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Error installing packages: {e}")
        return False

def main():
    print("=" * 60)
    print(f"Embedded Python {PYTHON_VERSION} Setup")
    print("=" * 60)
    
    # Check if already installed
    if PYTHON_EXE.exists():
        print(f"\nPython already installed at {PYTHON_DIR}")
        response = input("Reinstall? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
        
        # Remove existing installation
        print("Removing existing installation...")
        shutil.rmtree(PYTHON_DIR)
    
    # Create tools directory
    TOOLS_DIR.mkdir(exist_ok=True)
    
    # Step 1: Download Python
    print(f"\nStep 1/5: Downloading Python {PYTHON_VERSION}...")
    if not download_file(PYTHON_URL, PYTHON_ZIP):
        print("Setup failed.")
        return
    
    # Step 2: Extract Python
    print(f"\nStep 2/5: Extracting Python...")
    PYTHON_DIR.mkdir(exist_ok=True)
    if not extract_zip(PYTHON_ZIP, PYTHON_DIR):
        print("Setup failed.")
        return
    
    # Cleanup zip file
    PYTHON_ZIP.unlink()
    
    # Step 3: Create python312._pth
    print(f"\nStep 3/5: Configuring Python paths...")
    if not create_pth_file():
        print("Setup failed.")
        return
    
    # Step 4: Install pip
    print(f"\nStep 4/5: Installing pip...")
    if not install_pip():
        print("Setup failed (pip installation).")
        print("You can manually install pip later using get-pip.py")
    
    # Step 5: Install requirements
    print(f"\nStep 5/5: Installing required packages...")
    if not install_requirements():
        print("Warning: Some packages failed to install.")
        print("You can manually install them later using:")
        print(f"  {PYTHON_EXE} -m pip install -r requirements.txt")
    
    # Verify installation
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)
    
    try:
        import subprocess
        result = subprocess.run(
            [str(PYTHON_EXE), "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Python version: {result.stdout.strip()}")
        
        result = subprocess.run(
            [str(PYTHON_EXE), "-m", "pip", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ pip version: {result.stdout.strip()}")
        
        print("\n" + "=" * 60)
        print("Setup completed successfully!")
        print("=" * 60)
        print(f"\nPython installed at: {PYTHON_DIR}")
        print(f"Python executable: {PYTHON_EXE}")
        print("\nYou can now use the embedded Python for all scripts.")
        
    except Exception as e:
        print(f"\nWarning: Verification failed: {e}")
        print("Please check the installation manually.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

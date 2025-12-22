
import os
import sys
import subprocess
from pathlib import Path
import shutil
import urllib.request

# Define Paths
# Script -> dev/scripts
# Root -> HG_context_v2
ROOT_DIR = Path(__file__).resolve().parents[3]
TOOLS_DIR = ROOT_DIR / "ContextUp" / "tools"
COMFY_DIR = TOOLS_DIR / "ComfyUI"

def run_cmd(cmd, cwd=None):
    print(f"Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=cwd)

def setup_comfy():
    print("🛠️ Setting up ComfyUI Environment...")
    
    # 1. Check/Clone ComfyUI
    if not COMFY_DIR.exists():
        print(f"Downloading ComfyUI to {COMFY_DIR}...")
        try:
            run_cmd(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", str(COMFY_DIR)])
        except Exception as e:
            print(f"❌ Failed to clone ComfyUI: {e}")
            return
    else:
        print("✅ ComfyUI directory exists.")

    # 2. Install Dependencies
    print("📦 Installing ComfyUI Dependencies...")
    # Use the current python executable
    python_exe = sys.executable
    requirements_file = COMFY_DIR / "requirements.txt"
    
    if requirements_file.exists():
        try:
            run_cmd([python_exe, "-m", "pip", "install", "-r", str(requirements_file)], cwd=COMFY_DIR)
        except Exception as e:
            print(f"⚠️ Failed to install dependencies (might already be satisfied): {e}")
    
    # 3. Create Model Directories
    checkpoints_dir = COMFY_DIR / "models" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n✅ Setup Complete.")
    print("\n[NEXT STEPS]")
    print(f"1. Download the Z-Image Turbo Checkpoint (safetensors).")
    print(f"   Save to: {checkpoints_dir}")
    print(f"2. Ensure you have the 'z_image_turbo' workflow available.")
    print(f"3. Run the icon generator with local engine.")

if __name__ == "__main__":
    setup_comfy()

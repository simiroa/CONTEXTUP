
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

# Paths
ROOT_DIR = Path(__file__).resolve().parents[3]
CHECKPOINTS_DIR = ROOT_DIR / "ContextUp" / "tools" / "ComfyUI" / "models" / "checkpoints"

REPO_ID = "stabilityai/sdxl-turbo"
FILENAME = "sd_xl_turbo_1.0_fp16.safetensors"

def download_model():
    print(f"Downloading {FILENAME} from {REPO_ID} to {CHECKPOINTS_DIR}...")
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        file_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=CHECKPOINTS_DIR,
            local_dir_use_symlinks=False
        )
        print(f"\n✅ Download Complete! Saved to: {file_path}")
        
        # Rename if needed (optional, keeping original name is fine usually)
        # But our script expects "z_image_turbo.safetensors" or we pass args
        target_name = CHECKPOINTS_DIR / "z_image_turbo.safetensors"
        if Path(file_path).name != "z_image_turbo.safetensors":
             # Copy or rename? Rename is better
             if target_name.exists():
                 target_name.unlink()
             Path(file_path).rename(target_name)
             print(f"Renamed to {target_name}")

    except Exception as e:
        print(f"❌ Failed to download: {e}")

if __name__ == "__main__":
    download_model()

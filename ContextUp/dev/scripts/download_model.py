
import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

# Paths
ROOT_DIR = Path(__file__).resolve().parents[3]
CHECKPOINTS_DIR = ROOT_DIR / "ContextUp" / "tools" / "ComfyUI" / "models" / "checkpoints"

MODEL_URL = "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/z_image_turbo_bf16.safetensors"
MODEL_FILENAME = "z_image_turbo.safetensors"

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    
    with open(dest_path, 'wb') as file, tqdm(
        desc=dest_path.name,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            size = file.write(data)
            bar.update(size)
    print("\nDownload Complete!")

if __name__ == "__main__":
    dest = CHECKPOINTS_DIR / MODEL_FILENAME
    if dest.exists():
        print(f"File already exists at {dest}")
    else:
        try:
            download_file(MODEL_URL, dest)
        except Exception as e:
            print(f"Failed to download: {e}")

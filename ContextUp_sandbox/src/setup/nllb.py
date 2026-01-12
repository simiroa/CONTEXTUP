"""
Setup Script: Download NLLB-200 model for ctranslate2.
"""
import os
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download

def download_model():
    # Target directory
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    model_dir = project_root / "resources" / "models" / "nllb-200-distilled-600M-int8"
    
    if model_dir.exists() and (model_dir / "model.bin").exists():
        print(f"Model already exists at {model_dir}")
        return

    print(f"Downloading model to {model_dir}...")
    
    # Download from HF
    snapshot_download(
        repo_id="JustFrederik/nllb-200-distilled-600M-ct2",
        local_dir=str(model_dir),
        local_dir_use_symlinks=False
    )
    
    # Check for tokenizer
    sp_model = model_dir / "sentencepiece.bpe.model"
    if not sp_model.exists():
        print("Tokenizer not found in converted repo. Downloading from original...")
        hf_hub_download(
            repo_id="facebook/nllb-200-distilled-600M",
            filename="sentencepiece.bpe.model",
            local_dir=str(model_dir)
        )
    
    print("Download complete.")

if __name__ == "__main__":
    download_model()


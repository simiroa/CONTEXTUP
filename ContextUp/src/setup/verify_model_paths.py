"""
Model Path Verification Script for ContextUp.
Checks if all AI model paths are correctly configured and accessible.
"""
import sys
from pathlib import Path

# Add src to path
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
sys.path.append(str(SRC_DIR))

try:
    from utils import paths
except ImportError:
    print("Error: Could not import utils.paths.")
    sys.exit(1)


def check_rembg():
    """Check Rembg (u2net) model."""
    model_file = paths.REMBG_DIR / "u2net.onnx"
    if model_file.exists():
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"✓ Rembg: {model_file} ({size_mb:.1f} MB)")
        return True
    print(f"✗ Rembg: {model_file} NOT FOUND")
    return False


def check_marigold():
    """Check Marigold models (HuggingFace cache structure)."""
    if not paths.MARIGOLD_DIR.exists():
        print(f"✗ Marigold: {paths.MARIGOLD_DIR} NOT FOUND")
        return False
    
    # Check for model folders (HF cache uses 'models--' prefix)
    model_folders = list(paths.MARIGOLD_DIR.glob("models--*"))
    if model_folders:
        print(f"✓ Marigold: {len(model_folders)} model(s) cached in {paths.MARIGOLD_DIR}")
        return True
    print(f"✗ Marigold: No cached models in {paths.MARIGOLD_DIR}")
    return False


def check_whisper():
    """Check Whisper models."""
    if not paths.WHISPER_DIR.exists():
        print(f"✗ Whisper: {paths.WHISPER_DIR} NOT FOUND")
        return False
    
    # Whisper downloads to models subdirs
    model_files = list(paths.WHISPER_DIR.rglob("*.bin"))
    if model_files:
        print(f"✓ Whisper: {len(model_files)} file(s) in {paths.WHISPER_DIR}")
        return True
    print(f"✗ Whisper: No model files in {paths.WHISPER_DIR}")
    return False


def check_demucs():
    """Check Demucs models."""
    if not paths.DEMUCS_DIR.exists():
        print(f"✗ Demucs: {paths.DEMUCS_DIR} NOT FOUND")
        return False
    
    # Demucs stores in hub/checkpoints
    checkpoints = list(paths.DEMUCS_DIR.rglob("*.th"))
    if checkpoints:
        print(f"✓ Demucs: {len(checkpoints)} checkpoint(s) in {paths.DEMUCS_DIR}")
        return True
    print(f"✗ Demucs: No checkpoints in {paths.DEMUCS_DIR}")
    return False


def check_rife():
    """Check RIFE binary and models."""
    bin_path = paths.BIN_DIR / "rife"
    exe_path = bin_path / "rife-ncnn-vulkan.exe"
    
    if not exe_path.exists():
        print(f"✗ RIFE: {exe_path} NOT FOUND")
        return False
    
    # Check for model folder
    model_folders = list(bin_path.glob("rife-v*"))
    if model_folders:
        print(f"✓ RIFE: Binary and {len(model_folders)} model folder(s) found")
        return True
    print(f"⚠ RIFE: Binary exists but no model folders found")
    return False


def check_upscale():
    """Check Real-ESRGAN and GFPGAN cache."""
    cache_dir = Path.home() / ".cache" / "realesrgan"
    if cache_dir.exists() and any(cache_dir.glob("*.pth")):
        print(f"✓ Upscale (Real-ESRGAN): Models cached in {cache_dir}")
        return True
    print(f"✗ Upscale: No models in {cache_dir}")
    return False


def check_ocr():
    """Check PaddleOCR models."""
    # PaddleOCR uses ~/.paddleocr by default
    paddle_dir = Path.home() / ".paddleocr"
    if paddle_dir.exists() and any(paddle_dir.rglob("*.onnx")):
        print(f"✓ OCR: Models in {paddle_dir}")
        return True
    
    # Also check local path
    if paths.OCR_DIR.exists() and any(paths.OCR_DIR.rglob("*")):
        print(f"✓ OCR: Models in {paths.OCR_DIR}")
        return True
    
    print(f"✗ OCR: No models found")
    return False


def main():
    print("=== ContextUp Model Path Verification ===\n")
    print(f"Project Root: {paths.PROJECT_ROOT}")
    print(f"Resources Dir: {paths.RESOURCES_DIR}\n")
    
    results = {
        "Rembg": check_rembg(),
        "Marigold": check_marigold(),
        "Whisper": check_whisper(),
        "Demucs": check_demucs(),
        "RIFE": check_rife(),
        "Upscale": check_upscale(),
        "OCR": check_ocr(),
    }
    
    print("\n=== Verification Summary ===")
    all_ok = True
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {name}: {status}")
        if not ok:
            all_ok = False
    
    if all_ok:
        print("\nAll model paths verified successfully!")
        return 0
    else:
        print("\nSome models are missing. Run 'download_models.py' to fix.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

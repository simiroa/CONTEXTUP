import sys
import importlib
import subprocess
from pathlib import Path

def check_import(module_name, pip_name=None):
    try:
        importlib.import_module(module_name)
        print(f"[OK] {module_name} imported successfully.")
        return True
    except ImportError:
        print(f"[FAIL] {module_name} not found. (pip install {pip_name or module_name})")
        return False
    except Exception as e:
        print(f"[ERROR] {module_name} failed to load: {e}")
        return False

def check_cuda():
    try:
        import torch
        if torch.cuda.is_available():
            print(f"[OK] CUDA is available. Device: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("[WARN] CUDA is NOT available. PyTorch is running on CPU.")
            return False
    except ImportError:
        print("[FAIL] PyTorch not installed, cannot check CUDA.")
        return False

def main():
    print("=== AI Environment Verification (Embedded) ===")
    print(f"Python Executable: {sys.executable}")
    print("-" * 40)
    
    # Critical AI Libs
    libs = [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("rembg", "rembg"),
        ("cv2", "opencv-python"),
        ("PIL", "Pillow"),
        ("numpy", "numpy"),
        ("google.generativeai", "google-generativeai"),
        ("pymeshlab", "pymeshlab"),
        ("requests", "requests")
    ]
    
    all_passed = True
    for mod, pip in libs:
        if not check_import(mod, pip):
            all_passed = False
            
    print("-" * 40)
    check_cuda()
    print("-" * 40)
    
    if all_passed:
        print("✅ Environment seems healthy for AI tasks.")
    else:
        print("❌ Some dependencies are missing or broken.")

if __name__ == "__main__":
    main()

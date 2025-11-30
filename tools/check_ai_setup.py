"""
GPU detection and AI model setup utility.
"""
import subprocess
import sys
from pathlib import Path

def check_gpu():
    """Check for NVIDIA GPU and CUDA availability."""
    print("=" * 60)
    print("GPU Detection")
    print("=" * 60)
    
    try:
        # Check NVIDIA GPU
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                              capture_output=True, text=True, check=True)
        
        gpu_info = result.stdout.strip().split('\n')
        print(f"\n✓ NVIDIA GPU detected:")
        for i, info in enumerate(gpu_info):
            name, vram = info.split(',')
            print(f"  GPU {i}: {name.strip()}")
            print(f"  VRAM: {vram.strip()}")
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n✗ No NVIDIA GPU detected or nvidia-smi not found")
        print("  AI features will run on CPU (very slow)")
        return False

def check_pytorch():
    """Check PyTorch installation and CUDA support."""
    print("\n" + "=" * 60)
    print("PyTorch & CUDA Check")
    print("=" * 60)
    
    try:
        import torch
        print(f"\n✓ PyTorch installed: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.version.cuda}")
            print(f"✓ CUDA devices: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  Device {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            print("✗ CUDA not available")
            print("  Install PyTorch with CUDA:")
            print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
            return False
    except ImportError:
        print("\n✗ PyTorch not installed")
        print("  Install with:")
        print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        return False

def check_dependencies():
    """Check AI model dependencies."""
    print("\n" + "=" * 60)
    print("Dependencies Check")
    print("=" * 60)
    
    required = {
        'transformers': 'Hugging Face Transformers',
        'diffusers': 'Diffusers (for SUPIR)',
        'opencv-python': 'OpenCV',
        'pillow': 'PIL',
        'einops': 'Einops (for video models)'
    }
    
    missing = []
    for package, name in required.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def estimate_storage():
    """Estimate storage requirements for AI models."""
    print("\n" + "=" * 60)
    print("Storage Requirements")
    print("=" * 60)
    
    models = {
        'RMBG-2.0 (Background Removal)': '1.5 GB',
        'RIFE (Frame Interpolation)': '50 MB',
        'SUPIR (Advanced Upscaling)': '13 GB',
        'FlashVSR (Video Upscaling)': '100 MB',
        'Temp files (processing)': '10 GB'
    }
    
    print("\nEstimated storage per feature:")
    for model, size in models.items():
        print(f"  {model}: {size}")
    
    print(f"\n  Total (all features): ~25 GB")
    print(f"  Recommended free space: 50 GB")

def main():
    print("\n" + "=" * 60)
    print("Phase 4: AI Tools Setup Check")
    print("=" * 60)
    
    gpu_ok = check_gpu()
    pytorch_ok = check_pytorch()
    deps_ok = check_dependencies()
    estimate_storage()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if gpu_ok and pytorch_ok and deps_ok:
        print("\n✓ System ready for AI features!")
        print("\nRecommended next steps:")
        print("1. Start with Background Removal (RMBG-2.0)")
        print("2. Test performance with your GPU")
        print("3. Expand to other features")
    else:
        print("\n⚠ Setup incomplete")
        print("\nRequired actions:")
        if not gpu_ok:
            print("- NVIDIA GPU recommended (will be slow on CPU)")
        if not pytorch_ok:
            print("- Install PyTorch with CUDA support")
        if not deps_ok:
            print("- Install missing dependencies")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

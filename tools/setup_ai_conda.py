"""
Conda environment setup for AI tools.
Run this script to create and configure the ai_tools environment.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run command and show progress."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print("\n" + "="*60)
    print("Phase 4: AI Tools - Conda Environment Setup")
    print("="*60)
    
    # Find conda executable
    conda_paths = [
        r"C:\Users\HG\miniconda3\Scripts\conda.exe",
        r"C:\ProgramData\miniconda3\Scripts\conda.exe",
        r"C:\Users\HG\anaconda3\Scripts\conda.exe",
        "conda"  # Try PATH
    ]
    
    conda_exe = None
    for path in conda_paths:
        try:
            result = subprocess.run([path, '--version'], check=True, capture_output=True, timeout=5)
            conda_exe = path
            print(f"✓ Conda found: {path}")
            print(f"  Version: {result.stdout.decode().strip()}")
            break
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    if not conda_exe:
        print("✗ Conda not found. Please install Miniconda or Anaconda first.")
        return False
    
    # Create environment
    if not run_command(
        [conda_exe, 'create', '-n', 'ai_tools', 'python=3.10', '-y'],
        "Step 1/4: Creating conda environment 'ai_tools'"
    ):
        print("\n⚠ Environment might already exist. Continuing...")
    
    # Install PyTorch with CUDA
    if not run_command(
        [conda_exe, 'install', '-n', 'ai_tools', 'pytorch', 'torchvision', 
         'pytorch-cuda=12.1', '-c', 'pytorch', '-c', 'nvidia', '-y'],
        "Step 2/4: Installing PyTorch with CUDA 12.1"
    ):
        return False
    
    # Get conda environment path
    result = subprocess.run(
        [conda_exe, 'env', 'list'], 
        capture_output=True, text=True
    )
    
    env_path = None
    for line in result.stdout.split('\n'):
        if 'ai_tools' in line:
            parts = line.split()
            if len(parts) >= 2:
                env_path = parts[-1]
                break
    
    if not env_path:
        print("✗ Could not find ai_tools environment path")
        return False
    
    print(f"\n✓ Environment path: {env_path}")
    
    # Install pip packages
    pip_exe = Path(env_path) / "Scripts" / "pip.exe"
    
    packages = [
        'transformers',
        'diffusers', 
        'accelerate',
        'opencv-python',
        'pillow',
        'einops',
        'timm',
        'safetensors',
        'rembg',
        'scikit-image',
        'basicsr',
        'gfpgan',
        'realesrgan',
        'onnxruntime-gpu'
    ]
    
    if not run_command(
        [str(pip_exe), 'install'] + packages,
        f"Step 3/4: Installing AI packages ({len(packages)} packages)"
    ):
        return False
    
    # Save environment info
    info_file = Path(__file__).parent.parent / "src" / "scripts" / "ai_standalone" / "env_info.txt"
    info_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(info_file, 'w') as f:
        f.write(f"CONDA_ENV_PATH={env_path}\n")
        f.write(f"PYTHON_EXE={env_path}\\python.exe\n")
        f.write(f"PIP_EXE={env_path}\\Scripts\\pip.exe\n")
    
    print(f"\n✓ Environment info saved to: {info_file}")
    
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Test the environment: conda activate ai_tools")
    print("2. Verify PyTorch: python -c \"import torch; print(torch.cuda.is_available())\"")
    print("3. Run background removal test")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

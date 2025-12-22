"""
Fix AI environment configuration.
"""
import sys
from pathlib import Path

def main():
    print("Fixing AI environment configuration...")
    
    # Create env_info.txt
    env_info_path = Path(__file__).parent.parent / "src" / "scripts" / "ai_standalone" / "env_info.txt"
    env_info_path.parent.mkdir(parents=True, exist_ok=True)
    
    import os
    
    # Try to find the environment dynamically
    possible_paths = [
        Path(os.path.expanduser("~")) / "miniconda3" / "envs" / "ai_tools",
        Path(os.path.expanduser("~")) / "anaconda3" / "envs" / "ai_tools",
        Path(os.environ.get("CONDA_PREFIX", "")),
    ]
    
    env_path = None
    for p in possible_paths:
        if (p / "python.exe").exists():
            env_path = p
            break
            
    if not env_path:
        env_path = possible_paths[0] # Default fallback
    
    env_path = str(env_path)
    
    content = f"""CONDA_ENV_PATH={env_path}
PYTHON_EXE={env_path}\\python.exe
PIP_EXE={env_path}\\Scripts\\pip.exe
"""
    
    with open(env_info_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Created: {env_info_path}")
    
    # Verify conda environment exists
    python_exe = Path(env_path) / "python.exe"
    if python_exe.exists():
        print(f"✓ Conda environment found: {env_path}")
    else:
        print(f"✗ Conda environment not found: {env_path}")
        print("  Run: python tools/setup_ai_conda.py")
        return 1
    
    print("\n✓ AI environment fixed!")
    print("\nNext steps:")
    print("1. Test: Right-click image → Remove Background (AI) → InSPyReNet")
    print("2. For RMBG-2.0/BiRefNet: Set up HuggingFace token (see docs/ai_troubleshooting.md)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
Setup HuggingFace authentication for gated models.
"""
import sys
import subprocess
from pathlib import Path

def main():
    print("="*60)
    print("HuggingFace Authentication Setup")
    print("="*60)
    
    # Get token from user
    print("\nTo use RMBG-2.0 and BiRefNet models, you need a HuggingFace token.")
    print("\nSteps:")
    print("1. Create account: https://huggingface.co/join")
    print("2. Create token: https://huggingface.co/settings/tokens")
    print("3. Request access:")
    print("   - https://huggingface.co/briaai/RMBG-2.0")
    print("   - https://huggingface.co/ZhengPeng7/BiRefNet")
    print("\n" + "="*60)
    
    token = input("\nEnter your HuggingFace token (or press Enter to skip): ").strip()
    
    if not token:
        print("\nSkipped. You can still use InSPyReNet without authentication.")
        return 0
    
    # Install huggingface-hub if needed
    pip_exe = r"C:\Users\HG\miniconda3\envs\ai_tools\Scripts\pip.exe"
    python_exe = r"C:\Users\HG\miniconda3\envs\ai_tools\python.exe"
    
    print("\nInstalling huggingface-hub...")
    subprocess.run([pip_exe, "install", "huggingface-hub"], check=True)
    
    # Login with token
    print("\nLogging in to HuggingFace...")
    result = subprocess.run(
        [python_exe, "-c", f"from huggingface_hub import login; login('{token}')"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Successfully authenticated!")
        print("\nYou can now use:")
        print("- RMBG-2.0 (Best balance)")
        print("- BiRefNet (Highest quality)")
        print("- InSPyReNet (Fastest)")
    else:
        print("✗ Authentication failed:")
        print(result.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

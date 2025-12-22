import os
from pathlib import Path
import sys

def patch_basicsr():
    """
    Patch basicsr/data/degradations.py to fix ImportError with recent torchvision.
    Change: 'from torchvision.transforms.functional_tensor import rgb_to_grayscale'
    To:     'from torchvision.transforms.functional import rgb_to_grayscale'
    """
    print("Checking basicsr for necessary patches...")
    
    # Locate site-packages
    site_packages = None
    for path in sys.path:
        if "site-packages" in path and os.path.isdir(path):
            if (Path(path) / "basicsr").exists():
                site_packages = Path(path)
                break
    
    if not site_packages:
        # Try finding it relative to this script if sys.path is weird
        # Assuming src/setup/patch_libs.py -> src/setup -> src -> .. -> tools/python/Lib/site-packages
        # But commonly we run with embedded python, so sys.path should be correct.
        print("Could not locate site-packages containing basicsr. Skipping patch.")
        return

    target_file = site_packages / "basicsr" / "data" / "degradations.py"
    
    if not target_file.exists():
        print(f"basicsr not found at {target_file}. Skipping.")
        return

    try:
        content = target_file.read_text(encoding="utf-8")
        
        # The specific line to change
        old_import = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
        new_import = "from torchvision.transforms.functional import rgb_to_grayscale"
        
        if old_import in content:
            print(f"Patching {target_file.name}...")
            new_content = content.replace(old_import, new_import)
            target_file.write_text(new_content, encoding="utf-8")
            print("✓ basicsr patched successfully.")
        elif new_import in content:
            print("✓ basicsr is already patched.")
        else:
            print("Warning: Could not find target import line in degradations.py. It might be a different version.")
            
    except Exception as e:
        print(f"Error patching basicsr: {e}")

def run_patches():
    """Run all library patches."""
    print("--- Running Library Patches ---")
    patch_basicsr()
    print("-------------------------------")

if __name__ == "__main__":
    run_patches()

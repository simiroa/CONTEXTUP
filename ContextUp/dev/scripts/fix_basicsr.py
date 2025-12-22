import os
import sys
from pathlib import Path
import site

def fix_basicsr():
    # Find site-packages
    site_packages = site.getsitepackages()
    basicsr_path = None
    
    for path in site_packages:
        p = Path(path) / "basicsr"
        if p.exists():
            basicsr_path = p
            break
            
    if not basicsr_path:
        # Try finding in current python env
        import basicsr
        basicsr_path = Path(basicsr.__file__).parent
        
    print(f"Found basicsr at: {basicsr_path}")
    
    # File to fix
    target_file = basicsr_path / "data" / "degradations.py"
    
    if not target_file.exists():
        print(f"Error: {target_file} not found")
        return False
        
    # Read content
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Apply fix
    old_import = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
    new_import = "from torchvision.transforms.functional import rgb_to_grayscale"
    
    if old_import in content:
        print("Applying fix...")
        new_content = content.replace(old_import, new_import)
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✓ Fix applied successfully")
        return True
    elif new_import in content:
        print("✓ Already fixed")
        return True
    else:
        print("⚠ Could not find import statement to fix")
        return False

if __name__ == "__main__":
    try:
        if fix_basicsr():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

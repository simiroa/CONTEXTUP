"""
Test external tools availability.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.external_tools import get_mayo, get_blender, get_quadwild, get_realesrgan

def test_mayo():
    try:
        path = get_mayo()
        print(f"✓ Mayo found: {path}")
        return True
    except FileNotFoundError as e:
        print(f"✗ Mayo not found: {e}")
        return False

def test_blender():
    try:
        path = get_blender()
        print(f"✓ Blender found: {path}")
        return True
    except FileNotFoundError as e:
        print(f"✗ Blender not found: {e}")
        return False

def test_quadwild():
    try:
        path = get_quadwild()
        print(f"✓ QuadWild found: {path}")
        return True
    except FileNotFoundError as e:
        print(f"✗ QuadWild not found: {e}")
        return False

def test_realesrgan():
    try:
        path = get_realesrgan()
        print(f"✓ RealESRGAN found: {path}")
        return True
    except FileNotFoundError as e:
        print(f"✗ RealESRGAN not found: {e}")
        return False

if __name__ == "__main__":
    print("Testing external tools availability...\n")
    
    results = [
        test_mayo(),
        test_blender(),
        test_quadwild(),
        test_realesrgan()
    ]
    
    print(f"\nResults: {sum(results)}/{len(results)} tools found")
    
    if all(results):
        print("✓ All tools are available!")
        sys.exit(0)
    else:
        print("✗ Some tools are missing")
        sys.exit(1)

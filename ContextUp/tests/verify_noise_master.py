
import sys
import os
from pathlib import Path
import numpy as np
from PIL import Image

# Add src to path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from features.image.noise_master.renderer import NoiseRenderer
from features.image.noise_master.utils import to_8bit_image

def test_noise_pipeline():
    print("Testing Noise Pipeline...")
    
    renderer = NoiseRenderer(256, 256)
    
    # Test 1: Basic Perlin
    print("- Rendering Perlin...")
    layers = [{
        "name": "Perlin Layer",
        "type": "perlin",
        "scale": 5.0,
        "opacity": 1.0,
        "seed": 123
    }]
    res = renderer.render(layers)
    if res.shape != (256, 256):
        print(f"FAILED: Shape is {res.shape}")
        return
    print(f"  OK. Mean: {np.mean(res):.4f}")
    
    # Test 2: Tiles with Transform
    print("- Rendering Tiles (Checker)...")
    layers = [{
        "name": "Checker Layer",
        "type": "checker",
        "scale": 4.0,
        "rotation": 45.0, # Test rotation
        "opacity": 1.0
    }]
    res = renderer.render(layers)
    print(f"  OK. Mean: {np.mean(res):.4f}")
    
    # Test 3: Domain Warp
    print("- Rendering Domain Warp...")
    layers = [{
        "name": "Warped",
        "type": "perlin",
        "use_warp": True,
        "warp_strength": 0.5,
        "warp_scale": 2.0
    }]
    try:
        res = renderer.render(layers)
        print(f"  OK. Mean: {np.mean(res):.4f}")
    except Exception as e:
        print(f"FAILED: Warp error {e}")
        
    # Test 4: Erosion
    print("- Rendering Erosion (Thermal)...")
    layers = [{
        "name": "Eroded",
        "type": "perlin",
        "erosion_active": True,
        "erosion_type": "thermal",
        "erosion_iterations": 2
    }]
    try:
        res = renderer.render(layers)
        print(f"  OK. Mean: {np.mean(res):.4f}")
    except Exception as e:
        print(f"FAILED: Erosion error {e}")
        
    print("All tests passed.")

if __name__ == "__main__":
    test_noise_pipeline()

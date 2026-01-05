
import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from features.image.noise_master.generators import generate
from features.image.noise_master.layers import LayerConfig

def test_5d_suite():
    print("Testing Ultimate 5D Seamless Suite...")
    
    # 1. Test Seamlessness with Rotation and Stretching
    cfg = LayerConfig(
        type='fbm',
        scale=5.0,
        ratio=1.0,  # 2:1 Stretch
        rotation=37.0,
        seamless_mode='torus_4d',
        evolution=42.0, # Some W value
        detail=1
    )
    
    print(f"- Generating 5D Noise (Scale={cfg.scale}, Ratio={cfg.ratio}, Rot={cfg.rotation})...")
    img = generate(cfg, 512, 512)
    
    diff_h = np.abs(img[:, 0] - img[:, -1]).mean()
    diff_v = np.abs(img[0, :] - img[-1, :]).mean()
    
    print(f"  Horizontal Edge Diff: {diff_h:.6f}")
    print(f"  Vertical Edge Diff:   {diff_v:.6f}")
    
    if diff_h < 1e-5 and diff_v < 1e-5:
        print("  Seamlessness: PASSED")
    else:
        print("  Seamlessness: FAILED")
        sys.exit(1)
        
    # 2. Test Evolution (W-slider)
    cfg2 = LayerConfig(
        type='fbm',
        scale=5.0,
        seamless_mode='torus_4d',
        evolution=43.0, # Different W
        detail=1
    )
    img2 = generate(cfg2, 512, 512)
    
    # Check if images are different
    pixel_diff = np.abs(img - img2).mean()
    print(f"- Evolution Pixel Diff (W=42 vs W=43): {pixel_diff:.6f}")
    if pixel_diff > 0.01:
        print("  Evolution: PASSED")
    else:
        print("  Evolution: FAILED (No change detected)")
        sys.exit(1)
        
    print("\nALL 5D TESTS PASSED.")

if __name__ == "__main__":
    test_5d_suite()

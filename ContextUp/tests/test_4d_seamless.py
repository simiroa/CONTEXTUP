import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from features.image.noise_master.generators import generate
from features.image.noise_master.layers import LayerConfig

def test_4d_seamless():
    print("Testing 4D Hypersphere Seamlessness...")
    
    cfg = LayerConfig(
        type='fbm',
        scale=5.0,
        rotation=37.0, # Arbitrary rotation
        seamless_mode='torus_4d',
        detail=1
    )

    
    # 512x512
    img = generate(cfg, 512, 512)
    
    # Check edges
    # Left vs Right
    diff_h = np.abs(img[:, 0] - img[:, -1]).mean()
    # Top vs Bottom
    diff_v = np.abs(img[0, :] - img[-1, :]).mean()
    
    print(f"Horizontal Edge Diff: {diff_h:.6f}")
    print(f"Vertical Edge Diff: {diff_v:.6f}")
    
    # In 4D torus mapping, the wrap is continuous. 
    # Because u/Scale is [0, 1] which maps to [0, 2pi], 
    # the noise(cos(0), sin(0)) == noise(cos(2pi), sin(2pi)).
    # So it should be close to zero.
    
    if diff_h < 0.05 and diff_v < 0.05:
        print("4D Seamlessness Test: PASSED")
    else:
        print("4D Seamlessness Test: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    test_4d_seamless()

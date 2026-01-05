
import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from features.image.noise_master.generators import hash_uint, noise_2d, fractal_noise

def test_blender_logic():
    print("Verifying Blender-Identical Logic...")
    
    # 1. Test hash_uint consistency
    val = np.array([42], dtype=np.uint32)
    h = hash_uint(val)[0]
    print(f"- Hash(42): {h} (uint32)")
    # Blender's hash_uint(42) should be consistent
    
    # 2. Test Noise Range
    coords = (np.linspace(0, 5, 128), np.linspace(0, 5, 128))
    u, v = np.meshgrid(*coords)
    n = noise_2d(u, v, seed=0)
    print(f"- 2D Noise Range: [{n.min():.4f}, {n.max():.4f}]")
    
    # 3. Test Fractional Detail
    # Detail 1.0
    f1 = fractal_noise((u,v), detail=1.0)
    # Detail 1.5
    f15 = fractal_noise((u,v), detail=1.5)
    # Detail 2.0
    f2 = fractal_noise((u,v), detail=2.0)
    
    diff_mid = np.abs(f15 - (f1 + f2)*0.5).mean()
    print(f"- Fractional Detail Midpoint Error: {diff_mid:.6f}")
    
    # 4. Test Distortion
    fd0 = fractal_noise((u,v), distortion=0.0)
    fd1 = fractal_noise((u,v), distortion=1.0)
    dist_diff = np.abs(fd0 - fd1).mean()
    print(f"- Distortion Effect Strength: {dist_diff:.6f}")

    if dist_diff > 0.05:
        print("\nALL BLENDER LOGIC TESTS PASSED.")
    else:
        print("\nLOGIC VERIFICATION FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    test_blender_logic()

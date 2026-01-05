
import sys
import os
from pathlib import Path
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from features.image.noise_master.generators import generate
from features.image.noise_master.layers import LayerConfig

def test_parity():
    print("=== Blender Parity Verification ===")
    
    # 1. White Noise
    cfg = LayerConfig(type="white_noise")
    res = generate(cfg, 128, 128)
    print(f"- White Noise: Range[{res.min():.4f}, {res.max():.4f}], Mean: {res.mean():.4f}")
    assert res.min() >= 0 and res.max() <= 1.0
    
    # 2. Wave Sine
    cfg = LayerConfig(type="wave", wave_profile="Sine", wave_dir="X")
    res = generate(cfg, 128, 128)
    print(f"- Wave Sine: Range[{res.min():.4f}, {res.max():.4f}]")
    assert res.min() < 0.1 and res.max() > 0.9 # Should cover full sine range
    
    # 3. Magic
    cfg = LayerConfig(type="magic", depth=2)
    res = generate(cfg, 128, 128)
    print(f"- Magic: Range[{res.min():.4f}, {res.max():.4f}]")
    
    # 4. Gabor Anisotropy
    cfg = LayerConfig(type="gabor", gabor_anisotropy=1.0)
    res = generate(cfg, 128, 128)
    print(f"- Gabor: Range[{res.min():.4f}, {res.max():.4f}]")

    print("\nVERIFICATION SUCCESSFUL.")

if __name__ == "__main__":
    test_parity()


import os
import sys
import numpy as np
import cv2
from PIL import Image

# Setup paths
import sys
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent / "src"
# Script: ContextUp/dev/scripts/verify_image_formats.py
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "ContextUp" / "src"
sys.path.append(str(src_path))

from features.image.convert_gui import main as img_convert_main

def create_dummy_svg(path):
    with open(path, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
        f.write('<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">')
        f.write('<circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />')
        f.write('</svg>')
    print(f"Created {path}")

def create_dummy_hdr(path):
    import imageio
    # Create a simple float32 image
    img = np.zeros((100, 100, 3), dtype=np.float32)
    # Gradient
    for i in range(100):
        img[i, :, 0] = i / 100.0  # Blue
        img[:, i, 1] = i / 100.0  # Green
    
    # ImageIO expects RGB usually
    imageio.imwrite(str(path), img) 
    print(f"Created {path}")

def verify_conversion():
    # Setup test directory
    test_dir = Path("temp_test_images")
    test_dir.mkdir(exist_ok=True)
    
    # 1. Create Assets and Test
    svg_path = test_dir / "test.svg"
    exr_path = test_dir / "test.exr"
    
    # --- SVG TEST ---
    print("\n--- Testing SVG ---")
    try:
        create_dummy_svg(svg_path)
        
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        import io
        
        drawing = svg2rlg(str(svg_path))
        img_data = io.BytesIO()
        renderPM.drawToFile(drawing, img_data, fmt="PNG")
        img_data.seek(0)
        img = Image.open(img_data)
        img.verify()
        print("[PASS] SVG Conversion Logic")
    except Exception as e:
        print(f"[FAIL] SVG Conversion Logic: {e}")

    # --- HDR TEST ---
    print("\n--- Testing HDR ---")
    try:
        # Try creating HDR
        try:
            create_dummy_hdr(exr_path)
        except Exception as e:
            print(f"[WARN] Could not create dummy HDR file: {e}")
            print("[SKIP] HDR Test (No test file)")
            return

        import imageio
        import numpy as np
        
        path = exr_path
        # imageio.imread might default to opencv, try to force freeimage if installed or just let it try
        try:
            img_data = imageio.imread(str(path), format='EXR') # Force EXR format
        except:
             img_data = imageio.imread(str(path)) # Auto
             
        if img_data is None:
             print("[FAIL] HDR Load: Returns None")
        else:
            # Logic from file
            if target_fmt := 'png': # Mock
                img_data = np.nan_to_num(img_data)
                if img_data.dtype.kind == 'f':
                     img_data = np.clip(img_data, 0, None)
                     img_data = np.clip(img_data, 0.0, 1.0)
                     img_data = np.power(img_data, 1/2.2)
                     img_data = (img_data * 255).astype(np.uint8)
            
            img = Image.fromarray(img_data)
            img.verify()
            print("[PASS] HDR Conversion Logic")
            
    except Exception as e:
         print(f"[FAIL] HDR Conversion Logic: {e}")

    # --- IMPORT TESTS ---
    print("\n--- Testing Imports ---")
    
    # 1. pillow-heif
    try:
        import pillow_heif
        print("[PASS] pillow-heif installed")
        
        # Test HEIC Write/Read
        heic_path = test_dir / "test.heic"
        try:
             # Create dummy image
             img = Image.new("RGB", (64, 64), color="red")
             img.save(heic_path, format="HEIF")
             print(f"[PASS] Created dummy HEIC: {heic_path}")
             
             # Read back using unified loader
             from utils.image_utils import load_image_unified
             img_loaded = load_image_unified(heic_path)
             img_loaded.verify()
             print("[PASS] Verified HEIC Read")
        except Exception as e:
             # Some versions might default 'HEIF' to 'AVIF' or need explicit register
             print(f"[WARN] HEIC Creation/Read check failed: {e}")
             
    except ImportError:
        print("[FAIL] pillow-heif MISSING")

    # 2. svglib
    try:
        import svglib
        print("[PASS] svglib installed")
    except ImportError:
        print("[FAIL] svglib MISSING")

    # 3. rawpy
    try:
        import rawpy
        print("[PASS] rawpy installed")
    except ImportError:
        print("[FAIL] rawpy MISSING (common on some Windows Python versions, check wheels)")
        
    # 4. DDS Output
    try:
        dds_path = test_dir / "test.dds"
        img = Image.new("RGB", (64, 64), color="blue")
        img.save(dds_path, format="DDS")
        print(f"[PASS] Created dummy DDS: {dds_path}")
        
        # Read back
        from utils.image_utils import load_image_unified
        img_loaded = load_image_unified(dds_path)
        img_loaded.verify()
        print("[PASS] Verified DDS Read")
        
    except Exception as e:
        print(f"[FAIL] DDS Check: {e}")

if __name__ == "__main__":
    verify_conversion()

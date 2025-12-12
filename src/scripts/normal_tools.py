"""
Normal Map and Simple PBR Tools.
Provides utilities for normal map manipulation and legacy PBR generation.
"""
import sys
from pathlib import Path
from tkinter import messagebox

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from core.logger import setup_logger
from utils.explorer import get_selection_from_explorer

logger = setup_logger("normal_tools")


def flip_normal_green(target_path, selection=None):
    """
    Flip Green channel of normal map (DirectX <-> OpenGL conversion).
    No GUI - instant execution with notification.
    """
    from PIL import Image
    import numpy as np
    
    try:
        # Get selection
        if selection is None:
            selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [Path(target_path)]
        
        count = 0
        for path in selection:
            path = Path(path)
            if not path.exists():
                continue
                
            logger.info(f"Flipping green channel: {path}")
            
            img = Image.open(path)
            
            # Ensure RGB/RGBA
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
            
            arr = np.array(img)
            
            # Flip Green channel (index 1)
            arr[:, :, 1] = 255 - arr[:, :, 1]
            
            result = Image.fromarray(arr)
            out_path = path.parent / f"{path.stem}_flipped{path.suffix}"
            result.save(out_path)
            
            logger.info(f"Saved: {out_path}")
            count += 1
        
        messagebox.showinfo("Complete", f"Flipped {count} normal map(s).\nOutput: *_flipped.*")
        
    except Exception as e:
        logger.error(f"Normal flip failed: {e}", exc_info=True)
        messagebox.showerror("Error", f"Failed to flip normal: {e}")


def generate_simple_normal_roughness(target_path, selection=None):
    """
    Generate simple normal and roughness maps using legacy algorithms.
    Uses Sobel filter for normal map, inverted grayscale for roughness.
    No GUI - instant execution with notification.
    """
    from PIL import Image
    import numpy as np
    
    try:
        # Optional: scipy for better results, fallback to numpy
        try:
            from scipy.ndimage import sobel
            use_scipy = True
        except ImportError:
            use_scipy = False
            logger.warning("scipy not found, using simple gradient method")
        
        # Get selection
        if selection is None:
            selection = get_selection_from_explorer(target_path)
        
        if not selection:
            selection = [Path(target_path)]
        
        count = 0
        for path in selection:
            path = Path(path)
            if not path.exists():
                continue
                
            logger.info(f"Generating normal/roughness: {path}")
            
            # Load as grayscale
            img = Image.open(path).convert('L')
            arr = np.array(img, dtype=np.float32) / 255.0
            
            # === Roughness (Inverted grayscale) ===
            roughness = (1.0 - arr) * 255
            roughness_img = Image.fromarray(roughness.astype(np.uint8))
            roughness_path = path.parent / f"{path.stem}_roughness.png"
            roughness_img.save(roughness_path)
            logger.info(f"Saved roughness: {roughness_path}")
            
            # === Normal Map ===
            if use_scipy:
                dx = sobel(arr, axis=1)
                dy = sobel(arr, axis=0)
            else:
                # Simple gradient fallback
                dx = np.gradient(arr, axis=1)
                dy = np.gradient(arr, axis=0)
            
            dz = np.ones_like(arr) * 0.5  # Adjust strength
            
            # Normalize
            length = np.sqrt(dx**2 + dy**2 + dz**2)
            length[length == 0] = 1  # Avoid division by zero
            
            nx = (dx / length + 1) * 0.5 * 255
            ny = (dy / length + 1) * 0.5 * 255
            nz = (dz / length + 1) * 0.5 * 255
            
            normal_arr = np.stack([nx, ny, nz], axis=-1).astype(np.uint8)
            normal_img = Image.fromarray(normal_arr, mode='RGB')
            normal_path = path.parent / f"{path.stem}_normal.png"
            normal_img.save(normal_path)
            logger.info(f"Saved normal: {normal_path}")
            
            count += 1
        
        messagebox.showinfo("Complete", f"Generated {count} set(s).\nOutput: *_normal.png, *_roughness.png")
        
    except Exception as e:
        logger.error(f"Simple PBR generation failed: {e}", exc_info=True)
        messagebox.showerror("Error", f"Failed to generate: {e}")


if __name__ == "__main__":
    # Test entry point
    if len(sys.argv) > 2:
        action = sys.argv[1]
        path = sys.argv[2]
        
        if action == "flip":
            flip_normal_green(path)
        elif action == "simple":
            generate_simple_normal_roughness(path)
    else:
        print("Usage: python normal_tools.py <flip|simple> <path>")

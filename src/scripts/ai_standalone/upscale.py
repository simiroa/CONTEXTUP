import sys
import argparse
import cv2
import numpy as np
import torch
import warnings
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")

# Add libs to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "libs"))

from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
from gfpgan import GFPGANer

def ensure_model(model_name):
    """Download model if not exists."""
    import urllib.request
    import os
    
    # Cache directory
    cache_dir = Path.home() / ".cache" / "realesrgan"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    model_url = {
        'RealESRGAN_x4plus': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
    }
    
    if model_name not in model_url:
        raise ValueError(f"Unknown model: {model_name}")
        
    model_path = cache_dir / f"{model_name}.pth"
    
    if not model_path.exists():
        print(f"Downloading {model_name}...")
        urllib.request.urlretrieve(model_url[model_name], str(model_path))
        print("Download complete.")
        
    return str(model_path)

def upscale_image(input_path, output_path, scale=4, face_enhance=False, tile_size=0):
    """
    Upscale image using Real-ESRGAN and optionally GFPGAN.
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    
    # Load Real-ESRGAN model
    model_name = 'RealESRGAN_x4plus'
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    
    # Get model path
    model_path = ensure_model(model_name)
    
    print(f"Loading Real-ESRGAN ({model_name})...")
    upsampler = RealESRGANer(
        scale=4,
        model_path=model_path,
        model=model,
        tile=tile_size,
        tile_pad=10,
        pre_pad=0,
        half=True if device.type == 'cuda' else False,
        device=device,
    )
    
    # Load GFPGAN if requested
    face_enhancer = None
    if face_enhance:
        print("Loading GFPGAN for face enhancement...")
        face_enhancer = GFPGANer(
            model_path='https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth',
            upscale=scale,
            arch='clean',
            channel_multiplier=2,
            bg_upsampler=upsampler
        )
    
    # Read image
    img = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise Exception(f"Failed to read image: {input_path}")
    
    print(f"Processing: {input_path}")
    
    try:
        if face_enhance:
            _, _, output = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
        else:
            output, _ = upsampler.enhance(img, outscale=scale)
        
        # Save output
        cv2.imwrite(str(output_path), output)
        print(f"✓ Success: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error during processing: {e}")
        # If OOM, try with tiling
        if "CUDA out of memory" in str(e) and tile_size == 0:
            print("CUDA OOM detected. Retrying with tiling...")
            try:
                # Re-init with tiling
                upsampler = RealESRGANer(
                    scale=4,
                    model_path=None,
                    model=model,
                    tile=512, # Try 512 tile size
                    tile_pad=10,
                    pre_pad=0,
                    half=True if device.type == 'cuda' else False,
                    device=device,
                )
                if face_enhance:
                    face_enhancer.bg_upsampler = upsampler
                
                if face_enhance:
                    _, _, output = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
                else:
                    output, _ = upsampler.enhance(img, outscale=scale)
                
                cv2.imwrite(str(output_path), output)
                print(f"✓ Success (with tiling): {output_path}")
                return True
            except Exception as e2:
                print(f"Retry failed: {e2}")
                raise e2
        else:
            raise e

def main():
    parser = argparse.ArgumentParser(description='Advanced AI Upscaling')
    parser.add_argument('input_path', help='Input image path')
    parser.add_argument('--output', help='Output path (optional)')
    parser.add_argument('--scale', type=float, default=4, help='Upscale factor (default: 4)')
    parser.add_argument('--face-enhance', action='store_true', help='Enable face enhancement')
    parser.add_argument('--tile', type=int, default=0, help='Tile size (0 for auto)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: Image not found: {input_path}")
        return 1
    
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = "_upscaled"
        if args.face_enhance:
            suffix += "_face"
        output_path = input_path.with_name(f"{input_path.stem}{suffix}.png")
    
    try:
        upscale_image(
            str(input_path),
            str(output_path),
            scale=args.scale,
            face_enhance=args.face_enhance,
            tile_size=args.tile
        )
        return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
